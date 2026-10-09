#!/usr/bin/env python3
"""Build the distributable skill archive with layout and self-containment checks.

    python3 tools/package_skill.py                    # dist/paper-to-slides-<version>.zip
    python3 tools/package_skill.py --max-bytes 52428800

Marketplaces expect a zip whose root holds SKILL.md with valid frontmatter, with the
supporting directories beside it. This tool assembles that archive from the skill
directory, refuses anything that would make the copy incomplete, and reports the size
and SHA-256 so an upload can be identified later.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import zipfile

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SKILL = ROOT / "plugins" / "paper-to-slides" / "skills" / "paper-to-slides"
DEFAULT_MANIFEST = ROOT / "plugins" / "paper-to-slides" / ".zcode-plugin" / "plugin.json"
REQUIRED_DIRS = ("references", "assets", "scripts")
EXCLUDED_DIRS = {".git", ".venv", "__pycache__", "previews", "dist", ".github", "tests"}
EXCLUDED_SUFFIXES = {".aux", ".bbl", ".blg", ".fdb_latexmk", ".fls", ".log", ".nav", ".out",
                     ".snm", ".synctex.gz", ".toc", ".vrb", ".xdv", ".pyc", ".pyo",
                     ".build-output.txt", ".swp"}
EXCLUDED_NAMES = {".DS_Store", ".gitignore", ".gitattributes"}
MARKDOWN_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")


def fail(message):
    print(f"error: {message}", file=sys.stderr)
    return 2


def frontmatter(path):
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n") or "\n---\n" not in text[4:]:
        return None
    return text.split("\n---\n", 1)[0]


def collect(skill_dir):
    files, skipped = [], []
    for path in sorted(skill_dir.rglob("*")):
        relative = path.relative_to(skill_dir)
        if any(part in EXCLUDED_DIRS for part in relative.parts):
            continue
        if not path.is_file():
            continue
        if path.name in EXCLUDED_NAMES or path.suffix in EXCLUDED_SUFFIXES:
            skipped.append((str(relative), "build or OS artifact"))
        else:
            files.append(path)
    return files, skipped


def check_layout(skill_dir, files):
    """Every requirement a marketplace validates and the archive must satisfy to be usable."""
    problems = []
    front = frontmatter(skill_dir / "SKILL.md") if (skill_dir / "SKILL.md").is_file() else None
    if front is None:
        problems.append("SKILL.md is missing at the archive root or has no frontmatter")
    else:
        for field in ("name", "description"):
            if re.search(rf"^{field}:\s*\S", front, re.M) is None:
                problems.append(f"SKILL.md frontmatter has no {field}")
    for directory in REQUIRED_DIRS:
        if not (skill_dir / directory).is_dir():
            problems.append(f"missing directory SKILL.md relies on: {directory}/")
    packaged = {str(path.relative_to(skill_dir)) for path in files}
    for name in ("SKILL.md", "LICENSE", "THIRD_PARTY_NOTICES.md"):
        if name not in packaged:
            problems.append(f"{name} is not in the archive")
    # A link that leaves the skill directory still resolves in the repository but breaks
    # in an installed copy, which is the copy a marketplace ships.
    for path in files:
        if path.suffix != ".md":
            continue
        for target in MARKDOWN_LINK.findall(path.read_text(encoding="utf-8")):
            if target.startswith(("http://", "https://", "mailto:", "#")) or not target.split("#")[0]:
                continue
            resolved = (path.parent / target.split("#")[0]).resolve()
            if skill_dir.resolve() not in resolved.parents or not resolved.exists():
                problems.append(f"{path.relative_to(skill_dir)} links outside the archive: {target}")
    return problems


def build(skill_dir, manifest, output, max_bytes):
    name = manifest.get("name") or skill_dir.name
    version = manifest.get("version") or "0.0.0"
    files, skipped = collect(skill_dir)
    problems = check_layout(skill_dir, files)
    if problems:
        for problem in problems:
            print(f"error: {problem}", file=sys.stderr)
        return 2
    total = sum(path.stat().st_size for path in files)
    if total > max_bytes:
        return fail(f"uncompressed size {total} bytes exceeds the {max_bytes} byte limit")
    archive = output / f"{name}-{version}.zip"
    output.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for path in files:
            bundle.write(path, path.relative_to(skill_dir).as_posix())
    if archive.stat().st_size > max_bytes:
        return fail(f"archive size {archive.stat().st_size} bytes exceeds the {max_bytes} byte limit")
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    print(json.dumps({"archive": str(archive), "name": name, "version": version,
                      "files": len(files), "uncompressed_bytes": total,
                      "bytes": archive.stat().st_size, "sha256": digest,
                      "excluded": [{"path": path, "reason": reason} for path, reason in skipped],
                      "layout_root": "SKILL.md", "max_bytes": max_bytes},
                     ensure_ascii=False, indent=2))
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--skill-dir", type=Path, default=DEFAULT_SKILL)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST,
                        help="Plugin manifest that supplies the name and version")
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    parser.add_argument("--max-bytes", type=int, default=50 * 1024 * 1024,
                        help="Upload limit to respect; default: 50 MiB")
    args = parser.parse_args()
    skill_dir = args.skill_dir.resolve()
    if not skill_dir.is_dir():
        return fail(f"not a skill directory: {skill_dir}")
    if not args.manifest.is_file():
        return fail(f"no plugin manifest: {args.manifest}")
    return build(skill_dir, json.loads(args.manifest.read_text(encoding="utf-8")),
                 args.output.resolve(), args.max_bytes)


if __name__ == "__main__":
    sys.exit(main())