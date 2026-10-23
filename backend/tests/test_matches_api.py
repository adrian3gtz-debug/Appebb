from fastapi.testclient import TestClient
import pytest

from app.main import app
from app.services import match_repository
from app.models.match import Match


def test_demo_returns_valid_synthetic_match(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    response = TestClient(app).get('/api/matches/demo')
    assert response.status_code == 200
    payload = response.json()
    assert payload['source'] == 'synthetic'
    assert payload['duration_seconds'] == 5400
    match = Match.model_validate(payload['match'])
    assert match.id == 'synthetic-7'
    assert len(match.events) == 694


@pytest.mark.parametrize('content', [None, '{invalid', '{"id":"broken"}'])
def test_unavailable_demo_returns_safe_error(monkeypatch, tmp_path, content):
    path = tmp_path / 'demo.json'
    if content is not None:
        path.write_text(content, encoding='utf-8')
    monkeypatch.setattr(match_repository, 'DEMO_PATH', path)
    response = TestClient(app).get('/api/matches/demo')
    assert response.status_code == 503
    assert response.json() == {'detail': 'Demo match unavailable'}
