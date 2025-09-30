import os
import json
from typing import List, Dict, Any
from sqlalchemy import create_engine, text


def get_db_path() -> str:
    return os.environ.get("CONTENT_DB_PATH", "/data/content.db")


def get_engine():
    db_path = get_db_path()
    uri = f"sqlite:///{db_path}"
    return create_engine(uri, future=True)


def init_schema():
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text(
                """
        CREATE TABLE IF NOT EXISTS texts (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            text TEXT NOT NULL,
            lexile INTEGER,
            grade_band TEXT,
            phonics_focus TEXT,
            theme TEXT,
            embedding TEXT
        )
        """
            )
        )


def insert_or_update_text(doc: Dict[str, Any]):
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text(
                """
        INSERT INTO texts (id, title, text, lexile, grade_band, phonics_focus, theme, embedding)
        VALUES (:id, :title, :text, :lexile, :grade_band, :phonics_focus, :theme, :embedding)
        ON CONFLICT(id) DO UPDATE SET
            title=excluded.title,
            text=excluded.text,
            lexile=excluded.lexile,
            grade_band=excluded.grade_band,
            phonics_focus=excluded.phonics_focus,
            theme=excluded.theme,
            embedding=excluded.embedding
        """
            ),
            {
                "id": doc["id"],
                "title": doc["title"],
                "text": doc["text"],
                "lexile": doc.get("lexile"),
                "grade_band": doc.get("grade_band"),
                "phonics_focus": doc.get("phonics_focus"),
                "theme": doc.get("theme"),
                "embedding": json.dumps(doc.get("embedding"))
                if doc.get("embedding") is not None
                else None,
            },
        )


def list_texts(limit: int = 20) -> List[Dict[str, Any]]:
    engine = get_engine()
    with engine.begin() as conn:
        rows = conn.execute(
            text(
                "SELECT id,title,text,lexile,grade_band,phonics_focus,theme FROM texts LIMIT :l"
            ),
            {"l": limit},
        ).mappings().all()
        return [dict(row) for row in rows]


def search_texts(filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    limit = int(filters.get("limit", 10))
    clauses = []
    params: Dict[str, Any] = {"limit": limit}
    for key in ["grade_band", "phonics_focus", "theme"]:
        value = filters.get(key)
        if value:
            clauses.append(f"{key} = :{key}")
            params[key] = value
    if filters.get("lexile_min") is not None:
        clauses.append("lexile >= :lexile_min")
        params["lexile_min"] = int(filters["lexile_min"])
    if filters.get("lexile_max") is not None:
        clauses.append("lexile <= :lexile_max")
        params["lexile_max"] = int(filters["lexile_max"])
    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    sql = f"SELECT id,title,text,lexile,grade_band,phonics_focus,theme FROM texts{where} LIMIT :limit"
    engine = get_engine()
    with engine.begin() as conn:
        rows = conn.execute(text(sql), params).mappings().all()
        return [dict(row) for row in rows]


def get_all_with_embeddings() -> List[Dict[str, Any]]:
    engine = get_engine()
    with engine.begin() as conn:
        rows = conn.execute(
            text(
                "SELECT id, title, text, lexile, grade_band, phonics_focus, theme, embedding FROM texts"
            )
        ).mappings().all()
        documents = []
        for row in rows:
            embedding = json.loads(row["embedding"]) if row["embedding"] else None
            document = dict(row)
            document["embedding"] = embedding
            documents.append(document)
        return documents


