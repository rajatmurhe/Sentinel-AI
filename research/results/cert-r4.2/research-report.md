# SentinelAI research results

Detection rows use the temporally held-out r4.2 user-day test split. Static SentinelAI and ablations use validation-calibrated thresholds. Adaptive-attacker results come from a separate closed-loop simulator and must not be interpreted as CERT outcomes.

## Detection results

| Model | Precision | Recall | F1 | ROC-AUC | False-positive rate |
|---|---:|---:|---:|---:|---:|
| AAS ablation | 0.004 ± 0.000 | 0.043 ± 0.004 | 0.007 ± 0.001 | 0.743 ± 0.014 | 0.047 ± 0.000 |
| AAS + RES ablation | 0.003 ± 0.000 | 0.042 ± 0.003 | 0.006 ± 0.001 | 0.739 ± 0.014 | 0.047 ± 0.000 |
| Static SentinelAI baseline | 0.003 ± 0.000 | 0.041 ± 0.003 | 0.006 ± 0.000 | 0.700 ± 0.018 | 0.048 ± 0.000 |
| Proposed adaptive SentinelAI | 0.004 ± 0.000 | 0.043 ± 0.005 | 0.007 ± 0.001 | 0.754 ± 0.013 | 0.047 ± 0.000 |
| Isolation Forest | 0.002 ± 0.000 | 0.030 ± 0.002 | 0.004 ± 0.000 | 0.769 ± 0.009 | 0.049 ± 0.000 |
| One-Class SVM | 0.004 ± 0.000 | 0.045 ± 0.005 | 0.007 ± 0.001 | 0.438 ± 0.025 | 0.047 ± 0.001 |

## Closed-loop adaptive attacker and ablation

| Policy | Attack success rate | Successful actions | Attempts | Exfiltrated MiB | Risk after defence | Risk reduction | AAS | RES | Adaptation handling | Response ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| AAS ablation | 0.233 ± 0.054 | 0.640 ± 0.139 | 3.520 ± 0.612 | 18.563 ± 5.047 | 13.346 ± 2.992 | 0.036 ± 0.021 | 0.186 ± 0.017 | 0.550 ± 0.072 | 0.947 ± 0.064 | 2.232 ± 1.211 |
| AAS + RES ablation | 0.238 ± 0.060 | 0.610 ± 0.152 | 3.300 ± 0.465 | 18.358 ± 5.175 | 12.680 ± 2.527 | 0.040 ± 0.021 | 0.181 ± 0.012 | 0.556 ± 0.070 | 0.963 ± 0.063 | 1.735 ± 0.256 |
| Static SentinelAI baseline | 0.237 ± 0.049 | 0.780 ± 0.251 | 3.900 ± 0.737 | 19.273 ± 5.542 | 16.073 ± 3.655 | 0.027 ± 0.025 | 0.196 ± 0.018 | 0.527 ± 0.076 | 0.910 ± 0.051 | 1.864 ± 0.362 |
| Proposed adaptive SentinelAI | 0.232 ± 0.053 | 0.680 ± 0.168 | 3.740 ± 0.806 | 19.896 ± 6.516 | 13.213 ± 1.745 | 0.040 ± 0.024 | 0.186 ± 0.006 | 0.532 ± 0.045 | 0.957 ± 0.043 | 2.105 ± 0.787 |

Figures: `research-results.png` and `adaptive-metrics.png`.

## Interpretation limits

- CERT insider labels mark official activity windows; they do not label each event as malicious. The extracted observational data cannot establish that a response caused a later change, so its AAS/RES are observational temporal measures.
- CERT features use external-recipient email size as a transfer proxy, file event counts without sensitivity labels, and daily first-to-last event span as a duration proxy. See feature metadata for full definitions.
- The adaptive attacker and enforcement effects are explicitly simulated assumptions, separate from the offline detector evaluation.
- Seed variation measures training bootstrap and simulator randomness on one chronological split; it is not a population-level confidence interval.
