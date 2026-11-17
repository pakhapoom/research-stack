<p align="center">
  <img src="assets/banner.png" alt="research-stack: study, compare, and implement research papers with Claude Code" width="100%">
</p>

# research-stack

A [Claude Code](https://code.claude.com) plugin of skills for research work.

| Skill | What it does |
| --- | --- |
| [`/research-stack:study`](plugins/research-stack) | Give it a paper link (arXiv, Hugging Face Papers, ACL Anthology, OpenReview, DOI, publisher page, direct PDF) or a local PDF, and get a grounded study guide plus Q&A. |
| [`/research-stack:compare`](plugins/research-stack#compare-papers-you-have-studied) | Work across the papers you have studied: side-by-side comparisons, questions over your whole library, conflicting numbers, and syntheses such as a related-work draft. |
| [`/research-stack:implement`](plugins/research-stack#implement-a-paper) | Turn a paper into code: an implementation spec that cites the paper for every value, then a minimal implementation. Reuses an earlier study of the same paper. |

## Install

In Claude Code:

```text
/plugin marketplace add pakhapoom/research-stack
/plugin install research-stack@research-stack
```

Or from a terminal:

```bash
claude plugin marketplace add pakhapoom/research-stack
claude plugin install research-stack@research-stack
```

Restart Claude Code after installing. Update later with
`claude plugin marketplace update research-stack`.

## Use

```text
/research-stack:study <paper> [--quick | --deep] [--for PURPOSE] [--context [FILE]] [--out DIR] [--keep-notes]
/research-stack:implement <paper | study-guide.md> [--plan-only] [--code DIR] [--out DIR]
/research-stack:compare [guides or a question] [--out DIR] [--save]
```

```text
/research-stack:study https://arxiv.org/abs/1706.03762
/research-stack:study 10.18653/v1/N19-1423 --deep
/research-stack:study ~/Downloads/paper.pdf --quick
/research-stack:study 2106.09685 --for implement
/research-stack:study 2106.09685 --context notes/reviews.md
/research-stack:implement 2106.09685
/research-stack:compare 2021-lora 2023-dora
/research-stack:compare which papers I've read use human evaluation?
```

Or just paste a paper link on its own, or ask *"Help me study this paper:
https://arxiv.org/abs/2106.09685"*. The skill triggers automatically.

| Option | Effect |
| --- | --- |
| *(none)* | Full study guide |
| `--quick` | One-page brief |
| `--deep` | Full guide plus equation walkthroughs, reproduction notes, and a reviewer-style critique |
| `--for PURPOSE` | Shape the guide for what you will do with the paper: `implement`, `review`, `cite`, `present`, or `build-on` |
| `--context [FILE]` | Add an "Outside context" section from a file, from text you paste with the request, or (with no file) from a web lookup of reviews, follow-up work, and code |
| `--out DIR` | Save to `DIR` instead of `./paper-notes/` |
| `--keep-notes` | Also keep the reading notes next to the guide |

## What you get

A Markdown study guide saved to `./paper-notes/<year>-<slug>.md`, written in the
language you asked in. Every factual claim cites the section, table, figure, or
equation it comes from, and every number is checked against the paper text.

| Section | Contents |
| --- | --- |
| Front matter | Title, authors, year, venue, links, paper type, tags, and whether the guide is based on the full text |
| TL;DR | The problem, the idea, and the headline result with its number |
| Why this paper matters | The problem, why it is hard, and what was unsatisfying about prior approaches |
| Key contributions | What is actually new, each with a citation |
| Paper map | The paper's through-line, plus a table of what each section does and its key takeaway |
| Background you need | Short primers on the concepts a reader must know first |
| The core idea | Intuition, then mechanism, then the math with every symbol defined, often with a worked example |
| Experiments and results | Setup, headline numbers copied exactly, ablations, and what the results do *not* show |
| Critical assessment | Strengths, weaknesses, and a verdict for each claim, kept separate from the authors' own claims |
| How it fits in the literature | Closest prior work and the precise difference |
| Glossary | Terms and symbols as this paper uses them |
| Check your understanding | 5–8 self-test questions, with answers hidden in a collapsible block |
| Open questions and follow-ups | Gaps the paper leaves, extension ideas, and what to read next |

`--quick` keeps the TL;DR, contributions, paper map, a method sketch, the headline
result, and one limitation. `--deep` adds equation walkthroughs, reproduction notes,
and a reviewer-style critique.

After the guide, keep asking questions. Answers come from the paper with citations,
and the skill says so when a question goes beyond it.

### Example

Abridged from a real run on *Direct Preference Optimization* (arXiv:2305.18290):

> **TL;DR**
> RLHF trains a reward model on human preference pairs, then runs RL (PPO) to
> maximize that reward while staying close to a reference model. DPO notices that the
> optimal policy of that KL-regularized objective has a closed form. Rewriting the
> reward in terms of the policy turns the whole pipeline into a single binary
> cross-entropy loss on preference pairs, with no reward model, no sampling and no
> RL. […] On TL;DR summarization it reaches a GPT-4 win rate of about 61% against
> PPO's 57% (§6.2).
>
> **Paper map**
> Through-line: take RLHF's own objective, solve it analytically, and invert the
> solution so the preference loss is written in terms of the policy. Then show that
> this loses nothing (theory) and works at least as well as PPO (experiments).
>
> | Section | What it does | Key takeaway |
> | --- | --- | --- |
> | §3 Preliminaries | The 3-phase RLHF pipeline: SFT → reward model (Eq. 1-2) → KL-regularized RL (Eq. 3) | Defines the objective DPO will solve exactly |
> | §4 DPO | Derives Eq. 4 → 5 → 6 → 7; analyzes the gradient; gives the pipeline | The partition function cancels because Bradley-Terry only uses reward *differences* |
> | §6.1 Sentiment | Reward vs. KL frontier under a known reward (22 runs) | DPO "strictly dominates PPO", even PPO with ground-truth reward |
> | … | | |

### How it reads a paper

The skill reads in three passes, like an experienced researcher, and writes what it
learns to a notes file between passes:

1. **Overview**: the abstract, the intro's framing paragraph and contributions, and
   the conclusion, to see what the paper sets out to do and how it is organized.
2. **Understand**: each main section in order, one at a time, with the overview as
   context. References and appendices are skipped.
3. **Assess**: works from the notes, re-reading only the passages needed to check
   each claim.

The guide is then written from the notes. See the
[plugin README](plugins/research-stack) for details and supported sources.

## Repository layout

```text
.claude-plugin/marketplace.json   # marketplace catalog
plugins/
  research-stack/                 # the plugin
    .claude-plugin/plugin.json    # plugin manifest
    README.md
    skills/study/                 # the /research-stack:study skill
      SKILL.md                    # the skill instructions (three-pass reading)
      references/                 # guide/notes templates, critical-reading checklist,
                                  # reader-purpose and outside-context rules
      scripts/
        fetch_paper.py            # resolves and downloads papers; finds earlier studies
        outline_paper.py          # builds the three-pass reading plan
        verify_numbers.py         # checks the guide's numbers against the paper
    skills/compare/               # the /research-stack:compare skill
      SKILL.md
      references/                 # output formats for cross-paper work
      scripts/
        index_guides.py           # indexes and searches the saved study guides
    skills/implement/             # the /research-stack:implement skill
      SKILL.md
      references/                 # implementation spec template
      scripts/
        impl_plan.py              # picks the parts of a paper that code needs
                                  # (all scripts are standard-library Python)
```

New skills go in `plugins/research-stack/skills/<name>/` and become
`/research-stack:<name>`. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE)
