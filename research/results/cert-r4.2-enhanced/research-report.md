# SentinelAI research results

Detection rows use the temporally held-out r4.2 user-day test split. Static SentinelAI and ablations use validation-calibrated thresholds. Adaptive-attacker results come from a separate closed-loop simulator and must not be interpreted as CERT outcomes.

## Detection results

| Model | Precision | Recall | F1 | ROC-AUC | False-positive rate |
|---|---:|---:|---:|---:|---:|
| AAS ablation | 0.011 ± 0.001 | 0.057 ± 0.026 | 0.018 ± 0.001 | 0.793 ± 0.013 | 0.020 ± 0.011 |
| AAS + RES ablation | 0.012 ± 0.002 | 0.093 ± 0.040 | 0.020 ± 0.003 | 0.789 ± 0.013 | 0.032 ± 0.013 |
| Static SentinelAI baseline | 0.012 ± 0.001 | 0.079 ± 0.037 | 0.021 ± 0.001 | 0.771 ± 0.016 | 0.026 ± 0.013 |
| Proposed adaptive SentinelAI | 0.011 ± 0.002 | 0.102 ± 0.021 | 0.020 ± 0.003 | 0.799 ± 0.012 | 0.036 ± 0.007 |
| Isolation Forest | 0.013 ± 0.002 | 0.054 ± 0.055 | 0.016 ± 0.003 | 0.834 ± 0.008 | 0.019 ± 0.020 |
| One-Class SVM | 0.014 ± 0.001 | 0.045 ± 0.008 | 0.021 ± 0.002 | 0.632 ± 0.017 | 0.013 ± 0.002 |

## Closed-loop adaptive attacker and ablation

| Policy | Attack success rate | Successful actions | Attempts | Exfiltrated MiB | Risk after defence | Risk reduction | AAS | RES | Adaptation handling | Response ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| AAS ablation | 0.233 ± 0.054 | 0.640 ± 0.139 | 3.520 ± 0.612 | 18.563 ± 5.047 | 13.346 ± 2.992 | 0.036 ± 0.021 | 0.186 ± 0.017 | 0.550 ± 0.072 | 0.947 ± 0.064 | 1.780 ± 0.331 |
| AAS + RES ablation | 0.238 ± 0.060 | 0.610 ± 0.152 | 3.300 ± 0.465 | 18.358 ± 5.175 | 12.680 ± 2.527 | 0.040 ± 0.021 | 0.181 ± 0.012 | 0.556 ± 0.070 | 0.963 ± 0.063 | 1.976 ± 0.661 |
| Static SentinelAI baseline | 0.237 ± 0.049 | 0.780 ± 0.251 | 3.900 ± 0.737 | 19.273 ± 5.542 | 16.073 ± 3.655 | 0.027 ± 0.025 | 0.196 ± 0.018 | 0.527 ± 0.076 | 0.910 ± 0.051 | 2.267 ± 0.781 |
| Proposed adaptive SentinelAI | 0.232 ± 0.053 | 0.680 ± 0.168 | 3.740 ± 0.806 | 19.896 ± 6.516 | 13.213 ± 1.745 | 0.040 ± 0.024 | 0.186 ± 0.006 | 0.532 ± 0.045 | 0.957 ± 0.043 | 4.248 ± 3.716 |

## Average precision

| Model | AP mean ± SD |
|---|---:|
| AAS ablation | 0.010900 ± 0.000671 |
| AAS + RES ablation | 0.011232 ± 0.000673 |
| Static SentinelAI baseline | 0.010585 ± 0.000763 |
| Proposed adaptive SentinelAI | 0.011463 ± 0.000617 |
| Isolation Forest | 0.011885 ± 0.000604 |
| One-Class SVM | 0.011388 ± 0.001761 |

Figures: `research-results.png` and `adaptive-metrics.png`.

## Interpretation limits

- CERT insider labels mark official activity windows; they do not label each event as malicious. The extracted observational data cannot establish that a response caused a later change, so its AAS/RES are observational temporal measures.
- CERT features use external-recipient email size as a transfer proxy, file event counts without sensitivity labels, and daily first-to-last event span as a duration proxy. See feature metadata for full definitions.
- The adaptive attacker and enforcement effects are explicitly simulated assumptions, separate from the offline detector evaluation.
- Seed variation measures training bootstrap and simulator randomness on one chronological split; it is not a population-level confidence interval.

## Evaluation protocol and paired uncertainty

Protocol: enhanced. Thresholds: validation F1 under FPR ceiling.

The enhanced protocol was developed after inspecting the original benchmark results. Its training/validation selection avoids direct test fitting, but this is an exploratory rerun on the same test period, not a fresh confirmatory holdout. The synthetic response simulator is unchanged; its repeated outcomes do not demonstrate an effect of the new CERT preprocessing.

Paired differences, descriptive t intervals, exact seed sign-flip p-values and Holm-adjusted p-values are in `paired-comparisons.csv`. Five seeds on one time split are a small sample: the smallest possible two-sided exact sign-flip p-value is 0.0625. No population-level or statistically significant superiority is established by this run.
