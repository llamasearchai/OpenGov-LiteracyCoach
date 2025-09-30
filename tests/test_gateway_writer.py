from fastapi.testclient import TestClient
import litcoach.services.gateway.app as gateway


def test_agent_proxy(monkeypatch):
    client = TestClient(gateway.app)

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"content": "Coaching feedback here."}

    class FakeAsyncClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, json=None, **kwargs):
            return FakeResponse()

    def fake_async_client(*args, **kwargs):
        return FakeAsyncClient()

    monkeypatch.setattr(gateway.httpx, "AsyncClient", fake_async_client)

    response = client.post("/agent/respond", json={"messages": [{"role": "user", "content": "Help me write"}]})
    assert response.status_code == 200
    assert "content" in response.json()


def test_writing_score_proxy(monkeypatch):
    client = TestClient(gateway.app)

    class FakeScoreResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "rubric_scores": {
                    "ideas": 4,
                    "organization": 3,
                    "evidence": 3,
                    "conventions": 3,
                },
                "feedback": "Well structured",
            }

    class FakeLogResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"ok": True}

    class FakeAsyncClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, json=None, **kwargs):
            if url.endswith("/writing/score"):
                return FakeScoreResponse()
            return FakeLogResponse()

    def fake_async_client(*args, **kwargs):
        return FakeAsyncClient()

    monkeypatch.setattr(gateway.httpx, "AsyncClient", fake_async_client)

    response = client.post(
        "/api/writing/score",
        json={
            "user_id": "s1",
            "prompt": "P",
            "essay": "E",
            "grade_level": "5",
            "rubric_name": "writing_default",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["rubric_scores"]["ideas"] == 4


