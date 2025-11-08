"""
Integration tests for index module (MemoryIndexer).
"""
from datetime import datetime, timezone
from pathlib import Path

import pytest

from memdocs.index import MemoryIndexer
from memdocs.schemas import (
    DocumentIndex,
    FeatureSummary,
    ImpactSummary,
    ReferenceSummary,
    ScopeInfo,
    ScopeLevel,
)


@pytest.mark.slow
class TestMemoryIndexerIntegration:
    """Integration tests with real embeddings and search."""

    def test_index_document_real(self, tmp_path: Path):
        """Test indexing a document with real embeddings."""
        memory_dir = tmp_path / "memory"
        indexer = MemoryIndexer(memory_dir=memory_dir, use_embeddings=True)

        assert indexer.use_embeddings is True
        assert indexer.embedder is not None
        assert indexer.search is not None

        # Create a test document
        doc_index = DocumentIndex(
            commit="test123",
            timestamp=datetime.now(timezone.utc),
            scope=ScopeInfo(paths=[Path("test.py")], level=ScopeLevel.FILE, file_count=1),
            features=[
                FeatureSummary(
                    id="feat-001",
                    title="Add user authentication",
                    description="Implement JWT-based authentication for API endpoints",
                )
            ],
            impacts=ImpactSummary(),
            refs=ReferenceSummary(),
        )

        markdown_summary = """
# User Authentication Feature

## Overview
This feature implements JWT-based authentication for all API endpoints.

## Implementation Details
- Added login and logout endpoints
- Integrated JWT token generation
- Added middleware for token validation

## Security Considerations
- Tokens expire after 24 hours
- Refresh tokens supported
- Rate limiting on login attempts
        """

        stats = indexer.index_document(doc_index, markdown_summary)

        # Verify indexing worked
        assert stats["indexed"] is True
        assert stats["chunks"] > 0
        assert stats["embeddings_generated"] > 0
        assert "indices" in stats

        # Verify search index was updated
        search_stats = indexer.search.get_stats()
        assert search_stats["total"] == stats["embeddings_generated"]

    def test_query_memory_real(self, tmp_path: Path):
        """Test querying memory with real embeddings."""
        memory_dir = tmp_path / "memory"
        indexer = MemoryIndexer(memory_dir=memory_dir, use_embeddings=True)

        # Index multiple documents
        documents = [
            ("Python data analysis tutorial", "Learn pandas and numpy for data science"),
            ("JavaScript React guide", "Building modern web apps with React"),
            ("Python machine learning", "Introduction to scikit-learn and TensorFlow"),
        ]

        for i, (title, description) in enumerate(documents):
            doc_index = DocumentIndex(
                commit=f"commit{i}",
                timestamp=datetime.now(timezone.utc),
                scope=ScopeInfo(
                    paths=[Path(f"file{i}.py")], level=ScopeLevel.FILE, file_count=1
                ),
                features=[FeatureSummary(id=f"feat-{i}", title=title, description=description)],
                impacts=ImpactSummary(),
                refs=ReferenceSummary(),
            )

            markdown = f"# {title}\n\n{description}"
            indexer.index_document(doc_index, markdown)

        # Query for Python-related content
        results = indexer.query_memory("Python programming and data analysis", k=2)

        assert len(results) == 2
        # Should rank Python-related docs higher (threshold lowered for embedding variance)
        assert results[0]["score"] > 0.4
        # First result should be Python-related
        metadata = results[0]["metadata"]
        assert "Python" in str(metadata.get("features", []))

    def test_get_stats_real(self, tmp_path: Path):
        """Test getting stats with real index."""
        memory_dir = tmp_path / "memory"
        indexer = MemoryIndexer(memory_dir=memory_dir, use_embeddings=True)

        # Before indexing
        stats = indexer.get_stats()
        assert stats["enabled"] is True
        assert stats["total"] == 0

        # After indexing
        doc_index = DocumentIndex(
            commit="test",
            timestamp=datetime.now(timezone.utc),
            scope=ScopeInfo(paths=[Path("test.py")], level=ScopeLevel.FILE, file_count=1),
            features=[],
            impacts=ImpactSummary(),
            refs=ReferenceSummary(),
        )

        indexer.index_document(doc_index, "Test content for indexing")

        stats = indexer.get_stats()
        assert stats["total"] > 0
        assert stats["dimension"] == 384

    def test_index_persistence(self, tmp_path: Path):
        """Test that indexed data persists across instances."""
        memory_dir = tmp_path / "memory"

        # Create and populate index
        indexer1 = MemoryIndexer(memory_dir=memory_dir, use_embeddings=True)
        doc_index = DocumentIndex(
            commit="persistent",
            timestamp=datetime.now(timezone.utc),
            scope=ScopeInfo(paths=[Path("test.py")], level=ScopeLevel.FILE, file_count=1),
            features=[
                FeatureSummary(
                    id="feat-001", title="Persistent feature", description="This should persist"
                )
            ],
            impacts=ImpactSummary(),
            refs=ReferenceSummary(),
        )

        indexer1.index_document(doc_index, "Persistent content")

        # Create new instance and verify data is there
        indexer2 = MemoryIndexer(memory_dir=memory_dir, use_embeddings=True)

        stats = indexer2.get_stats()
        assert stats["total"] > 0

        # Should be able to query
        results = indexer2.query_memory("persistent", k=1)
        assert len(results) > 0
