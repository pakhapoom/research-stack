# Critical reading checklist

Use for the "Critical assessment" section and for `--deep` mode. Be fair: note
strengths as concretely as weaknesses, and distinguish "flawed" from "not shown".

## By paper type

| Type | What matters most |
| --- | --- |
| New method | Is the gain real and attributable to the proposed component? Strong, tuned baselines? Ablations isolating each part? Cost (compute, data, params) vs. gain? |
| Benchmark / dataset | Construction process, annotation quality and agreement, contamination/leakage risk, what capability it actually measures, licensing. |
| Empirical study | Breadth of settings, confounders, statistical rigor, whether conclusions generalize beyond the tested models/data. |
| Theory | Assumptions (and how realistic they are), tightness of bounds, whether proofs are complete, link between theory and any experiments. |
| Survey | Coverage and selection criteria, taxonomy quality, recency, whether it synthesizes or only lists. |
| Position | Strength of argument, counterarguments addressed, evidence offered. |
| System | Design trade-offs, real-world workload realism, comparison with production alternatives. |

## Evidence questions

- **Claims vs. evidence**: list each contribution claimed in the abstract/intro and
  find the exact experiment supporting it. Unsupported or partially supported claims
  are the most important finding.
- **Baselines**: are they recent, properly tuned, and given equal compute/data? Are
  numbers re-run or copied from other papers with different setups?
- **Statistics**: number of seeds/runs, variance or confidence intervals, significance
  of small gains, cherry-picked examples.
- **Data**: train/test leakage, benchmark contamination, dataset size, distribution
  shift between evaluation and claimed use case.
- **Ablations**: does removing the key component remove the gain?
- **Metrics**: do they measure what the paper claims? Any human evaluation, and how
  was it run?
- **Scope**: do conclusions extrapolate beyond tested scales, domains, or languages?
- **Reproducibility**: code, data, hyperparameters, compute budget reported?
- **Ethics and limitations**: societal impact, failure modes, and limitations the
  authors omit.

## Wording

- Use calibrated language: "the paper does not report…", "it is unclear whether…",
  "Table 3 suggests…, though with a single seed".
- Never fabricate a missing baseline's result or a citation. Suggest *what* should be
  compared, not invented numbers.
