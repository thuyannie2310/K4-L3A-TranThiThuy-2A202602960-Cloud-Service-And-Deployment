"""Additional edge cases; original checkpoint tests remain unchanged."""
from concurrent.futures import ThreadPoolExecutor
from fastapi import HTTPException
import pytest


def test_concurrent_requests_cannot_share_last_quota(fake_redis):
    from app.rate_limiter import RateLimiter
    limiter = RateLimiter(fake_redis, 3)
    def request(_):
        try:
            limiter.check('concurrent', now=1000.0)
            return 200
        except HTTPException as exc:
            return exc.status_code
    with ThreadPoolExecutor(max_workers=12) as pool:
        statuses = list(pool.map(request, range(30)))
    assert statuses.count(200) == 3
    assert statuses.count(429) == 27
    assert limiter.hit_count('concurrent', now=1000.0) == 3


def test_exact_window_boundary_expires(fake_redis):
    from app.rate_limiter import RateLimiter
    limiter = RateLimiter(fake_redis, 1)
    limiter.check('boundary', now=1000.0)
    limiter.check('boundary', now=1060.0)
    assert limiter.hit_count('boundary', now=1060.0) == 1


def test_budget_exactly_exhausted_is_blocked(fake_redis):
    from app.cost_guard import CostGuard
    guard = CostGuard(fake_redis, 1.0)
    guard.record('exhausted', 1.0)
    with pytest.raises(HTTPException) as exc:
        guard.check('exhausted')
    assert exc.value.status_code == 402


def test_startup_validates_settings(monkeypatch):
    from fastapi.testclient import TestClient
    from pydantic import ValidationError
    from app.config import Settings
    from app.main import app
    import app.main as main
    monkeypatch.delenv('AGENT_API_KEY', raising=False)
    monkeypatch.setattr(main, 'get_settings', lambda: Settings(_env_file=None))
    with pytest.raises(ValidationError):
        with TestClient(app):
            pass
