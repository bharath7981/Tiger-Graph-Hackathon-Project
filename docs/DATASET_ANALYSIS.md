# Dataset Analysis: GraphMind — Adaptive Agentic GraphRAG

## 1. Dataset Overview

The dataset is a specialized knowledge base and evaluation benchmark centered heavily on **Olympic Games events and history**, supplemented by contextual entities (notable athletes/persons, related films, officeholders, and tournaments). The benchmark is designed to systematically evaluate retrieval-augmented generation across standard vector RAG, GraphRAG, and Agentic GraphRAG.

| Component | Path | File Format | File Size | Record Count |
| :--- | :--- | :--- | :--- | :--- |
| **Corpus** | `corpus/corpus.jsonl` | JSON Lines (`.jsonl`) | 23,097,758 bytes (~22.0 MB) | 2,951 documents |
| **Public Questions** | `questions/eval_public.jsonl` | JSON Lines (`.jsonl`) | 36,253 bytes (~35.4 KB) | 100 questions |
| **Hidden Questions** | `questions/eval_hidden.jsonl` | JSON Lines (`.jsonl`) | 8,388 bytes (~8.2 KB) | 50 questions |

---

## 2. Corpus Files & Formats

### 2.1 File Characteristics
- **Path**: `corpus/corpus.jsonl`
- **Encoding**: UTF-8
- **Total Documents**: 2,951
- **Total Approximate Tokens**: 5,466,414 tokens (~5.47M tokens)
- **Token Statistics**:
  - Average tokens / document: ~1,852 tokens
  - Minimum tokens: 111 tokens
  - Maximum tokens: 26,874 tokens
- **No binary, PDF, or image files**: The corpus is purely clean text with rich structured infobox sections and markdown tables.

### 2.2 Corpus Document Schema
Every line in `corpus/corpus.jsonl` is a JSON object with 7 attributes:

| Field | Type | Description | Example |
| :--- | :--- | :--- | :--- |
| `doc_id` | `string` | Unique identifier (Wikidata QID format) | `"Q303623"` |
| `title` | `string` | Full title of the Wikipedia article | `"Canoeing at the 2012 Summer Olympics – Men's K-2 1000 metres"` |
| `url` | `string` | Canonical Wikipedia article URL | `"https://en.wikipedia.org/wiki/Canoeing_at_the_2012_Summer_Olympics_%E2%80%93_Men%27s_K-2_1000_metres"` |
| `wikidata_qid` | `string` | Matching Wikidata identifier (identical to `doc_id`) | `"Q303623"` |
| `wikipedia_pageid` | `integer` | Wikipedia internal page ID | `35771859` |
| `approx_tokens` | `integer` | Estimated token count of the document body | `704` |
| `text` | `string` | Structured markdown text containing infoboxes, summaries, tables | `"[Infobox Olympic event]\n  event: Men's canoe sprint K-2 1,000 metres\n  games: 2012 Summer\n  venue: Eton Dorney..."` |

### 2.3 Infobox Types Distribution
The text bodies feature structured key-value infobox headers:
- `Olympic event`: 2,162 documents (73.3% of corpus)
- `film`: 546 documents (18.5% of corpus)
- `officeholder`: 73 documents (2.5%)
- `person`: 65 documents (2.2%)
- `tennis tournament event`: 25 documents (0.8%)
- `company`: 16 documents
- `writer`: 8 documents
- `international football competition`: 8 documents
- `scientist`: 6 documents
- `other / no infobox`: 42 documents

---

## 3. Question Files & Schema

### 3.1 Public Questions (`questions/eval_public.jsonl`)
Contains **100 questions** equipped with full ground-truth answers and golden document identifiers.

#### Public Question Schema:
```json
{
  "qid": "pub-001",
  "question": "According to the provided corpus, how many biathlon events at the 2018 Winter Olympics had more than 73 competitors?",
  "qtype": "aggregation",
  "answer_named_in_question": false,
  "guess_baseline": 0.0,
  "gold_doc_ids": ["Q47091419", "Q47105341", "Q47155365", "Q47155371", ...],
  "answer_verified": true,
  "answer": ["5"]
}
```

| Field | Type | Description |
| :--- | :--- | :--- |
| `qid` | `string` | Unique question ID (e.g., `pub-001` to `pub-100`) |
| `question` | `string` | Natural language question targeting corpus knowledge |
| `qtype` | `string` | Reasoning category (`multi_hop`, `temporal`, `aggregation`, `lookup`, `superlative`) |
| `answer_named_in_question` | `boolean` | Flag indicating if answer entity is literally mentioned in prompt (`false` across dataset) |
| `guess_baseline` | `float` | Random guess baseline accuracy (`0.0`) |
| `gold_doc_ids` | `list[string]` | Exact `doc_id` references containing ground-truth evidence |
| `answer_verified` | `boolean` | Human / algorithmic verification status (`true`) |
| `answer` | `list[string]` | List of canonical ground truth answers (e.g., `["5"]`, `["Chen Ding"]`) |

#### Question Type (`qtype`) Breakdown:
- **`multi_hop`**: 28 questions (e.g., Connecting Venue + Date -> Event -> Medalist)
- **`temporal`**: 22 questions (e.g., Summer Olympics immediately before 2016 -> 2012 London -> Winner)
- **`aggregation`**: 21 questions (e.g., How many biathlon events had > 73 competitors?)
- **`lookup`**: 19 questions (e.g., How many nations competed in Women's RS:X?)
- **`superlative`**: 10 questions (e.g., Which athletics event in 2008 had the highest number of competitors?)

#### Evidence & Answer Verification Statistics:
- **Total gold document references**: 547 references across 100 questions.
- **Corpus match rate**: **100%** (0 missing; all 547 gold doc IDs exist in `corpus/corpus.jsonl`).
- **Gold documents per question**: Average 5.47 (range: 1 doc for simple lookups up to 43 docs for superlatives/aggregations).
- **Answer formats**:
  - `string/name`: 60 questions (entity names, event titles, athlete names)
  - `numeric`: 40 questions (discrete counts or values)

### 3.2 Hidden Questions (`questions/eval_hidden.jsonl`)
Contains **50 questions** intended for blind holdout testing.

#### Hidden Question Schema:
```json
{
  "qid": "eval-001",
  "question": "Who won the gold medal in the event held at Olympic Tennis Centre on 15 to 22 August 2004?",
  "qtype": "multi_hop"
}
```
- Contains only `qid`, `question`, and `qtype`.
- Ground truth (`answer`) and `gold_doc_ids` are deliberately omitted.
- Hidden question type distribution:
  - `aggregation`: 15 questions
  - `multi_hop`: 10 questions
  - `superlative`: 10 questions
  - `temporal`: 8 questions
  - `lookup`: 7 questions

---

## 4. Potential Entity & Relationship Types

### 4.1 Core Entity Types
1. **`Event`**: An Olympic competition instance (e.g., "Men's canoe sprint K-2 1,000 metres", "Men's 5000 metres").
   - *Attributes*: `id`, `name`, `date`, `competitors` (int), `nations` (int), `win_value`, `doc_id`.
2. **`Games`**: The Olympic Games edition (e.g., "2012 Summer", "2010 Winter", "1988 Summer").
   - *Attributes*: `id`, `name`, `year` (int), `season` ("Summer" / "Winter"), `host_city`.
3. **`Sport` / `Discipline`**: Categorization of event (e.g., "Canoeing", "Athletics", "Biathlon", "Judo", "Sailing").
4. **`Venue`**: The stadium, arena, or location hosting the event (e.g., "Eton Dorney", "Richmond Olympic Oval", "Olympic Weightlifting Gymnasium").
5. **`Athlete` / `Person`**: Competitors and medalists (e.g., "Chen Ding", "Naim Süleymanoğlu", "Martina Sáblíková").
6. **`Country` / `NOC`**: National Olympic Committees (e.g., "HUN", "CHN", "GER", "TUR").
7. **`Document` / `Chunk`**: Corpus document or text chunk holding provenance and citations.

### 4.2 Core Relationship Types
1. `(Event)-[:PART_OF_GAMES]->(Games)`
2. `(Event)-[:IN_SPORT]->(Sport)`
3. `(Event)-[:HELD_AT]->(Venue)`
4. `(Athlete)-[:WON_MEDAL {type: "gold"|"silver"|"bronze"}]->(Event)`
5. `(Athlete)-[:REPRESENTS]->(Country)`
6. `(Games)-[:PRECEDED_BY]->(Games)` / `(Games)-[:FOLLOWED_BY]->(Games)` (Temporal sequencing critical for temporal questions)
7. `(Document)-[:DESCRIBES]->(Event)` (Attribution and citation linking)

---

## 5. Recommended Ingestion Strategy

1. **Document Normalization**:
   - Parse each record in `corpus/corpus.jsonl` into a standard `DocumentRecord` dataclass.
   - Retain metadata: `doc_id`, `title`, `url`, `approx_tokens`, `wikipedia_pageid`.
2. **Deterministic Infobox Parsing**:
   - The corpus features structured infobox blocks (`[Infobox ...]`) with clean `key: value` pairs.
   - A deterministic parser extracts entities (`Games`, `Venue`, `Date`, `Competitors`, `Nations`, `Gold/Silver/Bronze winners`) with 100% precision without hallucination.
3. **Text Chunking**:
   - Use `RecursiveCharacterTextSplitter` for document prose sections (chunk size: 800 tokens, overlap: 100 tokens).
   - Preserve infoboxes as intact standalone header chunks attached to each child chunk to guarantee entity context during similarity search.
4. **Vector Store Ingestion**:
   - Store chunks in local persistent ChromaDB collection.
   - Embeddings generated via configurable embedding provider (`sentence-transformers/all-MiniLM-L6-v2` or OpenAI / Gemini embeddings).
5. **TigerGraph Ingestion**:
   - Build an idempotent vertex and edge upsert pipeline mapped from parsed entities and relationships.
   - Ensure every vertex and edge maintains a backlink `doc_id` to the source document for complete attribution.

---

## 6. Strategic Pipeline Comparison Rationale

This dataset is uniquely suited to reveal the trade-offs between RAG, GraphRAG, and Agentic GraphRAG:

| Question Type | Baseline RAG (Vector) | GraphRAG (TigerGraph) | Agentic GraphRAG (LangGraph) |
| :--- | :--- | :--- | :--- |
| **Lookup** (19%) | **High**: Semantic search directly matches key sentence in chunk. | **High**: Point lookup on vertex properties. | **High**, but higher token/latency overhead. |
| **Multi-hop** (28%) | **Low-Medium**: Vector search fails when bridging disjoint entities (e.g. Venue + Date -> Event -> Winner). | **Very High**: Graph traversal connects `(Venue)->(Event)->(Athlete)` deterministically. | **Very High**: Orchestrator dynamically links entities, traces hops, and verifies evidence. |
| **Temporal** (22%) | **Low**: Vector embeddings struggle with relative temporal constraints ("Summer Olympics held immediately before 2016"). | **Medium-High**: Needs temporal sequence links between Games (`2016 Summer` -> `2012 Summer`). | **Very High**: Reasoner identifies chronological predecessor games, queries targeted event, and extracts winner. |
| **Aggregation** (21%) | **Near Zero**: Vector search retrieves top-k (e.g. 5 chunks), missing the remaining 6+ events. Cannot count globally. | **High**: Graph query `COUNT(Event WHERE games=... AND competitors > 73)` traverses all nodes. | **Very High**: Orchestrator verifies completeness, gathers all matching nodes, and outputs verified count. |
| **Superlative** (10%) | **Near Zero**: Cannot compare all 43 events in an Olympic sport to find max competitors via 5 random chunks. | **High**: Graph aggregation query finds max attribute value across sport events. | **Very High**: Agent inspects candidate events, compares competitor figures, and verifies result against evidence. |

---

## 7. Risks and Unknowns

1. **Token Length in Detailed Articles**: Some documents exceed 20,000 tokens (e.g. detailed Olympic game summary pages). Chunks must carry parent document metadata to avoid context dilution.
2. **Infobox Multi-Name Fields**: Some infobox medal fields combine multiple names (e.g., team events: `"Rudolf DombiRoland Kökény"`). The entity extractor must split team names cleanly or reference the markdown result tables in the body text.
3. **Graph Ingestion Scale**: 2,951 documents generate ~30,000 vertices and ~75,000 edges. An efficient batch loading routine is necessary for TigerGraph or local graph fallback.
4. **Latency vs. Accuracy Tradeoff**: Agentic GraphRAG will require 3–5 LLM steps for aggregation/temporal questions. Caching and early stopping criteria are critical to keep benchmarks feasible.
