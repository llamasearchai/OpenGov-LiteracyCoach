from fastapi.testclient import TestClient
import litcoach.services.agent.app as agent


def test_agent_health():
    client = TestClient(agent.app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["service"] == "agent"


def test_agent_tool_flow(monkeypatch):
    client = TestClient(agent.app)

    def fake_chat_with_tools(messages, tools=None, temperature=0.4):
        if any(item.get("role") == "tool" for item in messages):
            return {"choices": [{"message": {"content": "Here are some texts you can read."}}]}
        tool_call = {
            "id": "call_1",
            "type": "function",
            "function": {
                "name": "lookup_texts",
                "arguments": "{\"grade_band\":\"K-1\",\"limit\":1}",
            },
        }
        return {"choices": [{"message": {"role": "assistant", "tool_calls": [tool_call]}}]}

    class FakeResponse:
        def __init__(self, json_obj):
            self._json = json_obj

        def raise_for_status(self):
            return None

        def json(self):
            return self._json

    class FakeAsyncClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, json=None, **kwargs):
            if url.endswith("/texts/search"):
                return FakeResponse({"results": [{"id": "decodable_cvc_01", "title": "Sam and the Cat"}]})
            raise AssertionError("Unexpected URL " + url)

    def fake_async_client(*args, **kwargs):
        return FakeAsyncClient()

    monkeypatch.setattr(agent, "chat_with_tools", fake_chat_with_tools)
    monkeypatch.setattr(agent.httpx, "AsyncClient", fake_async_client)

    payload = {"messages": [{"role": "user", "content": "Find me an easy decodable text"}]}
    response = client.post("/agent/respond", json=payload)
    assert response.status_code == 200
    assert "content" in response.json()


