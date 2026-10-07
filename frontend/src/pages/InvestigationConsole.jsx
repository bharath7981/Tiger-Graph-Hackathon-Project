import React, { useState } from 'react';
import { 
  Terminal, 
  Send, 
  Layers, 
  Sparkles, 
  Zap, 
  Clock, 
  Coins, 
  CheckCircle2, 
  AlertCircle, 
  ExternalLink,
  ChevronRight,
  ArrowRight,
  RefreshCw,
  GitFork,
  Database
} from 'lucide-react';
import { queryRAG, queryGraphRAG, queryAgentic, queryAdaptive } from '../services/api';

const PRESET_QUESTIONS = [
  {
    id: 'pub-001',
    label: 'Aggregation (Biathlon Competitors > 73)',
    text: 'According to the provided corpus, how many biathlon events at the 2018 Winter Olympics had more than 73 competitors?',
    type: 'Aggregation',
    expected: 'Exact count query with competitor filter'
  },
  {
    id: 'pub-002',
    label: 'Temporal Precedence (20km walk before 2016)',
    text: 'Who won the gold medal in the men\'s 20 kilometres walk athletics event at the Summer Olympics held immediately before 2016?',
    type: 'Temporal',
    expected: 'Preceding games traversal (2012 Summer -> Chen Ding)'
  },
  {
    id: 'pub-003',
    label: 'Aggregation (Shooting Competitors > 37)',
    text: 'According to the provided corpus, how many shooting events at the 2004 Summer Olympics had more than 37 competitors?',
    type: 'Aggregation',
    expected: 'Aggregation with vector fallback'
  },
  {
    id: 'pub-004',
    label: 'Superlative (Athletics highest competitors 2008)',
    text: 'According to the provided corpus, which athletics event at the 2008 Summer Olympics had the highest number of competitors?',
    type: 'Superlative',
    expected: 'Max competitor query'
  },
  {
    id: 'pub-005',
    label: 'Multi-Hop (Weightlifting 20 Sept 1988)',
    text: 'Who won the gold medal in the event held at Olympic Weightlifting Gymnasium on 20 September 1988?',
    type: 'Multi-Hop',
    expected: 'Venue + Date -> Event -> Medalist'
  }
];

export default function InvestigationConsole() {
  const [question, setQuestion] = useState(PRESET_QUESTIONS[1].text);
  const [activeQuestionId, setActiveQuestionId] = useState(PRESET_QUESTIONS[1].id);
  const [mode, setMode] = useState('adaptive'); // 'adaptive' | 'agentic' | 'compare'
  const [loading, setLoading] = useState(false);
  const [adaptiveResult, setAdaptiveResult] = useState(null);
  const [agenticResult, setAgenticResult] = useState(null);
  const [compareResults, setCompareResults] = useState(null);
  const [error, setError] = useState(null);

  const handleSelectPreset = (p) => {
    setQuestion(p.text);
    setActiveQuestionId(p.id);
  };

  const executeQuery = async () => {
    if (!question.trim()) return;
    setLoading(true);
    setError(null);

    try {
      if (mode === 'adaptive') {
        const res = await queryAdaptive(question, activeQuestionId);
        setAdaptiveResult(res);
      } else if (mode === 'agentic') {
        const res = await queryAgentic(question, activeQuestionId);
        setAgenticResult(res);
      } else {
        // Compare all 3 in parallel
        const [ragRes, graphRes, agentRes] = await Promise.all([
          queryRAG(question, activeQuestionId).catch(err => ({ error: err.message, answer: 'Error in RAG pipeline' })),
          queryGraphRAG(question, activeQuestionId).catch(err => ({ error: err.message, answer: 'Error in GraphRAG pipeline' })),
          queryAgentic(question, activeQuestionId).catch(err => ({ error: err.message, answer: 'Error in Agentic pipeline' })),
        ]);
        setCompareResults({ rag: ragRes, graphrag: graphRes, agentic: agentRes });
        setAgenticResult(agentRes);
      }
    } catch (err) {
      setError(err.message || 'Investigation query failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Controls Bar */}
      <div className="p-6 rounded-2xl bg-white border border-slate-200/90 shadow-sm backdrop-blur-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
          <div>
            <h2 className="text-lg font-bold text-slate-900 flex items-center space-x-2">
              <Terminal className="w-5 h-5 text-blue-600" />
              <span>Olympic Knowledge Investigation</span>
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Empirically compare Baseline RAG, TigerGraph GraphRAG, and LangGraph Agentic Investigation
            </p>
          </div>

          {/* Mode Switcher */}
          <div className="flex items-center p-1 rounded-xl bg-slate-100 border border-slate-200 text-xs self-start md:self-auto gap-1">
            <button
              onClick={() => setMode('adaptive')}
              className={`px-3 py-1.5 rounded-lg font-medium transition-all flex items-center space-x-1.5 ${
                mode === 'adaptive'
                  ? 'bg-gradient-to-r from-amber-500 to-orange-500 text-white shadow-sm shadow-amber-500/20'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Zap className="w-3.5 h-3.5 text-amber-100" />
              <span>Adaptive Auto-Route (Recommended)</span>
            </button>
            <button
              onClick={() => setMode('agentic')}
              className={`px-3 py-1.5 rounded-lg font-medium transition-all flex items-center space-x-1.5 ${
                mode === 'agentic'
                  ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-sm shadow-blue-500/20'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>Agentic Deep Dive</span>
            </button>
            <button
              onClick={() => setMode('compare')}
              className={`px-3 py-1.5 rounded-lg font-medium transition-all flex items-center space-x-1.5 ${
                mode === 'compare'
                  ? 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow-sm shadow-purple-500/20'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Layers className="w-3.5 h-3.5" />
              <span>3-Way Paradigm Comparison</span>
            </button>
          </div>
        </div>

        {/* Input Bar */}
        <div className="relative flex items-center">
          <input
            type="text"
            value={question}
            onChange={(e) => {
              const val = e.target.value;
              setQuestion(val);
              const matched = PRESET_QUESTIONS.find(p => p.text.trim().toLowerCase() === val.trim().toLowerCase());
              setActiveQuestionId(matched ? matched.id : null);
            }}
            onKeyDown={(e) => e.key === 'Enter' && executeQuery()}
            placeholder="Ask an Olympic question (e.g. Which athletics event had highest competitors in 2008?)..."
            className="w-full pl-4 pr-32 py-3 rounded-xl bg-slate-50 border border-slate-300 text-sm text-slate-900 placeholder-slate-400 focus:bg-white focus:outline-none focus:border-blue-600 focus:ring-1 focus:ring-blue-600 transition-all font-mono"
          />
          <button
            onClick={executeQuery}
            disabled={loading}
            className="absolute right-2 px-4 py-2 rounded-lg bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white text-xs font-semibold flex items-center space-x-1.5 shadow-md shadow-blue-500/20 transition-all disabled:opacity-50"
          >
            {loading ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>Investigating...</span>
              </>
            ) : (
              <>
                <span>Execute</span>
                <Send className="w-3.5 h-3.5" />
              </>
            )}
          </button>
        </div>

        {/* Presets Strip */}
        <div className="mt-4 pt-3 border-t border-slate-200">
          <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block mb-2">
            Benchmark Test Cases:
          </span>
          <div className="flex flex-wrap gap-2">
            {PRESET_QUESTIONS.map((p) => (
              <button
                key={p.id}
                onClick={() => handleSelectPreset(p)}
                className={`text-xs px-3 py-1.5 rounded-lg border transition-all flex items-center space-x-1.5 ${
                  activeQuestionId === p.id
                    ? 'bg-blue-50 border-blue-300 text-blue-700 font-medium shadow-xs'
                    : 'bg-slate-100 border-slate-200 text-slate-600 hover:bg-slate-200/70 hover:text-slate-900'
                }`}
              >
                <span className="font-mono text-[10px] text-blue-600 font-semibold">{p.id}</span>
                <span>{p.label}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-800 text-xs flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 text-red-600 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Mode: Adaptive Auto-Route */}
      {mode === 'adaptive' && adaptiveResult && (
        <div className="space-y-5">
          {/* Intelligent Dispatch Decision Banner */}
          <div className="p-5 rounded-2xl bg-gradient-to-r from-amber-50 via-orange-50/50 to-white border border-amber-300 shadow-sm backdrop-blur-xl">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-3 mb-3 border-b border-amber-200/80">
              <div className="flex items-center space-x-3">
                <div className="w-9 h-9 rounded-xl bg-amber-500/15 border border-amber-500/30 flex items-center justify-center">
                  <Zap className="w-5 h-5 text-amber-600" />
                </div>
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="text-xs uppercase tracking-wider font-mono text-amber-700 font-bold">
                      Pareto-Optimal Routing Decision
                    </span>
                    <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded-full bg-white border border-amber-200 text-slate-700 font-semibold">
                      Level {adaptiveResult.complexity_level} &bull; {adaptiveResult.complexity_label}
                    </span>
                  </div>
                  <h3 className="font-bold text-slate-900 text-base mt-0.5">
                    Dispatched to {adaptiveResult.chosen_paradigm === 'graphrag' ? 'TigerGraph GraphRAG' : adaptiveResult.chosen_paradigm === 'agentic' ? 'LangGraph Agentic GraphRAG' : 'Baseline Vector RAG'}
                  </h3>
                </div>
              </div>

              <div className="flex items-center space-x-2 self-start md:self-auto">
                {adaptiveResult.cost_efficiency_multiplier > 1.0 ? (
                  <div className="px-3 py-1.5 rounded-xl bg-emerald-100 border border-emerald-300 text-emerald-800 text-xs font-mono font-bold shadow-xs">
                    ⚡ {adaptiveResult.cost_efficiency_multiplier}x Token Efficiency
                  </div>
                ) : (
                  <div className="px-3 py-1.5 rounded-xl bg-blue-100 border border-blue-300 text-blue-800 text-xs font-mono font-bold">
                    🚀 Full Agentic Reasoning
                  </div>
                )}
              </div>
            </div>

            <p className="text-xs text-slate-800 leading-relaxed font-mono bg-white/90 p-3.5 rounded-xl border border-amber-200 shadow-xs">
              <span className="text-amber-700 font-bold">Routing Rationale:</span> {adaptiveResult.routing_rationale}
            </p>

            {adaptiveResult.is_conflict_suspected && (
              <div className="mt-3 p-2.5 rounded-xl bg-amber-100 border border-amber-300 text-amber-900 text-xs flex items-center space-x-2">
                <AlertCircle className="w-3.5 h-3.5 text-amber-600 flex-shrink-0" />
                <span>Retrospective conflict cues detected (handled by Conflict Resolution Swarm).</span>
              </div>
            )}
          </div>

          {/* Answer Card & Performance Metrics */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-4">
              <div className="p-6 rounded-2xl bg-white border border-slate-200/90 shadow-sm backdrop-blur-xl">
                <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-100">
                  <span className="font-semibold text-slate-900 text-sm flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                    <span>Grounded Answer</span>
                  </span>
                  <span className="text-[11px] font-mono text-slate-500 font-semibold px-2 py-0.5 rounded bg-slate-100 border border-slate-200">
                    {adaptiveResult.chosen_paradigm.toUpperCase()} Pipeline
                  </span>
                </div>

                <div className="text-slate-900 text-sm leading-relaxed p-4 rounded-xl bg-slate-50 border border-slate-200 font-mono">
                  {adaptiveResult.answer}
                </div>

                {/* Citations */}
                {adaptiveResult.citations && adaptiveResult.citations.length > 0 && (
                  <div className="mt-4 pt-3 border-t border-slate-100">
                    <span className="text-[11px] uppercase tracking-wider font-semibold text-slate-500 block mb-2">
                      Verified Citations:
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {adaptiveResult.citations.map((cite, idx) => (
                        <span
                          key={idx}
                          className="px-2.5 py-1 rounded-md bg-blue-50 border border-blue-200 text-blue-700 font-mono text-[11px] flex items-center space-x-1 font-medium hover:bg-blue-100 transition-all"
                        >
                          <span>[{cite}]</span>
                          <ExternalLink className="w-2.5 h-2.5 opacity-70" />
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Performance & Savings Statistics */}
            <div className="space-y-4">
              <div className="p-5 rounded-2xl bg-white border border-slate-200/90 shadow-sm backdrop-blur-xl space-y-4">
                <h4 className="text-xs uppercase font-semibold tracking-wider text-slate-500 border-b border-slate-100 pb-2">
                  Efficiency &amp; Resource Footprint
                </h4>

                <div className="space-y-3">
                  <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                    <span className="text-[11px] text-slate-500 block font-medium">Actual Latency</span>
                    <div className="flex items-baseline justify-between mt-0.5">
                      <span className="text-lg font-bold font-mono text-slate-900">{adaptiveResult.actual_latency_ms} ms</span>
                      {adaptiveResult.latency_saved_ms > 0 && (
                        <span className="text-xs font-mono text-emerald-600 font-semibold">-{adaptiveResult.latency_saved_ms} ms</span>
                      )}
                    </div>
                  </div>

                  <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                    <span className="text-[11px] text-slate-500 block font-medium">Token Consumption</span>
                    <div className="flex items-baseline justify-between mt-0.5">
                      <span className="text-lg font-bold font-mono text-slate-900">{adaptiveResult.actual_tokens}</span>
                      {adaptiveResult.tokens_saved > 0 && (
                        <span className="text-xs font-mono text-emerald-600 font-semibold">Saved {adaptiveResult.tokens_saved} tok</span>
                      )}
                    </div>
                  </div>

                  <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                    <span className="text-[11px] text-slate-500 block font-medium">Reference Multi-Agent Cost</span>
                    <span className="text-xs font-mono text-slate-600 mt-0.5 block">
                      {adaptiveResult.reference_agentic_tokens} tokens &bull; {adaptiveResult.reference_agentic_latency_ms} ms
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Mode 1: Agentic Deep Dive */}
      {mode === 'agentic' && agenticResult && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Answer & Evidence Card (2 cols) */}
          <div className="lg:col-span-2 space-y-5">
            <div className="p-6 rounded-2xl bg-white border border-slate-200/90 shadow-sm backdrop-blur-xl">
              <div className="flex items-center justify-between pb-4 mb-4 border-b border-slate-100">
                <div className="flex items-center space-x-2">
                  <div className="w-8 h-8 rounded-lg bg-blue-50 border border-blue-200 flex items-center justify-center">
                    <Sparkles className="w-4 h-4 text-blue-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-slate-900 text-sm">Synthesized Grounded Answer</h3>
                    <p className="text-[11px] text-slate-500">Grounded in verified multi-hop evidence</p>
                  </div>
                </div>

                <div className="flex items-center space-x-3 text-xs">
                  <div className="px-2.5 py-1 rounded-md bg-emerald-50 border border-emerald-300 text-emerald-800 flex items-center space-x-1 font-medium">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                    <span>Confidence: {(agenticResult.confidence * 100).toFixed(0)}%</span>
                  </div>
                </div>
              </div>

              <div className="text-slate-900 text-sm leading-relaxed p-4 rounded-xl bg-slate-50 border border-slate-200 font-mono">
                {agenticResult.answer}
              </div>

              {/* Citations Box */}
              {agenticResult.citations && agenticResult.citations.length > 0 && (
                <div className="mt-4 pt-3 border-t border-slate-100">
                  <span className="text-[11px] uppercase tracking-wider font-semibold text-slate-500 block mb-2">
                    Cited Sources:
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {agenticResult.citations.map((cite, idx) => (
                      <span
                        key={idx}
                        className="px-2.5 py-0.5 rounded-md bg-blue-50 border border-blue-200 text-blue-700 font-mono text-[11px] flex items-center space-x-1 font-medium"
                      >
                        <span>[{cite}]</span>
                        <ExternalLink className="w-2.5 h-2.5 opacity-70" />
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Step-by-Step Agent Trace Timeline */}
            <div className="p-6 rounded-2xl bg-white border border-slate-200/90 shadow-sm backdrop-blur-xl">
              <h3 className="font-semibold text-slate-900 text-sm flex items-center space-x-2 mb-4">
                <GitFork className="w-4 h-4 text-blue-600" />
                <span>Agent Investigation Trace ({agenticResult.steps} Steps)</span>
              </h3>

              <div className="space-y-3">
                {agenticResult.trace && agenticResult.trace.map((step, idx) => (
                  <div
                    key={idx}
                    className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-xs flex flex-col space-y-1.5 hover:border-slate-300 transition-all"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <span className="w-5 h-5 rounded-full bg-blue-100 border border-blue-300 text-blue-700 font-mono flex items-center justify-center text-[10px] font-bold">
                          {step.step_number}
                        </span>
                        <span className="font-bold text-slate-900">{step.agent || 'Specialized Agent'}</span>
                        <span className="text-slate-500 font-mono">[{step.tool}]</span>
                      </div>
                      <div className="flex items-center space-x-3 text-[11px] text-slate-500 font-mono">
                        <span className="flex items-center space-x-1">
                          <Clock className="w-3 h-3 text-amber-500" />
                          <span>{step.latency_ms}ms</span>
                        </span>
                        <span className="flex items-center space-x-1">
                          <Coins className="w-3 h-3 text-blue-600" />
                          <span>{step.tokens} tok</span>
                        </span>
                      </div>
                    </div>

                    <p className="text-slate-700 pl-7">{step.output_summary}</p>
                    {step.reason && (
                      <p className="text-[11px] text-slate-500 pl-7 italic">Reason: {step.reason}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Metrics & Metadata Sidebar (1 col) */}
          <div className="space-y-5">
            <div className="p-5 rounded-2xl bg-white border border-slate-200/90 shadow-sm backdrop-blur-xl">
              <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-4 border-b border-slate-100 pb-2">
                Investigation Execution Profile
              </h4>

              <div className="space-y-3">
                <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between">
                  <span className="text-xs text-slate-600 flex items-center space-x-2">
                    <Clock className="w-4 h-4 text-amber-500" />
                    <span>Total Latency</span>
                  </span>
                  <span className="font-mono text-sm text-slate-900 font-semibold">{agenticResult.latency_ms} ms</span>
                </div>

                <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between">
                  <span className="text-xs text-slate-600 flex items-center space-x-2">
                    <Coins className="w-4 h-4 text-blue-600" />
                    <span>Tokens Consumed</span>
                  </span>
                  <span className="font-mono text-sm text-slate-900 font-semibold">{agenticResult.tokens}</span>
                </div>

                <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between">
                  <span className="text-xs text-slate-600 flex items-center space-x-2">
                    <Layers className="w-4 h-4 text-purple-600" />
                    <span>Investigation Steps</span>
                  </span>
                  <span className="font-mono text-sm text-slate-900 font-semibold">{agenticResult.steps}</span>
                </div>
              </div>

              {/* Agents Activated */}
              <div className="mt-5 pt-4 border-t border-slate-100">
                <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block mb-2">
                  Specialized Agents Activated:
                </span>
                <div className="space-y-1.5">
                  {agenticResult.agents_used && agenticResult.agents_used.map((ag, idx) => (
                    <div
                      key={idx}
                      className="px-3 py-1.5 rounded-lg bg-blue-50/60 border border-blue-200 text-xs font-mono text-blue-800 flex items-center space-x-2 font-medium"
                    >
                      <span className="w-1.5 h-1.5 rounded-full bg-blue-600"></span>
                      <span>{ag}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Mode 2: 3-Way Paradigm Comparison */}
      {mode === 'compare' && compareResults && (
        <div className="space-y-6">
          <div className="p-4 rounded-xl bg-indigo-50 border border-indigo-200 text-indigo-900 text-xs flex items-center space-x-2 font-medium">
            <Sparkles className="w-4 h-4 text-indigo-600 flex-shrink-0" />
            <span>Parallel comparative evaluation: Review accuracy, citations, token cost, and latency for identical prompt.</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* 1. Baseline RAG Card */}
            <div className="p-5 rounded-2xl bg-white border border-blue-200 shadow-sm backdrop-blur-xl flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-100">
                  <span className="font-bold text-slate-900 text-sm flex items-center space-x-2">
                    <Database className="w-4 h-4 text-blue-600" />
                    <span>Baseline Vector RAG</span>
                  </span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-blue-50 border border-blue-200 text-blue-700 font-semibold">
                    ChromaDB
                  </span>
                </div>
                <div className="text-xs text-slate-800 p-3.5 rounded-xl bg-slate-50 border border-slate-200 font-mono min-h-[120px]">
                  {compareResults.rag.answer}
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-100 space-y-2 text-xs">
                <div className="flex justify-between text-slate-500">
                  <span>Latency:</span>
                  <span className="font-mono text-slate-800 font-semibold">{compareResults.rag.latency_ms} ms</span>
                </div>
                <div className="flex justify-between text-slate-500">
                  <span>Tokens:</span>
                  <span className="font-mono text-slate-800 font-semibold">{compareResults.rag.total_tokens || compareResults.rag.tokens}</span>
                </div>
                <div className="flex justify-between text-slate-500">
                  <span>Citations:</span>
                  <span className="font-mono text-slate-800 font-semibold">{compareResults.rag.citations?.length || 0} docs</span>
                </div>
              </div>
            </div>

            {/* 2. GraphRAG Card */}
            <div className="p-5 rounded-2xl bg-white border border-emerald-200 shadow-sm backdrop-blur-xl flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-100">
                  <span className="font-bold text-slate-900 text-sm flex items-center space-x-2">
                    <GitFork className="w-4 h-4 text-emerald-600" />
                    <span>TigerGraph GraphRAG</span>
                  </span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-700 font-semibold">
                    GSQL Traversal
                  </span>
                </div>
                <div className="text-xs text-slate-800 p-3.5 rounded-xl bg-slate-50 border border-slate-200 font-mono min-h-[120px]">
                  {compareResults.graphrag.answer}
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-100 space-y-2 text-xs">
                <div className="flex justify-between text-slate-500">
                  <span>Latency:</span>
                  <span className="font-mono text-slate-800 font-semibold">{compareResults.graphrag.latency_ms} ms</span>
                </div>
                <div className="flex justify-between text-slate-500">
                  <span>Tokens:</span>
                  <span className="font-mono text-slate-800 font-semibold">{compareResults.graphrag.total_tokens || compareResults.graphrag.tokens}</span>
                </div>
                <div className="flex justify-between text-slate-500">
                  <span>Citations:</span>
                  <span className="font-mono text-slate-800 font-semibold">{compareResults.graphrag.citations?.length || 0} docs</span>
                </div>
              </div>
            </div>

            {/* 3. Agentic GraphRAG Card */}
            <div className="p-5 rounded-2xl bg-white border-2 border-indigo-400 shadow-md shadow-indigo-100 backdrop-blur-xl flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-100">
                  <span className="font-bold text-slate-900 text-sm flex items-center space-x-2">
                    <Sparkles className="w-4 h-4 text-indigo-600" />
                    <span>Agentic GraphRAG</span>
                  </span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-indigo-50 border border-indigo-200 text-indigo-700 font-semibold">
                    LangGraph
                  </span>
                </div>
                <div className="text-xs text-slate-900 p-3.5 rounded-xl bg-slate-50 border border-indigo-200 font-mono min-h-[120px]">
                  {compareResults.agentic.answer}
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-100 space-y-2 text-xs">
                <div className="flex justify-between text-slate-500">
                  <span>Latency:</span>
                  <span className="font-mono text-indigo-700 font-bold">{compareResults.agentic.latency_ms} ms</span>
                </div>
                <div className="flex justify-between text-slate-500">
                  <span>Tokens:</span>
                  <span className="font-mono text-indigo-700 font-bold">{compareResults.agentic.tokens}</span>
                </div>
                <div className="flex justify-between text-slate-500">
                  <span>Steps Taken:</span>
                  <span className="font-mono text-indigo-700 font-bold">{compareResults.agentic.steps} steps</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
