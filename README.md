# GraphMind — Adaptive Agentic GraphRAG

> **Benchmarking RAG vs. GraphRAG vs. Agentic GraphRAG on Complex Knowledge Tasks**

---

## 🎯 Core Research Question

> **"When does agentic reasoning provide enough accuracy and reasoning benefit to justify its additional token and latency cost?"**

GraphMind compares three distinct retrieval paradigms across 2,951 documents and 150 benchmark questions spanning single-hop lookups, multi-hop relationship traversals, temporal dependencies, superlatives, and global aggregations.

---

## 🏗️ Architecture

```text
                    ┌─────────────────────────┐
                    │  React + Vite Frontend  │
                    │  Investigation Console  │
                    └───────────┬─────────────┘
                                │ HTTP / REST
                                ▼
                    ┌─────────────────────────┐
                    │    FastAPI Gateway      │
                    │      Port: 8000         │
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
   (Dense Top-k)         (Deterministic Path)       (Adaptive Loop)
```

---

## 🚀 Quick Start

### 1. Backend Setup
```bash
# Verify Python 3.11+
python --version

# Copy environment variables
cp .env.example .env

# Run FastAPI backend
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Verify Health
```bash
curl http://localhost:8000/health
# Response: {"status": "ok", "service": "graphmind"}

curl http://localhost:8000/api/v1/system/info
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

---

## 🧪 Benchmark Questions Taxonomy

| Question Type | Share | Primary Retrieval Challenge |
| :--- | :--- | :--- |
| **Lookup** | 19% | Direct single-chunk fact extraction |
| **Multi-Hop** | 28% | Traversal across disparate entities (Venue + Date -> Event -> Medalist) |
| **Temporal** | 22% | Relative chronological precedence (Olympics immediately before 2016) |
| **Aggregation** | 21% | Global entity counting across corpus |
| **Superlative** | 10% | Global extremum selection across a discipline |

---

## 🏆 Hackathon Deliverables & Verification

- **47 / 47 Passing Tests**: Run `python -m pytest backend/tests`
- **Hidden Set Predictions**: Persisted at `evaluation/results/submission_hidden_predictions.jsonl` (50 / 50 questions evaluated)
- **Submission Writeup**: Comprehensive Round 1 & Round 2 report at [`docs/HACKATHON_SUBMISSION_WRITEUP.md`](docs/HACKATHON_SUBMISSION_WRITEUP.md)
- **Video Demo Script**: 3.5-minute walkthrough script at [`docs/DEMO_VIDEO_SCRIPT.md`](docs/DEMO_VIDEO_SCRIPT.md)
- **Executive Web UI**: 6 interactive exploration views in modern light theme at `http://localhost:3000` (Investigation Console, Benchmark Lab, Conflict Lab, Agent Traces, Knowledge Graph, System Overview)

---

## 📄 License
MIT License.
