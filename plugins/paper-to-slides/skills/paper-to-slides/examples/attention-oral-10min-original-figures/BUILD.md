# Build and present this deck

This self-contained Beamer deck presents *Attention Is All You Need*, using
arXiv:1706.03762v7. It contains 12 main pages plus 3 backup pages, without
overlays. English slides are accompanied by a Chinese timed speaker script:
540 seconds of main narration plus 60 seconds of buffer for a 10-minute slot.

## Build

Use **pdfLaTeX + BibTeX**. A Chinese Markdown script does not require XeLaTeX.
Required TeX packages include Beamer, Fira Sans, TikZ/PGF, amsmath, amssymb,
booktabs, array, pifont, graphicx, hyperref, and appendixnumberbeamer.
TeX Live 2023 was used for verification. Fonts are supplied by TeX; no font
files are bundled. No network access or paper repository is needed to rebuild.

From this directory:

```bash
latexmk -norc -pdf -interaction=nonstopmode -halt-on-error -file-line-error -pdflatex="pdflatex -no-shell-escape %O %S" main.tex
```

The equivalent manual build is:

```bash
pdflatex -no-shell-escape -interaction=nonstopmode -halt-on-error main.tex
bibtex main
pdflatex -no-shell-escape -interaction=nonstopmode -halt-on-error main.tex
pdflatex -no-shell-escape -interaction=nonstopmode -halt-on-error main.tex
```

Keep the `strings,refs` BibTeX order. All inputs use local relative paths.
PDF 1.7 is enabled to accommodate PDF figure crops. The original architecture
and attention panels are PNG source assets; embedding them in a PDF does not
make them vector graphics.

If the paper-to-slides skill is installed, its optional strict check is:

```bash
python /path/to/paper-to-slides/scripts/build_slides.py /path/to/this-deck/main.tex --engine pdflatex --strict
```

The helper is not needed for normal compilation. Use one engine per build and
avoid simultaneous editor/helper compilation in the same directory. A fresh
copy is suitable for clean verification.

Without a TeX Live installation, Tectonic compiles the same sources and produces
the same 15 pages: `tectonic --untrusted --keep-logs ./main.tex`. It reports
XeLaTeX to `iftex`, so the slides are unaffected; 13 of the 15 pages are
text-identical to the bundled PDF, and the difference on the equation page is the
text-layer encoding of two large parentheses rather than printed content. Two
further differences are expected from a Tectonic rebuild: the output PDF version
is 1.5 instead of 1.7, because `\pdfminorversion` is a pdfTeX primitive, and the
bibliography entry uses an `@string` macro, which Tectonic's BibTeX expands
without inter-word spaces, rendering
`AdvancesinNeuralInformationProcessingSystems30`. Before a Tectonic rebuild,
replace `booktitle = neurips` with the literal
`booktitle = {Advances in Neural Information Processing Systems 30}` and keep
`strings.bib` empty, or build with pdflatex + BibTeX as above to reproduce the
bundled PDF exactly.

## Files and editing

- `main.pdf`: checked presentation; stop on main page 12 for questions.
- `main.tex`: editable slide content and supplemental inline TikZ illustrations.
- `config.tex`: colors, font selection, title, and anonymous-presenter metadata.
- `paper-slides.sty`: local theme, copied from the skill template.
- `figures/`: original images and PDF crops, with local paths.
- `speaker-script.md`: spoken Chinese, pointing cues, transitions, and timings
  for all 15 physical PDF pages; backup timing is separate.
- `sources.md`: version, checksums, figure inventory, transformations, claim audit,
  numeric conditions, and scholarly reproduction permission.
- `verification.md`, `content-checks.json`, `build-report.json`,
  `relocation-build-report.json`, and `packaging-build-report.json`: original
  generation checks and the later repository-packaging rebuild.
- `main.log` and `main.build-output.txt` are produced by a local build and by the
  helper, and are not tracked in the repository; the recorded results are in the
  JSON reports above.

The title page credits the public paper authors separately. Keep the anonymous
presenter placeholder unless the presentation's identity requirements change.
The title layout in `main.tex` uses the whole available header width; there is
no institution header in this anonymous deck.

## Verification

The final strict build, inspection of every rendered page, numeric/script
checks, and a clean relocation build are documented in `verification.md`.
The check validates the deck against the paper, not the original experiments.
Rehearse with a timer before presenting; timing is estimated.
