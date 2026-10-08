# Build the layout gallery

This is a ten-page synthetic layout gallery, not a research presentation.
Copy this entire directory before adapting it. Edit `config.tex` and `main.tex`.
Required: TeX Live or MiKTeX with Beamer, Fira Sans, TikZ, booktabs, pifont,
amsmath, latexmk and BibTeX; Chinese slides additionally need XeLaTeX, ctex and Fandol.

English (default):

```bash
latexmk -norc -pdf -interaction=nonstopmode -halt-on-error -file-line-error -pdflatex="pdflatex -no-shell-escape %O %S" main.tex
```

Chinese: set `\ChineseSlidestrue` in `config.tex`, then use a fresh output copy:

```bash
latexmk -norc -xelatex -interaction=nonstopmode -halt-on-error -file-line-error -xelatex="xelatex -no-shell-escape %O %S" main.tex
```

The optional skill helper `scripts/build_slides.py` additionally summarizes
warnings. It is not required to compile this folder. A generated talk should
replace this file with its actual engine, dependencies, input provenance and
verification results, and include `speaker-script.md` and `sources.md`.

## Original-figure layouts

Pages 9 and 10 show a full original-figure overview and a detail crop with
explanation. The original here is a self-created synthetic example, not a
third-party paper figure. Keep `figures/synthetic-method.pdf` when compiling
the gallery; its independent purple/orange palette demonstrates that the
slide theme applies to the surrounding title and explanation.

The editable source is `figures/synthetic-method.tex`. Regenerate the PDF
with the existing pdfLaTeX toolchain from this directory:

```bash
latexmk -norc -cd -pdf -interaction=nonstopmode -halt-on-error -file-line-error -pdflatex="pdflatex -no-shell-escape %O %S" figures/synthetic-method.tex
```

The detail uses TeX `trim`/`clip` on that PDF, so no extra crop file is required.
Its top-left crop rectangle is [106, 0, 312, 136] PDF points; the caption and
side explanation retain panel identity, flow direction, and the full legend.
For an actual paper, replace both views with the matching original and its
necessary detail; record the source, treatment, and final slide placement in
`sources.md`. Do not carry synthetic content into a research presentation.
