"""Stream official CERT r4.2 into user-day features without extracting raw logs.
Labels are active insider windows from the official answer key (not model inputs).
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import tarfile
import numpy as np
import pandas as pd
from research.download_cert import SHA256, digest

ANSWER_SHA = 'ed21bf921def01e97326b314f2d1fa77651a945bd31bf513095f8ac7658c9ddd'
MODALITIES = ('file', 'logon', 'device', 'email', 'http')
FEATURES = ['login_hour', 'files_accessed', 'bytes_transferred_mb', 'session_duration_min',
            'logon_events', 'device_events', 'external_emails', 'http_events', 'off_hours_events', 'email_events']


def read_insiders(archive):
    with tarfile.open(archive, 'r:bz2') as t:
        frame = pd.read_csv(t.extractfile('answers/insiders.csv'), dtype=str)
    frame = frame[frame.dataset.eq('4.2')].copy()
    if frame.empty:
        raise ValueError('No r4.2 insider windows in answer key')
    for name in ('start', 'end'):
        frame[name] = pd.to_datetime(frame[name], format='mixed', errors='raise').dt.normalize()
    return frame


def aggregate_chunk(chunk, modality, internal_domain='dtaa.com'):
    timestamp = pd.to_datetime(chunk['date'], format='%m/%d/%Y %H:%M:%S', errors='raise')
    d = pd.DataFrame({'user_id': chunk['user'], 'date': timestamp.dt.strftime('%Y-%m-%d')})
    d['off_hours_events'] = ((timestamp.dt.hour < 8) | (timestamp.dt.hour >= 18)).astype(int)
    d['_first'] = timestamp.astype('int64') / 60e9
    d['_last'] = d['_first']
    if modality == 'file':
        d['files_accessed'] = 1
    elif modality == 'device':
        d['device_events'] = chunk['activity'].str.lower().eq('connect').astype(int)
    elif modality == 'http':
        d['http_events'] = 1
    elif modality == 'logon':
        login = chunk['activity'].str.lower().eq('logon')
        d['logon_events'] = login.astype(int)
        d['login_hour'] = (timestamp.dt.hour + timestamp.dt.minute / 60.).where(login)
    elif modality == 'email':
        d['email_events'] = 1
        recipients = chunk[['to', 'cc', 'bcc']].fillna('').agg(';'.join, axis=1)
        def external(addresses):
            return any('@' in a and a.strip().lower().rsplit('@', 1)[1] != internal_domain
                       for a in addresses.split(';'))
        ext = recipients.map(external)
        d['external_emails'] = ext.astype(int)
        d['bytes_transferred_mb'] = pd.to_numeric(chunk['size'], errors='raise') * ext / (1024. ** 2)
    agg = {k: 'sum' for k in d if k not in ('user_id', 'date', '_first', '_last', 'login_hour')}
    agg.update(_first='min', _last='max')
    if 'login_hour' in d:
        agg['login_hour'] = 'min'
    return d.groupby(['user_id', 'date'], sort=False).agg(agg)


def merge_aggregates(left, right):
    if left is None:
        return right
    summed = left.drop(columns=['_first', '_last', 'login_hour'], errors='ignore').add(
        right.drop(columns=['_first', '_last', 'login_hour'], errors='ignore'), fill_value=0.)
    for name, op in [('_first', 'min'), ('_last', 'max'), ('login_hour', 'min')]:
        columns = [f[name] for f in (left, right) if name in f]
        if columns:
            summed[name] = getattr(pd.concat(columns, axis=1), op)(axis=1)
    return summed


def preprocess(archive, answers, output, chunksize=200000, modalities=MODALITIES):
    if digest(archive) != SHA256 or digest(answers) != ANSWER_SHA:
        raise ValueError('Official archive SHA256 mismatch; refusing to claim CERT provenance')
    insiders = read_insiders(answers)
    aggregate, seen, counts = None, set(), {}
    # Random-access mode yields a seekable member handle, as pandas requires.
    # tarfile still decompresses incrementally and no raw member is extracted.
    with tarfile.open(archive, 'r:bz2') as tar:
        for member in tar:
            modality = Path(member.name).stem
            if not member.isfile() or Path(member.name).suffix != '.csv' or modality not in modalities:
                continue
            if modality in seen:
                raise ValueError(f'Duplicate modality {modality}')
            seen.add(modality)
            print('Processing', member.name, flush=True)
            keep = {'date', 'user', 'activity'}
            if modality == 'email':
                keep.update(('to', 'cc', 'bcc', 'size'))
            count = 0
            for chunk in pd.read_csv(tar.extractfile(member), usecols=lambda c: c in keep,
                                     chunksize=chunksize, dtype=str):
                aggregate = merge_aggregates(aggregate, aggregate_chunk(chunk, modality))
                count += len(chunk)
            counts[modality] = count
            print('Completed', modality, count, flush=True)
    if seen != set(modalities):
        raise ValueError(f'Missing requested modalities: {set(modalities)-seen}')
    frame = aggregate.reset_index()
    frame['session_duration_min'] = (frame.pop('_last') - frame.pop('_first')).clip(0, 1440)
    for name in FEATURES:
        if name not in frame:
            frame[name] = np.nan
        elif name != 'login_hour':
            frame[name] = frame[name].fillna(0.)
    frame['label'] = 0
    dates = pd.to_datetime(frame.date)
    for record in insiders.itertuples():
        frame.loc[frame.user_id.eq(record.user) & dates.between(record.start, record.end), 'label'] = 1
    frame = frame.sort_values(['date', 'user_id']).reset_index(drop=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output, index=False)
    metadata = {
        'source': 'CERT', 'release': 'r4.2', 'doi': '10.1184/R1/12841247.v1',
        'archive_sha256': SHA256, 'answers_sha256': ANSWER_SHA,
        'features_sha256': digest(output), 'rows': len(frame), 'positive_user_days': int(frame.label.sum()),
        'users': int(frame.user_id.nunique()), 'source_event_counts': counts, 'features': FEATURES,
        'label_definition': 'Observed user-days within official insiders.csv start/end dates (inclusive). Window labels, not event-level maliciousness.',
        'feature_notes': {
            'bytes_transferred_mb': 'External-recipient email size in MiB; NOT total network exfiltration.',
            'files_accessed': 'File event count; sensitivity unavailable.',
            'session_duration_min': 'Daily first-to-last observed event span; NOT exact session duration.',
            'login_hour': 'First logon hour in day; missing when no logon.',
            'unavailable': 'No invented sensitive-file labels, failed-login counts or privilege levels.',
            'off_hours_events': 'Events before 08:00 or at/after 18:00; fixed research assumption.',
        },
    }
    output.with_suffix('.metadata.json').write_text(json.dumps(metadata, indent=2))
    print(json.dumps({k: metadata[k] for k in ('rows', 'positive_user_days', 'users')}, indent=2), flush=True)
    return frame


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive', type=Path, required=True)
    p.add_argument('--answers', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--chunksize', type=int, default=200000)
    a = p.parse_args()
    preprocess(a.archive, a.answers, a.output, a.chunksize)
