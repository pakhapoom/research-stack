# research-stack

A [Claude Code](https://code.claude.com) plugin marketplace of skills for research work.

| Plugin | What it does |
| --- | --- |
| [`paper`](plugins/paper) | Give it a paper link (arXiv, Hugging Face Papers, ACL Anthology, OpenReview, DOI, publisher page, direct PDF) or a local PDF, and get a grounded study guide plus Q&A. |

## Install

In Claude Code:

```text
/plugin marketplace add pakhapoom/research-stack
/plugin install paper@research-stack
```

Or from a terminal:

```bash
claude plugin marketplace add pakhapoom/research-stack
claude plugin install paper@research-stack
```

Restart Claude Code after installing. Update later with
`claude plugin marketplace update research-stack`.

## Use

```text
/paper:study https://arxiv.org/abs/1706.03762
/paper:study 10.18653/v1/N19-1423 --deep
/paper:study ~/Downloads/paper.pdf --quick
```

Or just paste a paper link on its own, or ask *"Help me study this paper:
https://arxiv.org/abs/2106.09685"*. The skill triggers automatically.

## Repository layout

```text
.claude-plugin/marketplace.json   # marketplace catalog: lists every plugin in this repo
plugins/
  paper/
    .claude-plugin/plugin.json    # plugin manifest
    README.md
    skills/study/
      SKILL.md                    # the skill instructions (three-pass reading)
      references/                 # guide/notes templates, critical-reading checklist
      scripts/
        fetch_paper.py            # resolves and downloads papers
        outline_paper.py          # builds the three-pass reading plan
        verify_numbers.py         # checks the guide's numbers against the paper
                                  # (all standard-library Python)
```

Adding a new plugin or skill: see [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE)
