"""Retrieval Manager for RAG functionality."""

import asyncio
from typing import Dict, Any, List, Optional
from ..agents.vector_store import VectorStoreManager


class RetrievalManager:
    """Manages retrieval-augmented generation functionality."""

    def __init__(self, vector_store: VectorStoreManager):
        self.vector_store = vector_store

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        metadata_filter: Optional[Dict[str, Any]] = None,
        min_similarity: float = 0.1
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant documents for a query."""
        try:
            results = await self.vector_store.search(
                query=query,
                top_k=top_k * 2,  # Get more candidates for filtering
                metadata_filter=metadata_filter
            )

            # Filter by minimum similarity
            filtered_results = [
                result for result in results
                if result.get("similarity", 0) >= min_similarity
            ]

            # Return top k results
            return filtered_results[:top_k]

        except Exception as e:
            print(f"Retrieval failed: {e}")
            return []

    async def retrieve_with_context(
        self,
        query: str,
        context_window: int = 1000,
        **kwargs
    ) -> Dict[str, Any]:
        """Retrieve documents with surrounding context."""
        results = await self.retrieve(query, **kwargs)

        # Add context around each result
        for result in results:
            original_text = result.get("text", "")
            if len(original_text) > context_window:
                # Truncate with context preservation
                words = original_text.split()
                if len(words) > context_window // 5:  # Rough word estimate
                    half_window = (context_window // 2) // 5
                    start = max(0, len(words) // 2 - half_window)
                    end = min(len(words), len(words) // 2 + half_window)
                    context_words = words[start:end]
                    result["context"] = " ".join(context_words)
                else:
                    result["context"] = original_text
            else:
                result["context"] = original_text

        return {
            "query": query,
            "results": results,
            "total_found": len(results),
            "context_window": context_window
        }

    async def retrieve_by_metadata(
        self,
        metadata_filter: Dict[str, Any],
        query: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Retrieve documents based on metadata filters."""
        try:
            if query:
                # Search with both query and metadata filter
                results = await self.vector_store.search(
                    query=query,
                    top_k=top_k * 2,
                    metadata_filter=metadata_filter
                )
            else:
                # Get all documents and filter by metadata
                # This is a simplified approach - in practice, you'd want indexed metadata
                all_docs = []
                for doc in self.vector_store.documents:
                    doc_metadata = doc.get("metadata", {})
                    if all(doc_metadata.get(k) == v for k, v in metadata_filter.items()):
                        all_docs.append({
                            "id": doc["id"],
                            "text": doc["text"],
                            "content_type": doc["content_type"],
                            "metadata": doc["metadata"],
                            "similarity": 1.0  # Perfect match for metadata
                        })

                results = all_docs[:top_k]

            return results

        except Exception as e:
            print(f"Metadata retrieval failed: {e}")
            return []

    async def build_context_from_results(
        self,
        results: List[Dict[str, Any]],
        max_context_length: int = 2000,
        include_metadata: bool = True
    ) -> str:
        """Build a context string from retrieval results."""
        if not results:
            return ""

        context_parts = []

        for i, result in enumerate(results):
            # Add source identifier
            source_id = result.get("id", f"source_{i}")
            context_parts.append(f"[Source: {source_id}]")

            # Add content
            content = result.get("text", "")
            if len(content) > 500:  # Truncate long content
                content = content[:500] + "..."
            context_parts.append(content)

            # Add metadata if requested
            if include_metadata:
                metadata = result.get("metadata", {})
                if metadata:
                    metadata_str = ", ".join(f"{k}: {v}" for k, v in metadata.items())
                    context_parts.append(f"[Metadata: {metadata_str}]")

            context_parts.append("")  # Empty line between sources

        # Combine and truncate to max length
        full_context = "\n".join(context_parts)
        if len(full_context) > max_context_length:
            full_context = full_context[:max_context_length] + "..."

        return full_context

    async def retrieve_and_build_context(
        self,
        query: str,
        max_context_length: int = 2000,
        **kwargs
    ) -> Dict[str, Any]:
        """Retrieve documents and build context in one call."""
        results = await self.retrieve(query, **kwargs)
        context = await self.build_context_from_results(results, max_context_length)

        return {
            "query": query,
            "context": context,
            "source_count": len(results),
            "context_length": len(context)
        }

    async def get_retrieval_stats(self) -> Dict[str, Any]:
        """Get retrieval system statistics."""
        store_stats = self.vector_store.get_stats()

        return {
            "vector_store": store_stats,
            "retrieval_ready": store_stats["total_documents"] > 0,
            "last_updated": store_stats.get("metadata", {}).get("last_updated")
        }