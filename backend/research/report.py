"""Render reproducible tables and figures from experiment CSV outputs."""
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def _mean_std(frame, columns, key):
    out = frame.groupby(key)[columns].agg(['mean', 'std', 'count'])
    out.columns = ['_'.join(c) for c in out.columns]
    return out.reset_index()


def _bar(ax, frame, label, mean, std, title, ylabel, color='#2563eb'):
    x = np.arange(len(frame))
    vals = frame[mean].to_numpy(dtype=float)
    err = frame[std].fillna(0).to_numpy(dtype=float)
    ax.bar(x, vals, yerr=err, capsize=4, color=color, alpha=.88)
    ax.set_xticks(x, frame[label].astype(str), rotation=18, ha='right')
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.grid(axis='y', alpha=.22)


def render_results(output):
    output = Path(output)
    detection_runs = pd.read_csv(output / 'detection-runs.csv')
    adaptive_runs = pd.read_csv(output / 'adaptive-runs.csv')
    manifest = pd.read_json(output / 'manifest.json', typ='series')
    provenance = manifest.get('provenance', {})
    source = provenance.get('source', 'Unknown') if isinstance(provenance, dict) else 'Unknown'
    release = provenance.get('release', '') if isinstance(provenance, dict) else ''
    dataset_label = f'{source} {release}'.strip()
    det = _mean_std(detection_runs, ['precision', 'recall', 'f1', 'roc_auc', 'false_positive_rate'], 'model')
    sim_metrics = ['attack_success_rate', 'successful_malicious_actions', 'malicious_attempts',
                   'exfiltrated_mb', 'risk_after_defence', 'risk_reduction', 'aas', 'res',
                   'adaptation_handling', 'response_ms']
    sim = _mean_std(adaptive_runs, sim_metrics, 'variant')
    det.to_csv(output / 'detection-summary.csv', index=False)
    sim.to_csv(output / 'adaptive-summary.csv', index=False)
    ablation = det[det.model.isin(adaptive_runs.variant.unique())].merge(
        sim, left_on='model', right_on='variant', how='inner')
    ablation.to_csv(output / 'ablation-summary.csv', index=False)

    fig, axes = plt.subplots(1, 3, figsize=(17, 5), constrained_layout=True)
    for ax, metric, title, color in [
        (axes[0], 'f1', 'Detection: F1', '#2563eb'),
        (axes[1], 'attack_success_rate', 'Simulated attacker: success rate', '#dc2626'),
        (axes[2], 'risk_reduction', 'Simulated attacker: risk reduction', '#059669'),
    ]:
        metric_frame = det if metric == 'f1' else sim
        key = 'model' if metric == 'f1' else 'variant'
        _bar(ax, metric_frame, key, f'{metric}_mean', f'{metric}_std', title,
             'mean ± SD across seeds', color)
    fig.suptitle(f'SentinelAI research evaluation ({dataset_label} detection and separate simulator)', fontsize=14)
    fig.savefig(output / 'research-results.png', dpi=180)
    plt.close(fig)

    fig, axes = plt.subplots(1, 3, figsize=(16, 4.8), constrained_layout=True)
    for ax, metric, title in [
        (axes[0], 'aas', 'Behaviour adaptation (AAS)'),
        (axes[1], 'res', 'Observed response effectiveness (RES)'),
        (axes[2], 'response_ms', 'Detect + decision time'),
    ]:
        _bar(ax, sim, 'variant', f'{metric}_mean', f'{metric}_std', title,
             'mean ± SD across seeds', '#7c3aed')
    fig.savefig(output / 'adaptive-metrics.png', dpi=180)
    plt.close(fig)

    names = {
        'Isolation Forest': 'Isolation Forest', 'One-Class SVM': 'One-Class SVM',
        'Baseline': 'Static SentinelAI baseline', '+ AAS': 'AAS ablation',
        '+ AAS + RES': 'AAS + RES ablation', 'Full SentinelAI': 'Proposed adaptive SentinelAI'
    }
    if source == 'CERT':
        detection_note = f'Detection rows use the temporally held-out {release} user-day test split. Static SentinelAI and ablations use validation-calibrated thresholds. Adaptive-attacker results come from a separate closed-loop simulator and must not be interpreted as CERT outcomes.'
    else:
        detection_note = f'Detection rows use the temporally held-out {dataset_label} data. This run is a pipeline smoke check, not the CERT paper evaluation. Adaptive-attacker results come from the separate closed-loop simulator.'
    lines = ['# SentinelAI research results', '', detection_note, '',
             '## Detection results', '',
             '| Model | Precision | Recall | F1 | ROC-AUC | False-positive rate |',
             '|---|---:|---:|---:|---:|---:|']
    for row in det.itertuples():
        label = names.get(row.model, row.model)
        lines.append(f'| {label} | {row.precision_mean:.3f} ± {row.precision_std:.3f} | {row.recall_mean:.3f} ± {row.recall_std:.3f} | {row.f1_mean:.3f} ± {row.f1_std:.3f} | {row.roc_auc_mean:.3f} ± {row.roc_auc_std:.3f} | {row.false_positive_rate_mean:.3f} ± {row.false_positive_rate_std:.3f} |')
    lines += ['', '## Closed-loop adaptive attacker and ablation', '',
              '| Policy | Attack success rate | Successful actions | Attempts | Exfiltrated MiB | Risk after defence | Risk reduction | AAS | RES | Adaptation handling | Response ms |',
              '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for row in sim.itertuples():
        label = names.get(row.variant, row.variant)
        def fmt(metric):
            mean, std = getattr(row, f'{metric}_mean'), getattr(row, f'{metric}_std')
            return 'n/a' if pd.isna(mean) else f'{mean:.3f} ± {std:.3f}'
        lines.append(f'| {label} | {fmt("attack_success_rate")} | {fmt("successful_malicious_actions")} | {fmt("malicious_attempts")} | {fmt("exfiltrated_mb")} | {fmt("risk_after_defence")} | {fmt("risk_reduction")} | {fmt("aas")} | {fmt("res")} | {fmt("adaptation_handling")} | {fmt("response_ms")} |')
    limits = []
    if source == 'CERT':
        limits += ['CERT insider labels mark official activity windows; they do not label each event as malicious. The extracted observational data cannot establish that a response caused a later change, so its AAS/RES are observational temporal measures.',
                   'CERT features use external-recipient email size as a transfer proxy, file event counts without sensitivity labels, and daily first-to-last event span as a duration proxy. See feature metadata for full definitions.']
    else:
        limits += ['This run uses the local synthetic demonstration generator and must not be reported as CERT performance.']
    limits += ['The adaptive attacker and enforcement effects are explicitly simulated assumptions, separate from the offline detector evaluation.',
               'Seed variation measures training bootstrap and simulator randomness on one chronological split; it is not a population-level confidence interval.']
    lines += ['', 'Figures: `research-results.png` and `adaptive-metrics.png`.', '',
              '## Interpretation limits', ''] + [f'- {item}' for item in limits] + ['']
    (output / 'research-report.md').write_text('\n'.join(lines))
