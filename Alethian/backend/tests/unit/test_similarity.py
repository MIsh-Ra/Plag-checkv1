"""
Unit tests for similarity module.
Uses REAL Qdrant instance at localhost:6333 — no mocks.
"""
import pytest
import uuid
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance

from app.core.similarity import QdrantManager, deduplicate, index_document, run_similarity
from app.core.shingling import generate_embedding


# Use a dedicated test collection to avoid polluting production data
TEST_COLLECTION = "test_document_chunks"


@pytest.fixture(scope="module")
def qdrant_client():
    """Connect to real Qdrant and create/clean a test collection."""
    client = QdrantClient(host="localhost", port=6333)
    # Recreate test collection
    try:
        client.delete_collection(TEST_COLLECTION)
    except Exception:
        pass
    client.create_collection(
        collection_name=TEST_COLLECTION,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE)
    )
    yield client
    # Cleanup
    try:
        client.delete_collection(TEST_COLLECTION)
    except Exception:
        pass


class TestQdrantManager:
    """Tests against real Qdrant instance."""

    def test_ensure_collection_exists(self):
        """Verify QdrantManager creates the collection on init."""
        qm = QdrantManager()
        info = qm.client.get_collection(qm.collection_name)
        assert info is not None

    def test_add_and_search_chunks(self, qdrant_client):
        """Index real embeddings and search them back."""
        text = "Data mining involves discovering patterns in large datasets."
        embedding = generate_embedding(text)

        from qdrant_client.models import PointStruct
        point_id = str(uuid.uuid4())
        qdrant_client.upsert(
            collection_name=TEST_COLLECTION,
            points=[PointStruct(
                id=point_id,
                vector=embedding,
                payload={"document_id": "doc-test-1", "text": text}
            )]
        )

        # Search with the same embedding → should find it
        results = qdrant_client.search(
            collection_name=TEST_COLLECTION,
            query_vector=embedding,
            limit=5,
            score_threshold=0.90
        )
        assert len(results) >= 1
        assert results[0].payload["text"] == text

    def test_search_similar_text(self, qdrant_client):
        """Search with paraphrased text should find original."""
        original = "Neural networks are a fundamental component of deep learning systems."
        paraphrase = "Deep learning relies heavily on neural network architectures."

        orig_emb = generate_embedding(original)
        para_emb = generate_embedding(paraphrase)

        from qdrant_client.models import PointStruct
        qdrant_client.upsert(
            collection_name=TEST_COLLECTION,
            points=[PointStruct(
                id=str(uuid.uuid4()),
                vector=orig_emb,
                payload={"document_id": "doc-test-2", "text": original}
            )]
        )

        results = qdrant_client.search(
            collection_name=TEST_COLLECTION,
            query_vector=para_emb,
            limit=5,
            score_threshold=0.5  # Lower threshold for paraphrase
        )
        assert len(results) >= 1
        assert results[0].score > 0.5


class TestDeduplicate:
    """Pure logic — no infrastructure needed."""

    def test_removes_duplicates(self):
        matches = [
            {"submitted_start_char": 0, "source_document_id": "doc-1", "text": "a"},
            {"submitted_start_char": 0, "source_document_id": "doc-1", "text": "b"},
            {"submitted_start_char": 100, "source_document_id": "doc-2", "text": "c"},
        ]
        result = deduplicate(matches)
        assert len(result) == 2

    def test_keeps_unique_entries(self):
        matches = [
            {"submitted_start_char": 0, "source_document_id": "doc-1"},
            {"submitted_start_char": 100, "source_document_id": "doc-2"},
            {"submitted_start_char": 200, "source_document_id": "doc-3"},
        ]
        result = deduplicate(matches)
        assert len(result) == 3
