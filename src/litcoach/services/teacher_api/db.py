import os
from typing import Any, Dict, List
from sqlalchemy import create_engine, text


def get_db_path() -> str:
    return os.environ.get("TEACHER_DB_PATH", "/data/teacher.db")


def get_engine():
    return create_engine(f"sqlite:///{get_db_path()}", future=True)


def init_schema():
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text(
                """
        CREATE TABLE IF NOT EXISTS classes (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL
        )
        """
            )
        )
        conn.execute(
            text(
                """
        CREATE TABLE IF NOT EXISTS students (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL
        )
        """
            )
        )
        conn.execute(
            text(
                """
        CREATE TABLE IF NOT EXISTS enrollments (
            class_id TEXT NOT NULL,
            student_id TEXT NOT NULL,
            PRIMARY KEY (class_id, student_id),
            FOREIGN KEY (class_id) REFERENCES classes(id),
            FOREIGN KEY (student_id) REFERENCES students(id)
        )
        """
            )
        )
        conn.execute(
            text(
                """
        CREATE TABLE IF NOT EXISTS assignments (
            id TEXT PRIMARY KEY,
            class_id TEXT NOT NULL,
            type TEXT NOT NULL,
            title TEXT NOT NULL,
            details TEXT NOT NULL
        )
        """
            )
        )
        conn.execute(
            text(
                """
        CREATE TABLE IF NOT EXISTS results_reading (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            class_id TEXT,
            assignment_id TEXT,
            session_id TEXT,
            wcpm INTEGER,
            accuracy REAL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
            )
        )
        conn.execute(
            text(
                """
        CREATE TABLE IF NOT EXISTS results_writing (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            class_id TEXT,
            assignment_id TEXT,
            rubric_scores TEXT,
            feedback TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
            )
        )


def create_id(prefix: str) -> str:
    import secrets

    return f"{prefix}_{secrets.token_hex(6)}"


def add_class(name: str) -> Dict[str, Any]:
    class_id = create_id("cls")
    with get_engine().begin() as conn:
        conn.execute(
            text("INSERT INTO classes (id, name) VALUES (:id, :name)"),
            {"id": class_id, "name": name},
        )
    return {"id": class_id, "name": name}


def list_classes() -> List[Dict[str, Any]]:
    with get_engine().begin() as conn:
        rows = conn.execute(
            text("SELECT id, name FROM classes ORDER BY name")
        ).mappings().all()
        return [dict(row) for row in rows]


def upsert_student(student_id: str, name: str):
    with get_engine().begin() as conn:
        conn.execute(
            text(
                """
            INSERT INTO students (id, name) VALUES (:id, :name)
            ON CONFLICT(id) DO UPDATE SET name=excluded.name
        """
            ),
            {"id": student_id, "name": name},
        )


def enroll_student(class_id: str, student_id: str):
    with get_engine().begin() as conn:
        conn.execute(
            text(
                """
            INSERT OR IGNORE INTO enrollments (class_id, student_id)
            VALUES (:class_id, :student_id)
        """
            ),
            {"class_id": class_id, "student_id": student_id},
        )


def class_students(class_id: str) -> List[Dict[str, Any]]:
    with get_engine().begin() as conn:
        rows = conn.execute(
            text(
                """
            SELECT s.id, s.name
            FROM students s
            JOIN enrollments e ON e.student_id = s.id
            WHERE e.class_id = :class_id
            ORDER BY s.name
        """
            ),
            {"class_id": class_id},
        ).mappings().all()
        return [dict(row) for row in rows]


def create_assignment(class_id: str, atype: str, title: str, details: str) -> Dict[str, Any]:
    assignment_id = create_id("asg")
    with get_engine().begin() as conn:
        conn.execute(
            text(
                """
            INSERT INTO assignments (id, class_id, type, title, details)
            VALUES (:id, :class_id, :type, :title, :details)
        """
            ),
            {
                "id": assignment_id,
                "class_id": class_id,
                "type": atype,
                "title": title,
                "details": details,
            },
        )
    return {
        "id": assignment_id,
        "class_id": class_id,
        "type": atype,
        "title": title,
        "details": details,
    }


def class_assignments(class_id: str) -> List[Dict[str, Any]]:
    with get_engine().begin() as conn:
        rows = conn.execute(
            text(
                """
            SELECT id, class_id, type, title, details
            FROM assignments
            WHERE class_id = :class_id
            ORDER BY id DESC
        """
            ),
            {"class_id": class_id},
        ).mappings().all()
        return [dict(row) for row in rows]


def add_reading_result(
    user_id: str,
    class_id: str | None,
    assignment_id: str | None,
    session_id: str,
    wcpm: int,
    accuracy: float,
):
    with get_engine().begin() as conn:
        conn.execute(
            text(
                """
            INSERT INTO results_reading (user_id, class_id, assignment_id, session_id, wcpm, accuracy)
            VALUES (:user_id, :class_id, :assignment_id, :session_id, :wcpm, :accuracy)
        """
            ),
            {
                "user_id": user_id,
                "class_id": class_id,
                "assignment_id": assignment_id,
                "session_id": session_id,
                "wcpm": wcpm,
                "accuracy": accuracy,
            },
        )


def add_writing_result(
    user_id: str,
    class_id: str | None,
    assignment_id: str | None,
    rubric_scores_json: str,
    feedback: str,
):
    with get_engine().begin() as conn:
        conn.execute(
            text(
                """
            INSERT INTO results_writing (user_id, class_id, assignment_id, rubric_scores, feedback)
            VALUES (:user_id, :class_id, :assignment_id, :rubric_scores, :feedback)
        """
            ),
            {
                "user_id": user_id,
                "class_id": class_id,
                "assignment_id": assignment_id,
                "rubric_scores": rubric_scores_json,
                "feedback": feedback,
            },
        )


def analytics_overview(class_id: str) -> Dict[str, Any]:
    with get_engine().begin() as conn:
        reading_stats = conn.execute(
            text(
                """
            SELECT COUNT(*) AS n, AVG(wcpm) AS avg_wcpm, AVG(accuracy) AS avg_acc
            FROM results_reading
            WHERE class_id = :class_id
        """
            ),
            {"class_id": class_id},
        ).mappings().one()
        writing_stats = conn.execute(
            text(
                """
            SELECT COUNT(*) AS n
            FROM results_writing
            WHERE class_id = :class_id
        """
            ),
            {"class_id": class_id},
        ).mappings().one()
    return {
        "class_id": class_id,
        "reading_samples": int(reading_stats["n"] or 0),
        "avg_wcpm": float(reading_stats["avg_wcpm"] or 0.0),
        "avg_accuracy": float(reading_stats["avg_acc"] or 0.0),
        "writing_samples": int(writing_stats["n"] or 0),
    }


