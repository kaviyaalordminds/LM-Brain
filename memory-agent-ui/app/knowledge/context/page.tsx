'use client';

import React, { useState } from 'react';
import { Sparkles, Terminal, Layers, AlertCircle, CheckCircle2 } from 'lucide-react';
import { getTaskContext } from '@/lib/api';
import { ContextResponse } from '@/lib/types';

export default function ContextPage() {
  const [taskId, setTaskId] = useState('');
  const [data, setData] = useState<ContextResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFetch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!taskId.trim() || loading) return;
    setLoading(true);
    setError(null);
    try {
      const res = await getTaskContext(taskId);
      setData(res);
    } catch (err: any) {
      setError(err.message || 'Task context not found');
      setData(null);
    }
    setLoading(false);
  };

  return (
    <div className="space-y-6">
      <div className="p-5 rounded-2xl bg-[#0F1420] border border-slate-800 shadow-xl space-y-3">
        <div>
          <h1 className="text-base font-bold text-white tracking-wide">
            Task Knowledge Context Inspector
          </h1>
          <p className="text-xs text-slate-400 font-mono">
            GET /api/v1/memory/context/{'{taskId}'} &bull; Never fabricates context (RULE 7)
          </p>
        </div>

        <form onSubmit={handleFetch} className="flex gap-2">
          <input
            type="text"
            value={taskId}
            onChange={(e) => setTaskId(e.target.value)}
            placeholder="Enter Task ID (e.g. task-001)..."
            className="flex-1 bg-[#090D15] border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sky-500 font-mono"
          />
          <button
            type="submit"
            disabled={loading}
            className="px-5 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold shadow-md shadow-purple-600/20 transition-all shrink-0 font-sans"
          >
            {loading ? 'Fetching...' : 'Fetch Task Context'}
          </button>
        </form>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-xs text-rose-400 font-mono">
          {error}
        </div>
      )}

      {data && (
        <div className="space-y-4">
          <div className="p-5 rounded-2xl bg-[#0F1420] border border-slate-800 space-y-3 font-mono text-xs">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <span>Task ID: <strong className="text-sky-400">{data.taskId}</strong></span>
              <span>Context Items: <strong className="text-emerald-400">{data.context.length}</strong></span>
            </div>

            {data.taskScope && (
              <div className="p-3 rounded-lg bg-[#090D15] border border-slate-800 space-y-1">
                <div className="text-sky-400 font-bold text-[11px] uppercase">Task Scope:</div>
                <div className="text-slate-300 text-[11px]">
                  Type: {data.taskScope.taskType} | Domain: {data.taskScope.domain || 'N/A'} | Entity: {data.taskScope.entity || 'None'}
                </div>
              </div>
            )}

            <pre className="text-slate-300 text-[11px] whitespace-pre-wrap bg-[#090D15] p-3 rounded-lg border border-slate-800 overflow-x-auto">
              {JSON.stringify(data, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}
