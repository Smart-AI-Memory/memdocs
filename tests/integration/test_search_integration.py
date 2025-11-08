"""
Integration tests for search module using real FAISS.
"""
from pathlib import Path

import numpy as np
import pytest

from memdocs.embeddings import LocalEmbedder
from memdocs.search import LocalVectorSearch, search_memory


@pytest.mark.slow
class TestLocalVectorSearchIntegration:
    """Integration tests with real FAISS."""

    def test_create_and_search_real_index(self, tmp_path: Path):
        """Test creating and searching a real FAISS index."""
        index_path = tmp_path / "test.index"
        metadata_path = tmp_path / "metadata.json"

        search = LocalVectorSearch(
            index_path=index_path, metadata_path=metadata_path, dimension=384
        )

        # Create some test embeddings
        embedder = LocalEmbedder(cache_dir=tmp_path / "cache")
        texts = [
            "Python programming language documentation",
            "JavaScript web development guide",
            "Machine learning with Python",
        ]
        embeddings = embedder.embed_documents(texts)

        # Add to index
        documents = [{"text": text, "id": i} for i, text in enumerate(texts)]
        indices = search.add_embeddings(embeddings, documents)

        assert len(indices) == 3
        assert search.index.ntotal == 3

        # Search for similar content
        query_embedding = embedder.embed_query("Python coding")
        results = search.search(query_embedding, k=2)

        assert len(results) == 2
        # Should find Python-related docs first
        assert "Python" in results[0]["metadata"]["text"]
        assert results[0]["score"] > results[1]["score"]

    def test_save_and_load_index(self, tmp_path: Path):
        """Test saving and loading FAISS index."""
        index_path = tmp_path / "test.index"
        metadata_path = tmp_path / "metadata.json"

        # Create and populate index
        search = LocalVectorSearch(
            index_path=index_path, metadata_path=metadata_path, dimension=384
        )

        embedder = LocalEmbedder(cache_dir=tmp_path / "cache")
        texts = ["Document 1", "Document 2"]
        embeddings = embedder.embed_documents(texts)
        documents = [{"text": t} for t in texts]

        search.add_embeddings(embeddings, documents)
        search.save()

        # Load in new instance
        search2 = LocalVectorSearch(
            index_path=index_path, metadata_path=metadata_path, dimension=384
        )

        assert search2.index.ntotal == 2
        assert len(search2.metadata) == 2

    def test_remove_and_rebuild(self, tmp_path: Path):
        """Test removing entries and rebuilding index."""
        search = LocalVectorSearch(
            index_path=tmp_path / "test.index",
            metadata_path=tmp_path / "metadata.json",
            dimension=384,
        )

        embedder = LocalEmbedder(cache_dir=tmp_path / "cache")
        texts = ["Keep this", "Delete this", "Keep this too"]
        embeddings = embedder.embed_documents(texts)
        documents = [{"text": t, "id": i} for i, t in enumerate(texts)]

        indices = search.add_embeddings(embeddings, documents)

        # Mark one for deletion
        search.remove_by_indices([indices[1]])

        assert search.metadata[str(indices[1])]["deleted"] is True

        # Rebuild
        removed = search.rebuild_index()

        assert removed == 1
        assert str(indices[1]) not in search.metadata

    def test_get_stats(self, tmp_path: Path):
        """Test getting index statistics."""
        search = LocalVectorSearch(
            index_path=tmp_path / "test.index",
            metadata_path=tmp_path / "metadata.json",
            dimension=384,
        )

        embedder = LocalEmbedder(cache_dir=tmp_path / "cache")
        texts = ["Doc 1", "Doc 2", "Doc 3"]
        embeddings = embedder.embed_documents(texts)
        documents = [{"text": t} for t in texts]

        search.add_embeddings(embeddings, documents)
        indices = list(range(3))
        search.remove_by_indices([indices[1]])

        stats = search.get_stats()

        assert stats["total"] == 3
        assert stats["deleted"] == 1
        assert stats["active"] == 2
        assert stats["dimension"] == 384


class TestSearchMemoryIntegration:
    """Test search_memory helper function."""

    def test_search_memory_end_to_end(self, tmp_path: Path):
        """Test full search workflow."""
        embedder = LocalEmbedder(cache_dir=tmp_path / "cache")
        search = LocalVectorSearch(
            index_path=tmp_path / "test.index",
            metadata_path=tmp_path / "metadata.json",
            dimension=embedder.dimension,
        )

        # Index some documents
        texts = [
            "How to use Python for data analysis",
            "JavaScript frameworks for frontend development",
            "Python libraries for machine learning",
        ]
        embeddings = embedder.embed_documents(texts)
        documents = [{"content": t} for t in texts]
        search.add_embeddings(embeddings, documents)

        # Search
        results = search_memory("Python data science", embedder, search, k=2)

        assert len(results) == 2
        # Python-related documents should rank higher
        assert "Python" in results[0]["metadata"]["content"]
