from fastapi.testclient import TestClient
import os
import litcoach.services.content.app as content_app


def test_content_health(monkeypatch, tmp_path):
    db_path = tmp_path / "content.db"
    texts_json = tmp_path / "texts.json"
    texts_json.write_text(
        """[
        {"id":"t1","title":"A","text":"alpha beta","lexile":200,"grade_band":"K-1","phonics_focus":"","theme":"a","embedding": null}
    ]""",
        encoding="utf-8",
    )
    monkeypatch.setenv("CONTENT_DB_PATH", str(db_path))
    monkeypatch.setenv("CONTENT_TEXTS_JSON", str(texts_json))

    def fake_embed(_text: str):
        return [0.1, 0.2, 0.3]

    monkeypatch.setattr(content_app, "embedding", fake_embed)
    monkeypatch.setattr("litcoach.services.content.ingest.embedding", fake_embed)

    with TestClient(content_app.app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        response = client.get("/texts")
        assert response.status_code == 200
        assert len(response.json()["results"]) == 1
        response = client.post("/texts/search", json={"grade_band": "K-1"})
        assert len(response.json()["results"]) == 1
        response = client.post("/rag/search", json={"query": "alpha", "k": 1})
        assert len(response.json()["results"]) == 1


