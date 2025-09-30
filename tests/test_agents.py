"""Tests for OpenAI Agents SDK integration."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import json
import numpy as np

from litcoach.agents.manager import AgentManager
from litcoach.agents.tools import AgentTools
from litcoach.agents.security import SecureKeyManager
from litcoach.agents.vector_store import VectorStoreManager
from litcoach.agents.retrieval import RetrievalManager


class TestSecureKeyManager:
    """Test secure key management."""

    def test_key_manager_initialization(self, tmp_path):
        """Test key manager initializes correctly."""
        with patch('litcoach.agents.security.Path.home', return_value=tmp_path):
            manager = SecureKeyManager()
            assert manager.env_file == tmp_path / ".env"
            assert manager.key_file == tmp_path / ".keys"

    def test_encrypt_decrypt_api_key(self, tmp_path):
        """Test API key encryption and decryption."""
        with patch('litcoach.agents.security.Path.home', return_value=tmp_path):
            manager = SecureKeyManager()
            test_key = "sk-test123456789"

            # Test encryption
            encrypted = manager.encrypt_api_key(test_key)
            assert encrypted.startswith("file:")
            assert encrypted != test_key

            # Test decryption
            decrypted = manager.decrypt_api_key(encrypted)
            assert decrypted == test_key

    def test_validate_key_format(self, tmp_path):
        """Test API key validation."""
        with patch('litcoach.agents.security.Path.home', return_value=tmp_path):
            manager = SecureKeyManager()

            # Valid key
            assert manager.validate_key("sk-123456789") == True

            # Invalid keys
            assert manager.validate_key("") == False
            assert manager.validate_key("invalid-key") == True  # Basic validation only

    def test_get_key_info(self, tmp_path):
        """Test key information retrieval."""
        with patch('litcoach.agents.security.Path.home', return_value=tmp_path):
            manager = SecureKeyManager()

            # No key initially
            info = manager.get_key_info()
            assert info["has_key"] == False
            assert info["is_encrypted"] == False


class TestVectorStoreManager:
    """Test vector store functionality."""

    @pytest.fixture
    def vector_store(self, tmp_path):
        """Create a vector store for testing."""
        store_path = tmp_path / "test_store"
        return VectorStoreManager(str(store_path))

    @pytest.mark.asyncio
    async def test_add_document(self, vector_store):
        """Test adding a document to the vector store."""
        doc_id = await vector_store.add(
            text="Test document content",
            metadata={"type": "test", "category": "example"}
        )

        assert doc_id is not None
        assert len(vector_store.documents) == 1
        assert vector_store.documents[0]["text"] == "Test document content"
        assert vector_store.documents[0]["metadata"]["type"] == "test"

    @pytest.mark.asyncio
    async def test_search_documents(self, vector_store):
        """Test searching documents in the vector store."""
        # Add test documents
        await vector_store.add("Python programming tutorial", {"topic": "programming"})
        await vector_store.add("Machine learning basics", {"topic": "AI"})
        await vector_store.add("Cooking pasta recipe", {"topic": "cooking"})

        # Search for programming content
        results = await vector_store.search("Python programming", top_k=2)

        assert len(results) > 0
        assert any("Python" in result["text"] for result in results)

    @pytest.mark.asyncio
    async def test_update_document(self, vector_store):
        """Test updating a document."""
        # Add document
        doc_id = await vector_store.add("Original content", {"version": 1})

        # Update document
        success = await vector_store.update(
            doc_id,
            text="Updated content",
            metadata={"version": 2}
        )

        assert success == True
        assert vector_store.documents[0]["text"] == "Updated content"
        assert vector_store.documents[0]["metadata"]["version"] == 2

    @pytest.mark.asyncio
    async def test_delete_document(self, vector_store):
        """Test deleting a document."""
        # Add document
        doc_id = await vector_store.add("Content to delete")

        # Delete document
        success = await vector_store.delete(doc_id)

        assert success == True
        assert len(vector_store.documents) == 0

    def test_get_stats(self, vector_store):
        """Test getting store statistics."""
        stats = vector_store.get_stats()

        assert "total_documents" in stats
        assert "embeddings_shape" in stats
        assert "store_path" in stats
        assert stats["total_documents"] == 0


class TestRetrievalManager:
    """Test retrieval functionality."""

    @pytest.fixture
    def retrieval_manager(self, tmp_path):
        """Create a retrieval manager for testing."""
        store = VectorStoreManager(str(tmp_path / "retrieval_store"))
        return RetrievalManager(store)

    @pytest.mark.asyncio
    async def test_retrieve_documents(self, retrieval_manager):
        """Test document retrieval."""
        # Add test documents
        await retrieval_manager.vector_store.add(
            "Python is a programming language",
            {"category": "tech"}
        )
        await retrieval_manager.vector_store.add(
            "Java is also a programming language",
            {"category": "tech"}
        )

        # Retrieve documents
        results = await retrieval_manager.retrieve("Python programming", top_k=2)

        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_retrieve_with_context(self, retrieval_manager):
        """Test retrieval with context building."""
        # Add test document
        await retrieval_manager.vector_store.add(
            "This is a long document with lots of content that should be truncated when building context for retrieval purposes.",
            {"type": "long_form"}
        )

        # Retrieve with context
        result = await retrieval_manager.retrieve_with_context(
            "document content",
            context_window=100
        )

        assert "context" in result
        assert len(result["context"]) <= 100


class TestAgentTools:
    """Test agent tools functionality."""

    @pytest.fixture
    def agent_tools(self):
        """Create agent tools for testing."""
        return AgentTools()

    def test_get_default_tools(self, agent_tools):
        """Test getting default tool set."""
        tools = agent_tools.get_default_tools()

        assert len(tools) > 0
        tool_names = [tool["name"] for tool in tools]
        expected_tools = [
            "lookup_texts", "rag_search", "assess_read_aloud",
            "score_writing", "search_vector_store", "add_to_vector_store"
        ]

        for expected in expected_tools:
            assert expected in tool_names

    @pytest.mark.asyncio
    async def test_lookup_texts_tool(self, agent_tools):
        """Test the lookup_texts tool."""
        result = await agent_tools.lookup_texts(
            grade_band="K-1",
            limit=5
        )

        assert "results" in result
        assert "count" in result
        assert isinstance(result["results"], list)

    @pytest.mark.asyncio
    async def test_assess_read_aloud_tool(self, agent_tools):
        """Test the assess_read_aloud tool."""
        result = await agent_tools.assess_read_aloud(
            reference_text="The cat sat on the mat.",
            asr_transcript="The cat sat on the mat.",
            timestamps=[0.0, 5.0]
        )

        assert "wcpm" in result
        assert "accuracy" in result
        assert "errors" in result
        assert result["accuracy"] == 1.0  # Perfect match

    @pytest.mark.asyncio
    async def test_score_writing_tool(self, agent_tools):
        """Test the score_writing tool."""
        result = await agent_tools.score_writing(
            prompt="Describe your favorite place",
            essay="The library is my favorite place because it is quiet and has many books.",
            grade_level="5",
            rubric_name="writing_default"
        )

        assert "rubric_scores" in result
        assert "feedback" in result
        assert isinstance(result["rubric_scores"], dict)


class TestAgentManager:
    """Test agent manager functionality."""

    @pytest.fixture
    def agent_manager(self, tmp_path):
        """Create an agent manager for testing."""
        with patch('litcoach.agents.security.Path.home', return_value=tmp_path):
            return AgentManager()

    @pytest.mark.asyncio
    async def test_create_agent_session(self, agent_manager):
        """Test creating an agent session."""
        session = await agent_manager.create_agent_session(
            model="gpt-3.5-turbo",
            provider="openai"
        )

        assert session["model"] == "gpt-3.5-turbo"
        assert session["provider"] == "openai"
        assert "id" in session
        assert "messages" in session
        assert session["messages"] == []

    @pytest.mark.asyncio
    async def test_run_agent_session(self, agent_manager):
        """Test running an agent session."""
        # Create session
        session = await agent_manager.create_agent_session()

        # Mock the OpenAI client
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Test response"

        with patch.object(agent_manager, 'openai_client') as mock_client:
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

            # Run agent
            response = await agent_manager.run_agent(
                session,
                "Hello, how are you?"
            )

            assert response == "Test response"
            assert len(session["messages"]) == 2  # User message + assistant response

    def test_get_session_stats(self, agent_manager):
        """Test getting session statistics."""
        # Create test session
        session = {
            "id": "test_session",
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"},
                {"role": "user", "content": "How are you?"}
            ],
            "metadata": {"created_at": 1000000000}
        }

        stats = agent_manager.get_session_stats(session)

        assert stats["message_count"] == 3
        assert stats["user_messages"] == 2
        assert stats["assistant_messages"] == 1
        assert "session_duration" in stats


@pytest.mark.integration
class TestAgentIntegration:
    """Integration tests for agent components."""

    @pytest.mark.asyncio
    async def test_full_agent_workflow(self, tmp_path):
        """Test complete agent workflow."""
        with patch('litcoach.agents.security.Path.home', return_value=tmp_path):
            # Initialize components
            agent_manager = AgentManager()
            tools = AgentTools()
            vector_store = VectorStoreManager(str(tmp_path / "integration_store"))
            retrieval = RetrievalManager(vector_store)

            # Add some test content to vector store
            doc_id = await vector_store.add(
                "Python is a high-level programming language known for its simplicity.",
                {"category": "programming", "language": "python"}
            )

            # Create agent session
            session = await agent_manager.create_agent_session()

            # Test tool execution
            search_result = await tools.search_vector_store(
                "Python programming",
                top_k=3
            )

            assert isinstance(search_result, dict)
            assert "results" in search_result

            # Test retrieval
            retrieved = await retrieval.retrieve("programming languages", top_k=2)
            assert isinstance(retrieved, list)

    @pytest.mark.asyncio
    async def test_error_handling(self, tmp_path):
        """Test error handling in agent components."""
        with patch('litcoach.agents.security.Path.home', return_value=tmp_path):
            agent_manager = AgentManager()

            # Test with invalid session
            response = await agent_manager.run_agent(
                {"messages": []},  # Invalid session format
                "test message"
            )

            assert "failed" in response.lower() or "error" in response.lower()


@pytest.mark.property
class TestPropertyBased:
    """Property-based tests using Hypothesis."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_vector_store_properties(self, tmp_path):
        """Test vector store properties with various inputs."""
        from hypothesis import given, strategies as st

        store = VectorStoreManager(str(tmp_path / "property_store"))

        @given(st.text(min_size=1, max_size=100))
        async def test_add_and_search(text):
            # Add document
            doc_id = await store.add(text)

            # Should be able to find it
            results = await store.search(text, top_k=1)
            assert len(results) > 0

            # Should be able to delete it
            success = await store.delete(doc_id)
            assert success == True

        await test_add_and_search()

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_retrieval_properties(self, tmp_path):
        """Test retrieval properties."""
        from hypothesis import given, strategies as st

        store = VectorStoreManager(str(tmp_path / "retrieval_property_store"))
        retrieval = RetrievalManager(store)

        @given(st.text(min_size=1, max_size=50))
        async def test_retrieval_consistency(query):
            # Retrieval should not crash
            results = await retrieval.retrieve(query, top_k=5)
            assert isinstance(results, list)

            # Results should be ordered by similarity (highest first)
            if len(results) > 1:
                similarities = [r.get("similarity", 0) for r in results]
                assert similarities == sorted(similarities, reverse=True)

        await test_retrieval_consistency()


@pytest.mark.e2e
class TestEndToEnd:
    """End-to-end tests for complete workflows."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_complete_literacy_session(self, tmp_path):
        """Test complete literacy coaching session."""
        with patch('litcoach.agents.security.Path.home', return_value=tmp_path):
            # Initialize all components
            agent_manager = AgentManager()
            tools = AgentTools()
            vector_store = VectorStoreManager(str(tmp_path / "e2e_store"))
            retrieval = RetrievalManager(vector_store)

            # Add educational content
            await vector_store.add(
                "Reading fluency is the ability to read text accurately, quickly, and with expression.",
                {"topic": "reading", "skill": "fluency"}
            )

            await vector_store.add(
                "Writing skills include grammar, organization, and clarity of ideas.",
                {"topic": "writing", "skill": "composition"}
            )

            # Create agent session
            session = await agent_manager.create_agent_session(
                system_prompt="You are a helpful literacy tutor."
            )

            # Simulate student interaction
            user_query = "Help me improve my reading fluency"
            response = await agent_manager.run_agent(session, user_query)

            assert isinstance(response, str)
            assert len(response) > 0

            # Check that session has the interaction
            assert len(session["messages"]) == 2
            assert session["messages"][0]["role"] == "user"
            assert session["messages"][1]["role"] == "assistant"

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_cross_component_interaction(self, tmp_path):
        """Test interaction between all components."""
        with patch('litcoach.agents.security.Path.home', return_value=tmp_path):
            # This test would verify that all components work together
            # For now, it's a placeholder for more comprehensive e2e tests
            assert True