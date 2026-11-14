# Study guide template

Use this structure for the default and `--deep` modes. Drop a section only if it truly
does not apply (e.g. no experiments in a theory paper) and say why in one line.

For `--quick`, write only: front matter, TL;DR, Key contributions, Paper map (table
only), Method sketch (≤ 1 paragraph), Headline result, One main limitation.

````markdown
---
title: "<exact paper title>"
authors: [<first author>, <second author>, ...]
year: <year>
venue: <venue or arXiv>
source: <landing URL>
pdf: <pdf URL if any>
paper_type: <method | benchmark | empirical | theory | survey | position | system>
tags: [<3-6 topic tags>]
studied: <today's date, YYYY-MM-DD>
depth: <quick | standard | deep>
content_basis: <full-text | summarized-fetch | abstract-only>
---

# <Paper title>

## TL;DR
2–3 sentences: the problem, the idea, and the headline result with its number.

## Why this paper matters
- The problem and why it is hard or important.
- What was unsatisfying about prior approaches (as the authors frame it).

## Key contributions
Numbered list of what is actually new, each with a citation (§, Table, Fig.).

## Paper map
How the paper is built, from the notes' "Concept of the paper" and actual section map:
one sentence on the through-line, then a table.

| Section | What it does | Key takeaway |
| --- | --- | --- |
| §2 Problem Statement | Formalizes … | … |

Mention appendix material only as "deferred to App. X" (appendices are not read).

## Background you need
Short primers on the 2–5 concepts a reader must know first, with pointers to
canonical references the paper cites.

## The core idea
1. **Intuition** — plain-language explanation or analogy.
2. **Mechanism** — how it works step by step; include a small diagram in text or a
   Mermaid block if it clarifies the pipeline/architecture.
3. **Formalism** — key equations, each followed by "where …" defining every symbol
   and one sentence on what the equation achieves.

## Experiments and results
- Setup: datasets, baselines, metrics, compute (as reported).
- Main results: a compact table of the headline numbers, copied exactly, with the
  table/figure reference.
- Ablations and analyses: what each one shows.
- What the results do *not* show.

## Critical assessment
Your own evaluation, clearly separated from the authors' claims:
- Strengths.
- Weaknesses, threats to validity, missing baselines or ablations.
- Do the experiments support each claimed contribution? (claim → evidence → verdict)
- Limitations the authors acknowledge vs. ones they do not.

## How it fits in the literature
- Closest prior work and the precise difference.
- What later work this enables or what it might be compared against.

## Glossary
| Term / symbol | Meaning in this paper |
| --- | --- |

## Check your understanding
5–8 questions ranging from recall to transfer, with concise answers in a
collapsible block:

<details><summary>Answers</summary>

1. ...

</details>

## Open questions and follow-ups
- Questions the paper leaves open.
- Ideas for extensions or experiments.
- Suggested next papers to read (only ones cited in the paper or that you are
  confident exist; mark any from outside knowledge).
````

## Extra sections for `--deep`

Insert after "Experiments and results":

- **Equation walkthrough** — every central equation derived or explained line by
  line, with a tiny numeric example where feasible.
- **Reproduction notes** — hyperparameters, data splits, compute, code/data links
  (if released), and anything underspecified that would block reproduction. Details
  deferred to an appendix may be looked up here; say which appendix lines you opened.
- **Reviewer-style critique** — follow `critical-reading.md`; end with a summary of
  the strongest and weakest claims.
