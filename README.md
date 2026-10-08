# paper-to-slides

An agent skill for turning research papers into editable Beamer slides, preserving original figures and adding timed speaker scripts.

Designed for **Codex and Claude Code**, it accepts LaTeX projects, local PDFs, and accessible paper links. The agent reads the paper, builds a narrative, and produces the presentation; the bundled Python tools handle PDF extraction, cropping, previews, and compilation. The output is LaTeX/Beamer and PDF, not native PowerPoint.

## Example: Attention Is All You Need

The [included example](examples/attention-oral-10min-original-figures/BUILD.md) was generated with this skill from [arXiv:1706.03762v7](https://arxiv.org/abs/1706.03762v7):

- **12 main slides + 3 backup slides**, in English.
- A **Chinese speaker script**, with 9 minutes of main narration and a 1-minute buffer for a 10-minute oral.
- Original architecture and attention diagrams, a connected detail view, and original result-table excerpts in the main talk.
- Editable source, local assets, citations, figure provenance, and build reports.

[View the slides](examples/attention-oral-10min-original-figures/main.pdf) · [Read the script](examples/attention-oral-10min-original-figures/speaker-script.md) · [Browse the source](examples/attention-oral-10min-original-figures/main.tex) · [See the evidence record](examples/attention-oral-10min-original-figures/sources.md)

This is an example of a completed output. New presentations start from the reusable template and the supplied paper; the example's topic, page count, and narrative are not requirements for other talks.

## What it produces

A self-contained output directory with:

```text
my-talk/
├── main.tex                 Editable Beamer presentation
├── config.tex               Colors, fonts, and presenter metadata
├── paper-slides.sty          Local slide theme
├── figures/                 Original assets and documented crops
├── strings.bib
├── refs.bib                  BibTeX references
├── main.pdf                 Compiled presentation
├── speaker-script.md        Per-page narration, cues, and timing
├── sources.md               Paper version, figures, and claim provenance
├── BUILD.md                 Build instructions and dependencies
└── build-report.json        Compilation diagnostics
```

The default is a **10-minute conference talk** or a **20-minute reading-group presentation**. Slides follow the paper's language; the script follows the conversation language. These can be selected independently. Main narration uses about 90% of the requested duration, leaving room for pauses and transitions.

The theme uses a 16:9 white background, blue titles and rules, gray takeaways, and restrained accent colors. Colors, fonts, and identity fields are configurable. Unspecified presenter identities remain anonymous; public paper authors are credited separately.

## Core original figures first

Method overviews, model architectures, and key evidence that support the talk's central story belong in the main talk, with explanation time reserved during outlining. The skill prefers standalone paper assets, then PDF crops that preserve existing vector content. Complex figures receive a complete overview plus necessary enlargements; original colors, arrows, symbols, and spatial relationships remain intact.

Redraws can supplement intuition. Replacing a core original requires a specific reason recorded in `sources.md`; layout convenience alone is insufficient. Figure selection follows the paper and speaking time, without a fixed count or ratio. A theory paper with no useful figures does not need forced imagery.

## Use with your agent

Clone or download this repository. All shell commands below assume the repository root is the current directory.

For a first run, ask your agent to read the entry point directly:

```text
Read ./SKILL.md and use paper-to-slides to process
https://arxiv.org/abs/1706.03762.
Create a 10-minute conference oral with English slides and a Chinese speaker
script. Keep the presenter anonymous and save the output to ./my-talk/.
```

For repeated use, copy or symlink the **entire repository directory**, under the name `paper-to-slides`, into a skills directory supported by your client. Copying only `SKILL.md` omits required resources. Directory locations and discovery behavior are documented in the [Codex skills documentation](https://developers.openai.com/codex/skills/) and [Claude Code skills documentation](https://code.claude.com/docs/en/skills). The core instructions do not depend on Codex's optional `agents/openai.yaml` UI metadata.

Once installed, an explicit Codex request can use the skill name:

```text
Use $paper-to-slides to turn ./paper/main.tex into a 10-minute conference talk.
Use English slides and an English speaker script. Write the output to ./talk/.
```

For a longer reading-group presentation:

```text
Use paper-to-slides to make a 20-minute presentation from ./paper.pdf.
I am presenting someone else's work. Explain the assumptions, methods,
evidence, limitations, and discussion questions. Use Chinese for both
slides and the speaker script.
```

The agent asks for missing essentials and proceeds through production and verification. If you want an outline or sample slides for review first, include that checkpoint in your request.

## Dependencies

- **Python 3.9+**. PDF operations require `PyMuPDF>=1.23,<2`.
- **TeX Live or MiKTeX**, including latexmk, BibTeX, Beamer, Fira Sans, TikZ/PGF, booktabs, pifont, amsmath, and their supporting packages. The included example also uses appendixnumberbeamer.
- **English slides:** pdfLaTeX. A Chinese Markdown script does not change the slide compilation engine.
- **Chinese slides:** XeLaTeX, ctex, and Fandol.
- **Linked papers:** network access and a download tool. Scanned papers require image-reading capability or separate OCR; the helper does not run OCR.

On Debian/Ubuntu, relevant packages commonly include `latexmk`, `texlive-latex-extra`, `texlive-fonts-extra`, `texlive-xetex`, and `texlive-lang-chinese`. Package availability varies by distribution.

Install the Python dependency in a virtual environment:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r scripts/requirements.txt
```

The skill uses your agent client's model access. The bundled Python helpers do not call model APIs or require a separate API key.

## Build and preview

Compile the included example:

```bash
.venv/bin/python scripts/build_slides.py examples/attention-oral-10min-original-figures/main.tex --engine pdflatex --strict
```

Or copy the template to a fresh directory:

```bash
cp -R assets/template ./my-talk
.venv/bin/python scripts/build_slides.py ./my-talk/main.tex --engine pdflatex --strict
.venv/bin/python scripts/pdf_tools.py preview ./my-talk/main.pdf --output-dir ./my-talk/previews
```

The template is a gallery of **ten layouts with synthetic content**. Replace its examples when producing a real talk. Its original-figure layouts use a self-created vector figure with editable LaTeX source; they compile without any paper repository or institutional assets.

Useful PDF operations:

```bash
.venv/bin/python scripts/pdf_tools.py extract paper.pdf --output paper.txt
.venv/bin/python scripts/pdf_tools.py crop paper.pdf --page 3 --rect 40 90 550 400 --output figure.pdf
```

Crop rectangles use PDF points and a top-left origin. Cropping preserves existing vectors but cannot convert raster content into vectors. Both scripts provide `--help`.

You can also build a generated deck without the Python helper. From the deck directory:

```bash
latexmk -norc -pdf -interaction=nonstopmode -halt-on-error -file-line-error -pdflatex="pdflatex -no-shell-escape %O %S" main.tex
```

Use XeLaTeX and enable the Chinese setting in `config.tex` when slides contain Chinese. See the [template build notes](assets/template/BUILD.md) for details.

## Repository structure

| Path | Purpose |
| --- | --- |
| [SKILL.md](SKILL.md) | Entry point, defaults, workflow, and completion criteria |
| `agents/openai.yaml` | Optional Codex UI metadata |
| `references/` | Reading, storytelling, visual design, and verification guidance |
| `assets/template/` | Reusable Beamer theme, configuration, ten layouts, and synthetic assets |
| `scripts/pdf_tools.py` | PDF text extraction, page previews, and cropping |
| `scripts/build_slides.py` | latexmk builds, classified diagnostics, and JSON reports |
| `examples/attention-oral-10min-original-figures/` | Complete generated Transformer oral, script, sources, and reports |

## Verification and limitations

The skill checks claims against the paper, records original-figure treatment, compiles in strict mode, inspects every rendered page, and rebuilds from a clean copy in another location. Strict mode rejects compilation errors, missing glyphs, unresolved references, and overflows. A warning-free build still needs visual and factual review.

The example's [verification record](examples/attention-oral-10min-original-figures/verification.md) documents the checks actually performed. These cover that deliverable; they are not a claim of exhaustive compatibility across languages, papers, or TeX installations. English and Chinese workflows are provided; other writing systems may need fonts and LaTeX configuration. Timing is estimated and should be rehearsed.

For maintenance, use the [verification guidance](references/verification.md), keep new checks and outputs in a temporary directory, and record what was actually run. Standard TeX dependencies are not bundled. Generated auxiliary files and local build logs are excluded by `.gitignore`; example PDFs and source assets are retained.

## License and attribution

The skill's original instructions, helper scripts, reusable template, and original example slide content are available under the [MIT License](LICENSE).

Reproduced paper figures, tables, and quoted text retain their original rights and are **not relicensed under MIT**. The Transformer example credits Vaswani et al.; the paper expressly permits attributed reproduction of its figures and tables for journalistic or scholarly works. See [third-party notices](THIRD_PARTY_NOTICES.md) and the example's [source record](examples/attention-oral-10min-original-figures/sources.md) for scope and provenance.

The design workflow was inspired by `frontend-slides`; this project's instructions, tools, and Beamer template were written independently and contain no code or templates from it.
