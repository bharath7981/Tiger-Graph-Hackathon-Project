"""Vector store management and indexing using ChromaDB."""

import os
from typing import List, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.models.document import ChunkRecord
from backend.app.services.embedding_service import embedding_service


class ChromaVectorStore:
    """Manages local persistent vector indexing and retrieval via ChromaDB."""

    def __init__(
        self,
        persist_dir: Optional[str] = None,
        collection_name: Optional[str] = None,
    ):
        self.persist_dir = persist_dir or settings.CHROMA_PERSIST_DIR
        self.collection_name = collection_name or settings.CHROMA_COLLECTION_NAME
        os.makedirs(self.persist_dir, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def count(self) -> int:
        """Returns the number of indexed chunks."""
        return self.collection.count()

    def index_chunks(
        self,
        chunks: List[ChunkRecord],
        batch_size: int = 128,
    ) -> int:
        """Indexes a list of ChunkRecords into the Chroma collection in batches.
        
        Args:
            chunks: List of ChunkRecord objects.
            batch_size: Number of chunks per embedding and indexing batch.
            
        Returns:
            Total number of chunks successfully indexed.
        """
        if not chunks:
            logger.warning("No chunks provided for vector store indexing.")
            return 0

        total_chunks = len(chunks)
        indexed_count = 0
        logger.info(f"Indexing {total_chunks} chunks into ChromaDB collection '{self.collection_name}'...")

        for i in range(0, total_chunks, batch_size):
            batch = chunks[i : i + batch_size]
            ids = [c.chunk_id for c in batch]
            texts = [c.text for c in batch]
            metadatas = [c.metadata for c in batch]

            try:
                # Compute dense embeddings via embedding_service
                embeddings = embedding_service.embed_documents(texts)
                # Upsert into ChromaDB
                self.collection.upsert(
                    ids=ids,
                    documents=texts,
                    metadatas=metadatas,
                    embeddings=embeddings,
                )
                indexed_count += len(batch)
                if indexed_count % 512 == 0 or indexed_count == total_chunks:
                    logger.info(f"Indexed {indexed_count}/{total_chunks} chunks ({indexed_count/total_chunks*100:.1f}%)")
            except Exception as e:
                logger.error(f"Error indexing batch {i} to {i + len(batch)}: {e}")
                raise e

        logger.info(f"Vector store indexing completed. Collection total: {self.collection.count()} chunks.")
        return indexed_count

    def similarity_search(
        self,
        query: str,
        top_k: int = 5,
        filter_metadata: Optional[dict] = None,
    ) -> List[dict]:
        """Performs cosine similarity search for a query string."""
        query_embedding = embedding_service.embed_query(query)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filter_metadata if filter_metadata else None,
            include=["documents", "metadatas", "distances"],
        )

        formatted_results = []
        if results and results.get("ids") and results["ids"][0]:
            ids = results["ids"][0]
            docs = results["documents"][0]
            metas = results["metadatas"][0]
            distances = results["distances"][0]

            for chunk_id, doc, meta, dist in zip(ids, docs, metas, distances):
                # Cosine distance to similarity score
                similarity = 1.0 - dist if dist is not None else 0.0
                formatted_results.append({
                    "chunk_id": chunk_id,
                    "text": doc,
                    "metadata": meta,
                    "score": round(similarity, 4),
                })

        return formatted_results


# Default vector store singleton
vector_store = ChromaVectorStore()
