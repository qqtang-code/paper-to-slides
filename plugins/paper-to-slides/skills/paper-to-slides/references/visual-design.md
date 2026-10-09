# Visual design and templates

The template is in `assets/template/`. `main.tex` is a compilable gallery of ten layouts using synthetic content; `config.tex` contains metadata, colors, and font options; `paper-slides.sty` implements the reusable theme. Copy the whole directory and replace the examples with the paper's content. The template has no real affiliation, contact information, or external logo by default.

## Configuration

- Edit `\title[Short title]{Full title}`, `\subtitle`, `\author{Anonymous Authors}`, `\Presenter`, `\institute`, `\HeaderInstitution`, `\Contact`, `\TalkType`, and `\date` in `config.tex`. Place long affiliations on the title slide; use an appropriate short form in the header or leave it blank.
- `SlideBlue` controls headings and rules; `SlideGray` controls takeaways and the footer; `SlideRed` and `SlideGreen` provide emphasis; `SlideLight` supplies pale blue backgrounds; `SlideInk` is the body-text color. Pair color with text, symbols, or shapes instead of relying on red/green distinctions alone.
- English slides default to pdfLaTeX and Fira Sans. `\LatinFontPackage` may be changed to an installed sans-serif package compatible with the `sfdefault` option; leave it empty to use the TeX default font. The theme does not silently substitute fonts. If a dependency is missing, install it or explain the limitation before choosing an available alternative.
- For Chinese slides, use XeLaTeX and set `\ChineseSlidestrue`. The default ctex font set is `fandol`, with FandolHei for Chinese sans-serif text; these fonts ship with TeX distributions. Change `\CJKFontSet` only to an available ctex font set. Avoid dependencies on platform-specific commercial fonts. A Chinese script accompanying English slides does not require an engine change.
- Use `\cite` for references. Add a reference slide when needed, with `\bibliographystyle{plain}` and `\bibliography{strings,refs}`, or another available BibTeX style. Replace synthetic bibliography entries with real sources from the paper. Write literal field values rather than `@string` macros: Tectonic's BibTeX drops inter-word spaces when it expands them, so a string-based entry renders as `AdvancesinNeuralInformationProcessingSystems30` under Tectonic while BibTeX renders it correctly. Read a paper's own `@string` definitions for reference, then copy the resolved text into literal values.
- Tectonic builds the same sources without a TeX Live installation. It reports XeLaTeX to `iftex`, so the theme's engine checks and the Chinese branch work; its bundled BibTeX has the `@string` limitation above. State the engine that was actually used in `BUILD.md`.
- Frame titles, subtitles, and metadata containing math such as `$\rightarrow$`, `\\`, or other non-ASCII text make hyperref warn that a token is not allowed in a PDF string. Wrap the offending content in `\texorpdfstring{<typeset>}{<plain text>}`, or disable the command for PDF strings with `\pdfstringdefDisableCommands{\def\translate#1{#1}}`, and confirm the warnings are gone.

## Choose layouts to fit the content

The gallery includes title, two-column explanation, method overview, equation or algorithm, results table, figure analysis, summary, closing, original-figure overview, and detail-with-explanation layouts. Select and combine them as appropriate; do not require all ten. Usually give each slide one main claim and write its takeaway as a short, verifiable sentence.

- Start with `\normalsize` in the 10pt Beamer template. Remove content or split slides before reducing type size. Do not shrink a whole slide with `\tiny` or `shrink` to make it fit.
- Keep only table rows and columns needed to support the claim, along with units and evaluation conditions. Put complete results in backup slides. Avoid scaling a long table until it becomes unreadable.
- Prefer vector PDFs, followed by original high-resolution raster images. Use `\includegraphics[width=...,height=...,keepaspectratio]` to avoid distortion and relative paths under `figures/`.
- Use the original-figure overview and detail-with-explanation layouts for core paper figures. The synthetic vector asset under `figures/` includes editable LaTeX source and compiles without the paper repository.
- Introduce equation symbols and conditions before emphasizing the main relationship. Break long equations across lines. In algorithm slides, retain the control flow needed for understanding.
- Allow long titles to wrap naturally. The heading, takeaway, footer, and body share limited vertical space. Shorten slide titles or header affiliations, or split the slide when crowded; do not let headings cover the body.

## Preserve and explain original figures

Give a core original enough space to lead the slide. Do not replace it with text blocks or a simpler redraw for layout convenience, and do not place it only in backup when it explains the main contribution. Prefer the standalone source asset, then a vector-preserving crop from the paper PDF. Use original high-resolution raster content when that is the available source; vector cropping cannot recover absent detail.

Keep the original layout, palette, arrows, symbols, and panel order. Apply the slide theme to surrounding titles, captions, and annotations without requiring the figure to be recolored. Boxes, numbered markers, and side notes can guide attention if they do not obscure labels or evidence. Attribute the original visibly and record crops and added annotations separately in `sources.md` and nearby `.tex` comments. Label redraws as presenter illustrations and use them to supplement the original by default. If replacement is necessary, document the specific availability, quality, or unresolved communication problem.

For a complex figure, use **complete overview plus necessary detail views**. The overview establishes spatial and structural relationships; zoom pages explain the required details. Keep legends, axis units, panel identifiers, and enough boundary context to interpret the crop. Show or name the zoom's location in the overview; include incoming connections when they are essential to the explanation. Essential small labels need readable enlargements or faithful nearby transcription, not a claim that a high-resolution render alone makes them legible on a projected slide.

Judge legibility from the size on the final slide, not from the source resolution. Estimate the scale you are applying to a PDF figure and the resulting size of its smallest essential label: text landing below roughly 6 pt will not read from the back of a room. When a panel cannot reach that size at full slide width, split the figure across frames — one frame per panel or per row — instead of shrinking the whole figure, and prefer a full-width crop of one region over a half-width crop of several. Confirm that every panel of a multi-panel figure is both present and readable; a crop that silently drops a panel of a pipeline misstates the method.

The gallery's last two layouts demonstrate this with the same self-created synthetic figure: an unchanged full view, then a crop of panel (b) with its incoming edge and an explanation outside the image. Its purple/orange palette intentionally differs from the blue slide theme. `figures/synthetic-method.tex` is the editable standalone source, and the bundled PDF lets the gallery compile immediately. See [the template build notes](../assets/template/BUILD.md) for regenerating that asset. These are layout examples, not real paper evidence.

Keep a useful figure with an explicit discrepancy note when the issue is local. When a diagram labels a component differently from the body text, explain the conflict as described in [Paper reading and provenance](paper-reading.md); do not silently relabel the original or drop the entire method figure.

## Visual inspection

Render every page to assess composition, whitespace, and pacing. Enlarge dense tables, equations, headers, and figure labels. Check whether the takeaway wraps too far below the blue rule, whether the footer collides with a figure, and whether a long affiliation overlaps the title. Inspect PDF metadata and the cover for compliance with anonymity requirements.

Build logs catch only some overflows. A warning-free build can still contain unreadable type, clipped labels inside images, or overlapping TikZ nodes. After a local edit, rerender affected pages. After changing the theme or global fonts, inspect every page again.
