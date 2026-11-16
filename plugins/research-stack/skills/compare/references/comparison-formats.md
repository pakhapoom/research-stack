# Output formats for cross-paper work

Pick the format for the task. Guide references use the guide's file name without
`.md`, then the section, then the guide's own citation into the paper:
`[2021-lora, Experiments: Table 2]`. Drop a row or part that has nothing in it.

## Compare

```markdown
**Guides used:** 2021-lora (standard), 2023-dora (quick)   **Left out:** … (why)

| | <Paper A, short name> | <Paper B> |
| --- | --- | --- |
| Problem | … | … |
| Core idea | … | … |
| What is trained / changed | … | … |
| Data and benchmarks | … | … |
| Headline result | number, metric, setting [ref] | … |
| Cost (compute, params, data) | … | … |
| Main weakness (from the guide's assessment) | … | … |

**Where they agree:** …
**Where they differ:** the precise difference, not "A is better".
**Can their numbers be compared?** Yes, on <dataset, metric, setting> / No, because ….
**My inference:** what follows from putting them together, labelled as inference.
```

Choose rows that fit the paper types; for benchmarks use construction, size, what is
measured, and known problems instead of core idea and cost.

## Library question

```markdown
**Answer:** one or two sentences.

| Guide | What it says | Where |
| --- | --- | --- |
| 2024-rolellm | Human evaluation on … with … annotators | [Experiments: Table 5] |

**Not mentioned in:** <guides that matched nothing>
**Guides not checked:** <if any were skipped, and why>
```

## Conflicts

```markdown
| # | Claim or number | Paper A says | Paper B says | Same setting? | Status |
| --- | --- | --- | --- | --- | --- |
| 1 | <method> on <dataset>, <metric> | 71.2 [ref] | 68.9 [ref] | No: B re-ran with a smaller model | explained |

Status is one of: `explained` (different setting, named), `open` (same setting as far
as the guides and papers say), `unclear` (a setting is not reported).
For each `open` or `unclear` row: what you checked in the papers' text and what
would settle it.
```

## Synthesis

```markdown
## <Topic>

**Scope:** the <n> guides used, and what the library does not cover.

### <Theme 1>
Two to five sentences that connect the papers, each statement with its guide
reference. Organise by theme or by disagreement, never one paragraph per paper.

### <Theme 2>
…

### Open problems
What the guides' "Open questions" and "Critical assessment" sections share.
```

For a related-work draft, write connected prose in the user's field's style and keep
the guide references as bracketed placeholders for the user to turn into citations.
Say that it covers only the papers in the library.

## Reading path

```markdown
| Next paper | Why | Suggested by |
| --- | --- | --- |
| <title> | Closest prior work of two papers you studied | 2021-lora, 2023-dora (follow-ups) |

Order: what to read first and what it unlocks. Mark anything that comes from
outside knowledge rather than from the guides.
```

## Front matter for `--save`

```markdown
---
title: "<short title of the comparison or synthesis>"
kind: <compare | question | conflicts | synthesis | reading-path>
guides: [<guide file names>]
created: <YYYY-MM-DD>
---
```
