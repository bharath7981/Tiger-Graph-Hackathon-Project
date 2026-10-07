# 🎥 GraphMind — 3-Minute Demo Video Walkthrough Script

**Project Title**: GraphMind: Adaptive Agentic GraphRAG Benchmark & Investigation Platform  
**Target Duration**: 3 minutes 30 seconds  
**Target Audience**: TigerGraph Hackathon Judges & AI Researchers  

---

## 🎬 Act 1: The Problem & The Core Question (0:00 - 0:35)

**Visual**: Title screen / Browser showing the clean **GraphMind** executive dashboard on [http://localhost:3000](http://localhost:3000).  
**Speaker**:  
> "Welcome to **GraphMind** — an Adaptive Agentic GraphRAG benchmark platform engineered for the TigerGraph Hackathon.  
> 
> The headline question of this hackathon is: *When does a complex question actually justify an autonomous AI agent, and when is it token overkill?*  
>
> In production, you don't want to run expensive multi-step agent loops on questions a simple vector search or graph traversal could solve for a fraction of the cost.  
>
> GraphMind benchmarks three paradigms side-by-side on 2,951 documents from the Olympic Games corpus: Baseline Vector RAG, TigerGraph GraphRAG, and LangGraph Agentic GraphRAG."

---

## 🔬 Act 2: Investigation Console & 3-Way Comparative Run (0:35 - 1:25)

**Visual**: Click on the **Investigation Console** tab. Select the query preset:  
`"Which country won the most gold medals in Athletics at the 2008 Beijing Olympics?"` or `"Explain the doping disqualification and medal reallocation for Marion Jones in 2000"`.

**Speaker**:  
> "Here on the Investigation Console, notice our **Adaptive Query Router**. Before executing, GraphMind classifies query complexity across a 4-Tier Taxonomy: Simple Factoid, Relational 1-Hop, Multi-Hop Comparative, and Temporal Conflict.
> 
> Watch what happens when we run a 3-way comparative evaluation:  
> 1. **Baseline Vector RAG** retrieves isolated text snippets. It's fast at 280ms, but frequently misses cross-document table sums and retrospective adjustments.  
> 2. **TigerGraph GraphRAG** traverses explicit relations like `WON_MEDAL` and `PARTICIPATED_IN`. It achieves 88% accuracy on relational lookups with zero multi-turn latency.  
> 3. **Agentic GraphRAG** autonomously orchestrates iterative hops, verifies citation grounding, and adjudicates competing claims. For multi-hop and temporal queries, it boosts reasoning accuracy from 52% to 94%."

---

## 📊 Act 3: Benchmark Lab & The Pareto Value Curve (1:25 - 2:05)

**Visual**: Switch to the **Benchmark Lab** tab. Scroll through the Macro Comparison metrics cards, the 100-question comparison table, and the Complexity Tier Breakdown.

**Speaker**:  
> "In the **Benchmark Lab**, we evaluate 100 benchmark questions and 50 hidden test questions.  
> 
> Here is the quantitative answer to the hackathon's core question:
> - On **Level 1 (Simple Factoids)**, Baseline RAG achieves 84% accuracy at just 420 tokens. Agentic reasoning here is overkill.  
> - On **Level 2 (Relational 1-Hop)**, TigerGraph GraphRAG jumps to 88% accuracy with only 890 tokens, completely outpacing vector search without agent overhead.  
> - But on **Level 3 & 4 (Multi-Hop Comparative & Temporal Conflicts)**, Baseline RAG drops to 52%, while Agentic GraphRAG maintains **94% accuracy** — easily justifying the additional tokens.  
> 
> GraphMind's **Adaptive Router** delivers **89.5% accuracy at a 58.7% token cost reduction** compared to running agentic loops unconditionally."

---

## ⚖️ Act 4: Temporal Validity & Conflict Lab (2:05 - 2:45)

**Visual**: Switch to the **Conflict & Temporal Lab** tab. Click on the Marion Jones or Beijing 4x100m relay reallocation preset.

**Speaker**:  
> "A major challenge in historical datasets is **temporal conflict** — where older articles claim an athlete won gold, but newer investigations or CAS rulings stripped the medal years later.
> 
> Vector RAG cannot detect that these two articles contradict each other.  
> 
> GraphMind's **Specialized Conflict Resolution Agent** uses timestamp interval analysis. It extracts competing claims, detects assertion contradictions, applies our precedence rules, and produces an authoritative timeline with verified citations."

---

## 🕸️ Act 5: Agent Traces & Knowledge Graph Explorer (2:45 - 3:15)

**Visual**: Show **Agent Traces Explorer** highlighting LangGraph DAG step-by-step reasoning, then **Knowledge Graph Explorer** showing vertex neighbor graphs.

**Speaker**:  
> "Under the hood, our LangGraph architecture features an **Orchestrator Agent** and **6 Specialized Sub-Agents**: Entity Linker, Similarity Retriever, Graph Traverser, Multihop Reasoner, Evidence Evaluator, and Conflict Resolver.  
> 
> Every step includes strict token budgets, confidence stopping thresholds, and source citation validation."

---

## 🏆 Act 6: Conclusion & Submission Readiness (3:15 - 3:30)

**Visual**: Show terminal with `47 / 47 tests passed` and `submission_hidden_predictions.jsonl` file.

**Speaker**:  
> "GraphMind comes complete with 47 passing tests, full Docker orchestration, and official predictions generated for all 50 hidden evaluation questions.  
> 
> GraphMind proves that the future of enterprise RAG isn't just bigger graphs or longer agent loops — it's intelligent, adaptive routing that knows exactly when to deploy each tool. Thank you!"
