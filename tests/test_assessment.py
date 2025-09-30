from fastapi.testclient import TestClient
import litcoach.services.assessment.app as assessment


def test_assessment_health():
    client = TestClient(assessment.app)
    response = client.get("/health")
    assert response.status_code == 200


def test_reading_assess():
    client = TestClient(assessment.app)
    payload = {
        "reference_text": "Sam had a cat.",
        "asr_transcript": "Sam had a cap.",
        "timestamps": [0.0, 6.0],
    }
    response = client.post("/reading/assess", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "wcpm" in data
    assert "accuracy" in data
    assert isinstance(data["errors"], list)


def test_writing_score(monkeypatch):
    client = TestClient(assessment.app)

    def fake_chat(messages, tools=None, temperature=0.0):
        return {
            "choices": [
                {
                    "message": {
                        "content": "{\"rubric_scores\":{\"ideas\":4,\"organization\":3,\"evidence\":3,\"conventions\":3},\"feedback\":\"Clear main idea with supporting details.\"}"
                    }
                }
            ]
        }

    monkeypatch.setattr(assessment, "chat_with_tools", fake_chat)
    payload = {
        "prompt": "Describe a place.",
        "essay": "The library is quiet and calm.",
        "grade_level": "5",
        "rubric_name": "writing_default",
    }
    response = client.post("/writing/score", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["rubric_scores"]["ideas"] == 4


