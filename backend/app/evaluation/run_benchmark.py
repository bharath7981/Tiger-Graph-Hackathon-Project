"""CLI runner for running full comparative benchmark and generating value analysis."""

import argparse
import sys
from pathlib import Path

# Fix Windows console UTF-8 encoding
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from backend.app.core.logging import logger
from backend.app.evaluation.benchmark import benchmark_engine
from backend.app.evaluation.value_analysis import generate_agentic_value_analysis


def main():
    parser = argparse.ArgumentParser(description="Run GraphMind Comparative Benchmark Engine")
    parser.add_argument("--limit", type=int, default=5, help="Number of questions to evaluate")
    parser.add_argument("--pipelines", nargs="+", default=["rag", "graphrag", "agentic"], help="Pipelines to benchmark")
    parser.add_argument("--generate-report", action="store_true", default=True, help="Generate AGENTIC_VALUE_ANALYSIS.md")

    args = parser.parse_args()

    print("\n" + "=" * 80)
    print(f" GRAPHMIND TRIPLE BENCHMARK (RAG vs GraphRAG vs Agentic GraphRAG)")
    print(f" Limit: {args.limit} questions | Pipelines: {args.pipelines}")
    print("=" * 80 + "\n")

    summary = benchmark_engine.run_benchmark(
        limit=args.limit,
        pipelines=args.pipelines,
    )

    print("\n" + "=" * 80)
    print(" BENCHMARK MACRO SUMMARY")
    print("=" * 80)
    for p, stats in summary.get("overall_metrics", {}).items():
        print(f"[{p.upper()}]")
        print(f"  Gold Doc Hit Rate : {stats.get('gold_hit_rate', 0)*100:.1f}%")
        print(f"  Citation Precision: {stats.get('citation_precision', 0)*100:.1f}%")
        print(f"  Avg Latency       : {stats.get('avg_latency_ms', 0):.2f} ms")
        print(f"  Avg Tokens        : {stats.get('avg_tokens', 0):.1f}")
        print("-" * 40)

    if args.generate_report:
        report_res = generate_agentic_value_analysis()
        print(f"\n[REPORT] Generated Agentic Value Analysis at: {report_res.get('file')}")

    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
