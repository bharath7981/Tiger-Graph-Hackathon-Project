"""Graph builder for ingesting corpus documents into TigerGraph and local graph store."""

import time
from typing import Any, Dict, List, Optional
from backend.app.core.logging import logger
from backend.app.models.document import DocumentRecord
from backend.app.graph.entity_extractor import entity_extractor
from backend.app.graph.client import graph_client, local_graph_store
from backend.app.ingestion.loader import load_documents_from_jsonl


def build_graph_from_documents(
    documents: List[DocumentRecord],
) -> Dict[str, Any]:
    """Extracts entities and relationships from documents and builds the graph."""
    start_time = time.time()
    logger.info(f"Extracting graph elements from {len(documents)} documents...")

    elements = entity_extractor.extract_from_documents(documents)

    total_vertices = 0
    total_edges = 0

    # 1. Upsert Vertices
    for v_type, v_list in elements.vertices.items():
        if v_list:
            count = graph_client.upsert_vertices(v_type, v_list)
            total_vertices += count
            logger.info(f"Upserted {count} vertices of type '{v_type}'.")

    # 2. Upsert Edges
    for e_type, e_list in elements.edges.items():
        if e_list:
            count = graph_client.upsert_edges(e_type, e_list)
            total_edges += count
            logger.info(f"Upserted {count} edges of type '{e_type}'.")

    # Persist local mirror
    local_graph_store._save_to_disk()

    elapsed = round(time.time() - start_time, 2)
    stats = {
        "status": "completed",
        "documents_processed": len(documents),
        "total_vertices": total_vertices,
        "total_edges": total_edges,
        "vertex_breakdown": {k: len(v) for k, v in elements.vertices.items()},
        "edge_breakdown": {k: len(v) for k, v in elements.edges.items()},
        "duration_seconds": elapsed,
    }
    logger.info(f"Graph construction completed in {elapsed}s: {stats}")
    return stats


def run_graph_build(corpus_path: str = "corpus/corpus.jsonl", limit: Optional[int] = None):
    """CLI / programmatic helper to run graph construction from corpus."""
    docs = load_documents_from_jsonl(corpus_path, limit=limit)
    return build_graph_from_documents(docs)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Build Knowledge Graph from Corpus")
    parser.add_argument("--corpus-path", default="corpus/corpus.jsonl", help="Path to corpus JSONL")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of documents")
    args = parser.parse_args()

    run_graph_build(corpus_path=args.corpus_path, limit=args.limit)
