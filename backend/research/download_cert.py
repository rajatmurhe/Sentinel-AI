"""Resumable ranged downloader for the official, SHA256-pinned CERT r4.2 release."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import subprocess

URL = 'https://ndownloader.figshare.com/files/24856766'
SIZE = 4824287500
ANSWERS_URL = 'https://ndownloader.figshare.com/files/24857828'
ANSWERS_SIZE = 1254678
ANSWERS_SHA256 = 'ed21bf921def01e97326b314f2d1fa77651a945bd31bf513095f8ac7658c9ddd'
SHA256 = '586446b00e83ce5cdabf9dc889b0b6e7a9f44556cee3c03d39445d790122556c'


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def download_answers(target):
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and target.stat().st_size == ANSWERS_SIZE:
        if digest(target) != ANSWERS_SHA256:
            raise ValueError('Existing answer archive failed SHA256; retain it for diagnosis')
        print('Verified existing CERT answer key', flush=True)
        return
    subprocess.run(['curl', '-L', '--fail', '--retry', '4', '--connect-timeout', '30',
                    '--max-time', '300', '-sS', ANSWERS_URL, '-o', str(target)], check=True)
    if target.stat().st_size != ANSWERS_SIZE or digest(target) != ANSWERS_SHA256:
        raise ValueError('CERT answer-key archive size or SHA256 mismatch')
    print('CERT answer key downloaded and SHA256 verified', flush=True)


def download(target, workers=8):
    target.parent.mkdir(parents=True, exist_ok=True)
    parts = target.with_suffix(target.suffix + '.parts')
    if target.exists() and target.stat().st_size == SIZE:
        if digest(target) != SHA256:
            raise ValueError('Existing full-size archive failed SHA256; retain it for diagnosis')
        print('Verified existing archive', flush=True)
        return
    parts.mkdir(exist_ok=True)
    prefix = parts / 'prefix'
    if target.exists():
        if prefix.exists():
            raise ValueError('Both an incomplete target and a prefix exist; inspect before resuming')
        target.rename(prefix)
    start = prefix.stat().st_size if prefix.exists() else 0
    segments = [(a, min(a + 64 * 1024 * 1024, SIZE) - 1) for a in range(start, SIZE, 64 * 1024 * 1024)]
    def fetch(segment):
        a, b = segment
        part = parts / f'{a:012d}-{b:012d}'
        if part.exists() and part.stat().st_size == b-a+1:
            return part
        subprocess.run(['curl', '-L', '--fail', '--retry', '4', '--connect-timeout', '30',
                        '--max-time', '900', '-sS', '-r', f'{a}-{b}', URL, '-o', str(part)], check=True)
        if part.stat().st_size != b-a+1:
            raise ValueError(f'Server did not honor byte range {a}-{b}')
        print(f'Downloaded range {a}-{b}', flush=True)
        return part
    with ThreadPoolExecutor(max_workers=workers) as pool:
        paths = list(pool.map(fetch, segments))
    with target.open('wb') as out:
        for p in ([prefix] if prefix.exists() else []) + paths:
            with p.open('rb') as src:
                for block in iter(lambda: src.read(8 * 1024 * 1024), b''):
                    out.write(block)
    actual = digest(target)
    if actual != SHA256:
        raise ValueError(f'SHA256 mismatch: {actual}')
    for p in ([prefix] if prefix.exists() else []) + paths:
        p.unlink()  # Remove only verified temporary download fragments.
    parts.rmdir()
    target.with_suffix(target.suffix + '.verified.json').write_text(json.dumps({
        'url': URL, 'sha256': actual, 'bytes': SIZE, 'release': 'r4.2'}, indent=2))
    print('CERT r4.2 downloaded and SHA256 verified', flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, default=Path('../research/data/raw/r4.2.tar.bz2'))
    p.add_argument('--workers', type=int, default=8)
    p.add_argument('--answers-output', type=Path, default=Path('../research/data/raw/answers.tar.bz2'))
    a = p.parse_args()
    download_answers(a.answers_output)
    download(a.output, a.workers)
