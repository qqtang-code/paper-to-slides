# Sources and evidence

## Input and scope

- Supplied URL: https://arxiv.org/abs/1706.03762
- Resolved version: https://arxiv.org/abs/1706.03762v7 (last revised 2 August 2023).
- Paper: *Attention Is All You Need*, Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N. Gomez, Łukasz Kaiser, and Illia Polosukhin. NeurIPS 2017.
- Retrieved 26 September 2026. Matching PDF and source returned HTTP 200, with `application/pdf` and `application/gzip` respectively. PDF signature and 15-page count checked. All 25 archive members were inspected before extraction; only safe relative regular-file/directory entries were accepted. No bundled scripts were executed.
- PDF: https://arxiv.org/pdf/1706.03762v7; 2,215,244 bytes; SHA-256 `bdfaa68d8984f0dc02beaca527b76f207d99b666d31d1da728ee0728182df697`.
- Source: https://arxiv.org/src/1706.03762v7; 1,150,988 bytes; SHA-256 `2e7a7d9ee2520d22eb23dae0cb148e167be02a30d6cb3f11b1c67723194339c6`.
- `ms.tex` includes `introduction.tex`, `background.tex`, `model_architecture.tex`, `why_self_attention.tex`, `training.tex`, `results.tex`, and `visualizations.tex`; the conclusion and bibliography are inline. Claims were checked against the source and matching PDF, including visual inspection of architecture/mechanism diagrams and result-table alignment.
- English slides, Chinese script, anonymous presenter. Public paper authors are credited separately. This is a presentation of the paper, not a claim that the presenter authored it.
- This deck is a standalone deliverable; it needs no other project, deck, or skill checkout to build.

## Core-figure inventory and reserved narrative time

Core original figures were assigned main-talk pages and time before the prose outline was completed. No core original was replaced by a redraw.

| Original | Role and contribution | Source asset / location | Final treatment and time |
| --- | --- | --- | --- |
| Figure 1 | Complete attention-based encoder–decoder; source/prefix information flow | `Figures/ModalNet-21.png`; `model_architecture.tex`, `fig:model-arch`; PDF p. 3 | Main page 3, complete original, 55 s; main page 6, connected enlargement, 55 s. No recoloring or relabeling. |
| Figure 2 left | Scaled dot-product attention and optional mask | `Figures/ModalNet-19.png`; `fig:multi-head-att`; PDF p. 4 | Main page 4, full original panel, 60 s. Equation and definitions outside the image. |
| Figure 2 right | Parallel projected attention heads and their combination | `Figures/ModalNet-20.png`; same figure | Main page 5, full original panel, 45 s. Panel order maintained across the two pages. |
| Table 2 | Main translation-quality and estimated-training-cost evidence | `results.tex:4–43`, `tab:wmt-results`; PDF p. 8 | Main page 9, original complete table grid, 65 s; all rows and headers preserved. Large EN–DE transcriptions guide the comparison. |
| Table 3, base and group (A) | Empirical support for multi-head choice | `results.tex:49–70,103–105`, `tab:variations`; PDF p. 9 | Main page 10, original contiguous crop with headers/base/group label, 45 s. Other variation groups are outside the head-count question; positional ablation stated in backup. |
| Figures 3–5 | Qualitative long-range, anaphora, and syntactic attention examples | `visualizations.tex`; `vis/*.pdf`; PDF pp. 13–15 | Omitted: the 10-minute story centers on architecture and quantitative translation evidence. Qualitative head examples are not necessary to support the selected claim and are not treated as causal explanations. |
| Table 4 | English constituency parsing | `results.tex:117–166`; PDF p. 10 | Omitted: secondary task outside the selected translation story. No claim of universal downstream superiority is made. |

## Asset transformations

All crop rectangles use physical pages, top-left origin, and PDF points `(x0,y0,x1,y1)`. The existing skill crop helper was used. PNG originals remain raster; PDF cropping does not vectorize them. Original colors, arrows, symbols, and order are retained. Slide captions, summaries, and large numeric callouts are presenter additions outside the images.

| Local asset | Original / transformation | Context preserved |
| --- | --- | --- |
| `figures/figure1-architecture.png` | Original, byte-for-byte `Figures/ModalNet-21.png` (1520 × 2239) | Entire architecture, input/output labels, positions, repeat markers, residual paths |
| `figures/figure2a-attention.png` | Original, byte-for-byte `Figures/ModalNet-19.png` (445 × 884) | Full left panel including Q/K/V, scale, optional mask, softmax, and output |
| `figures/figure2b-multihead.png` | Original, byte-for-byte `Figures/ModalNet-20.png` (835 × 1282) | Full right panel including original V/K/Q order, learned projections, h, concat, and output |
| `figures/figure1-attention-detail.pdf` | Crop of PDF p. 3: `(218,179,410,307)` | Encoder output route into decoder cross-attention, lower masked attention, residual paths, decoder repeat marker. Whole architecture is on page 3; omitted top decoder layers/embeddings named on page 6. Embedded content is raster. |
| `figures/table2-original.pdf` | Vector-preserving crop of PDF p. 8: `(130,94,483,245)` | Entire table grid including all rows, language/metric headers, units, and model names. Caption is outside the crop; evaluation split stated on the slide/script. |
| `figures/table3-heads-original.pdf` | Vector-preserving crop of PDF p. 9: `(107,128,509,212)` | Full column headers, base row, group (A), all four variation rows. Blank cells inherit base settings; conditions restated outside. |
| `figures/enfr-prose-original.pdf` | Vector-preserving crop of PDF p. 8: `(107,488,505,531)` | Section 6.1's full EN–FR paragraph, including 41.0 and dropout condition |
| Inline TikZ on page 2 | Supplemental presenter illustration | Selected recurrent/self-attention connections; not paper evidence or a replacement architecture |
| Inline TikZ on page 7 | Supplemental presenter illustration | Shifted-input causal mask with allowed/blocked legend and BOS definition; supplements Figures 1–2 |

No opaque labels or boxes cover the original image content. The overview establishes the whole architecture; enlargements, spoken pointing cues, and faithful nearby transcriptions explain its essential labels.

## Claim audit

Source line numbers refer to the matching v7 archive. Physical PDF pages supplement stable section/figure identifiers.

| PDF page / claim | Type | Evidence | Conditions / treatment |
| --- | --- | --- | --- |
| 1–2: attention replaces sequence-aligned recurrence/convolution | Author contribution | `introduction.tex:3–13`, `background.tex`; Sections 1–2 | Does not claim the model consists only of attention operators |
| 3: six encoder/six decoder layers, model width 512, residual then norm | Reported method | `model_architecture.tex:12–20`; Section 3.1, Figure 1 | Base model; post-norm ordering preserved |
| 4: softmax(QKᵀ/√d_k)V | Reported method | `model_architecture.tex:24–53`; Section 3.2.1, Eq. (1) | Scale discussion follows dot-product/gradient motivation; no unconditional probability or interpretability claim |
| 5: learned projections; eight heads, 64-dimensional keys/values | Reported method | `model_architecture.tex:82–99`; Section 3.2.2 | 8 × 64 = 512 is a dimensionality calculation; roles are learned |
| 6: decoder Q, final encoder K/V | Reported method | `model_architecture.tex:20,105–113`; Sections 3.1, 3.2.3 | Cross-attention differs from decoder masked self-attention |
| 7: shifted targets, causal mask, positions | Reported method + illustration | `model_architecture.tex:20,113,143–155`; Sections 3.1, 3.5 | With shifted inputs, diagonal access is allowed; future targets remain blocked. Parallel training does not imply parallel autoregressive generation. |
| 8: 4.5M/36M pairs; eight P100s; base 100K/~12 h; big 300K/~3.5 days | Reported setup | `training.tex:6,10`; Sections 5.1–5.2 | Paper-reported hardware and durations, not reproduced measurements |
| 8–9: test protocol and cost estimates | Reported setup + scope | `results.tex:41,43`; Section 6.1 | newstest2014; beam 4, length penalty 0.6; last 5 base/20 big checkpoints averaged. FLOPs estimated from duration, GPU count and throughput; systems have different budgets. |
| 9: big 28.4 vs ConvS2S ensemble 26.36 | Reported values + presenter arithmetic | `results.tex:23,26,37`; Table 2 EN–DE cells | 28.40 − 26.36 = **2.04 BLEU points**, not percent; strongest prior EN–DE row in this historical table |
| 9: base 27.3, estimated 3.3 × 10^18 training FLOPs | Reported values | `results.tex:25`; Table 2 | Within-paper conditions; not a matched-budget speedup or significance claim |
| 9, 14: EN–FR 41.8 vs 41.0 | Source discrepancy | `ms.tex:127`, `results.tex:26,39`; abstract/Table 2 vs Section 6.1 prose | Preserve both; headline uses consistent EN–DE values; discrepancy spoken on page 9 |
| 10: heads 1/4/8/16/32 → 24.9/25.5/25.8/25.8/25.4 | Reported values + arithmetic | `results.tex:49,64–70,103–105`; Table 3 base/(A) | newstest2013 dev, no checkpoint averaging. Vary dimensions with head count; 25.8 − 24.9 = 0.9 BLEU. Eight and sixteen tie; thirty-two declines. |
| 11: O(n²d) vs O(nd²), O(1) vs O(n) sequential steps/path | Reported asymptotics + presenter scope | `why_self_attention.tex:14–27,84–89`; Table 1 | Selected layer-type comparisons. Full blocks include projections/FFNs; no inference-latency guarantee. |
| 12: synthesis | Presenter synthesis | Sections 3, 4, 6 | Bounded to architecture and historical translation evidence |
| 13: FFN, PE equations, dropout, warmup, smoothing | Reported method | `model_architecture.tex:18–20,119–124,146–155`; `training.tex:12–25,42` | Base dimensions; dropout before residual addition; 4,000 warmup steps |
| 14: sinusoidal 25.8 vs learned 25.7 | Reported ablation | `results.tex:64,91,103,107`; Table 3 base/(E) | Development scores, near equality; no significance assertion |

## Narrative and timing

| PDF page | Frame ID | Question | Seconds | Cumulative |
| --- | --- | --- | ---: | --- |
| 1 | title | What is the central claim? | 20 | 0:20 |
| 2 | motivation | Why remove recurrence? | 45 | 1:05 |
| 3 | architecture | What is the complete architecture? | 55 | 2:00 |
| 4 | attention | How does one attention operation work? | 60 | 3:00 |
| 5 | multihead | Why project into multiple heads? | 45 | 3:45 |
| 6 | decoder | How do source and target interact? | 55 | 4:40 |
| 7 | order | How are order and causality retained? | 50 | 5:30 |
| 8 | setup | What exactly was evaluated? | 35 | 6:05 |
| 9 | results | Does translation quality improve? | 65 | 7:10 |
| 10 | ablation | Does head count matter? | 45 | 7:55 |
| 11 | limits | Where does the efficiency claim stop? | 35 | 8:30 |
| 12 | closing | What should the audience retain? | 30 | 9:00 |

540 seconds of main narration; 60 seconds of buffer to a 10-minute slot. Backup physical pages 13–15 are excluded. Timing includes pointing, pauses, and transitions; a live rehearsal is still needed.

## Attribution and reproduction

The v7 PDF p. 1 and `ms.tex:121–123` explicitly grant reproduction of figures and tables, with proper attribution, solely for journalistic or scholarly works. Original assets are included here for this scholarly presentation and credited on their slides. They are not relicensed as part of the reusable theme. The arXiv landing page separately links its nonexclusive distribution license. No commercial fonts, personal contacts, or institutional logos are bundled.
