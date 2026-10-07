"""Tests for document, question, and chunk ingestion."""

import os
import tempfile
import json
import pytest
from backend.app.models.document import DocumentRecord, ChunkRecord
from backend.app.models.question import QuestionRecord
from backend.app.ingestion.loader import load_documents_from_jsonl, load_questions_from_jsonl
from backend.app.ingestion.chunker import DocumentChunker
from backend.app.ingestion.vector_store import ChromaVectorStore


def test_document_record_creation():
    doc = DocumentRecord(
        document_id="Q12345",
        source="https://en.wikipedia.org/wiki/Test",
        title="Test Olympic Event",
        content="[Infobox Olympic event]\nevent: Test 100m\ngames: 2020 Summer",
        metadata={"approx_tokens": 15},
    )
    assert doc.document_id == "Q12345"
    assert doc.title == "Test Olympic Event"
    assert "2020 Summer" in doc.content


def test_question_record_creation():
    q = QuestionRecord(
        question_id="pub-001",
        question="How many events were held?",
        ground_truth=["5"],
        metadata={"qtype": "aggregation"},
    )
    assert q.question_id == "pub-001"
    assert q.ground_truth == ["5"]
    assert q.metadata["qtype"] == "aggregation"


def test_document_chunker():
    chunker = DocumentChunker(chunk_size=100, chunk_overlap=20)
    doc = DocumentRecord(
        document_id="Q1",
        source="test_src",
        title="100 Metres",
        content="Line 1 with some content here.\n\nLine 2 with additional data and words.\n\nLine 3 concludes the test event.",
        metadata={"approx_tokens": 20},
    )
    chunks = chunker.chunk_document(doc)
    assert len(chunks) >= 1
    for c in chunks:
        assert c.document_id == "Q1"
        assert c.chunk_id.startswith("Q1_c")
        assert "Document: 100 Metres" in c.text


def test_load_documents_and_questions_from_actual_dataset():
    docs = load_documents_from_jsonl("corpus/corpus.jsonl", limit=5)
    assert len(docs) == 5
    assert docs[0].document_id.startswith("Q")
    assert len(docs[0].title) > 0

    questions = load_questions_from_jsonl("questions/eval_public.jsonl", "questions/eval_hidden.jsonl")
    assert len(questions["public"]) == 100
    assert len(questions["hidden"]) == 50
    assert questions["public"][0].question_id == "pub-001"
    assert questions["public"][0].ground_truth == ["5"]


def test_chroma_vector_store_in_memory():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
        vs = ChromaVectorStore(persist_dir=tmp_dir, collection_name="test_col")
        test_chunk = ChunkRecord(
            chunk_id="test_c0",
            document_id="Q_TEST",
            text="Document: Swimming at 2016 Olympics\n\nMichael Phelps won multiple gold medals in Rio.",
            metadata={"title": "Swimming at 2016 Olympics", "document_id": "Q_TEST"},
        )
        count = vs.index_chunks([test_chunk])
        assert count == 1
        assert vs.count() == 1

        results = vs.similarity_search("Michael Phelps swimming medals", top_k=1)
        assert len(results) == 1
        assert results[0]["chunk_id"] == "test_c0"
        assert results[0]["score"] > 0.0
