"""Document and question loaders for GraphMind ingestion pipeline."""

import json
import os
from typing import Dict, List, Optional
from backend.app.models.document import DocumentRecord
from backend.app.models.question import QuestionRecord
from backend.app.core.logging import logger


def load_documents_from_jsonl(
    file_path: str,
    limit: Optional[int] = None,
) -> List[DocumentRecord]:
    """Loads documents from a JSONL file and normalizes them into DocumentRecords.
    
    Args:
        file_path: Path to the corpus JSONL file.
        limit: Optional maximum number of documents to load.
        
    Returns:
        List of normalized DocumentRecord objects.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Corpus file not found at: {file_path}")

    records: List[DocumentRecord] = []
    logger.info(f"Loading documents from {file_path} (limit={limit})...")

    with open(file_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            if limit and len(records) >= limit:
                break
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                doc_id = data.get("doc_id") or data.get("wikidata_qid") or f"doc_{line_num}"
                title = data.get("title", f"Document {doc_id}")
                source = data.get("url", file_path)
                content = data.get("text", "")

                metadata = {
                    "doc_id": doc_id,
                    "title": title,
                    "url": data.get("url", ""),
                    "wikidata_qid": data.get("wikidata_qid", ""),
                    "wikipedia_pageid": data.get("wikipedia_pageid"),
                    "approx_tokens": data.get("approx_tokens", 0),
                }

                records.append(
                    DocumentRecord(
                        document_id=str(doc_id),
                        source=str(source),
                        title=str(title),
                        content=str(content),
                        metadata=metadata,
                    )
                )
            except Exception as e:
                logger.error(f"Error parsing line {line_num} in {file_path}: {e}")

    logger.info(f"Successfully loaded {len(records)} documents from {file_path}")
    return records


def load_questions_from_jsonl(
    public_path: str,
    hidden_path: Optional[str] = None,
) -> Dict[str, List[QuestionRecord]]:
    """Loads evaluation questions from public and optional hidden JSONL files.
    
    Args:
        public_path: Path to eval_public.jsonl.
        hidden_path: Path to eval_hidden.jsonl.
        
    Returns:
        Dict with keys 'public' and 'hidden' containing QuestionRecords.
    """
    results: Dict[str, List[QuestionRecord]] = {"public": [], "hidden": []}

    # Public questions (with ground-truth and gold_doc_ids)
    if os.path.exists(public_path):
        logger.info(f"Loading public questions from {public_path}...")
        with open(public_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                qid = data.get("qid")
                q_text = data.get("question", "")
                ans = data.get("answer")
                ground_truth = ans if isinstance(ans, list) else ([str(ans)] if ans is not None else None)

                metadata = {
                    "qtype": data.get("qtype", "unknown"),
                    "answer_named_in_question": data.get("answer_named_in_question", False),
                    "guess_baseline": data.get("guess_baseline", 0.0),
                    "gold_doc_ids": data.get("gold_doc_ids", []),
                    "answer_verified": data.get("answer_verified", False),
                    "is_hidden": False,
                }
                results["public"].append(
                    QuestionRecord(
                        question_id=str(qid),
                        question=str(q_text),
                        ground_truth=ground_truth,
                        metadata=metadata,
                    )
                )
        logger.info(f"Loaded {len(results['public'])} public questions.")

    # Hidden questions
    if hidden_path and os.path.exists(hidden_path):
        logger.info(f"Loading hidden questions from {hidden_path}...")
        with open(hidden_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                qid = data.get("qid")
                q_text = data.get("question", "")
                metadata = {
                    "qtype": data.get("qtype", "unknown"),
                    "is_hidden": True,
                }
                results["hidden"].append(
                    QuestionRecord(
                        question_id=str(qid),
                        question=str(q_text),
                        ground_truth=None,
                        metadata=metadata,
                    )
                )
        logger.info(f"Loaded {len(results['hidden'])} hidden questions.")

    return results
