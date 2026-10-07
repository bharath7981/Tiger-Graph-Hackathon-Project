"""Document chunking module using RecursiveCharacterTextSplitter."""

from typing import List, Optional
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    from langchain.text_splitter import RecursiveCharacterTextSplitter

from backend.app.models.document import DocumentRecord, ChunkRecord
from backend.app.core.logging import logger


class DocumentChunker:
    """Splits documents into overlapping chunks with preserved document context."""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 150,
        separators: Optional[List[str]] = None,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", " ", ""]
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=self.separators,
        )

    def chunk_document(self, doc: DocumentRecord) -> List[ChunkRecord]:
        """Splits a single DocumentRecord into ChunkRecords."""
        if not doc.content.strip():
            return []

        raw_chunks = self.splitter.split_text(doc.content)
        chunks: List[ChunkRecord] = []
        total_chunks = len(raw_chunks)

        for idx, text in enumerate(raw_chunks):
            chunk_id = f"{doc.document_id}_c{idx}"
            # Prepend contextual title header to empower vector similarity search
            chunk_text = f"Document: {doc.title}\n\n{text}"

            metadata = {
                "chunk_id": chunk_id,
                "document_id": doc.document_id,
                "title": doc.title,
                "source": doc.source,
                "chunk_index": idx,
                "total_chunks": total_chunks,
                "char_length": len(chunk_text),
                "wikidata_qid": doc.metadata.get("wikidata_qid", ""),
            }

            chunks.append(
                ChunkRecord(
                    chunk_id=chunk_id,
                    document_id=doc.document_id,
                    text=chunk_text,
                    metadata=metadata,
                )
            )

        return chunks

    def chunk_documents(self, documents: List[DocumentRecord]) -> List[ChunkRecord]:
        """Chunks a batch of DocumentRecords."""
        all_chunks: List[ChunkRecord] = []
        for doc in documents:
            all_chunks.extend(self.chunk_document(doc))
        logger.info(f"Chunked {len(documents)} documents into {len(all_chunks)} chunks (avg {len(all_chunks)/max(1, len(documents)):.1f} chunks/doc)")
        return all_chunks
