# Verification record

Checked 26 September 2026. Input: arXiv:1706.03762v7. Output: 15 physical PDF
pages (12 main + 3 backup), English slides and a Chinese timed speaker script.
These are checks performed for this deck in this run, not inherited results
from earlier presentations or skill-maintenance tests.

## Completed checks

- Resolved the unversioned arXiv URL to v7 and downloaded the matching PDF and
  source. Both returned HTTP 200 with the expected content types and sizes.
  Verified the PDF signature, 15-page paper count, hashes, and safe archive
  member paths/types before extracting. No paper scripts were executed.
- Read the included method, training, results, background, conclusion, and
  visualization sources. Inspected the original Figure 1, Figure 2, Table 2,
  and Table 3 page images to verify labels, arrows, column alignment, and
  numerical conditions. Stable section/figure/table locations and source
  lines are recorded in `sources.md` and frame-adjacent comments.
- Original Figure 1 appears as a complete overview on main page 3 and a
  connected decoder-detail enlargement on main page 6. Original Figure 2's
  full left/right panels appear on main pages 4/5. Their source PNGs match
  the archive byte-for-byte. No method redraw replaces these originals.
- The detail crop preserves the encoder-output route into decoder
  cross-attention and the masked self-attention below it. Its relationship
  to the complete figure and omitted regions is explicit. The overview,
  readable detail, nearby transcriptions, and script jointly explain the
  essential labels. Original raster content is not described as vector.
- Original Table 2 appears in the main talk with every row/header retained;
  large callouts emphasize the selected EN–DE comparison. Table 3's original
  header/base/group (A) crop retains the inheritance and comparison context.
- Parsed the v7 source table rows and recomputed 28.40 − 26.36 = 2.04 BLEU
  points and 25.8 − 24.9 = 0.9 BLEU points. Verified the 8/16-head tie and
  32-head decline. Test versus development, checkpoint averaging, varying
  head dimensions, and estimated FLOPs are stated explicitly. No statistical
  significance or matched-budget inference is asserted.
- Preserved and disclosed the v7 EN–FR discrepancy: abstract/Table 2 report
  41.8, Section 6.1 prose reports 41.0. It is visible and spoken on main page
  9 and documented with an original prose excerpt on backup page 14.
- The final strict **pdfLaTeX + BibTeX** build passed with zero errors,
  missing glyphs, unresolved references, overflows, or other warnings.
  See `build-report.json`; `main.log` and `main.build-output.txt` are produced by
  a local build and are not tracked in the repository.
- Rendered and visually inspected all 15 final pages at 150 dpi. Inspected
  pages 3–6, 9–10, and 14 again at 240 dpi for original-figure labels, matrix
  notation, table cells, crop boundaries, and attribution. Checked cover,
  headings, captions, body text, and footers for visible overlap/clipping.
- Matched all frame IDs, script titles, and physical PDF pages. Every page
  has spoken content, pointing cues, and a transition. Main timings sum to
  540 seconds with a 60-second buffer; backup pages are separate. The main
  spoken prose contains 1,994 Chinese characters plus technical terms, before
  transitions. Figure-reading and pauses are included in the estimates.
- Copied only source/style/bibliography, figures, and Markdown into a new
  directory containing spaces. Rebuilt with no prior PDF or auxiliary files.
  The strict relocation build passed, and all 15 page renders are identical
  to the checked original build. Its dependency log has no path to the original
  paper, skill installation, existing decks, or initial build directory.
- PDF author metadata is Anonymous Presenter; `config.tex` retains
  `Anonymous Authors`. The cover separately credits the original public paper
  authors. No personal contacts, logos, or commercial fonts are bundled.
- Checked hashes of 228 pre-existing manuscript/template/skill/deck files:
  all unchanged. This task creates a new output directory.

`content-checks.json` records frame/script counts, computed values, asset hashes,
render equivalence, and preservation results. `relocation-build-report.json`
is the clean second build summary. Both builds were isolated from editor builds
to avoid concurrent writes to shared LaTeX auxiliary files.

## Limits

This checks consistency with the paper, build portability, and slide layout.
It does not rerun model training or benchmarks. The original EN–FR discrepancy
remains unresolved. No live speaker rehearsal or physical-projector test was
performed; rehearse using the 9-minute script and the provided buffer.
Figure/table reproduction terms remain those of the original paper, recorded
in `sources.md`.

## Repository packaging check

On 26 September 2026, this generated deck was moved into
`examples/attention-oral-10min-original-figures/` as the skill's public output
example. Its original 22 files were compared by SHA-256 immediately after the
move; all were unchanged. A fresh copy containing only source, styles,
bibliography, and local figures was then strictly rebuilt with pdfLaTeX and
BibTeX in a separate directory containing spaces. The build passed with no
errors or warnings, and all 15 rendered pages matched the bundled PDF. The
new dependency log has no path to the original project or skill installation.

See `packaging-build-report.json` for this rebuild's diagnostics. The skill's
official format validator and local Markdown-link checks also passed. This
packaging check did not repeat the original paper audit, visual review, or
script rehearsal; earlier checks and their limitations remain documented
above. Local LaTeX logs are generated on rebuild and ignored by the repository's
`.gitignore`; they are not required to compile the example.
