import base64
import litcoach.services.gateway.app as gateway
from fastapi.testclient import TestClient


def test_gateway_health():
    client = TestClient(gateway.app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["service"] == "gateway"


def test_voice_turn_monkeypatch(monkeypatch):
    client = TestClient(gateway.app)

    def fake_transcribe(_bytes, filename="audio.webm"):
        return "Hello coach"

    def fake_speak(_text, voice="alloy"):
        return b"FAKEAUDIOBYTES"

    class FakeGatewayResponse:
        def __init__(self, payload):
            self._payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self._payload

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, json=None, **kwargs):
            if "/agent/" in url:
                return FakeGatewayResponse({"content": "Hi learner, let's practice."})
            return FakeGatewayResponse({"wcpm": 120, "accuracy": 0.98, "errors": []})

    def fake_async_client(*args, **kwargs):
        return FakeClient()

    monkeypatch.setattr(gateway, "transcribe_audio", fake_transcribe)
    monkeypatch.setattr(gateway, "synthesize_speech", fake_speak)
    monkeypatch.setattr(gateway.httpx, "AsyncClient", fake_async_client)

    data = {
        "session_id": "s1",
        "mode": "tutor",
        "grade_level": "3",
        "user_id": "u1",
        "reference_text": "",
    }
    files = {"audio": ("audio.webm", b"123", "audio/webm")}
    response = client.post("/api/voice/turn", data=data, files=files)
    assert response.status_code == 200
    body = response.json()
    assert body["transcript"] == "Hello coach"
    assert "coach_text" in body
    assert base64.b64decode(body["coach_audio_b64_mp3"]) == b"FAKEAUDIOBYTES"


