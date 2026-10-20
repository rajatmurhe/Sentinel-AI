"""Run reproducible detection, closed-loop and ablation experiments.

Example (from backend):
python run_experiments.py --dataset ../research/data/cert_r4.2_features.csv \
    --output ../research/results/cert-r4.2 --seeds 0 1 2 3 4
"""
import argparse
import hashlib
import json
import platform
import subprocess
from pathlib import Path
import sys
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import sklearn
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix, average_precision_score
from app.ml.feature_pipeline import FEATURE_ORDER
from app.ml.generator import SyntheticDataGenerator
from research.protocol import ResearchModels, VARIANTS, split_chronologically, replay
from research.simulation import run_episode, initial_profile
from research.download_cert import digest


def classification_metrics(y, scores, threshold):
    predictions = np.asarray(scores) > threshold
    tn, fp, fn, tp = confusion_matrix(y, predictions, labels=[0, 1]).ravel()
    return {'precision': precision_score(y, predictions, zero_division=0),
            'recall': recall_score(y, predictions, zero_division=0),
            'f1': f1_score(y, predictions, zero_division=0),
            'roc_auc': roc_auc_score(y, scores) if len(np.unique(y)) == 2 else np.nan,
            'average_precision': average_precision_score(y, scores),
            'false_positive_rate': fp / (fp+tn) if fp+tn else np.nan,
            'tp': int(tp), 'fp': int(fp), 'tn': int(tn), 'fn': int(fn), 'threshold': threshold}


def clean_json(obj):
    if isinstance(obj, dict):
        return {k: clean_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [clean_json(v) for v in obj]
    if isinstance(obj, (float, np.floating)):
        return float(obj) if np.isfinite(obj) else None
    if isinstance(obj, np.integer):
        return int(obj)
    return obj


def aggregate_runs(frame, group):
    numeric = [c for c in frame.select_dtypes(include='number') if c != 'seed']
    summary = frame.groupby(group)[numeric].agg(['mean', 'std', 'count'])
    summary.columns = ['_'.join(c) for c in summary.columns]
    return summary.reset_index()


def synthetic_frame(seed, n=2400):
    data = SyntheticDataGenerator(seed).generate_baseline_dataset(n)
    data['user_id'] = [f'demo-{i % 40}' for i in range(len(data))]
    data['date'] = [(pd.Timestamp('2020-01-01') + pd.Timedelta(days=i//40)).strftime('%Y-%m-%d') for i in range(len(data))]
    return data


def load_data(args):
    if args.demo:
        return synthetic_frame(1234), list(FEATURE_ORDER), {'source': 'LOCAL_SYNTHETIC_DEMO', 'not_CERT': True}
    if not args.dataset:
        raise ValueError('Supply a verified CERT feature file or explicitly choose --demo')
    metadata_path = args.dataset.with_suffix('.metadata.json')
    if not metadata_path.exists():
        raise ValueError('Missing source metadata. Run research.preprocess_cert; do not relabel an unverified CSV as CERT.')
    metadata = json.loads(metadata_path.read_text())
    if metadata.get('source') != 'CERT' or metadata.get('features_sha256') != digest(args.dataset):
        raise ValueError('Feature provenance/hash validation failed')
    frame = pd.read_csv(args.dataset, dtype={'user_id': str, 'date': str})
    if args.user_limit:
        # Deterministic label-independent user subset; always recorded in manifest.
        users = sorted(frame.user_id.unique(), key=lambda x: hashlib.sha256(x.encode()).hexdigest())[:args.user_limit]
        frame = frame[frame.user_id.isin(users)]
        metadata = dict(metadata, evaluation_user_limit=args.user_limit, evaluated_users=users)
    return frame.sort_values(['date', 'user_id']).reset_index(drop=True), metadata['features'], metadata


def run(args):
    output = args.output
    output.mkdir(parents=True, exist_ok=True)
    frame, features, provenance = load_data(args)
    if not set(frame.label.unique()).issubset({0, 1}):
        raise ValueError('Labels must be binary')
    train, valid, test = split_chronologically(frame)
    if test.label.nunique() != 2:
        raise ValueError('Test split needs benign and malicious user-days for a meaningful comparison')
    manifest = {'started_utc': datetime.now(timezone.utc).isoformat(), 'provenance': provenance,
                'evaluation_mode': args.protocol,
                'threshold_selection': 'validation F1 under FPR ceiling' if args.protocol == 'enhanced' else 'benign validation quantile',
                'seeds': args.seeds, 'max_train': args.max_train, 'episodes_per_seed': args.episodes,
                'turns': args.turns, 'target_validation_fpr': args.target_fpr,
                'splits': {name: {'rows': len(f), 'positives': int(f.label.sum()), 'first_date': f.date.min(),
                                  'last_date': f.date.max()} for name, f in [('train',train),('validation',valid),('test',test)]},
                'versions': {'python': platform.python_version(), 'numpy': np.__version__, 'pandas': pd.__version__, 'sklearn': sklearn.__version__},
                'source_hashes': {str(p.relative_to(Path(__file__).parent)): digest(p) for p in sorted(Path(__file__).parent.rglob('*.py')) if '.venv' not in p.parts},
                'protocol': '60/20/20 chronological dates; clean training bootstrap; scaler on training only; validation benign score anchors and FPR thresholds; per-user causal histories reset for each partition.',
                'limitations': ['CERT labels are insider activity windows, not exact event maliciousness.',
                    'Offline CERT replay cannot establish causal defence effectiveness; AAS/RES are observational.',
                    'Closed-loop stress tests use a separate synthetic detector and explicit simulated enforcement, not CERT counterfactuals.',
                    'Five seeds measure training/simulator variability on one temporal split, not confidence intervals across populations.',
                    'Ablations may worsen performance. No improvement is assumed.']}
    (output/'manifest.json').write_text(json.dumps(clean_json(manifest), indent=2, allow_nan=False))
    detection, simulation, episodes, selection = [], [], [], []
    from research.enhanced import EnhancedResearchModels, validation_threshold
    model_class = EnhancedResearchModels if args.protocol == 'enhanced' else ResearchModels
    def threshold_for(labels, scores):
        if args.protocol == 'enhanced':
            return validation_threshold(labels, scores, args.target_fpr)
        return float(np.quantile(np.asarray(scores)[np.asarray(labels) == 0], 1.-args.target_fpr))
    for seed in args.seeds:
        print(f'Seed {seed}: train and score detection models', flush=True)
        models = model_class(features, seed, args.max_train).fit(train, valid)
        if args.protocol == 'enhanced':
            selection.extend(models.selection)
            pd.DataFrame(selection).to_csv(output/'validation-selection.csv',index=False)
        if args.save_models:
            import joblib
            joblib.dump(models, output/f'detector-seed-{seed}.joblib')
        validation_scores, test_scores = models.scores(valid), models.scores(test)
        for name in ('Isolation Forest', 'One-Class SVM'):
            threshold = threshold_for(valid.label, validation_scores[name])
            detection.append({'seed': seed, 'model': name, **classification_metrics(test.label, test_scores[name], threshold)})
            pd.DataFrame({'user_id':test.user_id, 'date':test.date, 'label':test.label,
                          'score':test_scores[name], 'threshold':threshold,
                          'prediction':test_scores[name] > threshold}).to_csv(output/f'detection-{seed}-{name.replace(" ", "_")}.csv',index=False)
        for variant in VARIANTS:
            print(f'Seed {seed}: replay {variant}', flush=True)
            vs, _ = replay(valid, validation_scores['risk'], variant, models.metrics)
            ts, records = replay(test, test_scores['risk'], variant, models.metrics)
            threshold = threshold_for(valid.label, vs)
            detection.append({'seed':seed, 'model':variant, **classification_metrics(test.label, ts, threshold)})
            trace = pd.DataFrame(records)
            trace['threshold'], trace['prediction'] = threshold, ts > threshold
            trace.to_csv(output/f'detection-{seed}-{VARIANTS.index(variant)}.csv', index=False)
        # Counterfactual attacker behaviour is tested in a distinct synthetic environment.
        demo = synthetic_frame(10000+seed)
        dt, dv, _ = split_chronologically(demo)
        demo_models = ResearchModels(FEATURE_ORDER, seed, args.max_train).fit(dt, dv)
        def risk_function(b):
            return demo_models.scores(pd.DataFrame([b]))['risk'][0]
        for variant in VARIANTS:
            episode_rows = []
            with (output/f'closed-loop-{seed}-{VARIANTS.index(variant)}.jsonl').open('w') as trace_file:
                for episode in range(args.episodes):
                    episode_seed = seed*10000 + episode
                    summary, traces = run_episode(risk_function, variant, episode_seed, args.turns,
                                                  initial_profile(episode_seed), metrics=demo_models.metrics)
                    row = {'seed':seed, 'variant':variant, 'episode':episode, **summary}
                    episode_rows.append(row)
                    episodes.append(row)
                    for trace in traces:
                        trace['episode'] = episode
                        trace_file.write(json.dumps(clean_json(trace), allow_nan=False)+'\n')
            averages = pd.DataFrame(episode_rows).select_dtypes(include='number').drop(columns=['seed','episode']).mean().to_dict()
            simulation.append({'seed':seed, 'variant':variant, **averages})
        pd.DataFrame(detection).to_csv(output/'detection-runs.csv',index=False)
        pd.DataFrame(simulation).to_csv(output/'adaptive-runs.csv',index=False)
        pd.DataFrame(episodes).to_csv(output/'adaptive-episodes.csv',index=False)
    det_summary = aggregate_runs(pd.DataFrame(detection), 'model')
    sim_summary = aggregate_runs(pd.DataFrame(simulation), 'variant')
    det_summary.to_csv(output/'detection-summary.csv',index=False)
    sim_summary.to_csv(output/'adaptive-summary.csv',index=False)
    det_summary[det_summary.model.isin(VARIANTS)].merge(sim_summary, left_on='model',right_on='variant').to_csv(output/'ablation-summary.csv',index=False)
    from research.report import render_results
    render_results(output)
    from research.statistics import write_comparisons
    write_comparisons(output)
    manifest['completed_utc'] = datetime.now(timezone.utc).isoformat()
    (output/'manifest.json').write_text(json.dumps(clean_json(manifest), indent=2, allow_nan=False))
    print('Completed:', output.resolve(), flush=True)


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dataset',type=Path)
    p.add_argument('--demo',action='store_true')
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--seeds',type=int,nargs='+',default=[0,1,2,3,4])
    p.add_argument('--protocol',choices=['original','enhanced'],default='original')
    p.add_argument('--save-models',action='store_true')
    p.add_argument('--max-train',type=int,default=6000)
    p.add_argument('--episodes',type=int,default=20)
    p.add_argument('--turns',type=int,default=8)
    p.add_argument('--target-fpr',type=float,default=.05)
    p.add_argument('--user-limit',type=int)
    args=p.parse_args()
    if len(set(args.seeds))!=len(args.seeds) or args.episodes<1 or args.turns<2 or not 0<args.target_fpr<1 or args.max_train<20:
        p.error('Use unique seeds, episodes>=1, turns>=2, max-train>=20, and 0<target-fpr<1')
    run(args)
