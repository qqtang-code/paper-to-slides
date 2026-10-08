#!/usr/bin/env python3
"""Assert that a rebuild looks sane: usable report, no errors or overflows, expected page count.

Used by CI after building a deck with a non-default engine:

    python tests/check_built_deck.py <deck>/build-report.json 15
"""

import json
from pathlib import Path
import sys

try:
    # PyMuPDF >= 1.24 exposes `pymupdf`; the deprecated `fitz` alias warns on stdout there.
    import pymupdf as fitz
except ImportError:  # pragma: no cover - exercised only with PyMuPDF < 1.24
    import fitz


def main():
    if len(sys.argv) != 3:
        print(__doc__.strip())
        return 2
    report_path, expected_pages = Path(sys.argv[1]), int(sys.argv[2])
    report = json.loads(report_path.read_text(encoding="utf-8"))
    problems = []
    if not report.get("compiled"):
        problems.append(f"not compiled: {report.get('errors')}")
    if report.get("errors"):
        problems.append(f"errors: {report['errors']}")
    if report.get("overflows"):
        problems.append(f"overflows: {report['overflows'][:3]}")
    pdf_path = report_path.parent / report.get("pdf", "")
    if not pdf_path.is_file():
        problems.append(f"missing PDF: {pdf_path}")
    else:
        with fitz.open(pdf_path) as doc:
            if doc.page_count != expected_pages:
                problems.append(f"page count {doc.page_count}, expected {expected_pages}")
            blank = [n + 1 for n in range(doc.page_count) if not doc[n].get_text().strip()]
            if blank:
                problems.append(f"pages without text: {blank}")
    if problems:
        for problem in problems:
            print(f"FAIL  {problem}")
        return 1
    print(f"ok    {report['engine']}: {expected_pages} pages, no errors or overflows, "
          f"{len(report.get('other_warnings', []))} non-blocking warning(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())