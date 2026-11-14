# paper

Study an academic paper from a link and come away understanding it.

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
/plugin install paper@research-stack
```

## Usage

```text
/paper:study <url | arXiv-id | DOI | path.pdf> [--quick | --deep] [--out DIR] [--keep-notes]
```

| Mode | Output |
| --- | --- |
| `--quick` | One-page brief |
| default | Full study guide |
| `--deep` | Adds equation walkthroughs, reproduction notes, and a reviewer-style critique |

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
`./paper-notes/.work/<paper>/` (git-ignored automatically),
never executed, and treated as untrusted content: instructions embedded in a paper
are ignored and reported to you.
