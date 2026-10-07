import React, { useState, useEffect } from 'react';
import { 
  GitFork, 
  Search, 
  Layers, 
  ExternalLink, 
  RefreshCw,
  ArrowRight,
  Database
} from 'lucide-react';
import { getGraphEntity, getGraphNeighbors } from '../services/api';

const PRESET_ENTITIES = [
  { id: '2016 Summer', type: 'Games' },
  { id: '2012 Summer', type: 'Games' },
  { id: 'Athletics', type: 'Sport' },
  { id: 'Biathlon', type: 'Sport' },
  { id: 'Olympic Stadium', type: 'Venue' },
];

export default function KnowledgeGraphExplorer() {
  const [searchId, setSearchId] = useState('2016 Summer');
  const [entityData, setEntityData] = useState(null);
  const [neighbors, setNeighbors] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchGraphData = async (idToFetch) => {
    const id = idToFetch || searchId;
    if (!id.trim()) return;

    try {
      setLoading(true);
      setError(null);
      const [ent, neigh] = await Promise.all([
        getGraphEntity(id).catch(() => null),
        getGraphNeighbors(id).catch(() => []),
      ]);
      setEntityData(ent);
      setNeighbors(neigh || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGraphData('2016 Summer');
  }, []);

  return (
    <div className="space-y-6">
      <div className="p-6 rounded-2xl bg-white border border-slate-200/90 shadow-sm backdrop-blur-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-slate-900 flex items-center space-x-2">
            <GitFork className="w-5 h-5 text-blue-600" />
            <span>Knowledge Graph Explorer</span>
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Browse TigerGraph vertices, inspect relationship edges, and trace document backlinks
          </p>
        </div>

        {/* Search Bar */}
        <div className="flex items-center space-x-2">
          <div className="relative">
            <input
              type="text"
              value={searchId}
              onChange={(e) => setSearchId(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && fetchGraphData()}
              placeholder="Search vertex ID or name..."
              className="pl-8 pr-4 py-2 rounded-xl bg-slate-50 border border-slate-300 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:bg-white focus:border-blue-600 focus:ring-1 focus:ring-blue-600 font-mono w-64 transition-all"
            />
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
          </div>

          <button
            onClick={() => fetchGraphData()}
            disabled={loading}
            className="px-3 py-2 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white text-xs font-semibold flex items-center space-x-1 shadow-md shadow-blue-500/20 transition-all disabled:opacity-50"
          >
            {loading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <span>Inspect</span>}
          </button>
        </div>
      </div>

      {/* Preset Entities */}
      <div className="flex flex-wrap gap-2 text-xs">
        <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider self-center mr-1">
          Common Vertices:
        </span>
        {PRESET_ENTITIES.map((p) => (
          <button
            key={p.id}
            onClick={() => {
              setSearchId(p.id);
              fetchGraphData(p.id);
            }}
            className="px-2.5 py-1 rounded-lg bg-slate-100 border border-slate-200 text-slate-700 hover:border-blue-300 hover:bg-blue-50 hover:text-blue-700 transition-all font-mono text-xs font-medium"
          >
            <span>{p.id}</span>
            <span className="text-slate-500 text-[10px] ml-1.5 font-sans">({p.type})</span>
          </button>
        ))}
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-800 text-xs font-medium">
          {error}
        </div>
      )}

      {/* Vertex Details & Neighbors */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Vertex Card (1 col) */}
        <div className="p-5 rounded-2xl bg-white border border-slate-200/90 shadow-sm">
          <h3 className="font-bold text-slate-900 text-sm pb-3 mb-3 border-b border-slate-100 flex items-center space-x-2">
            <Database className="w-4 h-4 text-blue-600" />
            <span>Target Vertex</span>
          </h3>

          {entityData ? (
            <div className="space-y-3 text-xs font-mono">
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
                <span className="text-slate-500 uppercase text-[10px] block font-semibold">Vertex ID:</span>
                <span className="text-blue-700 font-bold text-sm">{entityData.id}</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
                <span className="text-slate-500 uppercase text-[10px] block font-semibold">Vertex Type:</span>
                <span className="text-slate-800 font-medium">{entityData.type}</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
                <span className="text-slate-500 uppercase text-[10px] block font-semibold">Properties:</span>
                <pre className="text-slate-700 text-[11px] overflow-x-auto">
                  {JSON.stringify(entityData.properties, null, 2)}
                </pre>
              </div>
            </div>
          ) : (
            <div className="text-xs text-slate-500 p-4 text-center">
              No vertex loaded. Search or select a vertex above.
            </div>
          )}
        </div>

        {/* Neighbors List (2 cols) */}
        <div className="md:col-span-2 p-5 rounded-2xl bg-white border border-slate-200/90 shadow-sm">
          <h3 className="font-bold text-slate-900 text-sm pb-3 mb-3 border-b border-slate-100 flex items-center justify-between">
            <span className="flex items-center space-x-2">
              <GitFork className="w-4 h-4 text-emerald-600" />
              <span>Neighbor Relationships ({neighbors.length})</span>
            </span>
          </h3>

          {neighbors.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-h-[480px] overflow-y-auto pr-1">
              {neighbors.map((n, idx) => (
                <div
                  key={idx}
                  onClick={() => {
                    setSearchId(n.neighbor_id);
                    fetchGraphData(n.neighbor_id);
                  }}
                  className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 hover:border-blue-300 hover:bg-blue-50/20 transition-all cursor-pointer flex flex-col justify-between text-xs space-y-2"
                >
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="px-2 py-0.5 rounded bg-emerald-100 border border-emerald-200 text-emerald-800 font-mono text-[10px] font-bold">
                      {n.edge_type}
                    </span>
                    <span className="text-slate-500 text-[10px]">({n.direction})</span>
                  </div>

                  <div className="font-semibold text-slate-900 font-mono truncate" title={n.neighbor_id}>
                    {n.neighbor_id}
                  </div>

                  <div className="text-[10px] text-slate-500 flex items-center justify-between pt-1 border-t border-slate-200 font-medium">
                    <span>Type: {n.neighbor_type}</span>
                    <ArrowRight className="w-3 h-3 text-blue-600" />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-xs text-slate-500 p-8 text-center">
              No adjacent graph neighbors discovered for this node.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
