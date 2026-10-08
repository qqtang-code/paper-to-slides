#!/usr/bin/env python3
"""Build a Beamer entrypoint with latexmk or tectonic and summarize actionable diagnostics."""

import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

FONT_REQUEST = re.compile(r'Requested font "([^"]+)"')
FONT_RESOLUTION = re.compile(r"^\s*->\s*(\S+)\s*$")
OVERFULL_MAGNITUDE = re.compile(r"\(([0-9.]+)pt too (?:wide|high)\)")
MISSING_CHARACTER = re.compile(r"Missing character: There is no .*?\(U\+([0-9A-Fa-f]{4,6})\)")
UNREPRESENTABLE = re.compile(r"could not represent character .*?\(0x([0-9A-Fa-f]{4,6})\).*?font\s+\"?\[?([^\"\];]+)")
FONT_IN_LOG = re.compile(r"Missing character:.*?in font\s+\"?\[?([^\"\];]+)")
TECTONIC_PREFIX = re.compile(r"^warning:\s*\S+:\d+:\s*")
STRING_MACRO = re.compile(r"^\s*@string\s*\{", re.I | re.M)
# Tectonic echoes a summary line after listing the warnings themselves, repeats each font
# lookup on stderr, emits a bare file:line header for those records, and indents the advice
# that follows an unrepresentable-character warning.
FILTERED_WARNING = re.compile(
    r"^\s*warning:\s*(?:warnings were issued by the TeX engine"
    r"|choose a different font"
    r"|you may need to load"
    r"|\S+:\d+:\s*(?:->\s*\S+)?\s*$)")


def font_key(name):
    """Reduce a font identifier such as ``[FiraSans-Regular.otf]/OT:script=latn`` to a bare name."""
    name = name.split("]")[0].lstrip("[")
    name = re.split(r"[/:]", name)[0].strip()
    for suffix in (".otf", ".ttf", ".pfb", ".ttc"):
        if name.lower().endswith(suffix):
            name = name[: -len(suffix)]
    return name.lower()


def glyph_key(line):
    """Canonical form so the log entry and the stderr warning for one glyph collapse."""
    unrepr = UNREPRESENTABLE.search(line)
    if unrepr:
        return f"Missing character: U+{unrepr.group(1).upper()} in font {font_key(unrepr.group(2)) or unrepr.group(2)}"
    char = MISSING_CHARACTER.search(line)
    match = FONT_IN_LOG.search(line)
    if char and match:
        return f"Missing character: U+{char.group(1).upper()} in font {font_key(match.group(1)) or match.group(1)}"
    return line.strip()


def add(categories, key, message):
    if message not in categories[key]:
        categories[key].append(message)


def diagnostics(text, categories, overfull_tolerance):
    lines = text.splitlines()
    for index, line in enumerate(lines):
        # Warnings can wrap across lines, notably long citation keys.
        window = " ".join(lines[index:index + 4])
        # Tectonic repeats engine messages on stderr with a file:line prefix; strip it so the
        # two copies of one defect collapse instead of inflating the report.
        bare = TECTONIC_PREFIX.sub("", line.strip())
        if line.startswith("!") or line.startswith("error: ") or re.search(r"(?:^|:)\d+:\s*(?:.*?Error:|Undefined control sequence|Missing |Extra |Emergency stop)", line) or re.search(r"(?:LaTeX|Package \S+) Error:|Emergency stop|Fatal error occurred|I couldn't open|unrecoverable error", line):
            add(categories, "errors", bare)
        elif "Missing character:" in line or UNREPRESENTABLE.search(line):
            add(categories, "missing_glyphs", glyph_key(line))
        elif ("Warning" in line and re.search(r"(?:Citation|Reference).*?undefined|undefined (?:references|citations)|Rerun to get|Label\(s\) may have changed", window, re.I)) or "I didn't find a database entry" in line:
            add(categories, "unresolved_references", bare if "undefined" in line.lower() else window.strip())
        elif re.search(r"Overfull \\[hv]box", line):
            magnitude = OVERFULL_MAGNITUDE.search(line)
            if magnitude and float(magnitude.group(1)) < overfull_tolerance:
                continue
            add(categories, "overflows", bare)
        elif re.search(r"Underfull \\[hv]box", line):
            add(categories, "underfull_boxes", bare)
        elif FONT_REQUEST.search(line):
            # Tectonic records each font lookup and its resolution on two lines.
            requested = FONT_REQUEST.search(line).group(1)
            resolved = ""
            if index + 1 < len(lines):
                match = FONT_RESOLUTION.match(lines[index + 1])
                if match:
                    resolved = match.group(1)
            if resolved and font_key(requested) != font_key(resolved):
                add(categories, "other_warnings",
                    f"Font substitution: {font_key(requested) or requested} -> {font_key(resolved) or resolved}")
            else:
                add(categories, "font_resolutions", font_key(requested) or requested)
        elif FILTERED_WARNING.search(line) or line.strip() == "->":
            continue
        elif "Warning" in line or line.startswith("warning:"):
            add(categories, "other_warnings", bare)
    return categories


def string_macros_bibtex_warning(main_dir):
    """Tectonic's BibTeX drops inter-word spaces when it expands @string macros."""
    files = sorted(p.name for p in main_dir.glob("*.bib") if STRING_MACRO.search(p.read_text(encoding="utf-8", errors="replace")))
    if not files:
        return None
    return ("Tectonic expands @string macros without preserving inter-word spaces; "
            f"write literal values in {', '.join(files)} and confirm the rendered bibliography")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("main", type=Path, help="Main .tex path; builds in its parent directory")
    parser.add_argument("--engine", choices=("pdflatex", "xelatex", "tectonic"), default="pdflatex",
                        help="Tectonic needs no TeX Live and runs BibTeX itself")
    parser.add_argument("--strict", action="store_true", help="Fail on missing glyphs, unresolved references, or box overflows")
    parser.add_argument("--report", type=Path, help="JSON path; default: main's directory/build-report.json")
    parser.add_argument("--timeout", type=int, default=180, help="Maximum build seconds; default: 180")
    parser.add_argument("--overfull-tolerance", type=float, default=0.0, metavar="PT",
                        help="Ignore overfull boxes smaller than this many points; default: 0")
    args = parser.parse_args()
    main_path = args.main.resolve()
    if main_path.suffix != ".tex" or not main_path.is_file():
        parser.error(f"Main LaTeX file does not exist or is not .tex: {main_path}")
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    if args.overfull_tolerance < 0:
        parser.error("--overfull-tolerance must not be negative")
    report_path = args.report.resolve() if args.report else main_path.parent / "build-report.json"
    pdf_path = main_path.with_suffix(".pdf")
    log_path = main_path.with_suffix(".log")
    aux_path = main_path.with_suffix(".aux")
    output_path = main_path.with_suffix(".build-output.txt")
    if report_path in (main_path, pdf_path, log_path, output_path, main_path.with_suffix(".bib")) or report_path.suffix != ".json":
        parser.error("--report must be a separate .json file")
    categories = {key: [] for key in ("errors", "missing_glyphs", "unresolved_references",
                                      "overflows", "underfull_boxes", "font_resolutions", "other_warnings")}
    report = {"main": main_path.name, "engine": args.engine, "strict": args.strict,
              "overfull_tolerance": args.overfull_tolerance,
              "compiled": False, "passed": False, "returncode": None,
              "pdf": pdf_path.name, "log": log_path.name, "build_output": output_path.name}
    report.update(categories)

    if args.engine == "tectonic":
        tools = ["tectonic"]
    else:
        tools = ["latexmk", args.engine, "bibtex"]
    missing = [name for name in tools if shutil.which(name) is None]
    if missing:
        report["errors"].append("Missing dependencies: " + ", ".join(missing))
    else:
        report["engine_version"] = tool_version(args.engine)
        if args.engine == "tectonic":
            # --untrusted disables shell escape; tectonic runs BibTeX itself.
            command = ["tectonic", "--untrusted", "--keep-logs", "./" + main_path.name]
        else:
            mode = "-pdf" if args.engine == "pdflatex" else "-xelatex"
            command = ["latexmk", "-norc", mode, "-g", "-bibtex", "-interaction=nonstopmode",
                       "-halt-on-error", "-file-line-error",
                       f"-{args.engine}={args.engine} -no-shell-escape %O %S", "./" + main_path.name]
        report["command"] = command
        # Both engines are asked for a fresh pass; drop the previous run's outputs.
        log_path.unlink(missing_ok=True)
        aux_path.unlink(missing_ok=True)
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
            report["errors"].append(f"Cannot start {command[0]}: {exc}")
        output_path.write_text(output, encoding="utf-8")
        log = log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else ""
        # Inspect the final log plus, for tectonic, the engine's own warning stream.
        diagnostics(log, report, args.overfull_tolerance)
        if args.engine == "tectonic":
            diagnostics(output, report, args.overfull_tolerance)
            warning = string_macros_bibtex_warning(main_path.parent)
            if warning:
                report["other_warnings"].append(warning)
        report["compiled"] = report["returncode"] == 0 and pdf_path.is_file() and pdf_path.stat().st_size > 0
        if not report["compiled"] and not report["errors"]:
            report["errors"].append(f"{command[0]} failed (exit {report['returncode']}); see {output_path.name}")
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


def tool_version(engine):
    command = ["tectonic", "--version"] if engine == "tectonic" else [engine, "--version"]
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, errors="replace", timeout=30)
        return result.stdout.strip().splitlines()[0] if result.stdout.strip() else engine
    except (OSError, subprocess.TimeoutExpired, IndexError):
        return engine


if __name__ == "__main__":
    sys.exit(main())