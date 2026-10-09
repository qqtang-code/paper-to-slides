# Third-party notices

The repository's MIT license covers its original skill instructions, helper
scripts, reusable template, and original presentation content. It does not
relicense reproduced research figures, tables, or quoted passages. Their
original rights and applicable conditions continue to apply, including when
they are embedded in a generated PDF.

## Attention Is All You Need

The example under `examples/attention-oral-10min-original-figures/` presents
*Attention Is All You Need* by Ashish Vaswani, Noam Shazeer, Niki Parmar,
Jakob Uszkoreit, Llion Jones, Aidan N. Gomez, Łukasz Kaiser, and Illia
Polosukhin (NeurIPS 2017).

Version: [arXiv:1706.03762v7](https://arxiv.org/abs/1706.03762v7).

The paper's first PDF page and matching `ms.tex` state:

> Provided proper attribution is provided, Google hereby grants permission to
> reproduce the tables and figures in this paper solely for use in journalistic
> or scholarly works.

The scholarly example reproduces these items with slide-level attribution:

- Figure 1: `figure1-architecture.png` and `figure1-attention-detail.pdf`.
- Figure 2: `figure2a-attention.png` and `figure2b-multihead.png`.
- Table 2: `table2-original.pdf`.
- Table 3, base row and group (A): `table3-heads-original.pdf`.

`enfr-prose-original.pdf` quotes a paragraph from Section 6.1 to document a
discrepancy between the paper's prose and table. It remains attributed paper
text, outside the MIT license. The figure/table permission quoted above is
specific to figures and tables.

The original paper's arXiv record links the
[arXiv non-exclusive distribution license](https://arxiv.org/licenses/nonexclusive-distrib/1.0/).
This is not an MIT license for the paper. Asset paths, checksums, crop
coordinates, and source locations are recorded in the example's
[sources.md](https://github.com/qqtang-code/paper-to-slides/blob/main/plugins/paper-to-slides/skills/paper-to-slides/examples/attention-oral-10min-original-figures/sources.md).

## Dependencies

Python and TeX dependencies are installed separately and retain their own
licenses. No commercial fonts or TeX distribution files are bundled. The
synthetic figure in `assets/template/figures/` was created for this project
and is not a third-party paper figure.
