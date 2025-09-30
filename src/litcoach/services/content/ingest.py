import os
import json
from typing import List, Dict, Any
from litcoach.services.content.db import init_schema, insert_or_update_text, get_all_with_embeddings
from litcoach.utils.openai_client import embedding


def load_texts(json_path: str) -> List[Dict[str, Any]]:
    with open(json_path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    return data


def ensure_embeddings(docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    enriched: List[Dict[str, Any]] = []
    for doc in docs:
        if doc.get("embedding") is None:
            doc["embedding"] = embedding(doc["text"])
        enriched.append(doc)
    return enriched


def run_ingest():
    init_schema()
    json_path = os.environ.get("CONTENT_TEXTS_JSON", "")
    if not json_path or not os.path.exists(json_path):
        raise RuntimeError("CONTENT_TEXTS_JSON must point to a valid JSON file")
    docs = load_texts(json_path)
    current = get_all_with_embeddings()
    current_ids = {item["id"] for item in current}
    docs_to_write = []
    for doc in docs:
        if doc["id"] not in current_ids or doc.get("embedding") is None:
            docs_to_write.append(doc)
    if docs_to_write:
        docs_to_write = ensure_embeddings(docs_to_write)
    for doc in docs:
        if doc.get("embedding") is None:
            for current_doc in current:
                if current_doc["id"] == doc["id"]:
                    doc["embedding"] = current_doc["embedding"]
                    break
        insert_or_update_text(doc)


if __name__ == "__main__":
    run_ingest()


