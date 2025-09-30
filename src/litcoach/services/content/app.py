import os
from typing import Dict, Any
from fastapi import FastAPI
from pydantic import BaseModel
import numpy as np

from litcoach.services.content.db import init_schema, list_texts, search_texts, get_all_with_embeddings
from litcoach.services.content.ingest import run_ingest
from litcoach.utils.openai_client import embedding


app = FastAPI(title="Literacy Coach Content")


class SearchBody(BaseModel):
    lexile_min: int | None = None
    lexile_max: int | None = None
    grade_band: str | None = None
    phonics_focus: str | None = None
    theme: str | None = None
    limit: int = 10


class RagBody(BaseModel):
    query: str
    k: int = 5


@app.on_event("startup")
def startup():
    init_schema()
    run_ingest()


@app.get("/health")
def health():
    return {"ok": True, "service": "content"}


@app.get("/texts")
def get_texts(limit: int = 20):
    return {"results": list_texts(limit=limit)}


@app.post("/texts/search")
def texts_search(body: SearchBody):
    results = search_texts(body.model_dump())
    return {"results": results}


@app.post("/rag/search")
def rag_search(body: RagBody):
    documents = get_all_with_embeddings()
    query_vector = np.array(embedding(body.query), dtype=np.float32)
    scored = []
    for document in documents:
        if not document.get("embedding"):
            continue
        vector = np.array(document["embedding"], dtype=np.float32)
        denom = float(np.linalg.norm(query_vector) * np.linalg.norm(vector))
        similarity = float(np.dot(query_vector, vector) / denom) if denom > 0 else 0.0
        scored.append((similarity, document))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    top = [item[1] for item in scored[: body.k]]
    return {
        "results": [
            {
                "id": doc["id"],
                "title": doc["title"],
                "text": doc["text"],
                "lexile": doc["lexile"],
            }
            for doc in top
        ]
    }


def main():
    import uvicorn

    uvicorn.run("litcoach.services.content.app:app", host="0.0.0.0", port=8002, reload=False, workers=1)


if __name__ == "__main__":
    main()


