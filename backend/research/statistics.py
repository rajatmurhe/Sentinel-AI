"""Paired seed summaries. Descriptive intervals, not a superiority declaration."""
import json
from itertools import product
import numpy as np
import pandas as pd
from scipy.stats import t


def write_comparisons(output):
    rows = []
    for file, group, full, metrics in [
        ('detection-runs.csv','model','Full SentinelAI',['f1','roc_auc','average_precision']),
        ('adaptive-runs.csv','variant','Full SentinelAI',['attack_success_rate','risk_after_defence','exfiltrated_mb','res','adaptation_handling'])]:
        frame = pd.read_csv(output/file)
        proposed = frame[frame[group].eq(full)].set_index('seed')
        for other in frame[group].unique():
            if other == full: continue
            baseline = frame[frame[group].eq(other)].set_index('seed')
            for metric in metrics:
                if metric not in frame: continue
                paired = pd.concat([proposed[metric],baseline[metric]],axis=1).dropna()
                d = paired.iloc[:,0].to_numpy()-paired.iloc[:,1].to_numpy(); n=len(d)
                if n < 2: continue
                mean, sd = d.mean(),d.std(ddof=1)
                width = t.ppf(.975,n-1)*sd/np.sqrt(n)
                signs = np.array(list(product([-1,1],repeat=n))) if n <= 15 else np.random.default_rng(0).choice([-1,1],(10000,n))
                p = float(np.mean(np.abs((signs*d).mean(axis=1)) >= abs(mean)-1e-15))
                rows.append({'experiment':file,'comparator':other,'metric':metric,'n_pairs':n,
                             'full_minus_comparator_mean':mean,'paired_sd':sd,
                             'descriptive_t95_low':mean-width,'descriptive_t95_high':mean+width,
                             'two_sided_sign_flip_p':p})
    result = pd.DataFrame(rows)
    # Holm correction within each experiment across reported comparisons.
    result['holm_p'] = np.nan
    for _, group in result.groupby('experiment'):
        order = group.sort_values('two_sided_sign_flip_p').index
        adjusted = np.maximum.accumulate([min(1.,result.loc[idx,'two_sided_sign_flip_p']*(len(order)-i)) for i,idx in enumerate(order)])
        result.loc[order,'holm_p'] = adjusted
    result.to_csv(output/'paired-comparisons.csv',index=False)
    with (output/'research-report.md').open('a') as stream:
        manifest = json.loads((output/'manifest.json').read_text())
        stream.write('\n## Evaluation protocol and paired uncertainty\n\n')
        stream.write(f"Protocol: {manifest.get('evaluation_mode','original')}. Thresholds: {manifest.get('threshold_selection','validation quantile')}.\n\n")
        stream.write('The enhanced protocol was developed after inspecting the original benchmark results. Its training/validation selection avoids direct test fitting, but this is an exploratory rerun on the same test period, not a fresh confirmatory holdout. The synthetic response simulator is unchanged; its repeated outcomes do not demonstrate an effect of the new CERT preprocessing.\n\n')
        stream.write('Paired differences, descriptive t intervals, exact seed sign-flip p-values and Holm-adjusted p-values are in `paired-comparisons.csv`. Five seeds on one time split are a small sample: the smallest possible two-sided exact sign-flip p-value is 0.0625. No population-level or statistically significant superiority is established by this run.\n')
