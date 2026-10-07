import React, { useState, useEffect } from 'react';
import { 
  ShieldAlert, 
  CheckCircle2, 
  Clock, 
  Scale, 
  RefreshCw, 
  Send, 
  AlertTriangle,
  Award,
  Layers,
  ChevronRight
} from 'lucide-react';
import { analyzeConflicts, getConflictExamples } from '../services/api';

export default function ConflictLab() {
  const [examples, setExamples] = useState([]);
  const [textInput, setTextInput] = useState('');
  const [entityName, setEntityName] = useState('Olympic Event');
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchExamples = async () => {
    try {
      const data = await getConflictExamples();
      setExamples(data || []);
      if (data && data.length > 0) {
        setTextInput(data[0].context);
        setEntityName(data[0].event);
      }
    } catch (err) {
      setError(err.message);
    }
  };

  useEffect(() => {
    fetchExamples();
  }, []);

  const handleAnalyze = async (textToAnalyze, nameToAnalyze) => {
    const txt = textToAnalyze || textInput;
    const name = nameToAnalyze || entityName;
    if (!txt.trim()) return;

    try {
      setLoading(true);
      setError(null);
      const res = await analyzeConflicts(txt, name);
      setReport(res);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const selectExample = (ex) => {
    setTextInput(ex.context);
    setEntityName(ex.event);
    handleAnalyze(ex.context, ex.event);
  };

  return (
    <div className="space-y-6">
      {/* Header Bar */}
      <div className="p-6 rounded-2xl bg-white border border-slate-200/90 shadow-sm backdrop-blur-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-slate-900 flex items-center space-x-2">
            <Scale className="w-5 h-5 text-amber-600" />
            <span>Temporal Validity &amp; Conflict Resolution Lab</span>
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Detect factual contradictions, adjudicate retrospective Olympic medal reallocations, and weigh source authority
          </p>
        </div>

        <button
          onClick={() => handleAnalyze()}
          disabled={loading}
          className="px-4 py-2 rounded-xl bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white text-xs font-semibold flex items-center space-x-1.5 shadow-md shadow-amber-500/20 transition-all self-start md:self-auto disabled:opacity-50"
        >
          {loading ? (
            <>
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              <span>Adjudicating...</span>
            </>
          ) : (
            <>
              <ShieldAlert className="w-3.5 h-3.5" />
              <span>Adjudicate Claims</span>
            </>
          )}
        </button>
      </div>

      {/* Preset Case Studies */}
      <div className="flex flex-wrap gap-2 text-xs">
        <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider self-center mr-1">
          Historical Case Studies:
        </span>
        {examples.map((ex) => (
          <button
            key={ex.id}
            onClick={() => selectExample(ex)}
            className="px-3 py-1.5 rounded-lg bg-slate-100 border border-slate-200 text-slate-700 hover:border-amber-300 hover:bg-amber-50 hover:text-amber-900 transition-all flex items-center space-x-1.5 font-medium"
          >
            <span className="font-mono text-[10px] text-amber-600 font-bold">{ex.games}</span>
            <span>{ex.event}</span>
          </button>
        ))}
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-800 text-xs font-medium">
          {error}
        </div>
      )}

      {/* Input Box */}
      <div className="p-5 rounded-2xl bg-white border border-slate-200/90 shadow-sm space-y-3">
        <label className="text-xs font-semibold text-slate-600 uppercase tracking-wider block">
          Olympic Passage or Contradictory Evidence Text:
        </label>
        <textarea
          rows={3}
          value={textInput}
          onChange={(e) => setTextInput(e.target.value)}
          placeholder="Paste an Olympic report discussing disqualification, medal stripping, or competing claims..."
          className="w-full p-3.5 rounded-xl bg-slate-50 border border-slate-300 text-xs text-slate-900 placeholder-slate-400 focus:bg-white focus:outline-none focus:border-amber-500 focus:ring-1 focus:ring-amber-500 font-mono resize-none leading-relaxed transition-all"
        />
      </div>

      {/* Adjudication Results */}
      {report && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Main Resolution Card (2 cols) */}
          <div className="md:col-span-2 p-6 rounded-2xl bg-white border border-slate-200/90 shadow-sm space-y-5">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100">
              <div className="flex items-center space-x-3">
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${report.has_conflict ? 'bg-amber-100 text-amber-700 border border-amber-200' : 'bg-emerald-100 text-emerald-700 border border-emerald-200'}`}>
                  {report.has_conflict ? <AlertTriangle className="w-4 h-4" /> : <CheckCircle2 className="w-4 h-4" />}
                </div>
                <div>
                  <h3 className="font-semibold text-slate-900 text-sm">
                    {report.has_conflict ? 'Contradiction Detected &amp; Adjudicated' : 'Unanimous Agreement'}
                  </h3>
                  <p className="text-[11px] text-slate-500 font-mono">
                    Conflict Type: {report.conflict_type}
                  </p>
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <span className="text-[11px] text-slate-500 font-medium">Residual Uncertainty:</span>
                <span className="px-2 py-0.5 rounded bg-amber-50 border border-amber-200 font-mono text-xs text-amber-800 font-bold">
                  {(report.residual_uncertainty * 100).toFixed(1)}%
                </span>
              </div>
            </div>

            {/* Authoritative Winner Callout */}
            {report.resolved_claim && (
              <div className="p-4 rounded-xl bg-gradient-to-r from-emerald-50 via-teal-50/30 to-white border border-emerald-300 flex items-center justify-between">
                <div>
                  <span className="text-[10px] font-mono uppercase tracking-wider text-emerald-800 block font-bold mb-0.5">
                    Authoritative Current Record (Gold Medalist):
                  </span>
                  <span className="text-lg font-bold text-slate-900 font-mono flex items-center space-x-2">
                    <Award className="w-5 h-5 text-amber-500" />
                    <span>{report.resolved_claim.value}</span>
                  </span>
                </div>

                <div className="text-right">
                  <span className="text-[10px] text-slate-500 block">Authority Weight:</span>
                  <span className="text-sm font-bold text-emerald-700 font-mono">
                    {(report.resolved_claim.authority_score * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            )}

            {/* Rationale */}
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-xs space-y-1.5">
              <span className="text-[10px] uppercase font-semibold text-slate-500 tracking-wider block">
                Source Authority &amp; Temporal Precedence Rationale:
              </span>
              <p className="text-slate-800 leading-relaxed font-mono">
                {report.resolution_rationale}
              </p>
            </div>
          </div>

          {/* Competing Claims Sidebar (1 col) */}
          <div className="p-5 rounded-2xl bg-white border border-slate-200/90 shadow-sm space-y-4">
            <h4 className="text-xs font-semibold text-slate-600 uppercase tracking-wider pb-2 border-b border-slate-100 flex items-center justify-between">
              <span>Competing Assertions</span>
              <span className="font-mono text-blue-600 font-bold">{report.competing_claims.length} claims</span>
            </h4>

            <div className="space-y-3">
              {report.competing_claims.map((c, idx) => (
                <div
                  key={idx}
                  className={`p-3.5 rounded-xl border text-xs space-y-1.5 transition-all ${
                    c.status === 'superseded'
                      ? 'bg-red-50/60 border-red-200'
                      : 'bg-emerald-50/60 border-emerald-200'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-900 font-mono">{c.value}</span>
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase ${
                        c.status === 'superseded'
                          ? 'bg-red-100 text-red-700 border border-red-200'
                          : 'bg-emerald-100 text-emerald-700 border border-emerald-200'
                      }`}
                    >
                      {c.status}
                    </span>
                  </div>

                  <div className="flex justify-between text-[11px] text-slate-500 pt-1 border-t border-slate-200/60 font-medium">
                    <span>Authority: {(c.authority_score * 100).toFixed(0)}%</span>
                    <span>{c.temporal_interval?.is_current ? 'Current' : 'Historical (Revoked)'}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
