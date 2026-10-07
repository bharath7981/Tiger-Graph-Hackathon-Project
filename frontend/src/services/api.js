/**
 * GraphMind API client services connecting to all backend endpoints.
 */

const API_BASE = '/api/v1';

export async function checkHealth() {
  const res = await fetch('/health');
  if (!res.ok) throw new Error(`Health check failed: ${res.statusText}`);
  return res.json();
}

export async function getSystemInfo() {
  const res = await fetch(`${API_BASE}/system/info`);
  if (!res.ok) throw new Error(`System info failed: ${res.statusText}`);
  return res.json();
}

// 1. Baseline RAG
export async function queryRAG(question, questionId = null) {
  const res = await fetch(`${API_BASE}/rag/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, question_id: questionId }),
  });
  if (!res.ok) throw new Error(`RAG query failed: ${res.statusText}`);
  return res.json();
}

// 2. GraphRAG
export async function queryGraphRAG(question, questionId = null) {
  const res = await fetch(`${API_BASE}/graphrag/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, question_id: questionId }),
  });
  if (!res.ok) throw new Error(`GraphRAG query failed: ${res.statusText}`);
  return res.json();
}

// 3. Agentic GraphRAG
export async function queryAgentic(question, questionId = null, maxIterations = 6, tokenBudget = 8000) {
  const res = await fetch(`${API_BASE}/agentic/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      question,
      question_id: questionId,
      max_iterations: maxIterations,
      token_budget: tokenBudget,
    }),
  });
  if (!res.ok) throw new Error(`Agentic investigation failed: ${res.statusText}`);
  return res.json();
}

// 4. Benchmark Suite
export async function getBenchmarkSummary() {
  const res = await fetch(`${API_BASE}/benchmark/summary`);
  if (!res.ok) throw new Error(`Benchmark summary failed: ${res.statusText}`);
  return res.json();
}

export async function getBenchmarkQuestions(limit = 20) {
  const res = await fetch(`${API_BASE}/benchmark/questions?limit=${limit}`);
  if (!res.ok) throw new Error(`Fetch benchmark questions failed: ${res.statusText}`);
  return res.json();
}

export async function getBenchmarkValueAnalysis() {
  const res = await fetch(`${API_BASE}/benchmark/value-analysis`);
  if (!res.ok) throw new Error(`Value analysis failed: ${res.statusText}`);
  return res.json();
}

export async function runBenchmark(limit = 5, pipelines = ['rag', 'graphrag', 'agentic']) {
  const res = await fetch(`${API_BASE}/benchmark/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ limit, pipelines }),
  });
  if (!res.ok) throw new Error(`Benchmark run failed: ${res.statusText}`);
  return res.json();
}

// 5. Knowledge Graph
export async function getGraphEntity(id) {
  const res = await fetch(`${API_BASE}/graph/entities/${encodeURIComponent(id)}`);
  if (!res.ok) throw new Error(`Fetch entity failed: ${res.statusText}`);
  return res.json();
}

export async function getGraphNeighbors(id) {
  const res = await fetch(`${API_BASE}/graph/neighbors/${encodeURIComponent(id)}`);
  if (!res.ok) throw new Error(`Fetch neighbors failed: ${res.statusText}`);
  return res.json();
}

// 6. Temporal Validity & Conflict Resolution
export async function analyzeConflicts(text, entityName = 'Olympic Event') {
  const res = await fetch(`${API_BASE}/conflicts/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, entity_name: entityName }),
  });
  if (!res.ok) throw new Error(`Conflict analysis failed: ${res.statusText}`);
  return res.json();
}

export async function getConflictExamples() {
  const res = await fetch(`${API_BASE}/conflicts/examples`);
  if (!res.ok) throw new Error(`Fetch conflict examples failed: ${res.statusText}`);
  return res.json();
}

// 7. Adaptive Router & Pareto-Optimal Dispatcher
export async function classifyQuery(question, questionType = 'unknown') {
  const res = await fetch(`${API_BASE}/adaptive/classify`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, question_type: questionType }),
  });
  if (!res.ok) throw new Error(`Query classification failed: ${res.statusText}`);
  return res.json();
}

export async function queryAdaptive(question, questionId = null, overrideParadigm = null) {
  const res = await fetch(`${API_BASE}/adaptive/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      question,
      question_id: questionId,
      override_paradigm: overrideParadigm,
    }),
  });
  if (!res.ok) throw new Error(`Adaptive query failed: ${res.statusText}`);
  return res.json();
}
