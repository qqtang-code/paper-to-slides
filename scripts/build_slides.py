#!/usr/bin/env python3
"""Build a Beamer entrypoint with latexmk and summarize actionable diagnostics."""

import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys


def diagnostics(log):
    categories = {key: [] for key in ("errors", "missing_glyphs", "unresolved_references", "overflows", "other_warnings")}
    lines = log.splitlines()
    for index, line in enumerate(lines):
        # Warnings can wrap across lines, notably long citation keys.
        window = " ".join(lines[index:index + 4])
        if line.startswith("!") or re.search(r"(?:^|:)\d+:\s*(?:.*?Error:|Undefined control sequence|Missing |Extra |Emergency stop)", line) or re.search(r"(?:LaTeX|Package \S+) Error:|Emergency stop|Fatal error occurred|I couldn't open", line):
            key = "errors"
        elif "Missing character:" in line:
            key = "missing_glyphs"
        elif ("Warning" in line and re.search(r"(?:Citation|Reference).*?undefined|undefined (?:references|citations)|Rerun to get|Label\(s\) may have changed", window, re.I)) or "I didn't find a database entry" in line:
            key = "unresolved_references"
        elif re.search(r"Overfull \\[hv]box", line):
            key = "overflows"
        elif "Warning" in line:
            key = "other_warnings"
        else:
            continue
        message = line.strip()
        if key == "unresolved_references" and "undefined" not in line.lower():
            message = window.strip()
        if message not in categories[key]:
            categories[key].append(message)
    return categories


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("main", type=Path, help="Main .tex path; builds in its parent directory")
    parser.add_argument("--engine", choices=("pdflatex", "xelatex"), default="pdflatex")
    parser.add_argument("--strict", action="store_true", help="Fail on missing glyphs, unresolved references, or box overflows")
    parser.add_argument("--report", type=Path, help="JSON path; default: main's directory/build-report.json")
    parser.add_argument("--timeout", type=int, default=180, help="Maximum build seconds; default: 180")
    args = parser.parse_args()
    main_path = args.main.resolve()
    if main_path.suffix != ".tex" or not main_path.is_file():
        parser.error(f"Main LaTeX file does not exist or is not .tex: {main_path}")
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    report_path = args.report.resolve() if args.report else main_path.parent / "build-report.json"
    pdf_path = main_path.with_suffix(".pdf")
    log_path = main_path.with_suffix(".log")
    output_path = main_path.with_suffix(".build-output.txt")
    if report_path in (main_path, pdf_path, log_path, output_path, main_path.with_suffix(".bib")) or report_path.suffix != ".json":
        parser.error("--report must be a separate .json file")
    report = {"main": main_path.name, "engine": args.engine, "strict": args.strict,
              "compiled": False, "passed": False, "returncode": None,
              "pdf": pdf_path.name, "log": log_path.name, "build_output": output_path.name,
              **diagnostics("")}
    missing = [name for name in ("latexmk", args.engine, "bibtex") if shutil.which(name) is None]
    if missing:
        report["errors"].append("Missing dependencies: " + ", ".join(missing))
    else:
        mode = "-pdf" if args.engine == "pdflatex" else "-xelatex"
        command = ["latexmk", "-norc", mode, "-g", "-bibtex", "-interaction=nonstopmode",
                   "-halt-on-error", "-file-line-error",
                   f"-{args.engine}={args.engine} -no-shell-escape %O %S", "./" + main_path.name]
        report["command"] = command
        # -g forces a fresh pass; discard only the previous generated diagnostic log.
        log_path.unlink(missing_ok=True)
        output = ""
        try:
            result = subprocess.run(command, cwd=main_path.parent, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, text=True, errors="replace", timeout=args.timeout)
            output = result.stdout
            report["returncode"] = result.returncode
        except subprocess.TimeoutExpired as exc:
            output = exc.stdout or ""
            if isinstance(output, bytes):
                output = output.decode("utf-8", errors="replace")
            report["errors"].append(f"Build timed out after {args.timeout} seconds")
        except OSError as exc:
            report["errors"].append(f"Cannot start latexmk: {exc}")
        output_path.write_text(output, encoding="utf-8")
        log = log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else ""
        # Inspect the final TeX log, not transient unresolved citations from earlier passes.
        found = diagnostics(log)
        for key, values in found.items():
            report[key].extend(values)
        report["compiled"] = report["returncode"] == 0 and pdf_path.is_file() and pdf_path.stat().st_size > 0
        if not report["compiled"] and not report["errors"]:
            report["errors"].append(f"latexmk failed (exit {report['returncode']}); see {output_path.name}")
            report["output_tail"] = output.splitlines()[-25:]
    blockers = ("errors", "missing_glyphs", "unresolved_references", "overflows") if args.strict else ("errors",)
    report["passed"] = report["compiled"] and not any(report[key] for key in blockers)
    try:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except OSError as exc:
        parser.exit(2, f"Cannot write build report: {exc}\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
