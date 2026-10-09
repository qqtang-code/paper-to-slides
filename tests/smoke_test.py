#!/usr/bin/env python3
"""Smoke-test the skill and its plugin packaging.

Runs with the standard library plus PyMuPDF, so it works locally and in CI:

    python3 -m venv .venv && .venv/bin/python -m pip install -r scripts/requirements.txt
    .venv/bin/python tests/smoke_test.py

Add --network to also fetch a small real paper and confirm the recorded hashes are stable.
"""

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
PLUGIN = ROOT / "plugins" / "paper-to-slides"
SKILL = PLUGIN / "skills" / "paper-to-slides"
MARKETPLACE = ROOT / ".claude-plugin" / "marketplace.json"
SCRIPTS = SKILL / "scripts"
EXAMPLE = SKILL / "examples" / "attention-oral-10min-original-figures"
EXAMPLE_PDF = EXAMPLE / "main.pdf"
MARKETPLACE_NAME = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")
PLACEHOLDER = re.compile(r"\bTODO\b|\bFIXME\b|<your[-_ ][^>]+>|YOUR_API_KEY")
SCANNED_SUFFIXES = {".json", ".md", ".mjs", ".cjs", ".js", ".ts", ".txt", ".yaml", ".yml", ".toml"}
ROOT_FILES = ["README.md", "LICENSE", "THIRD_PARTY_NOTICES.md", ".gitignore",
              ".claude-plugin/marketplace.json",
              "plugins/paper-to-slides/.zcode-plugin/plugin.json",
              "plugins/paper-to-slides/.claude-plugin/plugin.json"]
SKILL_FILES = ["SKILL.md", "LICENSE", "THIRD_PARTY_NOTICES.md", "agents/openai.yaml",
               "references/paper-reading.md", "references/storytelling.md",
               "references/visual-design.md", "references/verification.md",
               "assets/template/main.tex", "assets/template/config.tex",
               "assets/template/paper-slides.sty", "assets/template/refs.bib",
               "assets/template/strings.bib", "assets/template/BUILD.md",
               "assets/template/figures/synthetic-method.pdf",
               "assets/template/figures/synthetic-method.tex",
               "scripts/pdf_tools.py", "scripts/build_slides.py", "scripts/fetch_paper.py",
               "scripts/requirements.txt",
               "examples/attention-oral-10min-original-figures/main.tex",
               "examples/attention-oral-10min-original-figures/main.pdf",
               "examples/attention-oral-10min-original-figures/sources.md",
               "examples/attention-oral-10min-original-figures/speaker-script.md",
               "examples/attention-oral-10min-original-figures/verification.md",
               "examples/attention-oral-10min-original-figures/content-checks.json"]
ABSOLUTE_PATH = re.compile(r"/(?:Users|home)/[A-Za-z0-9._-]+/")
GENERATED = {"*.aux", "*.bbl", "*.blg", "*.log", "*.fls", "*.fdb_latexmk", "*.build-output.txt",
             "*.nav", "*.out", "*.snm", "*.toc", "*.xdv"}

try:
    # PyMuPDF >= 1.24 exposes `pymupdf`; the deprecated `fitz` alias warns on stdout there.
    import pymupdf as fitz
except ImportError:  # pragma: no cover - exercised only with PyMuPDF < 1.24
    try:
        import fitz
    except ImportError:
        fitz = None

failures = []


def check(label, condition, detail=""):
    if condition:
        print(f"  ok    {label}")
    else:
        print(f"  FAIL  {label}{': ' + detail if detail else ''}")
        failures.append(label)


def run(*args, expect=0, **kwargs):
    result = subprocess.run([sys.executable, *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, errors="replace", **kwargs)
    if expect is not None and result.returncode != expect:
        raise AssertionError(f"{' '.join(map(str, args))} exited {result.returncode}: "
                             f"{(result.stderr or result.stdout).strip()[:400]}")
    return result


def json_output(result, label):
    """Parse a helper's JSON, or record a diagnostic check failure instead of a traceback."""
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        check(f"{label} emits JSON", False,
              f"{exc}; stdout={result.stdout[:160]!r} stderr={result.stderr[:240]!r}")
        return None


def test_structure():
    print("structure")
    missing = [name for name in ROOT_FILES if not (ROOT / name).is_file()]
    missing += [name for name in SKILL_FILES if not (SKILL / name).is_file()]
    check("required files present", not missing, ", ".join(missing))
    front = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    check("SKILL.md has frontmatter", front.startswith("---\n") and "\n---\n" in front[4:])
    head = front.split("\n---\n", 1)[0]
    check("frontmatter declares name", re.search(r"^name:\s*paper-to-slides\s*$", head, re.M) is not None)
    description = re.search(r"^description:\s*(.+)$", head, re.M)
    check("frontmatter declares description", description is not None and len(description.group(1)) > 80)
    check("skill directory matches the declared name", SKILL.name == "paper-to-slides")
    leaked = []
    for path in sorted(ROOT.rglob("*")):
        if path.is_file() and path.suffix in SCANNED_SUFFIXES | {".tex", ".py", ".sty", ".bib"}:
            if ABSOLUTE_PATH.search(path.read_text(encoding="utf-8", errors="replace")):
                leaked.append(str(path.relative_to(ROOT)))
    check("no absolute home paths in text files", not leaked, ", ".join(leaked))


def test_links():
    print("markdown links")
    broken = []
    for path in sorted(ROOT.rglob("*.md")):
        for target in re.findall(r"\[[^\]]*\]\(([^)\s]+)\)", path.read_text(encoding="utf-8")):
            if target.startswith(("http://", "https://", "mailto:", "#")) or not target.split("#")[0]:
                continue
            if not (path.parent / target.split("#")[0]).resolve().exists():
                broken.append(f"{path.relative_to(ROOT)} -> {target}")
    check("every relative link resolves", not broken, "; ".join(broken))


def test_plugin_packaging():
    print("plugin and marketplace packaging")
    catalog = json.loads(MARKETPLACE.read_text(encoding="utf-8"))
    check("marketplace name is valid", bool(MARKETPLACE_NAME.match(catalog.get("name", ""))),
          str(catalog.get("name")))
    check("marketplace declares an owner", isinstance(catalog.get("owner"), dict)
          and bool(catalog["owner"].get("name")))
    entries = catalog.get("plugins")
    check("marketplace lists plugins", isinstance(entries, list) and bool(entries))
    for entry in entries or []:
        source = entry.get("source", "")
        # A relative source must stay inside the marketplace root; "./" would resolve to the root.
        check(f"{entry.get('name')}: source is a relative path",
              isinstance(source, str) and source.startswith("./") and source != "./", source)
        plugin_root = (ROOT / source).resolve() if isinstance(source, str) else None
        check(f"{entry.get('name')}: source exists inside the marketplace root",
              plugin_root is not None and plugin_root.is_dir()
              and ROOT.resolve() in plugin_root.parents)
        if plugin_root is None or not plugin_root.is_dir():
            continue
        manifests = {}
        for label, relative in (("zcode", ".zcode-plugin/plugin.json"),
                                ("claude", ".claude-plugin/plugin.json")):
            path = plugin_root / relative
            check(f"{entry.get('name')}: has a {label} manifest", path.is_file())
            if path.is_file():
                manifests[label] = json.loads(path.read_text(encoding="utf-8"))
        check(f"{entry.get('name')}: directory name matches the manifest name",
              all(m.get("name") == plugin_root.name for m in manifests.values()))
        check(f"{entry.get('name')}: listing name matches the manifest name",
              all(m.get("name") == entry.get("name") for m in manifests.values()))
        check(f"{entry.get('name')}: listing version matches the manifest version",
              all(m.get("version") == entry.get("version") for m in manifests.values()))
        for label, manifest in manifests.items():
            declared = manifest.get("skills")
            check(f"{entry.get('name')}: {label} manifest declares skills", bool(declared))
            check(f"{entry.get('name')}: {label} manifest uses a plugin-relative path",
                  isinstance(declared, str) and declared.startswith("./"), str(declared))
            if not (isinstance(declared, str) and declared.startswith("./")):
                continue
            directory = plugin_root / declared[2:]
            check(f"{entry.get('name')}: {label} skills directory exists", directory.is_dir())
            if directory.is_dir():
                found = sorted(p.parent.name for p in directory.glob("*/SKILL.md"))
                check(f"{entry.get('name')}: {label} finds the skill",
                      found == [entry.get("name")], ", ".join(found) or "none")
            check(f"{entry.get('name')}: no unresolved placeholders in the {label} manifest",
                  not PLACEHOLDER.search(json.dumps(manifest)))
        resources = [plugin_root / str(m.get("skills", "")).lstrip("./") for m in manifests.values()]
        scanned = []
        for resource in resources:
            for path in sorted(resource.rglob("*")) if resource.is_dir() else []:
                if path.is_file() and path.suffix in SCANNED_SUFFIXES:
                    if PLACEHOLDER.search(path.read_text(encoding="utf-8", errors="replace")):
                        scanned.append(str(path.relative_to(plugin_root)))
        check(f"{entry.get('name')}: no unresolved placeholders in declared resources",
              not scanned, ", ".join(scanned))
        check(f"{entry.get('name')}: no plugin source escapes the plugin root",
              all(plugin_root.resolve() in p.resolve().parents
                  for p in plugin_root.rglob("*") if p.is_file()))
    for name in ("LICENSE", "THIRD_PARTY_NOTICES.md"):
        check(f"{name} travels with the skill",
              (SKILL / name).read_bytes() == (ROOT / name).read_bytes())


def test_recorded_hashes():
    print("example hashes against content-checks.json")
    checks = json.loads((EXAMPLE / "content-checks.json").read_text(encoding="utf-8"))
    recorded = json_output(run(str(SCRIPTS / "pdf_tools.py"), "hash", str(EXAMPLE_PDF)), "hash")
    if recorded is None:
        return
    check("main.pdf matches pdf_sha256", recorded[0]["sha256"] == checks["pdf_sha256"], recorded[0]["sha256"])
    for name, entry in checks["original_assets"].items():
        result = json_output(run(str(SCRIPTS / "pdf_tools.py"), "hash",
                                 str(EXAMPLE / "figures" / name)), "hash")
        if result is None:
            return
        check(f"{name} unchanged", result[0]["sha256"] == entry["sha256"], result[0]["sha256"])


def test_pdf_tools(work):
    print("pdf_tools.py on the packaged example")
    state = json_output(run(str(SCRIPTS / "pdf_tools.py"), "check", str(EXAMPLE_PDF)), "check")
    if state is None:
        return
    check("check reports 15 pages", state["document"]["page_count"] == 15)
    check("check reports no rotated pages", state["document"]["rotated_pages"] == [])
    check("check reports no unreadable pages", state["document"]["pages_without_text"] == [])

    parts = work / "parts"
    result = run(str(SCRIPTS / "pdf_tools.py"), "extract", str(EXAMPLE_PDF), "--output",
                 str(parts / "paper.txt"), "--max-chars", "4000")
    written = sorted(parts.glob("paper-part*.txt"))
    check("extract splits a long document", len(written) > 1, f"{len(written)} part(s)")
    check("parts start at a page boundary",
          all(p.read_text(encoding="utf-8").startswith("===== PDF page") for p in written))
    check("extract reports the character count", "characters across" in result.stderr)

    preview = work / "previews"
    run(str(SCRIPTS / "pdf_tools.py"), "preview", str(EXAMPLE_PDF), "--pages", "1-2",
        "--output-dir", str(preview), "--dpi", "72")
    manifest = json.loads((preview / "manifest.json").read_text(encoding="utf-8"))
    check("preview renders the requested pages", len(manifest["pages"]) == 2)
    check("preview writes one PNG per page", len(list(preview.glob("page-*.png"))) == 2)

    crop = work / "crop.pdf"
    run(str(SCRIPTS / "pdf_tools.py"), "crop", str(EXAMPLE_PDF), "--page", "3",
        "--rect", "40", "20", "400", "200", "--output", str(crop))
    with fitz.open(crop) as doc:
        check("crop keeps the requested size",
              abs(doc[0].rect.width - 360) < 0.01 and abs(doc[0].rect.height - 180) < 0.01)
        check("crop keeps text as text", bool(doc[0].get_text().strip()))

    outside = run(str(SCRIPTS / "pdf_tools.py"), "crop", str(EXAMPLE_PDF), "--page", "3",
                  "--rect", "0", "0", "9000", "9000", "--output", str(work / "bad.pdf"), expect=None)
    check("crop rejects a rectangle outside the page", outside.returncode != 0)
    existing = run(str(SCRIPTS / "pdf_tools.py"), "extract", str(EXAMPLE_PDF), "--pages", "1",
                   "--output", str(work / "parts" / "paper-part01.txt"), expect=None)
    check("refuses to overwrite without --force", existing.returncode != 0)


def test_build_helper(work):
    print("build_slides.py")
    check("--help works", run(str(SCRIPTS / "build_slides.py"), "--help").returncode == 0)
    unused = run(str(SCRIPTS / "build_slides.py"), str(ROOT / "README.md"), expect=None)
    check("rejects a non-.tex main file", unused.returncode != 0)

    deck = work / "deck"
    deck.mkdir()
    template = SKILL / "assets" / "template"
    for name in ("main.tex", "config.tex", "paper-slides.sty", "refs.bib", "strings.bib"):
        (deck / name).write_bytes((template / name).read_bytes())
    (deck / "figures").mkdir()
    for asset in (template / "figures").iterdir():
        (deck / "figures" / asset.name).write_bytes(asset.read_bytes())

    engine = "tectonic" if subprocess.run(["which", "tectonic"], stdout=subprocess.DEVNULL,
                                          stderr=subprocess.DEVNULL).returncode == 0 else "pdflatex"
    report_path = deck / "build-report.json"
    run(str(SCRIPTS / "build_slides.py"), str(deck / "main.tex"), "--engine", engine,
        "--strict", "--report", str(report_path), expect=None)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    for key in ("errors", "missing_glyphs", "unresolved_references", "overflows",
                "underfull_boxes", "font_resolutions", "other_warnings"):
        check(f"report has a {key} list", isinstance(report.get(key), list))
    if engine == "tectonic":
        check("template builds cleanly with tectonic", report["passed"], json.dumps(report["errors"]))
        check("template records the engine", report.get("engine_version", "").startswith("Tectonic"))
        check("no @string warning after the bib fix",
              not any("@string" in warning for warning in report["other_warnings"]),
              json.dumps(report["other_warnings"]))
    else:
        check("missing-dependency path is reported",
              report["compiled"] is False and any("Missing dependencies" in e for e in report["errors"]))


def test_fetch_helper(work, network):
    print("fetch_paper.py")
    sys.path.insert(0, str(SCRIPTS))
    import fetch_paper

    check("parses an arXiv identifier", fetch_paper.parse_reference("1706.03762v7")["kind"] == "arxiv")
    check("parses an arXiv abs URL",
          fetch_paper.parse_reference("https://arxiv.org/abs/1706.03762")["identifier"] == "1706.03762")
    check("parses a versioned PDF URL",
          fetch_paper.parse_reference("https://arxiv.org/pdf/1706.03762v7")["identifier"] == "1706.03762v7")
    check("parses a direct PDF URL",
          fetch_paper.parse_reference("https://example.org/p.pdf")["kind"] == "pdf")
    for bad in ("not a paper", "https://arxiv.org/list/cs.CL/2401", "ftp://example.org/a.pdf"):
        rejected = False
        try:
            fetch_paper.parse_reference(bad)
        except ValueError:
            rejected = True
        check(f"rejects {bad!r}", rejected)

    check("rejects an absolute member path", not fetch_paper.lexically_safe("/etc/passwd"))
    check("rejects a traversal member", not fetch_paper.lexically_safe("../../etc/passwd"))
    check("accepts a nested member", fetch_paper.lexically_safe("figures/model.png"))
    check("contains resolution inside the root", fetch_paper.inside("/tmp/root", "a/b"))
    check("rejects resolution outside the root", not fetch_paper.inside("/tmp/root", "../b"))

    import io
    import tarfile
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        for name in ("paper.tex", "../escape.tex", "/absolute.tex"):
            info = tarfile.TarInfo(name)
            info.size = 4
            archive.addfile(info, io.BytesIO(b"text"))
    archive_path = work / "source.tar.gz"
    archive_path.write_bytes(buffer.getvalue())
    summary = fetch_paper.archive_members(archive_path, buffer.getvalue())
    check("archive audit counts safe files", summary["files"] == 1, json.dumps(summary))
    check("archive audit rejects traversal and absolute paths", len(summary["rejected"]) == 2)

    if network:
        target = work / "fetch"
        run(str(SCRIPTS / "fetch_paper.py"), "1706.03762v7", "--dir", str(target), "--extract")
        record = json.loads((target / "provenance.json").read_text(encoding="utf-8"))
        check("resolves version 7", record["version"] == "7")
        check("records both artifacts", len(record["artifacts"]) == 2)
        check("records the title", "Attention" in record["title"])
        check("audits the source archive", record["source_archive"]["rejected"] == [])
    else:
        print("  skip  network fetch (pass --network to run it)")


def test_no_generated_artifacts():
    print("repository hygiene")
    stray = []
    for pattern in GENERATED:
        for path in ROOT.rglob(pattern):
            if path.is_file() and ".venv" not in path.parts:
                stray.append(str(path.relative_to(ROOT)))
    check("no build artifacts are committed", not stray, ", ".join(stray))


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--network", action="store_true",
                        help="Also fetch arXiv:1706.03762v7 and check its recorded hashes")
    args = parser.parse_args()
    if fitz is None:
        print("PyMuPDF is required: python3 -m pip install -r scripts/requirements.txt")
        return 2
    with tempfile.TemporaryDirectory() as directory:
        work = Path(directory)
        test_structure()
        test_links()
        test_plugin_packaging()
        test_recorded_hashes()
        test_pdf_tools(work)
        test_build_helper(work)
        test_fetch_helper(work, args.network)
        test_no_generated_artifacts()
    print()
    if failures:
        print(f"{len(failures)} check(s) failed:")
        for name in failures:
            print(f"  - {name}")
        return 1
    print("all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())