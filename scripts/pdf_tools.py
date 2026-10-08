#!/usr/bin/env python3
"""Extract PDF text, render pages, or crop a page without rasterizing it."""

import argparse
import json
import math
from pathlib import Path
import sys


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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("extract", "preview", "crop"):
        p = sub.add_parser(name)
        p.add_argument("pdf", type=Path)
        p.add_argument("--force", action="store_true", help="Replace existing output files")
        if name != "crop":
            p.add_argument("--pages", default="all", help="1-based pages, e.g. 1,3-5; default: all")
        if name == "extract":
            p.add_argument("--output", type=Path, help="UTF-8 output; default: stdout")
        elif name == "preview":
            p.add_argument("--output-dir", required=True, type=Path)
            p.add_argument("--dpi", type=int, default=120, help="Render resolution (36..600)")
        else:
            p.add_argument("--page", type=int, required=True, help="1-based physical page")
            p.add_argument("--rect", nargs=4, type=float, required=True,
                           metavar=("X0", "Y0", "X1", "Y1"),
                           help="PDF points, origin top-left; rotated pages must be normalized first")
            p.add_argument("--output", type=Path, required=True, help="Vector-preserving PDF crop")
    args = parser.parse_args()
    try:
        import fitz
    except ImportError:
        parser.exit(2, "Missing dependency: PyMuPDF. Run: python -m pip install -r scripts/requirements.txt\n")
    try:
        with fitz.open(args.pdf) as doc:
            if not doc.is_pdf:
                raise ValueError(f"Not a PDF: {args.pdf}")
            if doc.needs_pass:
                raise ValueError("PDF is encrypted; provide a readable, decrypted copy")
            if not doc.page_count:
                raise ValueError("PDF has no pages")
            if args.command == "crop":
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
                    content = "\n".join(chunks)
                    if args.output:
                        check_outputs([args.output], args.pdf, args.force)
                        args.output.parent.mkdir(parents=True, exist_ok=True)
                        args.output.write_text(content, encoding="utf-8")
                        print(args.output)
                    else:
                        print(content)
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
