"""Enhanced tool definitions for OpenAI Agents SDK."""

import json
from typing import Dict, Any, List, Optional
import httpx
from ..services.content.db import search_texts, get_all_with_embeddings
from ..services.assessment.app import assess_reading, score_writing
from ..utils.openai_client import embedding
from ..agents.vector_store import VectorStoreManager


class AgentTools:
    """Enhanced tools for the literacy coaching agent."""

    def __init__(self):
        self.content_url = "http://localhost:8002"
        self.assessment_url = "http://localhost:8003"
        self.vector_store = VectorStoreManager()

    def get_default_tools(self) -> List[Dict[str, Any]]:
        """Get default set of tools for the agent."""
        return [
            {
                "name": "lookup_texts",
                "description": "Search leveled texts by lexile, grade, phonics focus, or theme",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "lexile_min": {"type": "integer", "description": "Minimum lexile level"},
                        "lexile_max": {"type": "integer", "description": "Maximum lexile level"},
                        "grade_band": {"type": "string", "description": "Grade band (K-1, 2-4, 5-7, etc.)"},
                        "phonics_focus": {"type": "string", "description": "Phonics pattern focus"},
                        "theme": {"type": "string", "description": "Text theme"},
                        "limit": {"type": "integer", "description": "Maximum results to return", "default": 10}
                    },
                    "required": []
                }
            },
            {
                "name": "rag_search",
                "description": "Semantic search over curated corpus using vector similarity",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "k": {"type": "integer", "description": "Number of results", "default": 5}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "assess_read_aloud",
                "description": "Compute WCPM and accuracy from read-aloud transcripts",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reference_text": {"type": "string", "description": "Original text"},
                        "asr_transcript": {"type": "string", "description": "Speech-to-text transcript"},
                        "timestamps": {
                            "type": "array",
                            "items": {"type": "number"},
                            "description": "Word timing data"
                        }
                    },
                    "required": ["reference_text", "asr_transcript"]
                }
            },
            {
                "name": "score_writing",
                "description": "Score student writing using rubric dimensions and provide feedback",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {"type": "string", "description": "Writing prompt"},
                        "essay": {"type": "string", "description": "Student essay"},
                        "grade_level": {"type": "string", "description": "Grade level"},
                        "rubric_name": {"type": "string", "description": "Rubric to use", "default": "writing_default"}
                    },
                    "required": ["essay", "rubric_name"]
                }
            },
            {
                "name": "search_vector_store",
                "description": "Search the vector store for relevant information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "top_k": {"type": "integer", "description": "Number of results", "default": 5},
                        "metadata_filter": {"type": "object", "description": "Metadata filters"}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "add_to_vector_store",
                "description": "Add content to the vector store for future retrieval",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "content": {"type": "string", "description": "Content to add"},
                        "metadata": {"type": "object", "description": "Metadata for the content"},
                        "content_type": {"type": "string", "description": "Type of content", "default": "text"}
                    },
                    "required": ["content"]
                }
            },
            {
                "name": "get_session_context",
                "description": "Get context about the current tutoring session",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "session_id": {"type": "string", "description": "Session identifier"},
                        "context_type": {"type": "string", "description": "Type of context needed"}
                    },
                    "required": ["session_id"]
                }
            }
        ]

    async def lookup_texts(
        self,
        lexile_min: Optional[int] = None,
        lexile_max: Optional[int] = None,
        grade_band: Optional[str] = None,
        phonics_focus: Optional[str] = None,
        theme: Optional[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Search for leveled texts."""
        try:
            filters = {}
            if lexile_min is not None:
                filters["lexile_min"] = lexile_min
            if lexile_max is not None:
                filters["lexile_max"] = lexile_max
            if grade_band:
                filters["grade_band"] = grade_band
            if phonics_focus:
                filters["phonics_focus"] = phonics_focus
            if theme:
                filters["theme"] = theme

            results = search_texts(filters, limit)

            return {
                "results": results,
                "count": len(results),
                "filters_applied": filters
            }

        except Exception as e:
            return {"error": f"Text lookup failed: {str(e)}"}

    async def rag_search(self, query: str, k: int = 5) -> Dict[str, Any]:
        """Perform semantic search over the corpus."""
        try:
            # Get all texts with embeddings
            docs = get_all_with_embeddings()

            if not docs:
                return {"results": [], "count": 0}

            # Calculate embeddings for query
            query_emb = embedding(query)

            # Calculate similarities
            import numpy as np
            scored = []
            for doc in docs:
                if not doc.get("embedding"):
                    continue

                doc_emb = np.array(doc["embedding"], dtype=np.float32)
                query_emb_array = np.array(query_emb, dtype=np.float32)

                # Calculate cosine similarity
                denom = (np.linalg.norm(query_emb_array) * np.linalg.norm(doc_emb))
                if denom > 0:
                    sim = float(np.dot(query_emb_array, doc_emb) / denom)
                else:
                    sim = 0.0

                scored.append((sim, doc))

            # Sort by similarity and get top k
            scored.sort(key=lambda x: x[0], reverse=True)
            top_docs = [doc for _, doc in scored[:k]]

            results = []
            for doc in top_docs:
                results.append({
                    "id": doc["id"],
                    "title": doc["title"],
                    "text": doc["text"][:200] + "..." if len(doc["text"]) > 200 else doc["text"],
                    "lexile": doc.get("lexile"),
                    "grade_band": doc.get("grade_band"),
                    "similarity": scored[:k][results.index({
                        "id": doc["id"],
                        "title": doc["title"],
                        "text": doc["text"][:200] + "..." if len(doc["text"]) > 200 else doc["text"],
                        "lexile": doc.get("lexile"),
                        "grade_band": doc.get("grade_band")
                    })-len(results)+len(results)][0] if results else 0.0
                })

            return {
                "results": results,
                "count": len(results),
                "query": query
            }

        except Exception as e:
            return {"error": f"RAG search failed: {str(e)}"}

    async def assess_read_aloud(
        self,
        reference_text: str,
        asr_transcript: str,
        timestamps: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """Assess reading fluency."""
        try:
            # Create mock request objects for the assessment function
            class MockInput:
                def __init__(self):
                    self.reference_text = reference_text
                    self.asr_transcript = asr_transcript
                    self.timestamps = timestamps or [0.0, 60.0]

            mock_input = MockInput()

            # Call the existing assessment function
            result = assess_reading(mock_input)

            return {
                "wcpm": result.wcpm,
                "accuracy": result.accuracy,
                "errors": result.errors,
                "reference_text": reference_text,
                "transcript": asr_transcript
            }

        except Exception as e:
            return {"error": f"Reading assessment failed: {str(e)}"}

    async def score_writing(
        self,
        prompt: str,
        essay: str,
        grade_level: str,
        rubric_name: str = "writing_default"
    ) -> Dict[str, Any]:
        """Score student writing."""
        try:
            # Create mock request objects for the scoring function
            class MockInput:
                def __init__(self):
                    self.prompt = prompt
                    self.essay = essay
                    self.grade_level = grade_level
                    self.rubric_name = rubric_name

            mock_input = MockInput()

            # Call the existing scoring function
            result = score_writing(mock_input)

            return {
                "rubric_scores": result.rubric_scores,
                "feedback": result.feedback,
                "prompt": prompt,
                "essay": essay,
                "grade_level": grade_level
            }

        except Exception as e:
            return {"error": f"Writing scoring failed: {str(e)}"}

    async def search_vector_store(
        self,
        query: str,
        top_k: int = 5,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Search the vector store."""
        try:
            results = await self.vector_store.search(query, top_k=top_k)
            return {
                "results": results,
                "count": len(results),
                "query": query
            }
        except Exception as e:
            return {"error": f"Vector store search failed: {str(e)}"}

    async def add_to_vector_store(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        content_type: str = "text"
    ) -> Dict[str, Any]:
        """Add content to vector store."""
        try:
            doc_id = await self.vector_store.add(
                text=content,
                metadata=metadata or {},
                content_type=content_type
            )

            return {
                "success": True,
                "document_id": doc_id,
                "content_length": len(content)
            }

        except Exception as e:
            return {"error": f"Vector store add failed: {str(e)}"}

    async def get_session_context(self, session_id: str, context_type: str) -> Dict[str, Any]:
        """Get session context information."""
        # This would integrate with the session management system
        return {
            "session_id": session_id,
            "context_type": context_type,
            "available_context": ["history", "preferences", "progress"]
        }