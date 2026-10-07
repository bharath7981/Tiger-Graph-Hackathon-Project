# Project Plan: GraphMind — Adaptive Agentic GraphRAG

## Executive Summary

**GraphMind** is a production-grade benchmark and investigation platform comparing three distinct question-answering architectures on an Olympic Games knowledge corpus:
1. **Baseline Vector RAG** (ChromaDB + Dense Retrieval)
2. **GraphRAG** (TigerGraph Schema + Structured Graph Traversals)
3. **Agentic GraphRAG** (LangGraph Orchestration + Autonomous Specialized Agents)

The core deliverable is an empirical answer to the question:
> **"When does agentic reasoning provide enough accuracy and reasoning benefit to justify its additional token and latency cost?"**

---

## Architecture Overview

```text
                    ┌─────────────────────────┐
                    │  React + Vite Frontend  │
                    │  Investigation Console  │
                    └───────────┬─────────────┘
                                │ HTTP / WebSocket
                                ▼
                    ┌─────────────────────────┐
                    │    FastAPI Gateway      │
                    │  /api/v1/{rag,graph,...}│
                    └───────────┬─────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
   ┌─────────┐            ┌───────────┐         ┌───────────────┐
   │ Baseline│            │ GraphRAG  │         │  Agentic RAG  │
   │   RAG   │            │ Pipeline  │         │ Orchestrator  │
   └────┬────┘            └─────┬─────┘         └───────┬───────┘
        │                       │                       │
        ▼                       ▼                       ▼
    ChromaDB                TigerGraph              LangGraph
   (Dense Top-k)         (1-2 Hop Queries)              │
                                                ┌───────┴───────┐
                                                │               │
                                                ▼               ▼
                                            Retrieval       Reasoning
                                             Agents          Agents
                                                │               │
                                                └───────┬───────┘
                                                        │
                                                        ▼
                                                Evidence Evaluator
                                                        │
                                                        ▼
                                                Answer Verification
                                                        │
                                                        ▼
                                                Benchmark Engine
                                                        │
                                                        ▼
                                                Metrics Dashboard
```

---

## Phased Implementation Plan

### Phase 1: Infrastructure & Core Skeleton
- **Goals**: Establish a robust backend and frontend architecture without implementing retrieval pipelines yet.
- **Components**:
  - Python FastAPI backend with Pydantic v2 schemas and modular package layout.
  - React + Vite + Tailwind CSS frontend shell with navigation layout.
  - Configuration management via Pydantic Settings supporting environment variables (`.env`).
  - Abstraction layers for LLM provider, vector database, and TigerGraph connection.
  - System health (`GET /health`) and info (`GET /api/v1/system/info`) endpoints.
  - Automated smoke test suite.
- **Acceptance Criteria**:
  - Backend starts cleanly; `/health` returns `{"status": "ok", "service": "graphmind"}`.
  - System info endpoint reports configured services without exposing secrets.
  - Initial unit tests pass.

### Phase 2: Ingestion Pipeline (Documents & Questions)
- **Goals**: Ingest the 2,951 documents from `corpus/corpus.jsonl` and 150 evaluation questions.
- **Components**:
  - `DocumentRecord` and `QuestionRecord` normalization models.
  - Robust document loader supporting large `.jsonl` files and infobox parsing.
  - Recursive text chunker preserving section and infobox context.
  - Embeddings service abstraction (local HuggingFace / MiniLM or API-based).
  - Local persistent ChromaDB vector store builder.
  - CLI runner: `python -m app.ingestion.run --documents --questions --all`.
  - Ingestion statistics generator outputting `evaluation/results/ingestion_report.json`.
- **Acceptance Criteria**:
  - All 2,951 documents chunked and indexed into ChromaDB.
  - All 100 public questions and 50 hidden questions loaded into normalized structures.
  - Ingestion report generated with verified zero data corruption.

### Phase 3: Baseline RAG Pipeline
- **Goals**: Implement standard dense retrieval-augmented generation as a clean baseline.
- **Components**:
  - `backend/app/pipelines/rag.py` executing: `Question -> Embedding -> Chroma top-k -> Context Assembly -> LLM -> Grounded Answer`.
  - Structured output `RAGResult` capturing answer, retrieved chunks, citations, latency, and token metrics.
  - Prompt engineering enforcing citation groundedness and strict refusal on insufficient evidence.
  - Endpoints: `POST /api/v1/rag/query` and `POST /api/v1/rag/evaluate/{question_id}`.
  - CLI runner: `python -m app.pipelines.run_rag --question-id <id>`.
- **Acceptance Criteria**:
  - Baseline RAG answers public questions with measurable token usage and latency.
  - Results stored in `evaluation/results/rag/`.

### Phase 4: GraphRAG Pipeline (TigerGraph)
- **Goals**: Build deterministic graph-based retrieval using TigerGraph.
- **Components**:
  - Graph schema representing `Event`, `Games`, `Sport`, `Venue`, `Athlete`, `Country`, and `Document`.
  - Idempotent entity and relationship extraction and loading script.
  - TigerGraph client abstraction with connection pooling and GSQL query wrappers.
  - Deterministic GraphRAG pipeline: `Question -> Entity Linking -> Graph Query -> Supporting Evidence -> LLM -> Grounded Answer`.
  - Endpoints: `POST /api/v1/graphrag/query`, `GET /api/v1/graph/entities/{id}`, `GET /api/v1/graph/neighbors/{id}`.
  - CLI runner: `python -m app.pipelines.run_graphrag --question-id <id>`.
- **Acceptance Criteria**:
  - Graph traversals resolve multi-hop links (e.g. Venue + Date -> Event -> Medalist).
  - GraphRAG returns structured `GraphRAGResult` with explicit graph paths and citations.

### Phase 5: Agentic GraphRAG (LangGraph Orchestration)
- **Phase 5A: Dynamic Agent Harness**:
  - LangGraph state machine with dynamic loop: `Orchestrator -> Tool Execution -> Evidence Check -> Decision (Loop or Final Answer)`.
  - Explicit tool registry: `entity_link`, `vector_search`, `graph_traversal`, `document_retrieval`, `evidence_evaluation`, `conflict_detection`, `final_answer`.
  - Guardrails: Maximum iteration ceiling, token budget cap, no arbitrary code execution.
- **Phase 5B: Specialized Investigation Agents**:
  - Decoupled agents for Entity Linking, Graph Traversal, Similarity Search, Document Retrieval, Evidence Evaluation, and Multi-Hop Reasoning.
  - Orchestrator dynamically activates only the necessary agents based on accumulated state.
- **Phase 5C: Evidence Intelligence & Answer Verification**:
  - Evidence scoring, coverage check, contradiction detection, and citation validation before final emission.
- **Acceptance Criteria**:
  - Simple questions trigger concise 1-2 step paths; complex questions trigger multi-hop iterative investigations.
  - Complete `TraceStep` records saved with step-by-step reasoning, tokens, and latencies.

### Phase 6: Benchmark Engine & Agentic Value Analysis
- **Phase 6A: Automated Benchmark Engine**:
  - Evaluation harness executing RAG, GraphRAG, and Agentic GraphRAG against evaluation questions.
  - Multi-dimensional scoring: Exact Match / Accuracy, Completeness, Groundedness, Citation Coverage, Latency, and Token Consumption.
  - Outputs: `evaluation/results/benchmark_summary.json` and CSV exports.
  - CLI runner: `python -m app.evaluation.benchmark --pipeline all --limit 5`.
- **Phase 6B: "When Does Agentic Help?" Analysis**:
  - Question complexity classifier (Level 1 Simple, Level 2 Relational, Level 3 Multi-hop, Level 4 Complex/Aggregation).
  - Metrics computation: `Agentic Gain`, `Additional Token Cost`, `Additional Latency`.
  - Data-backed recommendation matrix demonstrating the exact complexity inflection point where Agentic GraphRAG justifies its cost.
  - Generation of `docs/AGENTIC_VALUE_ANALYSIS.md`.

### Phase 7: React Investigation Dashboard
- **Goals**: Create an interactive AI investigation console and benchmark laboratory.
- **Pages**:
  1. **Investigation Console**: Interactive prompt execution with real-time trace visualizer, pipeline comparison toggle, and evidence inspector.
  2. **Benchmark Lab**: Aggregate comparison charts (Accuracy, Tokens, Latency, Complexity Breakdown).
  3. **Agent Trace Explorer**: Step-by-step DAG visualization of orchestrator decisions and tool invocations.
  4. **Knowledge Graph Explorer**: Interactive node/edge relationship graph with document backlinks.
  5. **Question Evaluation Explorer**: Question-by-question comparative breakdown with ground-truth verification.
  6. **System Status**: Real-time service health, configuration, and index statistics.
- **Acceptance Criteria**:
  - Dark mode aesthetic tailored for research consoles; 100% powered by real backend API data.

### Phase 8: Comprehensive MVP Validation
- Complete end-to-end acceptance run validating all 24 criteria outlined in the MVP specification.
- Generation of `docs/MVP_STATUS.md`.

### Phase 9: Advanced Temporal, Conflicting & Uncertain Knowledge (Round 2)
- Temporal validity model (`valid_from`, `valid_to`, `source_date`, `supersedes`).
- Conflict detection and source authority resolution agent.
- Transparent reporting of competing claims and residual uncertainty.

---

## Immediate Next Step

Proceed to **Prompt 1: Project Skeleton Creation**, establishing the unified backend and frontend directory structure, core dependencies, configuration, and `/health` endpoint.
