#!/usr/bin/env python3
"""Extract PDF text, render pages, crop a page without rasterizing it, or report tooling state."""

import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys

REQUIREMENTS_HINT = "Run: python3 -m pip install -r {requirements}"


def requirements_path():
    return Path(__file__).resolve().parent / "requirements.txt"


def page_numbers(spec, count):
    if spec == "all":
        return list(range(count))
    pages = set()
    try:
        for part in spec.split(","):
            ends = part.strip().split("-")
            if len(ends) == 1:
                start = end = int(ends[0])
            elif len(ends) == 2:
                start, end = map(int, ends)
            else:
                raise ValueError
            if not 1 <= start <= end <= count:
                raise ValueError
            pages.update(range(start - 1, end))
    except ValueError as exc:
        raise ValueError(f"Invalid pages {spec!r}; use 1-based pages within 1..{count}, e.g. 1,3-5") from exc
    return sorted(pages)


def check_outputs(paths, source, force):
    for path in paths:
        if path.resolve() == source.resolve():
            raise ValueError("Output must not overwrite the input PDF")
        if path.exists() and not force:
            raise ValueError(f"Output exists: {path}; use --force to replace it")


def group_pages(chunks, max_chars):
    """Split page blocks into parts that stay under max_chars without cutting a page."""
    parts, current = [], []
    for chunk in chunks:
        if current and sum(len(c) for c in current) + len(chunk) > max_chars:
            parts.append(current)
            current = []
        current.append(chunk)
    if current:
        parts.append(current)
    return ["\n".join(part) for part in parts]


def file_hash(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return {"file": str(path), "bytes": path.stat().st_size, "sha256": digest.hexdigest()}


def tool_state():
    state = {"python": sys.version.split()[0], "pymupdf": None,
             "engines": {}, "note": "Tectonic needs no TeX Live and runs BibTeX itself."}
    try:
        import pymupdf as fitz
    except ImportError:
        try:
            import fitz
        except ImportError:
            fitz = None
    if fitz is None:
        state["note"] = REQUIREMENTS_HINT.format(requirements=requirements_path())
    else:
        state["pymupdf"] = fitz.__version__
    for name in ("latexmk", "pdflatex", "xelatex", "tectonic", "bibtex"):
        path = shutil.which(name)
        if not path:
            state["engines"][name] = None
            continue
        version = name
        try:
            result = subprocess.run([name, "--version"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    text=True, errors="replace", timeout=30)
            if result.stdout.strip():
                version = result.stdout.strip().splitlines()[0]
        except (OSError, subprocess.TimeoutExpired):
            pass
        state["engines"][name] = version
    state["usable_engines"] = [name for name in ("latexmk", "tectonic") if state["engines"].get(name)]
    return state


def document_state(path, doc, scan):
    state = {"file": str(path), "page_count": doc.page_count, "needs_pass": doc.needs_pass,
             "rotated_pages": [number + 1 for number in range(doc.page_count) if doc[number].rotation],
             "page_size_pt": {"width": round(doc[0].rect.width, 3), "height": round(doc[0].rect.height, 3)},
             "metadata": {key: value for key, value in doc.metadata.items() if value}}
    if scan:
        empty = [number + 1 for number in range(doc.page_count) if not doc[number].get_text("text").strip()]
        state["pages_without_text"] = empty
        state["note"] = ("Pages without extractable text may be scanned images; inspect them visually"
                         if empty else "Every page yields extractable text.")
    return state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("extract", "preview", "crop", "check"):
        p = sub.add_parser(name)
        p.add_argument("pdf", type=Path, nargs="?" if name == "check" else None)
        p.add_argument("--force", action="store_true", help="Replace existing output files")
        if name not in ("crop", "check"):
            p.add_argument("--pages", default="all", help="1-based pages, e.g. 1,3-5; default: all")
        if name == "extract":
            p.add_argument("--output", type=Path, help="UTF-8 output; default: stdout")
            p.add_argument("--max-chars", type=int, metavar="N",
                           help="Split the output into N-character parts at page boundaries")
        elif name == "preview":
            p.add_argument("--output-dir", required=True, type=Path)
            p.add_argument("--dpi", type=int, default=120, help="Render resolution (36..600)")
        elif name == "crop":
            p.add_argument("--page", type=int, required=True, help="1-based physical page")
            p.add_argument("--rect", nargs=4, type=float, required=True,
                           metavar=("X0", "Y0", "X1", "Y1"),
                           help="PDF points, origin top-left; rotated pages must be normalized first")
            p.add_argument("--output", type=Path, required=True, help="Vector-preserving PDF crop")
        else:
            p.add_argument("--no-scan", action="store_true", help="Skip the per-page text check")
    sub.add_parser("hash", help="SHA-256 and byte size, for provenance records").add_argument(
        "files", type=Path, nargs="+")
    args = parser.parse_args()

    if args.command == "hash":
        missing = [str(path) for path in args.files if not path.is_file()]
        if missing:
            parser.exit(2, "Not a file: " + ", ".join(missing) + "\n")
        print(json.dumps([file_hash(path) for path in args.files], ensure_ascii=False, indent=2))
        return

    if args.command == "check" and args.pdf is None:
        state = tool_state()
        print(json.dumps(state, ensure_ascii=False, indent=2))
        if not state["pymupdf"]:
            sys.exit(1)
        return

    try:
        # PyMuPDF >= 1.24 exposes `pymupdf`; importing the deprecated `fitz` alias there
        # prints a notice on stdout, which would corrupt this script's machine-readable
        # output.
        import pymupdf as fitz
    except ImportError:
        try:
            import fitz
        except ImportError:
            parser.exit(2, "Missing dependency: PyMuPDF. " +
                        REQUIREMENTS_HINT.format(requirements=requirements_path()) + "\n")
    try:
        with fitz.open(args.pdf) as doc:
            if not doc.is_pdf:
                raise ValueError(f"Not a PDF: {args.pdf}")
            if doc.needs_pass:
                raise ValueError("PDF is encrypted; provide a readable, decrypted copy")
            if not doc.page_count:
                raise ValueError("PDF has no pages")
            if args.command == "check":
                state = tool_state()
                state["document"] = document_state(args.pdf, doc, not args.no_scan)
                print(json.dumps(state, ensure_ascii=False, indent=2))
            elif args.command == "crop":
                if args.output.suffix.lower() != ".pdf":
                    raise ValueError("Crop output must have a .pdf extension")
                if not 1 <= args.page <= len(doc):
                    raise ValueError(f"Page must be within 1..{len(doc)}")
                page = doc[args.page - 1]
                if page.rotation:
                    raise ValueError(f"Page has /Rotate={page.rotation}; normalize rotation in a copy before cropping")
                x0, y0, x1, y1 = args.rect
                if not all(math.isfinite(v) for v in args.rect) or not (0 <= x0 < x1 <= page.rect.width and 0 <= y0 < y1 <= page.rect.height):
                    raise ValueError(f"Rectangle must lie inside page: 0 0 {page.rect.width:g} {page.rect.height:g}")
                check_outputs([args.output], args.pdf, args.force)
                args.output.parent.mkdir(parents=True, exist_ok=True)
                with fitz.open() as out:
                    target = out.new_page(width=x1 - x0, height=y1 - y0)
                    target.show_pdf_page(target.rect, doc, args.page - 1, clip=fitz.Rect(args.rect))
                    out.save(args.output, garbage=4, deflate=True)
                print(args.output)
            else:
                pages = page_numbers(args.pages, len(doc))
                if args.command == "extract":
                    chunks = []
                    for number in pages:
                        content = doc[number].get_text("text", sort=True)
                        if not content.strip():
                            print(f"Warning: page {number + 1} has no extractable text; inspect its image / use OCR", file=sys.stderr)
                        chunks.append(f"===== PDF page {number + 1} / {len(doc)} =====\n{content}")
                    if args.output:
                        if args.max_chars is not None and args.max_chars <= 0:
                            raise ValueError("--max-chars must be positive")
                        parts = group_pages(chunks, args.max_chars) if args.max_chars else ["\n".join(chunks)]
                        paths = [args.output] if len(parts) == 1 else [
                            args.output.with_name(f"{args.output.stem}-part{index:02d}{args.output.suffix}")
                            for index in range(1, len(parts) + 1)]
                        check_outputs(paths, args.pdf, args.force)
                        args.output.parent.mkdir(parents=True, exist_ok=True)
                        for path, part in zip(paths, parts):
                            path.write_text(part, encoding="utf-8")
                            print(path)
                        total = sum(len(part) for part in parts)
                        print(f"Wrote {total} characters across {len(paths)} file(s) for {len(pages)} page(s)",
                              file=sys.stderr)
                    else:
                        print("\n".join(chunks))
                else:
                    if not 36 <= args.dpi <= 600:
                        raise ValueError("DPI must be within 36..600")
                    paths = [args.output_dir / f"page-{n + 1:03d}.png" for n in pages]
                    manifest_path = args.output_dir / "manifest.json"
                    check_outputs(paths + [manifest_path], args.pdf, args.force)
                    args.output_dir.mkdir(parents=True, exist_ok=True)
                    manifest = {"source": str(args.pdf.resolve()), "page_count": len(doc), "dpi": args.dpi, "pages": []}
                    for number, path in zip(pages, paths):
                        page = doc[number]
                        pix = page.get_pixmap(dpi=args.dpi, alpha=False)
                        pix.save(path)
                        manifest["pages"].append({"page": number + 1, "image": path.name,
                                                  "width_pt": page.rect.width, "height_pt": page.rect.height,
                                                  "rotation": page.rotation})
                    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                    print(f"Rendered {len(pages)} pages: {manifest_path}")
    except Exception as exc:
        parser.exit(2, f"PDF operation failed: {exc}\n")


if __name__ == "__main__":
    main()