"""Offline HTTP smoke test through ASGI; uses one shared FakeRedis server."""
import json
import os
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ['AGENT_API_KEY'] = secrets.token_urlsafe(32)
os.environ['REDIS_URL'] = 'fake://'

import fakeredis
from fastapi.testclient import TestClient
from app.main import app, get_store, get_rate_limiter, get_cost_guard
from app.store import ConversationStore
from app.rate_limiter import RateLimiter
from app.cost_guard import CostGuard

redis = fakeredis.FakeRedis(decode_responses=True)
app.dependency_overrides[get_store] = lambda: ConversationStore(redis)
app.dependency_overrides[get_rate_limiter] = lambda: RateLimiter(redis, 10)
app.dependency_overrides[get_cost_guard] = lambda: CostGuard(redis, 10.0)
headers = {'X-API-Key': os.environ['AGENT_API_KEY'], 'X-User-Id': 'smoke-user'}
try:
    with TestClient(app) as client:
        for endpoint in ('/health', '/ready'):
            response = client.get(endpoint)
            assert response.status_code == 200
            print(endpoint, response.status_code, json.dumps(response.json()))
        response = client.post('/ask', json={'question': 'Hello'})
        assert response.status_code == 401
        print('Missing API key:', response.status_code)
        histories = []
        statuses = []
        for index in range(15):
            response = client.post('/ask', headers=headers, json={'question': 'Docker là gì?'})
            statuses.append(response.status_code)
            if response.status_code == 200:
                histories.append(response.json()['history_length'])
        assert statuses == [200] * 10 + [429] * 5
        assert histories == list(range(0, 20, 2))
        print('15 requests:', statuses)
        print('History lengths:', histories)
        redis.set(CostGuard._key('over-budget'), '11')
        response = client.post('/ask', headers={**headers, 'X-User-Id': 'over-budget'}, json={'question': 'Hello'})
        assert response.status_code == 402
        print('Over budget:', response.status_code)
finally:
    app.dependency_overrides.clear()
