import React, { useState } from 'react';
import { 
  Activity, 
  GitFork, 
  Clock, 
  Coins, 
  Terminal, 
  ArrowRight, 
  CheckCircle2, 
  FileText,
  Search,
  Sparkles
} from 'lucide-react';

const SAMPLE_TRACES = [
  {
    id: 'pub-002',
    title: 'pub-002: Temporal Predecessor (Men\'s 20km Walk)',
    question: 'Who won the gold medal in the men\'s 20 kilometres walk athletics event at the Summer Olympics held immediately before 2016?',
    steps: [
      {
        step: 1,
        agent: 'EntityLinkingAgent',
        tool: 'entity_link',
        latency_ms: 0.2,
        tokens: 46,
        summary: 'Disambiguated 2 entities: 2016 Summer, Athletics. Identified temporal target: Summer Olympics held immediately before 2016.',
        reason: 'Identify sports, games, dates, and venues from question prompt.',
      },
      {
        step: 2,
        agent: 'GraphTraversalAgent',
        tool: 'graph_traversal',
        latency_ms: 7.1,
        tokens: 465,
        summary: 'Traversed 22 graph paths across Games(2016) -[PRECEDED_BY]-> Games(2012) -> Event(Men\'s 20km walk). Found gold medalist Chen Ding [Q1050909].',
        reason: 'Execute structured graph traversal for relational/aggregation constraints.',
      },
      {
        step: 3,
        agent: 'EvidenceEvaluationAgent',
        tool: 'evidence_evaluation',
        latency_ms: 0.5,
        tokens: 56,
        summary: 'Verified sufficient evidence: 5 verified sources, 0 contradictions, gold medalist fact explicitly resolved.',
        reason: 'Evaluate evidence relevance and verify sufficiency.',
      },
      {
        step: 4,
        agent: 'MultiHopReasoningAgent',
        tool: 'final_answer',
        latency_ms: 10.9,
        tokens: 142,
        summary: 'Synthesized grounded answer citing [Q1050909] (Chen Ding, 2012 Summer Olympics in London).',
        reason: 'Synthesize best grounded answer with current accumulated evidence.',
      }
    ]
  },
  {
    id: 'pub-001',
    title: 'pub-001: Set Cardinality Aggregation (Biathlon > 73)',
    question: 'According to the provided corpus, how many biathlon events at the 2018 Winter Olympics had more than 73 competitors?',
    steps: [
      {
        step: 1,
        agent: 'EntityLinkingAgent',
        tool: 'entity_link',
        latency_ms: 0.2,
        tokens: 42,
        summary: 'Disambiguated entities: 2018 Winter, Biathlon, competitor threshold > 73.',
        reason: 'Identify sports, games, dates, and venues from question prompt.',
      },
      {
        step: 2,
        agent: 'GraphTraversalAgent',
        tool: 'graph_traversal',
        latency_ms: 6.8,
        tokens: 95,
        summary: 'Executed GSQL aggregation: WHERE competitors > 73. Returned exact count: 2 events with gold document Q47155555.',
        reason: 'Execute structured graph traversal for relational/aggregation constraints.',
      },
      {
        step: 3,
        agent: 'EvidenceEvaluationAgent',
        tool: 'evidence_evaluation',
        latency_ms: 0.4,
        tokens: 51,
        summary: 'Coverage: 100%. Direct count fact verified. Sufficient to conclude.',
        reason: 'Evaluate evidence relevance and verify sufficiency.',
      }
    ]
  }
];

export default function AgentTraceExplorer() {
  const [selectedTraceId, setSelectedTraceId] = useState('pub-002');
  const activeTrace = SAMPLE_TRACES.find(t => t.id === selectedTraceId) || SAMPLE_TRACES[0];

  return (
    <div className="space-y-6">
      <div className="p-6 rounded-2xl bg-white border border-slate-200/90 shadow-sm backdrop-blur-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-slate-900 flex items-center space-x-2">
            <Activity className="w-5 h-5 text-blue-600" />
            <span>Agent Trace DAG &amp; Timeline Explorer</span>
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Inspect autonomous step-by-step orchestrator decisions, specialized agent activations, and evidence lineage
          </p>
        </div>

        {/* Trace Selector */}
        <div className="flex space-x-2">
          {SAMPLE_TRACES.map((t) => (
            <button
              key={t.id}
              onClick={() => setSelectedTraceId(t.id)}
              className={`px-3 py-1.5 rounded-xl border text-xs font-semibold transition-all ${
                selectedTraceId === t.id
                  ? 'bg-blue-50 border-blue-300 text-blue-700 shadow-xs'
                  : 'bg-slate-100 border-slate-200 text-slate-600 hover:bg-slate-200 hover:text-slate-900'
              }`}
            >
              {t.id}
            </button>
          ))}
        </div>
      </div>

      {/* Question Header Card */}
      <div className="p-5 rounded-2xl bg-white border border-slate-200/90 shadow-sm">
        <span className="text-[11px] font-mono uppercase tracking-wider text-blue-600 font-bold block mb-1">
          Investigated Prompt [{activeTrace.id}]:
        </span>
        <h3 className="text-sm font-semibold text-slate-900 leading-relaxed font-mono">
          {activeTrace.question}
        </h3>
      </div>

      {/* DAG Timeline */}
      <div className="p-6 rounded-2xl bg-white border border-slate-200/90 shadow-sm">
        <h4 className="text-xs font-semibold text-slate-600 uppercase tracking-wider mb-6 flex items-center space-x-2">
          <GitFork className="w-4 h-4 text-blue-600" />
          <span>Execution Path (Orchestrator Dynamic Loop)</span>
        </h4>

        <div className="relative pl-6 space-y-6 before:absolute before:left-3 before:top-2 before:bottom-2 before:w-0.5 before:bg-gradient-to-b before:from-blue-600 before:via-indigo-500 before:to-purple-600">
          {activeTrace.steps.map((st, idx) => (
            <div key={idx} className="relative group">
              {/* Node Bullet */}
              <div className="absolute -left-[31px] top-1.5 w-6 h-6 rounded-full bg-white border-2 border-blue-600 flex items-center justify-center text-[10px] font-bold font-mono text-blue-600 shadow-sm">
                {st.step}
              </div>

              {/* Step Card */}
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 hover:border-blue-300 hover:bg-blue-50/20 transition-all text-xs space-y-2">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center space-x-2">
                    <span className="font-bold text-slate-900 text-sm">{st.agent}</span>
                    <span className="px-2 py-0.5 rounded bg-blue-100 border border-blue-200 font-mono text-[10px] text-blue-800 font-semibold">
                      tool: {st.tool}
                    </span>
                  </div>

                  <div className="flex items-center space-x-3 text-slate-500 text-[11px] font-mono">
                    <span className="flex items-center space-x-1">
                      <Clock className="w-3 h-3 text-amber-500" />
                      <span>{st.latency_ms} ms</span>
                    </span>
                    <span className="flex items-center space-x-1">
                      <Coins className="w-3 h-3 text-blue-600" />
                      <span>{st.tokens} tokens</span>
                    </span>
                  </div>
                </div>

                <p className="text-slate-800 leading-relaxed font-mono text-xs">{st.summary}</p>
                {st.reason && (
                  <p className="text-slate-500 text-[11px] italic">Decision Reason: {st.reason}</p>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
