"""Evaluation metrics for RAG, GraphRAG, and Agentic GraphRAG pipelines."""

import re
from typing import Any, Dict, List, Optional, Set


def normalize_text(s: str) -> str:
    """Normalizes string for comparison by lowercasing and stripping punctuation and articles."""
    def remove_articles(text: str) -> str:
        return re.sub(r"\b(a|an|the)\b", " ", text)

    def white_space_fix(text: str) -> str:
        return " ".join(text.split())

    def remove_punc(text: str) -> str:
        return re.sub(r"[^\w\s]", "", text)

    return white_space_fix(remove_articles(remove_punc(s.lower())))


def compute_exact_match(prediction: str, ground_truth: Optional[List[str]]) -> float:
    """Computes exact match binary score between prediction and any ground truth variant."""
    if not ground_truth:
        return 0.0
    norm_pred = normalize_text(prediction)
    for gt in ground_truth:
        norm_gt = normalize_text(gt)
        if norm_gt in norm_pred or norm_pred == norm_gt:
            return 1.0
    return 0.0


def compute_token_f1(prediction: str, ground_truth: Optional[List[str]]) -> float:
    """Computes token-level precision, recall, and F1 score against ground truth."""
    if not ground_truth:
        return 0.0

    pred_tokens = normalize_text(prediction).split()
    if not pred_tokens:
        return 0.0

    f1_scores = []
    for gt in ground_truth:
        gt_tokens = normalize_text(gt).split()
        if not gt_tokens:
            continue

        common = set(pred_tokens) & set(gt_tokens)
        if not common:
            f1_scores.append(0.0)
            continue

        precision = len(common) / len(pred_tokens)
        recall = len(common) / len(gt_tokens)
        f1 = (2 * precision * recall) / (precision + recall)
        f1_scores.append(f1)

    return max(f1_scores, default=0.0)


def compute_citation_metrics(
    predicted_citations: List[str],
    gold_document_ids: List[str],
) -> Dict[str, float]:
    """Calculates Hit Rate, Precision, Recall, and F1 for document citations."""
    gold_set = set(gold_document_ids)
    pred_set = set(predicted_citations)

    if not gold_set:
        return {
            "hit_rate": 1.0 if not pred_set else 0.0,
            "precision": 1.0 if not pred_set else 0.0,
            "recall": 1.0,
            "f1": 1.0 if not pred_set else 0.0,
        }

    matched = pred_set & gold_set
    hit_rate = 1.0 if len(matched) > 0 else 0.0
    precision = len(matched) / len(pred_set) if pred_set else 0.0
    recall = len(matched) / len(gold_set) if gold_set else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "hit_rate": round(hit_rate, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "matched_count": len(matched),
        "gold_count": len(gold_set),
    }


def evaluate_prediction(
    prediction: str,
    citations: List[str],
    ground_truth: Optional[List[str]],
    gold_document_ids: List[str],
    latency_ms: float,
    tokens: int,
) -> Dict[str, Any]:
    """Evaluates a single prediction across accuracy, citation quality, and resource usage."""
    em = compute_exact_match(prediction, ground_truth)
    f1 = compute_token_f1(prediction, ground_truth)
    cite_metrics = compute_citation_metrics(citations, gold_document_ids)

    return {
        "exact_match": em,
        "token_f1": round(f1, 4),
        "citation_hit": cite_metrics["hit_rate"] == 1.0,
        "citation_precision": cite_metrics["precision"],
        "citation_recall": cite_metrics["recall"],
        "citation_f1": cite_metrics["f1"],
        "latency_ms": round(latency_ms, 2),
        "tokens": tokens,
    }
