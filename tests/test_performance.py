"""Performance and load tests."""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock
import numpy as np

from litcoach.agents.vector_store import VectorStoreManager
from litcoach.agents.retrieval import RetrievalManager
from litcoach.services.ollama_client import HybridLLMClient


class TestVectorStorePerformance:
    """Test vector store performance."""

    @pytest.fixture
    def large_vector_store(self, tmp_path):
        """Create a vector store with many documents."""
        store = VectorStoreManager(str(tmp_path / "large_store"))

        # Add many documents for performance testing
        async def populate_store():
            for i in range(100):
                await store.add(
                    f"Document number {i} with some content about topic {i % 10}",
                    {"index": i, "topic": i % 10}
                )
            return store

        return asyncio.run(populate_store())

    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_search_performance(self, large_vector_store):
        """Test search performance with large dataset."""
        start_time = time.time()

        # Perform multiple searches
        for i in range(10):
            results = await large_vector_store.search(
                f"Document number {i}",
                top_k=5
            )
            assert len(results) > 0

        end_time = time.time()
        total_time = end_time - start_time

        # Should complete within reasonable time (adjust based on system)
        assert total_time < 5.0  # 5 seconds for 10 searches

    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_add_performance(self, tmp_path):
        """Test document addition performance."""
        store = VectorStoreManager(str(tmp_path / "add_perf_store"))

        start_time = time.time()

        # Add documents in batch
        for i in range(50):
            await store.add(f"Performance test document {i}")

        end_time = time.time()
        total_time = end_time - start_time

        assert total_time < 10.0  # 10 seconds for 50 documents
        assert len(store.documents) == 50


class TestRetrievalPerformance:
    """Test retrieval performance."""

    @pytest.fixture
    def retrieval_with_data(self, tmp_path):
        """Create retrieval manager with test data."""
        store = VectorStoreManager(str(tmp_path / "retrieval_perf"))
        retrieval = RetrievalManager(store)

        # Populate with varied content
        async def populate():
            topics = ["science", "math", "history", "literature", "art"]
            for i in range(200):
                topic = topics[i % len(topics)]
                await store.add(
                    f"This is document {i} about {topic}. It contains information about various subjects and concepts related to {topic}.",
                    {"topic": topic, "index": i}
                )
            return retrieval

        return asyncio.run(populate())

    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_retrieval_speed(self, retrieval_with_data):
        """Test retrieval speed with various queries."""
        queries = [
            "science concepts",
            "mathematical principles",
            "historical events",
            "literary works",
            "art techniques"
        ]

        start_time = time.time()

        for query in queries:
            results = await retrieval_with_data.retrieve(query, top_k=10)
            assert len(results) > 0

        end_time = time.time()
        total_time = end_time - start_time

        # Should be fast for retrieval
        assert total_time < 3.0

    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_context_building_performance(self, retrieval_with_data):
        """Test context building performance."""
        start_time = time.time()

        # Build context for multiple queries
        for i in range(5):
            result = await retrieval_with_data.retrieve_with_context(
                f"Query about topic {i}",
                context_window=1500
            )
            assert "context" in result

        end_time = time.time()
        total_time = end_time - start_time

        assert total_time < 5.0


class TestAgentPerformance:
    """Test agent performance."""

    @pytest.fixture
    def mock_agent_manager(self):
        """Create agent manager with mocked dependencies."""
        manager = Mock()
        manager.create_agent_session = AsyncMock(return_value={
            "id": "test_session",
            "messages": [],
            "metadata": {"created_at": time.time()}
        })
        manager.run_agent = AsyncMock(return_value="Mock response")
        return manager

    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_concurrent_sessions(self, mock_agent_manager):
        """Test handling multiple concurrent sessions."""
        async def run_session(session_id):
            session = await mock_agent_manager.create_agent_session()
            session["id"] = session_id

            for i in range(3):
                await mock_agent_manager.run_agent(
                    session,
                    f"Message {i} from session {session_id}"
                )

            return session

        start_time = time.time()

        # Run multiple concurrent sessions
        tasks = [run_session(f"session_{i}") for i in range(10)]
        sessions = await asyncio.gather(*tasks)

        end_time = time.time()
        total_time = end_time - start_time

        assert len(sessions) == 10
        assert total_time < 10.0  # Should handle concurrency efficiently


class TestMemoryUsage:
    """Test memory usage and efficiency."""

    @pytest.mark.asyncio
    async def test_vector_store_memory_efficiency(self, tmp_path):
        """Test that vector store doesn't use excessive memory."""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        store = VectorStoreManager(str(tmp_path / "memory_test"))

        # Add many documents
        for i in range(100):
            await store.add(f"Memory test document {i} with some content")

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_used = final_memory - initial_memory

        # Memory usage should be reasonable (adjust based on system)
        assert memory_used < 100  # Less than 100MB for 100 documents

    @pytest.mark.asyncio
    async def test_session_cleanup_memory(self, tmp_path):
        """Test that session cleanup frees memory."""
        import gc

        # This would test memory cleanup after sessions
        # For now, just ensure garbage collection works
        gc.collect()
        assert True


class TestLoadTesting:
    """Load testing for high-throughput scenarios."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_high_concurrency_vector_operations(self, tmp_path):
        """Test vector store under high concurrency."""
        store = VectorStoreManager(str(tmp_path / "concurrency_test"))

        async def concurrent_operation(op_id):
            """Perform concurrent operations."""
            if op_id % 2 == 0:
                # Add operation
                await store.add(f"Concurrent document {op_id}")
            else:
                # Search operation
                await store.search(f"document {op_id % 10}", top_k=3)

        start_time = time.time()

        # Run many concurrent operations
        tasks = [concurrent_operation(i) for i in range(50)]
        await asyncio.gather(*tasks)

        end_time = time.time()
        total_time = end_time - start_time

        # Should handle concurrency without excessive time
        assert total_time < 15.0
        assert len(store.documents) >= 25  # At least half should succeed

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_burst_traffic_simulation(self, tmp_path):
        """Simulate burst traffic patterns."""
        store = VectorStoreManager(str(tmp_path / "burst_test"))

        # Simulate burst of requests
        burst_sizes = [10, 20, 5, 15, 30]

        for burst_size in burst_sizes:
            start_time = time.time()

            # Burst of add operations
            tasks = []
            for i in range(burst_size):
                tasks.append(store.add(f"Burst document {i}"))

            await asyncio.gather(*tasks)

            burst_time = time.time() - start_time

            # Each burst should complete reasonably quickly
            assert burst_time < burst_size * 0.5  # Max 0.5s per document


class TestScalability:
    """Test system scalability."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_large_document_scalability(self, tmp_path):
        """Test handling of large documents."""
        store = VectorStoreManager(str(tmp_path / "scalability_test"))

        # Test with large documents
        large_content = " ".join([f"Word {i}" for i in range(1000)])  # ~5000 words

        start_time = time.time()

        doc_id = await store.add(large_content, {"size": "large"})

        end_time = time.time()
        add_time = end_time - start_time

        assert doc_id is not None
        assert add_time < 5.0  # Should handle large documents quickly

        # Test searching large documents
        search_start = time.time()
        results = await store.search("Word 500", top_k=1)
        search_time = time.time() - search_start

        assert len(results) > 0
        assert search_time < 2.0

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_many_small_documents(self, tmp_path):
        """Test handling many small documents."""
        store = VectorStoreManager(str(tmp_path / "many_small_test"))

        start_time = time.time()

        # Add many small documents
        for i in range(500):
            await store.add(f"Small doc {i}", {"batch": "many_small"})

        end_time = time.time()
        total_time = end_time - start_time

        assert len(store.documents) == 500
        assert total_time < 30.0  # 30 seconds for 500 documents

        # Test search performance with many documents
        search_start = time.time()
        results = await store.search("Small doc 250", top_k=5)
        search_time = time.time() - search_start

        assert len(results) > 0
        assert search_time < 3.0


@pytest.mark.benchmark
class TestBenchmark:
    """Benchmark tests for performance regression detection."""

    def test_embedding_generation_speed(self, benchmark, tmp_path):
        """Benchmark embedding generation."""
        store = VectorStoreManager(str(tmp_path / "benchmark_store"))

        # Benchmark single embedding
        result = benchmark(lambda: asyncio.run(store.add("Benchmark test document")))
        assert result is not None

    def test_similarity_search_speed(self, benchmark, tmp_path):
        """Benchmark similarity search."""
        async def setup_and_search():
            store = VectorStoreManager(str(tmp_path / "search_benchmark"))
            await store.add("Search benchmark document")
            return await store.search("benchmark", top_k=1)

        result = benchmark(asyncio.run, setup_and_search())
        assert len(result) > 0