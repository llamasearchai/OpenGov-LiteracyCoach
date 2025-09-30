from fastapi.testclient import TestClient
import litcoach.services.teacher_api.app as teacher_api


def test_teacher_health(tmp_path, monkeypatch):
    monkeypatch.setenv("TEACHER_DB_PATH", str(tmp_path / "teacher.db"))
    with TestClient(teacher_api.app) as client:
        response = client.get("/health")
        assert response.status_code == 200


def test_roster_and_assignments(tmp_path, monkeypatch):
    monkeypatch.setenv("TEACHER_DB_PATH", str(tmp_path / "teacher.db"))
    with TestClient(teacher_api.app) as client:
        created_class = client.post("/classes", json={"name": "Period 1"}).json()
        class_id = created_class["id"]
        csv_data = "student_id,student_name\ns1,Ada\ns2,Alan\n"
        response = client.post(
            f"/roster/import?class_id={class_id}",
            data=csv_data,
            headers={"Content-Type": "text/csv"},
        )
        assert response.status_code == 200

        roster = client.get(f"/classes/{class_id}/students").json()["results"]
        assert len(roster) == 2

        assignment = client.post(
            "/assignments",
            json={
                "class_id": class_id,
                "type": "reading",
                "title": "Decodable A",
                "details": "decodable_cvc_01",
            },
        ).json()
        assert assignment["type"] == "reading"

        assignments = client.get(f"/classes/{class_id}/assignments").json()["results"]
        assert len(assignments) == 1

        reading_result = client.post(
            "/events/reading_result",
            json={
                "user_id": "s1",
                "class_id": class_id,
                "assignment_id": assignment["id"],
                "session_id": "sess1",
                "wcpm": 80,
                "accuracy": 0.95,
            },
        )
        assert reading_result.status_code == 200

        writing_result = client.post(
            "/events/writing_result",
            json={
                "user_id": "s1",
                "class_id": class_id,
                "assignment_id": assignment["id"],
                "rubric_scores": {
                    "ideas": 3,
                    "organization": 3,
                    "evidence": 2,
                    "conventions": 3,
                },
                "feedback": "Good work",
            },
        )
        assert writing_result.status_code == 200

        stats = client.get(f"/analytics/overview?class_id={class_id}").json()
        assert stats["reading_samples"] == 1


