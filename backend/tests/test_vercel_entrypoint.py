"""The root entry must run without the developer's working directory or source tree."""

import os
from pathlib import Path
import shutil
import subprocess
import sys


def test_deployment_bundle_loads_fixture_and_enforces_cors(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    shutil.copy(root / 'main.py', tmp_path / 'main.py')
    shutil.copytree(root / 'backend/app', tmp_path / 'backend/app',
                    ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copytree(root / 'data/synthetic', tmp_path / 'data/synthetic')
    environment = os.environ.copy()
    environment.pop('PYTHONPATH', None)
    environment['BACKEND_CORS_ORIGINS'] = 'https://frontend.example.org'
    script = '''
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)
origin = {'Origin': 'https://frontend.example.org'}
response = client.get('/api/health', headers=origin)
assert response.json() == {'status': 'ok'}
assert response.headers['access-control-allow-origin'] == origin['Origin']
assert 'access-control-allow-origin' not in client.get('/api/health', headers={'Origin': 'https://unrelated.example.org'}).headers
preflight = client.options('/api/matches/demo', headers={**origin, 'Access-Control-Request-Method': 'GET'})
assert preflight.status_code == 200
assert preflight.headers['access-control-allow-origin'] == origin['Origin']
fixture = client.get('/api/matches/demo')
assert fixture.status_code == 200
assert fixture.json()['match']['id'] == 'synthetic-7'
assert len(fixture.json()['match']['events']) == 694
analysis = client.get('/api/matches/demo/recoveries?scenario=higher_recoveries&second=1200')
assert analysis.status_code == 200
assert analysis.json()['insights'][0]['current']['shot_sequences'] == 3
varied = client.get('/api/matches/demo/analysis?scenario=varied&second=1200')
assert varied.status_code == 200
assert varied.json()['statistics']['as_of_second'] == 1200
assert varied.json()['source'] == 'synthetic'
assert client.get('/docs').status_code == 200
'''
    result = subprocess.run([sys.executable, '-c', script], cwd=tmp_path, env=environment,
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
