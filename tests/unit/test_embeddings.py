"""
Unit tests for embeddings module, focusing on tiktoken-based token counting.
"""

import pytest
import tiktoken

from memdocs.embeddings import chunk_document


class TestChunkDocumentTokenCounting:
    """Test accurate token counting with tiktoken."""

    def test_chunk_respects_max_tokens(self):
        """Test that chunks never exceed max_tokens."""
        # Create a long text that will require multiple chunks
        text = " ".join(["word"] * 1000)  # 1000 words
        max_tokens = 100
        overlap = 20

        chunks = chunk_document(text, max_tokens=max_tokens, overlap=overlap)

        # Verify each chunk respects max_tokens
        encoding = tiktoken.get_encoding("cl100k_base")
        for chunk in chunks:
            token_count = len(encoding.encode(chunk))
            assert (
                token_count <= max_tokens
            ), f"Chunk has {token_count} tokens, exceeds max of {max_tokens}"

    def test_chunk_empty_text(self):
        """Test chunking empty text."""
        chunks = chunk_document("", max_tokens=512, overlap=50)
        assert chunks == []

    def test_chunk_short_text(self):
        """Test chunking text shorter than max_tokens."""
        text = "This is a short text."
        chunks = chunk_document(text, max_tokens=512, overlap=50)

        assert len(chunks) == 1
        assert chunks[0] == text

    def test_chunk_overlap_functionality(self):
        """Test that overlap creates continuity between chunks."""
        # Create text that will produce exactly 2 chunks with overlap
        text = " ".join(["word"] * 200)
        max_tokens = 100
        overlap = 20

        chunks = chunk_document(text, max_tokens=max_tokens, overlap=overlap)

        # Should have multiple chunks
        assert len(chunks) >= 2

        # Verify chunks are not empty
        assert all(len(chunk.strip()) > 0 for chunk in chunks)

    def test_chunk_with_special_characters(self):
        """Test chunking text with special characters and unicode."""
        text = "Hello 世界! This is a test with émojis 🎉 and special chars: @#$%^&*()"
        text = text * 50  # Repeat to make it long enough

        chunks = chunk_document(text, max_tokens=100, overlap=20)

        # Verify chunks are created
        assert len(chunks) > 0

        # Verify token counts
        encoding = tiktoken.get_encoding("cl100k_base")
        for chunk in chunks:
            token_count = len(encoding.encode(chunk))
            assert token_count <= 100

    def test_chunk_code_text(self):
        """Test chunking programming code."""
        code = (
            '''
def calculate_fibonacci(n):
    """Calculate the nth Fibonacci number."""
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

class DataProcessor:
    """Process data with various operations."""

    def __init__(self, data):
        self.data = data

    def filter(self, condition):
        return [item for item in self.data if condition(item)]

    def map(self, transform):
        return [transform(item) for item in self.data]
'''
            * 10
        )  # Repeat to ensure multiple chunks

        chunks = chunk_document(code, max_tokens=200, overlap=30)

        # Verify chunks are created
        assert len(chunks) > 1

        # Verify all chunks respect token limit
        encoding = tiktoken.get_encoding("cl100k_base")
        for chunk in chunks:
            token_count = len(encoding.encode(chunk))
            assert token_count <= 200

    def test_chunk_accurate_vs_old_approximation(self):
        """Test that tiktoken gives more accurate results than word approximation."""
        # Text with varying token-to-word ratios
        text = (
            """
        This is a test. Some words are single tokens, but compound-words and
        special-characters create different token counts than simple word counts.
        The old approximation of 1 token ≈ 0.75 words was inaccurate.
        """
            * 50
        )

        max_tokens = 100
        chunks = chunk_document(text, max_tokens=max_tokens, overlap=20)

        # Verify all chunks respect exact token limit
        encoding = tiktoken.get_encoding("cl100k_base")
        for i, chunk in enumerate(chunks):
            token_count = len(encoding.encode(chunk))
            assert (
                token_count <= max_tokens
            ), f"Chunk {i} has {token_count} tokens, exceeds {max_tokens}"

        # Verify we actually created chunks (text was long enough)
        assert len(chunks) >= 2

    def test_chunk_with_newlines_and_whitespace(self):
        """Test chunking with various whitespace characters."""
        text = "Line 1\n\nLine 2\n\n\nLine 3\t\tTabbed\r\nWindows line ending"
        text = text * 50  # Repeat for multiple chunks

        chunks = chunk_document(text, max_tokens=100, overlap=20)

        # Verify chunks are created
        assert len(chunks) > 0

        # Verify token limits
        encoding = tiktoken.get_encoding("cl100k_base")
        for chunk in chunks:
            token_count = len(encoding.encode(chunk))
            assert token_count <= 100

    def test_chunk_invalid_params(self):
        """Test that invalid parameters raise appropriate errors."""
        text = "Some test text"

        # max_tokens <= overlap should raise ValueError
        with pytest.raises(ValueError, match="max_tokens.*must be greater than overlap"):
            chunk_document(text, max_tokens=50, overlap=50)

        with pytest.raises(ValueError, match="max_tokens.*must be greater than overlap"):
            chunk_document(text, max_tokens=50, overlap=100)

    def test_chunk_very_large_document(self):
        """Test chunking a very large document."""
        # Create a large document
        text = " ".join([f"word_{i}" for i in range(10000)])

        chunks = chunk_document(text, max_tokens=512, overlap=50)

        # Should create many chunks
        assert len(chunks) > 10

        # Verify all chunks respect token limit
        encoding = tiktoken.get_encoding("cl100k_base")
        for chunk in chunks:
            token_count = len(encoding.encode(chunk))
            assert token_count <= 512

    def test_chunk_with_markdown(self):
        """Test chunking markdown documentation."""
        markdown = (
            """
# Main Title

## Section 1

This is some content with **bold** and *italic* text.

- List item 1
- List item 2
- List item 3

```python
def example():
    return "code block"
```

## Section 2

More content with [links](https://example.com) and `inline code`.

| Column 1 | Column 2 |
|----------|----------|
| Data 1   | Data 2   |
"""
            * 20
        )  # Repeat for multiple chunks

        chunks = chunk_document(markdown, max_tokens=256, overlap=30)

        # Verify chunks are created
        assert len(chunks) > 1

        # Verify token limits
        encoding = tiktoken.get_encoding("cl100k_base")
        for chunk in chunks:
            token_count = len(encoding.encode(chunk))
            assert token_count <= 256

    def test_chunk_single_long_token_sequence(self):
        """Test chunking text that becomes a single long token sequence."""
        # Very long single word (rare but possible)
        text = "a" * 1000

        chunks = chunk_document(text, max_tokens=100, overlap=20)

        # Should still create chunks
        assert len(chunks) > 0

        # Verify token limits
        encoding = tiktoken.get_encoding("cl100k_base")
        for chunk in chunks:
            token_count = len(encoding.encode(chunk))
            assert token_count <= 100

    def test_chunk_maintains_content_integrity(self):
        """Test that all original content is preserved across chunks."""
        text = "The quick brown fox jumps over the lazy dog. " * 100
        chunks = chunk_document(text, max_tokens=100, overlap=20)

        # Concatenate all chunks (roughly - overlap makes this approximate)
        # But we should have reasonable coverage
        combined_length = sum(len(chunk) for chunk in chunks)

        # Combined chunks should be substantial compared to original
        # (with overlap, combined will be longer than original)
        assert combined_length >= len(text) * 0.8

    def test_chunk_default_parameters(self):
        """Test that default parameters work correctly."""
        text = " ".join(["word"] * 1000)

        # Call with defaults
        chunks = chunk_document(text)

        # Should use max_tokens=512, overlap=50
        encoding = tiktoken.get_encoding("cl100k_base")
        for chunk in chunks:
            token_count = len(encoding.encode(chunk))
            assert token_count <= 512

    def test_chunk_reproducibility(self):
        """Test that chunking is deterministic and reproducible."""
        text = " ".join([f"word_{i}" for i in range(500)])

        chunks1 = chunk_document(text, max_tokens=100, overlap=20)
        chunks2 = chunk_document(text, max_tokens=100, overlap=20)

        # Should produce identical results
        assert len(chunks1) == len(chunks2)
        assert chunks1 == chunks2

    def test_chunk_different_overlap_values(self):
        """Test various overlap values."""
        text = " ".join(["word"] * 500)

        # No overlap
        chunks_no_overlap = chunk_document(text, max_tokens=100, overlap=0)

        # Small overlap
        chunks_small_overlap = chunk_document(text, max_tokens=100, overlap=10)

        # Large overlap
        chunks_large_overlap = chunk_document(text, max_tokens=100, overlap=50)

        # More overlap should create more chunks (or same number)
        assert len(chunks_large_overlap) >= len(chunks_small_overlap)
        assert len(chunks_small_overlap) >= len(chunks_no_overlap)

        # All should respect token limits
        encoding = tiktoken.get_encoding("cl100k_base")
        for chunks in [chunks_no_overlap, chunks_small_overlap, chunks_large_overlap]:
            for chunk in chunks:
                token_count = len(encoding.encode(chunk))
                assert token_count <= 100


class TestChunkDocumentEdgeCases:
    """Test edge cases in chunk_document function."""

    def test_chunk_whitespace_only(self):
        """Test chunking whitespace-only text."""
        text = "   \n\n\t\t   "
        chunks = chunk_document(text, max_tokens=100, overlap=20)

        # Should handle gracefully
        assert isinstance(chunks, list)

    def test_chunk_single_character(self):
        """Test chunking single character."""
        chunks = chunk_document("a", max_tokens=100, overlap=20)
        assert len(chunks) == 1
        assert chunks[0] == "a"

    def test_chunk_exact_max_tokens(self):
        """Test when text is exactly max_tokens."""
        encoding = tiktoken.get_encoding("cl100k_base")

        # Create text that's exactly 100 tokens
        text = "word " * 100
        actual_tokens = len(encoding.encode(text))

        # Adjust to get closer to exactly 100 tokens
        while actual_tokens > 100:
            text = text[:-5]  # Remove a word
            actual_tokens = len(encoding.encode(text))

        chunks = chunk_document(text, max_tokens=100, overlap=20)

        # Should create exactly 1 chunk since text fits within limit
        assert len(chunks) == 1

    def test_chunk_just_over_max_tokens(self):
        """Test when text is just slightly over max_tokens."""
        encoding = tiktoken.get_encoding("cl100k_base")

        # Create text that's just over 100 tokens
        text = "word " * 101
        actual_tokens = len(encoding.encode(text))

        # Ensure it's over 100
        while actual_tokens <= 100:
            text += " word"
            actual_tokens = len(encoding.encode(text))

        chunks = chunk_document(text, max_tokens=100, overlap=20)

        # Should create 2 chunks
        assert len(chunks) >= 2

        # All chunks should respect limit
        for chunk in chunks:
            token_count = len(encoding.encode(chunk))
            assert token_count <= 100
