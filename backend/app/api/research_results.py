"""Read-only, allowlisted research artifacts; never execute submitted paths."""
import csv
import json
import os
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from app.core.security import require_role

ROOT = Path(os.environ.get('RESEARCH_RESULTS_DIR',
    str(Path(__file__).resolve().parents[3] / 'research' / 'results' / 'cert-r4.2-enhanced')))
FILES = {'detection-summary.csv', 'adaptive-summary.csv', 'ablation-summary.csv',
         'research-report.md', 'research-results.png', 'adaptive-metrics.png', 'manifest.json',
         'paired-comparisons.csv', 'validation-selection.csv', 'precision-recall.png'}
router = APIRouter(prefix='/api/research', tags=['Research'],
                   dependencies=[Depends(require_role(['Admin', 'Analyst']))])


def read_rows(name):
    path = ROOT / name
    if not path.is_file():
        return []
    with path.open() as stream:
        return list(csv.DictReader(stream))


@router.get('/results')
def results():
    if not (ROOT / 'detection-summary.csv').exists():
        raise HTTPException(404, 'Research results have not been installed')
    manifest = ROOT / 'manifest.json'
    metadata = json.loads(manifest.read_text()) if manifest.exists() else {}
    return {'detection': read_rows('detection-summary.csv'),
            'adaptive': read_rows('adaptive-summary.csv'),
            'comparisons': read_rows('paired-comparisons.csv'),
            'manifest': metadata,
            'files': sorted(name for name in FILES if (ROOT / name).is_file()),
            'note': 'CERT detection and separate simulated response experiments. Mean ± seed SD is not a significance claim.'}


@router.get('/files/{name}')
def artifact(name: str):
    if name not in FILES or not (ROOT / name).is_file():
        raise HTTPException(404, 'Artifact not found')
    return FileResponse(ROOT / name, filename=name)
