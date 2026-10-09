# Paper reading and provenance

## LaTeX projects

Identify the actual main file from its document class, title, document body, and bibliography. Follow `\input`, `\include`, `\subfile`, `\import`, and similar dependencies, keeping a visited set to avoid cycles. Try `.tex` when an extension is omitted. Resolve relative paths according to the project's compilation directory and import semantics, not automatically relative to each child file. Account for `\includeonly`, conditional branches, and custom macros. If static inspection is ambiguous, consult the existing PDF, build configuration, or `.fls` file; a regular expression is not a complete TeX parser.

Track `\graphicspath`, `\includegraphics`, TikZ/PGFPlots data files, table inputs, algorithms, local `.sty`/`.cls` files, and all `.bib` files in `\bibliography`. Read bibliography `@string` definitions. Preserve `\bibliography{strings,refs}` ordering when used by the project. Copy required figures into the output's `figures/` directory and use relative paths. Do not inadvertently copy identifying email addresses, acknowledgments, or institutional logos into an anonymous presentation.

Start with the abstract, stated contributions, methods, result tables, conclusion, and limitations. Then read the background, appendices, proofs, and experimental details needed to support the talk. Existing presentations may inform the design and narrative, but verify their claims against the paper.

## Local PDFs

1. Start with `pdf_tools.py check paper.pdf`, which reports the page count, page size, rotation, metadata, and any page without extractable text. Then use `pdf_tools.py extract` to produce text with physical page numbers, and confirm that the extraction is plausible. A PyMuPDF repair message on stderr (`MuPDF error: format error ... object out of range`) means the cross-reference table was damaged, not that the text is unusable; confirm by inspecting rendered pages. For a long paper, pass `--max-chars` so the output is split at page boundaries and can be read in parts.
2. Use `pdf_tools.py preview` to render pages. Inspect method figures, tables spanning columns, equations, footnotes, and garbled text visually. Do not infer table alignment from text-extraction order.
3. Scanned pages require available OCR or an image-capable model. Empty extracted text does not mean a page has no content. If neither capability is available, identify the pages that cannot be read reliably instead of inventing their contents.
4. When standalone source assets are unavailable, prefer `crop` to reuse PDF figures while preserving vector text and paths. Retain legends, axis units, error bars, and comparison conditions. If identifying information must be removed, recreate an anonymous figure: PDF cropping is not secure redaction, and underlying content may remain recoverable.

Coordinates use a top-left origin, points as units, and the order `x0 y0 x1 y1`. Page numbers start at 1. Choose coordinates from an unrotated PDF page as displayed in the preview. The helper rejects pages with a nonzero `/Rotate` value and explains why. Normalize rotation in a copy first, or use another tool that handles it and inspect the result again. Divide preview pixel coordinates by `dpi/72` before using them as PDF points.

## Public paper links

Use `scripts/fetch_paper.py <reference> --dir <dir> --extract` rather than assembling download, hash,
and extraction commands by hand. It accepts an arXiv identifier, an arXiv URL, or a direct file URL;
resolves an unversioned link to the concrete version; performs the checks below; and writes
`provenance.json` with the supplied URL, resolved URL, title, authors, version, retrieval time,
byte count, and SHA-256 for every artifact, plus a member audit of the source archive. Read its
record when filling in `sources.md`, and state which values came from it. The rules it enforces:

- Record the supplied URL, resolved URL, title, authors, version, retrieval date, and file SHA-256. Prefer LaTeX source for the same version. For example, arXiv `.../abs/1706.03762v7` corresponds to `.../src/1706.03762v7` and `.../pdf/1706.03762v7`. If the URL omits a version, resolve and record the actual version used.
- Use a download tool with a reasonable timeout. Check HTTP status, content type, file signature, and nonzero size so a login or error page is not mistaken for a PDF. Check again after redirects. If source is unavailable, use the PDF instead of repeatedly retrying the same failed endpoint.
- Inspect an external source archive before extraction. Reject absolute paths, `..` traversal, and links escaping the extraction directory. Do not execute bundled scripts; if compilation is needed, keep shell escape disabled.
- An inaccessible link establishes only that retrieval failed. An abstract or landing page cannot replace the full experiments, proofs, and limitations. State what remains unknown and request readable full text.

## Core-figure inventory

While reading, identify the method overview, model architecture, and key evidence figures that support the talk's central contributions. Inspect their content before writing the outline. Add a short inventory to the existing `sources.md`, not a separate file:

| Figure | Role and contribution | Asset / paper location | Planned use and reason |
| --- | --- | --- | --- |
| Fig. 1 | Architecture; explains the proposed information flow | `figures/model.pdf`, `fig:model`, PDF p. 3 | Main talk: full overview, then attention detail |
| Fig. 3 | Key evidence for the efficiency claim | PDF p. 7; standalone source unavailable | Main talk: vector-preserving crop with axes and legend |
| Fig. 5 | Sensitivity outside the talk's selected scope | `figures/sensitivity.pdf`, PDF p. 9 | Backup: supports optional hyperparameter discussion |

These rows illustrate decisions, not a quota. Select figures by relevance and duration. If the paper has no useful figures, record that briefly and use its definitions, proofs, or examples instead. Update planned use to final slide locations after production. Explain substantive omissions, backup-only choices, and replacements of candidate core figures; layout convenience is not a sufficient reason.

Prefer the independent figure asset from matching-version source; otherwise extract it with the existing PDF crop helper. Record the original path or PDF page and crop rectangle, the local asset, and any transformations. Distinguish **original**, **crop**, **annotation**, and **redraw** (combinations are possible). A redraw supplements intuition by default; a replacement requires a concrete reason such as an unavailable original, inadequate source quality, or an explanatory problem that cannot be resolved with notes. Do not count an added box or slide caption as an original part of the paper.

## Evidence record

Each output should include a concise `sources.md` identifying the paper and file versions, followed by a mapping such as:

| Slide or claim | Type | Source location | Values, conditions, or figure | Treatment |
| --- | --- | --- | --- | --- |
| The method ties the baseline | Reported result | `results.tex:88`, Table 2, task A | Both 40.00%, same model | Describe as a tie |
| +1.52 percentage points | Presenter calculation | Table 2: 65.15% and 63.63% | 65.15 - 63.63 = 1.52 pp | Not a relative percentage gain |
| Possible transfer limitation | Presenter analysis | Evaluated on only two models | Not tested by the paper | Label as analysis |

Add comments beside important frames, for example:

```tex
% Source: paper/results.tex:88, tab:main, model A / task B.
% Derived: 65.15 - 63.63 = 1.52 percentage points; rounded inputs.
% Presenter analysis: transfer beyond the evaluated models is untested.
```

For PDFs, use physical page numbers and add printed page numbers or figure/table identifiers where useful. For source, use file paths, line numbers, and stable labels. If prose, tables, or figures disagree, record the conflict and narrow the claim to verifiable evidence. Do not silently repair the paper and attribute the repaired conclusion to its authors.

Keep a core figure when a local conflict can be explained alongside it. A method overview may label a component differently from the prose that describes it: a diagram can tag an operation with one level or stage while the corresponding section uses another, and an appendix can introduce a third naming. Preserve the method diagram and disclose the conflicting labels; explain what each component does operationally instead of treating the diagram's labels as literal definitions. A local naming mismatch alone is not a reason to discard the entire overview.
