# research-stack plugin

Study an academic paper from a link and come away understanding it, then turn it
into code.

Given a URL, arXiv ID, DOI, or local PDF, the `study` skill fetches the full
text, reads the whole paper, and writes a Markdown study guide to `./paper-notes/`:

- TL;DR and why the paper matters
- Key contributions, each cited to a section, table, or equation
- Background primers, the core idea (intuition → mechanism → math)
- Experiments and results, copied exactly with references
- A critical assessment kept separate from the authors' claims
- Glossary, self-check questions with answers, and follow-up reading

After the guide, keep asking questions; answers stay grounded in the paper.

## How it reads a paper

The skill reads in three passes and controls what enters Claude's context at each
stage, writing a notes file between passes:

| Pass | Reads | Writes to notes |
| --- | --- | --- |
| 1. Overview | Section outline, abstract, the intro's framing paragraph and contributions, the conclusion | Big picture, claim ledger, section map with each section's expected objective |
| 2. Understand | Each main section in order, one at a time (references and appendices skipped) | Per-section notes, then the "concept of the paper": how the sections build the argument |
| 3. Assess | The notes, plus targeted re-reads to verify | Verdict per claim, strengths, weaknesses |

The guide is written from the notes, and every number in it is checked against the
paper text. Use `--keep-notes` to keep the notes file.

## Install

```text
/plugin marketplace add pakhapoom/research-stack
/plugin install research-stack@research-stack
```

## Usage

```text
/research-stack:study <url | arXiv-id | DOI | path.pdf> [--quick | --deep] [--for PURPOSE] [--context [FILE]] [--out DIR] [--keep-notes]
```

| Mode | Output |
| --- | --- |
| `--quick` | One-page brief |
| default | Full study guide |
| `--deep` | Adds equation walkthroughs, reproduction notes, and a reviewer-style critique |

### Reading for a purpose

`--for` shifts what the guide spends its words on and adds one section:

| `--for` | Adds |
| --- | --- |
| `implement` | Reproduction notes: hyperparameters, data, compute, and what is underspecified |
| `review` | Review material: strengths, weaknesses tied to evidence, questions for the authors |
| `cite` | What the paper can and cannot be cited for, quotable sentences, BibTeX |
| `present` | A slide-by-slide talk outline with likely audience questions |
| `build-on` | Research directions: assumptions to relax and concrete extension ideas |

Saying it in words works too: *"I have to review this paper: <link>"*.

### Outside context

`--context` adds an "Outside context" section for what others say about the paper,
kept apart from what the paper itself says. Supply it as:

- a file: `--context notes/reviews.md`
- pasted text: paste reviews, a thread, or your own notes into the request
- nothing: `--context` alone looks up reviews, follow-up work, and the official code
  on the web

The paper is always read and assessed first, so the outside material cannot colour
the guide's own verdicts.

## Compare papers you have studied

```text
/research-stack:compare [guide names, paper references, or a question] [--out DIR] [--save]
```

Works from the study guides already in `./paper-notes/`, so it needs at least two.

| Ask | You get |
| --- | --- |
| *"compare 2021-lora and 2023-dora"* | A side-by-side table, where they agree and differ, and whether their numbers can be compared at all |
| *"which papers I've read use human evaluation?"* | An answer over the whole library, with the guide and section for each hit |
| *"do these papers agree on X?"* | Conflicting claims or numbers, each marked explained, open, or unclear |
| *"draft related work from my notes"* | A synthesis organised by theme, every statement traced to a guide |
| *"what should I read next?"* | A reading path built from the guides' own follow-up lists |

It reads only the relevant sections of each guide, using an index of section line
ranges, and never fills in a paper you have not studied from the model's memory.
`--save` writes the result to `paper-notes/syntheses/`.

`study` uses the same index: when you study a new paper, it finds related guides you
already have, links to them, and states the precise difference instead of
re-explaining shared background. New guides also record `datasets`, `metrics`, and
`baselines` in their front matter so the library can be searched by them.

## Implement a paper

```text
/research-stack:implement <url | arXiv-id | DOI | path.pdf | study-guide.md> [--plan-only] [--code DIR] [--out DIR]
```

Writes `SPEC.md`, an implementation spec in which every component, equation,
hyperparameter, and target number cites its place in the paper, and anything the
paper leaves open is labelled `ASSUMED`. Then it writes a minimal implementation of
the core method, with comments pointing at the equations, and tests for the
properties the paper states. `--plan-only` stops after the spec.

It gets the paper's context the cheapest way available:

| You have | It does |
| --- | --- |
| Studied the paper before | Reads the saved reading notes (section map, notation, appendix pointers), then only the method, setup, and appendix lines the code needs |
| Only the study guide | Reads the guide for orientation, then the same targeted lines |
| Nothing | Reads the abstract and the targeted lines; it does not run a full study |

Appendices are read here even though `study` skips them, because that is where
hyperparameters usually are.

The skill also triggers when you paste a paper link on its own, or ask naturally, e.g.
*"break down this paper for me: <link>"*.

## Supported sources

| Source | Notes |
| --- | --- |
| arXiv (`arxiv.org/abs`, `/pdf`, `/html`, `arXiv:ID`, bare IDs) | Prefers the arXiv HTML render for clean text and equations |
| Hugging Face Papers, alphaXiv | Resolved to arXiv |
| ACL Anthology | PDF and metadata |
| DOI (`doi.org/…` or bare `10.x/…`) | Metadata via Semantic Scholar / Crossref; open-access PDF when one exists |
| Publisher and proceedings pages (PMLR, NeurIPS, ACM, …) | Uses standard `citation_*` meta tags to find the PDF |
| Direct PDF links and local PDFs | Read directly |
| OpenReview | Metadata and PDF are behind a human-verification challenge; the skill asks you for the PDF or looks for an arXiv version |

Paywalled papers: if only the abstract is reachable, the guide is clearly labelled
*abstract-only* and you are asked for a PDF.

## Requirements

- `python3` (standard library only) for the bundled resolver. Without it the skill
  falls back to Claude Code's built-in web fetching.
- Recommended for non-arXiv PDFs: poppler (`brew install poppler` /
  `apt install poppler-utils`), or `pip install pypdf`. arXiv papers don't need it
  because their HTML render is converted to text directly.

## Privacy and safety

The resolver contacts only the paper's host and public metadata APIs (arXiv,
Semantic Scholar, Crossref, OpenReview) with a generic user agent. No API keys and
no personal data are sent. Downloaded papers, extracted text, and reading notes are saved under
`./paper-notes/.work/<paper>/` (git-ignored automatically) and reused on later runs,
never executed, and treated as untrusted content: instructions embedded in a paper
are ignored and reported to you.
