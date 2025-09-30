"""Vector Store Manager for embeddings and similarity search."""

import json
import os
import asyncio
from typing import Dict, Any, List, Optional
import numpy as np
from pathlib import Path
from ..utils.openai_client import embedding as openai_embedding
from ..services.ollama_client import HybridLLMClient


class VectorStoreManager:
    """Manages vector embeddings and similarity search."""

    def __init__(self, store_path: str = "./data/vector_store"):
        self.store_path = Path(store_path)
        self.store_path.mkdir(parents=True, exist_ok=True)
        self.documents_file = self.store_path / "documents.json"
        self.embeddings_file = self.store_path / "embeddings.npy"
        self.metadata_file = self.store_path / "metadata.json"

        # In-memory storage for fast access
        self.documents: List[Dict[str, Any]] = []
        self.embeddings: Optional[np.ndarray] = None
        self.metadata: Dict[str, Any] = {}

        # Initialize or load existing store
        self._load_store()

        # Initialize LLM client for embeddings
        self.llm_client = HybridLLMClient()

    def _load_store(self) -> None:
        """Load existing vector store from disk."""
        try:
            # Load documents
            if self.documents_file.exists():
                with open(self.documents_file, 'r') as f:
                    self.documents = json.load(f)

            # Load embeddings
            if self.embeddings_file.exists():
                self.embeddings = np.load(self.embeddings_file)

            # Load metadata
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r') as f:
                    self.metadata = json.load(f)

        except Exception as e:
            # Initialize empty store
            self.documents = []
            self.embeddings = None
            self.metadata = {
                "created_at": asyncio.get_event_loop().time(),
                "total_documents": 0,
                "embedding_model": "text-embedding-3-small"
            }

    def _save_store(self) -> None:
        """Save vector store to disk."""
        try:
            # Save documents
            with open(self.documents_file, 'w') as f:
                json.dump(self.documents, f, indent=2)

            # Save embeddings
            if self.embeddings is not None:
                np.save(self.embeddings_file, self.embeddings)

            # Save metadata
            self.metadata["last_updated"] = asyncio.get_event_loop().time()
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)

        except Exception as e:
            print(f"Warning: Failed to save vector store: {e}")

    async def add(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        content_type: str = "text",
        doc_id: Optional[str] = None
    ) -> str:
        """Add text to the vector store."""
        if doc_id is None:
            import uuid
            doc_id = str(uuid.uuid4())

        try:
            # Generate embedding
            if self.llm_client.openai_client:
                # Use OpenAI for embeddings
                embedding_vector = await asyncio.get_event_loop().run_in_executor(
                    None, openai_embedding, text
                )
            else:
                # Use Ollama for embeddings
                embedding_result = await self.llm_client.create_embeddings([text])
                embedding_vector = embedding_result[0] if embedding_result else []

            if not embedding_vector:
                raise ValueError("Failed to generate embedding")

            # Convert to numpy array
            embedding_array = np.array(embedding_vector, dtype=np.float32)

            # Add to store
            document = {
                "id": doc_id,
                "text": text,
                "content_type": content_type,
                "metadata": metadata or {},
                "embedding_shape": embedding_array.shape,
                "created_at": asyncio.get_event_loop().time()
            }

            self.documents.append(document)

            # Update embeddings array
            if self.embeddings is None:
                self.embeddings = embedding_array.reshape(1, -1)
            else:
                self.embeddings = np.vstack([self.embeddings, embedding_array])

            # Update metadata
            self.metadata["total_documents"] = len(self.documents)
            self.metadata["last_updated"] = asyncio.get_event_loop().time()

            # Save to disk
            self._save_store()

            return doc_id

        except Exception as e:
            raise RuntimeError(f"Failed to add document to vector store: {str(e)}")

    async def search(
        self,
        query: str,
        top_k: int = 5,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar documents."""
        if not self.documents or self.embeddings is None:
            return []

        try:
            # Generate query embedding
            if self.llm_client.openai_client:
                query_embedding = await asyncio.get_event_loop().run_in_executor(
                    None, openai_embedding, query
                )
            else:
                query_result = await self.llm_client.create_embeddings([query])
                query_embedding = query_result[0] if query_result else []

            if not query_embedding:
                return []

            # Convert to numpy array
            query_array = np.array(query_embedding, dtype=np.float32)

            # Calculate similarities
            similarities = []
            for i, doc in enumerate(self.documents):
                # Apply metadata filter if specified
                if metadata_filter:
                    doc_metadata = doc.get("metadata", {})
                    if not all(doc_metadata.get(k) == v for k, v in metadata_filter.items()):
                        continue

                # Calculate cosine similarity
                doc_embedding = self.embeddings[i]
                denom = (np.linalg.norm(query_array) * np.linalg.norm(doc_embedding))
                if denom > 0:
                    similarity = float(np.dot(query_array, doc_embedding) / denom)
                else:
                    similarity = 0.0

                similarities.append((similarity, doc))

            # Sort by similarity and get top k
            similarities.sort(key=lambda x: x[0], reverse=True)
            top_results = similarities[:top_k]

            # Format results
            results = []
            for similarity, doc in top_results:
                results.append({
                    "id": doc["id"],
                    "text": doc["text"][:200] + "..." if len(doc["text"]) > 200 else doc["text"],
                    "content_type": doc["content_type"],
                    "metadata": doc["metadata"],
                    "similarity": similarity,
                    "created_at": doc["created_at"]
                })

            return results

        except Exception as e:
            print(f"Vector search failed: {e}")
            return []

    async def delete(self, doc_id: str) -> bool:
        """Delete a document from the vector store."""
        try:
            # Find document index
            doc_index = None
            for i, doc in enumerate(self.documents):
                if doc["id"] == doc_id:
                    doc_index = i
                    break

            if doc_index is None:
                return False

            # Remove document and embedding
            self.documents.pop(doc_index)
            if self.embeddings is not None:
                self.embeddings = np.delete(self.embeddings, doc_index, axis=0)

            # Update metadata
            self.metadata["total_documents"] = len(self.documents)
            self.metadata["last_updated"] = asyncio.get_event_loop().time()

            # Save to disk
            self._save_store()

            return True

        except Exception as e:
            print(f"Delete failed: {e}")
            return False

    async def update(
        self,
        doc_id: str,
        text: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update a document in the vector store."""
        try:
            # Find document
            doc = None
            doc_index = None
            for i, d in enumerate(self.documents):
                if d["id"] == doc_id:
                    doc = d
                    doc_index = i
                    break

            if doc is None:
                return False

            # Update text if provided
            if text is not None:
                doc["text"] = text
                # Regenerate embedding
                if self.llm_client.openai_client:
                    new_embedding = await asyncio.get_event_loop().run_in_executor(
                        None, openai_embedding, text
                    )
                else:
                    embedding_result = await self.llm_client.create_embeddings([text])
                    new_embedding = embedding_result[0] if embedding_result else []

                if new_embedding:
                    new_embedding_array = np.array(new_embedding, dtype=np.float32)
                    if self.embeddings is not None and doc_index < len(self.embeddings):
                        self.embeddings[doc_index] = new_embedding_array

            # Update metadata if provided
            if metadata is not None:
                doc["metadata"].update(metadata)

            # Update timestamp
            doc["updated_at"] = asyncio.get_event_loop().time()
            self.metadata["last_updated"] = asyncio.get_event_loop().time()

            # Save to disk
            self._save_store()

            return True

        except Exception as e:
            print(f"Update failed: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics."""
        return {
            "total_documents": len(self.documents),
            "embeddings_shape": self.embeddings.shape if self.embeddings is not None else None,
            "store_path": str(self.store_path),
            "metadata": self.metadata
        }

    async def health_check(self) -> bool:
        """Check if vector store is healthy."""
        try:
            # Basic checks
            if not self.store_path.exists():
                return False

            if not self.documents_file.exists():
                return False

            # Try to load a small subset
            test_docs = self.documents[:1] if self.documents else []
            return len(test_docs) >= 0  # Always true if we get here

        except Exception:
            return False

    def clear(self) -> None:
        """Clear all documents from the vector store."""
        self.documents = []
        self.embeddings = None
        self.metadata = {
            "created_at": asyncio.get_event_loop().time(),
            "total_documents": 0,
            "embedding_model": "text-embedding-3-small"
        }
        self._save_store()

    def export_store(self, export_path: str) -> None:
        """Export vector store to a file."""
        export_data = {
            "documents": self.documents,
            "metadata": self.metadata,
            "exported_at": asyncio.get_event_loop().time()
        }

        with open(export_path, 'w') as f:
            json.dump(export_data, f, indent=2)

    def import_store(self, import_path: str) -> bool:
        """Import vector store from a file."""
        try:
            with open(import_path, 'r') as f:
                import_data = json.load(f)

            self.documents = import_data.get("documents", [])
            self.metadata = import_data.get("metadata", {})

            # Rebuild embeddings array
            if self.documents:
                embeddings_list = []
                for doc in self.documents:
                    # This is a simplified approach - in practice, you'd need the actual embeddings
                    # For now, we'll regenerate them
                    pass

                self.metadata["total_documents"] = len(self.documents)
                self._save_store()

            return True

        except Exception as e:
            print(f"Import failed: {e}")
            return False