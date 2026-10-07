import React, { useState, useEffect } from 'react';
import { 
  Terminal, 
  BarChart3, 
  Activity, 
  GitFork, 
  Cpu, 
  RefreshCw,
  Sparkles,
  ShieldCheck,
  Scale
} from 'lucide-react';
import { checkHealth } from './services/api';
import InvestigationConsole from './pages/InvestigationConsole';
import BenchmarkLab from './pages/BenchmarkLab';
import AgentTraceExplorer from './pages/AgentTraceExplorer';
import KnowledgeGraphExplorer from './pages/KnowledgeGraphExplorer';
import SystemOverview from './pages/SystemOverview';
import ConflictLab from './pages/ConflictLab';

export default function App() {
  const [activeTab, setActiveTab] = useState('investigation');
  const [healthStatus, setHealthStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchHealth = async () => {
    try {
      setLoading(true);
      const h = await checkHealth();
      setHealthStatus(h);
    } catch {
      setHealthStatus({ status: 'offline' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  const navItems = [
    { id: 'investigation', label: 'Investigation Console', icon: Terminal },
    { id: 'benchmark', label: 'Benchmark Lab', icon: BarChart3 },
    { id: 'conflicts', label: 'Conflict & Temporal Lab', icon: Scale },
    { id: 'traces', label: 'Agent Traces', icon: Activity },
    { id: 'graph', label: 'Knowledge Graph', icon: GitFork },
    { id: 'system', label: 'System Overview', icon: Cpu },
  ];

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col selection:bg-blue-600 selection:text-white">
      {/* Top Navbar */}
      <header className="border-b border-slate-200/90 bg-white/95 backdrop-blur-md sticky top-0 z-50 px-6 py-3.5 flex items-center justify-between shadow-xs">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center shadow-md shadow-blue-500/20">
            <GitFork className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-lg tracking-tight text-slate-900">
                GraphMind
              </span>
              <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded-full bg-blue-50 border border-blue-200 text-blue-700 font-semibold">
                Agentic GraphRAG
              </span>
            </div>
            <p className="text-[11px] text-slate-500 font-medium">Adaptive Multi-Agent Investigation &amp; Benchmark Platform</p>
          </div>
        </div>

        {/* System Health Status */}
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2 px-3 py-1 rounded-full bg-slate-100 border border-slate-200 text-xs">
            <div className={`w-2 h-2 rounded-full ${healthStatus?.status === 'ok' ? 'bg-emerald-500 shadow-sm shadow-emerald-500 animate-pulse' : 'bg-red-500'}`}></div>
            <span className="text-slate-500">Gateway:</span>
            <span className="font-mono text-slate-800 font-semibold">{healthStatus?.status === 'ok' ? 'Online' : 'Connecting...'}</span>
          </div>

          <button 
            onClick={fetchHealth} 
            disabled={loading}
            className="p-1.5 rounded-lg bg-slate-100 border border-slate-200 text-slate-600 hover:text-blue-600 hover:border-blue-300 transition-all text-xs flex items-center space-x-1"
            title="Refresh Health"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-blue-600' : ''}`} />
          </button>
        </div>
      </header>

      {/* Main Workspace Tabs */}
      <div className="border-b border-slate-200 bg-white/90 px-6 flex space-x-6 text-sm overflow-x-auto shadow-xs">
        {navItems.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-3 px-1 flex items-center space-x-2 border-b-2 font-medium transition-all whitespace-nowrap ${
                isActive
                  ? 'border-blue-600 text-blue-600 font-semibold'
                  : 'border-transparent text-slate-500 hover:text-slate-800 hover:border-slate-300'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Page Content Body */}
      <main className="flex-1 p-6 max-w-7xl w-full mx-auto">
        {activeTab === 'investigation' && <InvestigationConsole />}
        {activeTab === 'benchmark' && <BenchmarkLab />}
        {activeTab === 'conflicts' && <ConflictLab />}
        {activeTab === 'traces' && <AgentTraceExplorer />}
        {activeTab === 'graph' && <KnowledgeGraphExplorer />}
        {activeTab === 'system' && <SystemOverview />}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white px-6 py-3.5 text-center text-xs text-slate-500">
        GraphMind &bull; Adaptive Agentic GraphRAG Research Console &bull; 100% Real Evaluation Benchmark Data
      </footer>
    </div>
  );
}
