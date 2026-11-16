# Reader's purpose (`--for`)

The purpose changes what the guide spends its words on. It does not change the three
passes, the grounding rules, or the template's section order. For each purpose:
expand the listed sections, keep the others to a few lines, and add the one purpose
section after "Critical assessment". Record the purpose in the front matter.

| Purpose | The reader will… | Expand | Keep short | Purpose section to add |
| --- | --- | --- | --- | --- |
| `implement` | write code for the method | The core idea (mechanism and formalism), experiment setup | Why this paper matters, How it fits in the literature | **Reproduction notes** |
| `review` | referee the paper or judge it for a reading group | Critical assessment, Experiments and results | Background you need, Glossary | **Review material** |
| `cite` | cite it in their own writing | Key contributions, what the results do *not* show | The core idea (intuition only), Check your understanding | **Citing this paper** |
| `present` | explain it to an audience | Why this paper matters, The core idea (intuition and one worked example) | Formalism beyond the key equation | **Talk outline** |
| `build-on` | extend it in their own research | Critical assessment, Open questions and follow-ups | Background you need | **Research directions** |

## Purpose sections

**Reproduction notes** (`implement`). Hyperparameters, data splits, preprocessing,
compute, code and data links, and everything underspecified that would block a
reimplementation. This purpose may open deferred appendix ranges that hold
implementation details; record which lines you opened in the notes. Write the
self-check questions about mechanics ("what is the shape of…", "what happens at
initialization"). This is the same section `--deep` adds; do not write it twice.

**Review material** (`review`). Use all of `critical-reading.md`. Give: a neutral
summary of the claims in three or four sentences; strengths; weaknesses, each tied
to a claim and its evidence; questions for the authors; experiments or analyses that
would change your assessment. Provide points with evidence, not a score or an
accept/reject recommendation: that judgement is the reviewer's.

**Citing this paper** (`cite`). What the paper can be cited for, as precise
statements with their scope (model, data, setting) and source; what it should *not*
be cited for (claims it does not test, or that Pass 3 found unsupported); two or
three sentences worth quoting, verbatim with line references; and a BibTeX entry
built only from the fetched metadata, leaving out any field you do not have.

**Talk outline** (`present`). A slide-by-slide outline (8–12 slides) that follows
the paper's through-line, the figures and tables worth showing (by number), the one
equation to keep, and the questions an audience is likely to ask, with answers
grounded in the paper.

**Research directions** (`build-on`). Assumptions that could be relaxed, settings
left untested, and weaknesses that are opportunities; three to five concrete
extension ideas, each with the first experiment to run and what it would need
(data, code, compute, as far as the paper reports them). Label every idea as your
inference, not the paper's claim.
