# Implementation spec template

The spec is the contract between the paper and the code. Keep it terse: tables and
line references, not prose. Sources are line ranges of `text_path` (`L184-253`) plus
the paper's own label (§, Eq., Table, Alg., App.).

Labels for anything that does not come from the paper's text:
`ASSUMED` (your choice, with the reason), `FROM OFFICIAL CODE`, `USER`.

````markdown
# Implementation spec: <paper title>

paper: <landing URL>
text: <text_path>
context: <study notes | study guide | none (targeted read)>
framework: <e.g. PyTorch 2.x>   scope: <what this implementation covers>
official code: <URL (L…) | none linked>   consulted: <no | yes, for …>

## Scope
- Implemented: …
- Not implemented: … (why)

## Components
| # | Component | Paper source | Code (file: symbol) | Notes |
| --- | --- | --- | --- | --- |
| 1 | Low-rank update of a linear layer | §4.1, Eq. 3, L201-214 | `lora.py: LoRALinear.forward` | … |

## Equations
For each equation the code implements: the equation as written, every symbol with
its shape or type, and the code line that implements it.

| Eq. | As in the paper | Symbols | Code |
| --- | --- | --- | --- |
| 3 | $h = W_0 x + BAx$ | $W_0 \in \mathbb{R}^{d \times k}$ frozen; $B \in \mathbb{R}^{d \times r}$; $A \in \mathbb{R}^{r \times k}$ | `LoRALinear.forward` |

## Algorithm
Numbered steps or pseudocode, following the paper's algorithm box if it has one
(Alg. …, L…). Mark each step you had to infer.

## Hyperparameters and settings
| Name | Value | Source | Label |
| --- | --- | --- | --- |
| rank $r$ | 8 | App. D, Table 9, L1301 | |
| dropout | 0.0 | not reported | ASSUMED: common default; no effect on the core module |

## Data and evaluation
- Datasets, splits, preprocessing: … (source)
- Metrics and how they are computed: … (source)
- Baselines, if in scope: …

## Target numbers
The rows a full reproduction should match, copied exactly.

| Setting | Metric | Value | Source |
| --- | --- | --- | --- |

## Properties to test
Facts the paper states that code can check without training.

| Property | Source | Test |
| --- | --- | --- |
| The update is zero at initialization ($B = 0$) | §4.1, L209 | `test_zero_init` |

## Gaps and ambiguities
| Item | What the paper says | Decision | Label |
| --- | --- | --- | --- |
| Which layers are adapted | "attention weights" (L231); Table 5 varies them | $W_q$ and $W_v$ | ASSUMED: best row of Table 5 |
````
