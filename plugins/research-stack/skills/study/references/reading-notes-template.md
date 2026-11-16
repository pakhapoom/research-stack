# Reading notes template

The notes file is the paper's understanding written to disk. It is built in three
stages, one per pass, and is the source of truth for the study guide and for later
Q&A. Keep it terse: fragments and line references, not prose. Every number is copied
verbatim with its line reference (`L123`) or table/figure label.

```markdown
# Reading notes: <title>
source: <text_path>   outline: <run outline_paper.py again if needed>

## Pass 1: Overview
<!-- Read so far: outline, abstract, intro framing ¶, contributions, roadmap ¶, conclusion. -->

### Big picture
- Problem: … (L…)
- Gap in prior work: … (L…)
- Proposal: … (L…)
- Claimed results: … (L…)
- Paper type: method | benchmark | empirical | theory | survey | position | system

### Claims (ledger)
- C1: "<claim in the authors' words, shortened>" (L…)
- C2: …

### Section map (expected)
| § | Lines | Expected objective (from heading, first sentence, roadmap) |
| --- | --- | --- |
| 2 Problem Statement | L117-142 | Formalize full fine-tuning and its cost |

### Related guides in the library
- <guide file>: <one line from its TL;DR> (omit this block if none matched)

### Expectations and questions for pass 2
- Q1: How does <proposal> avoid <limitation>?
- Prediction: the method probably …; main evidence probably in §5, Table 4.

## Pass 2: Section notes
<!-- One block per chunk, appended right after reading it. -->

### §4 Our Method (L184-253)
- Objective: … (as expected / differs: …)
- Key points: …
- Notation: $W_0$ frozen pre-trained weights (L113); $r$ rank (L114)
- Evidence: "<number or result>" (L…) → supports C1
- Figures/tables: Fig. 1 (L68) shows …
- Deferred: hyperparameters → App. D (L1286); not opened
- Answers Q1: … | New question Q3: …

### Concept of the paper
<!-- Written once, after the last pass-2 chunk. This is the materialized understanding. -->
- Through-line (3-5 sentences): problem → key insight → mechanism → evidence → scope.
- How the sections build the argument: §2 sets up …, §3 rules out …, §4 …, §5 shows …, §7 explains why ….
- Surprises vs. pass-1 expectations: …
- Section map (actual): update the pass-1 table's objectives where they changed.

## Pass 3: Assessment
| Claim | Evidence (where) | Verdict | Note |
| --- | --- | --- | --- |
| C1 | Table 4 L397-411 | supported | single seed for WikiSQL? |

- Strengths: …
- Weaknesses / threats to validity: …
- Re-read to verify: L…-L… (what was checked)
- Appendix lookups (only if a verdict depended on deferred content): App. … L… → …
- Open questions: …
```
