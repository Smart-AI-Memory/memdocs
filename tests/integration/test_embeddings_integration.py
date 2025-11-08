"""
Integration tests for embeddings module using real sentence-transformers.
"""

from pathlib import Path

import pytest

from memdocs.embeddings import (
    LocalEmbedder,
    chunk_document,
    load_embeddings,
    save_embeddings,
)


@pytest.mark.slow
class TestLocalEmbedderIntegration:
    """Integration tests with real sentence-transformers."""

    def test_embedder_real_model(self, tmp_path: Path):
        """Test embedder with real model (downloads ~90MB on first run)."""
        cache_dir = tmp_path / "cache"
        embedder = LocalEmbedder(cache_dir=cache_dir)

        assert embedder.model_name == "all-MiniLM-L6-v2"
        assert embedder.dimension == 384
        assert embedder.cache_dir == cache_dir

    def test_embed_documents_real(self, tmp_path: Path):
        """Test embedding real documents."""
        embedder = LocalEmbedder(cache_dir=tmp_path / "cache")

        texts = [
            "This is a test document about Python programming.",
            "Another document discussing machine learning concepts.",
        ]

        embeddings = embedder.embed_documents(texts)

        assert len(embeddings) == 2
        assert len(embeddings[0]) == 384  # Dimension
        assert all(isinstance(val, float) for val in embeddings[0])
        # Embeddings should be different for different texts
        assert embeddings[0] != embeddings[1]

    def test_embed_query_real(self, tmp_path: Path):
        """Test embedding a real query."""
        embedder = LocalEmbedder(cache_dir=tmp_path / "cache")

        query = "What is Python?"
        embedding = embedder.embed_query(query)

        assert len(embedding) == 384
        assert all(isinstance(val, float) for val in embedding)

    def test_similar_texts_have_similar_embeddings(self, tmp_path: Path):
        """Test that similar texts produce similar embeddings."""
        import numpy as np

        embedder = LocalEmbedder(cache_dir=tmp_path / "cache")

        texts = [
            "Python is a programming language",
            "Python is used for coding",
            "The sky is blue and beautiful",
        ]

        embeddings = embedder.embed_documents(texts)

        # Calculate cosine similarity
        def cosine_similarity(a, b):
            return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

        # Similar texts (0 and 1) should have higher similarity than dissimilar (0 and 2)
        sim_01 = cosine_similarity(embeddings[0], embeddings[1])
        sim_02 = cosine_similarity(embeddings[0], embeddings[2])

        assert sim_01 > sim_02


class TestChunkingIntegration:
    """Test chunking with real documents."""

    def test_chunk_real_code(self):
        """Test chunking real Python code."""
        code = '''
def calculate_sum(numbers):
    """Calculate the sum of a list of numbers."""
    total = 0
    for num in numbers:
        total += num
    return total

class MathOperations:
    """A class for mathematical operations."""

    def add(self, a, b):
        return a + b

    def subtract(self, a, b):
        return a - b
        '''

        chunks = chunk_document(code, max_tokens=50, overlap=10)

        # Should create multiple chunks
        assert len(chunks) >= 2
        # All chunks should contain some content
        assert all(len(chunk.strip()) > 0 for chunk in chunks)


class TestSaveLoadIntegration:
    """Test save/load with real embeddings."""

    def test_save_load_real_embeddings(self, tmp_path: Path):
        """Test saving and loading real embeddings."""
        embedder = LocalEmbedder(cache_dir=tmp_path / "cache")

        texts = ["Test document 1", "Test document 2"]
        embeddings = embedder.embed_documents(texts)

        # Save
        output_file = tmp_path / "embeddings.json"
        metadata = {"doc_id": "test123", "chunks": texts}
        save_embeddings(embeddings, metadata, output_file)

        # Load
        loaded_embeddings, loaded_metadata = load_embeddings(output_file)

        # Verify
        assert loaded_embeddings == embeddings
        assert loaded_metadata["doc_id"] == "test123"
        assert loaded_metadata["chunks"] == texts
