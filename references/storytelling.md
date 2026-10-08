# Storytelling and speaker scripts

## Adapt to the setting

A conference talk defaults to 10 minutes. Use a concrete problem to introduce the central idea, explain enough of the method to make it understandable, then answer the opening question with strong evidence and explicit conditions. Move secondary lengthy tables, proofs, and ablations to backup slides; keep original figures essential to the central method or evidence in the main talk. Let information density, figures, and speaking pace determine the slide count; do not fix it at 12. Include title and closing slides in the timing budget.

A reading-group presentation defaults to 20 minutes. Add problem definitions, prerequisite concepts, key derivations or examples, experimental design, failure cases, and discussion. Identify the paper authors and presenter separately on the title slide. Use phrases such as "the authors propose," "the results show," and "my analysis" instead of automatically saying "we." Discussion slides may pose open questions without inventing answers.

Use the core-figure inventory in `sources.md` while outlining. Allocate pages and speaking time to the central original diagrams and evidence before filling in prose. Do not build a text-only outline and treat the originals as optional decoration afterward. A complex figure often needs a complete overview followed by a focused enlargement; give each a distinct question and pointing sequence. Select based on relevance and duration, without a fixed number or fraction of figures.

Before layout, identify the question each slide answers, its single main takeaway, its evidence, and its duration. Unless the user requests a review, outlining is an internal step: proceed to production afterward.

## Adapt to the paper type

| Type | Narrative | Evidence and constraints |
| --- | --- | --- |
| Empirical or systems | Bottleneck → method → setup → results → cost and limitations | Fair comparisons, metric direction, budgets, uncertainty, and whether statistical tests were reported |
| Theoretical | Definitions and assumptions → theorem → intuition or example → key proof steps → scope | Preserve quantifiers, conditions, constants, and asymptotic meaning; do not force in benchmark tables or figures when none serve the argument |
| Survey | Scope and search method → taxonomy → representative work → disagreements → research gaps | Distinguish the survey's synthesis from original studies; state the coverage cutoff and do not invent a new method |

## Numbers and conclusions

- Keep the model, dataset, split, evaluation protocol, and compute budget consistent within a comparison. Do not combine incompatible settings into a claim of superiority.
- A change from 50% to 55% is **+5 percentage points**, or a **10% relative increase**. Name the baseline, units, direction, and rounding; avoid an ambiguous "5% improvement."
- Describe identical reported values as a tie or as equal at the reported precision. Do not call a difference statistically significant without supporting tests.
- An average gain must not hide declines on individual tasks. Correlations in ablations do not establish strict causal guarantees.
- Distinguish theoretical guarantees, author claims, empirical observations, and presenter inferences. Passing an LLM verifier does not establish formal correctness.

## Slide-by-slide script

Write `speaker-script.md` in the selected script language. Identify the paper, deck, slide language, script language, target duration, estimated main-talk duration, and buffer. Begin with a table of PDF page numbers, frame identifiers, titles, seconds, and cumulative time. Avoid overlays by default. If overlays are needed, record the PDF page range for each frame and each advance. List backup pages separately.

Each page should include:

```markdown
## Slide 3 — Method overview (60 seconds; cumulative 2:20)

Say: Complete spoken prose that explains relationships in the figure rather
than simply repeating the slide's bullets.

Point: Start with the input on the left, follow the arrows through the central
modules, and finish at the output.

Transition: The next slide enlarges the step that most affects the result.
```

Allocate about `target seconds × 0.9` to the main talk: approximately 540 seconds for 10 minutes or 1,080 seconds for 20 minutes. The total must match the per-slide timings. Include transitions, pauses, figure reading, and short demonstrations. Estimate using the actual language and speaker's pace, then rehearse; word count alone cannot guarantee timing. Allow time to explain complex figures. Name the figure or panel in pointing cues, trace its actual arrows or axes, and connect detail views back to the overview. Include any figure/prose discrepancy in the spoken explanation as well as the source notes. If the talk runs long, remove secondary material or move it to backup slides before increasing the speaking pace.
