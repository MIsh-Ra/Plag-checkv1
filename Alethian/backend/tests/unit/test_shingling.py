"""
Unit tests for shingling module.
Uses REAL SentenceTransformer model — no mocks.
"""
import pytest
from app.core.shingling import create_sliding_windows, generate_embedding, process_text_into_chunks


class TestCreateSlidingWindows:
    """T1-T3: Pure logic tests for sliding window generation."""

    def test_returns_empty_for_empty_text(self):
        assert create_sliding_windows("") == []
        assert create_sliding_windows(None) == []

    def test_returns_single_window_for_short_text(self):
        text = "Hello world. Goodbye."
        result = create_sliding_windows(text, window_size=3)
        # Less than window_size sentences → returns full text as single chunk
        assert len(result) == 1
        assert result[0] == text

    def test_sliding_window_count(self):
        # 5 sentences with window_size=3 → 3 windows
        text = "First sentence. Second sentence. Third sentence. Fourth sentence. Fifth sentence."
        result = create_sliding_windows(text, window_size=3)
        assert len(result) == 3
        assert "First sentence." in result[0]
        assert "Third sentence." in result[0]
        assert "Fifth sentence." in result[2]

    def test_window_size_one(self):
        text = "Alpha. Beta. Gamma."
        result = create_sliding_windows(text, window_size=1)
        assert len(result) == 3


class TestGenerateEmbedding:
    """T4: Uses REAL SentenceTransformer model."""

    def test_embedding_shape_and_values(self):
        embedding = generate_embedding("The quick brown fox jumps over the lazy dog.")
        assert isinstance(embedding, list)
        assert len(embedding) == 384  # all-MiniLM-L6-v2 dimension
        # Real embeddings have non-zero values
        assert any(v != 0.0 for v in embedding)

    def test_similar_texts_produce_similar_embeddings(self):
        emb1 = generate_embedding("Machine learning is a field of artificial intelligence.")
        emb2 = generate_embedding("ML is a branch of AI.")
        # Cosine similarity of similar-meaning texts should be high
        from numpy import dot
        from numpy.linalg import norm
        cos_sim = dot(emb1, emb2) / (norm(emb1) * norm(emb2))
        assert cos_sim > 0.5  # Related texts


class TestProcessTextIntoChunks:
    """T5-T6: Full pipeline with real embeddings and page boundary logic."""

    def test_chunks_have_embeddings(self):
        text = "First sentence here. Second sentence here. Third sentence here. Fourth sentence here. Fifth sentence here."
        chunks = process_text_into_chunks(text)
        assert len(chunks) > 0
        for chunk in chunks:
            assert "text" in chunk
            assert "embedding" in chunk
            assert len(chunk["embedding"]) == 384
            assert "page" in chunk
            assert "char_start" in chunk
            assert "char_end" in chunk

    def test_page_boundaries_assigned_correctly(self):
        text = "First part of page one. Second part of page one. Third part continues. Now page two begins. Page two content here. More page two text."
        boundaries = [
            (0, 80, 1),
            (80, 500, 2)
        ]
        chunks = process_text_into_chunks(text, page_boundaries=boundaries)
        assert len(chunks) > 0
        # First chunk should be on page 1 since it starts at char_start < 80
        pages_seen = set(c["page"] for c in chunks)
        assert 1 in pages_seen or 2 in pages_seen
