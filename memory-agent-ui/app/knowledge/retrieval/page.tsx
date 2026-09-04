'use client';

import React, { useState } from 'react';
import { FileCheck2, Search, Sparkles, Layers, ShieldCheck, BookOpen } from 'lucide-react';
import { searchMemory } from '@/lib/api';
import { SearchResponse, MemoryResult, TaskScope, KnowledgeGapItem } from '@/lib/types';
import Link from 'next/link';

export default function RetrievalPage() {
  const [taskQuery, setTaskQuery] = useState('Create a creative website for e-commerce');
  const [taskId, setTaskId] = useState('');
  const [data, setData] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  const handleRetrieve = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!taskQuery.trim() || loading) return;
    setLoading(true);
    try {
      const res = await searchMemory(taskQuery, taskId || undefined);
      setData(res);
      setHasSearched(true);
    } catch (err) {
      setData(null);
    }
    setLoading(false);
  };

  return (
    <div className="space-y-6">
      <div className="p-5 rounded-2xl bg-[#0F1420] border border-slate-800 shadow-xl space-y-3">
        <div>
          <h1 className="text-base font-bold text-white tracking-wide">
            Task Knowledge Context Retrieval &amp; Attribution
          </h1>
          <p className="text-xs text-slate-400 font-mono">
            RetrievalService context assembly with provenance tracking and domain relevance gating
          </p>
        </div>

        <form onSubmit={handleRetrieve} className="space-y-3">
          <div className="flex gap-2">
            <input
              type="text"
              value={taskQuery}
              onChange={(e) => setTaskQuery(e.target.value)}
              placeholder="Enter client prompt or goal (e.g. Create a creative website for Tesla)..."
              className="flex-1 bg-[#090D15] border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sky-500 font-mono"
            />
            <button
              type="submit"
              disabled={loading}
              className="px-5 py-2.5 rounded-xl bg-sky-500 hover:bg-sky-400 text-white text-xs font-semibold shadow-md shadow-sky-500/20 transition-all font-sans shrink-0"
            >
              {loading ? 'Retrieving...' : 'Retrieve Context'}
            </button>
          </div>
        </form>
      </div>

      {hasSearched && data && (
        <div className="space-y-5">
          {/* Scope Card */}
          {data.taskScope && (
            <div className="p-4 rounded-xl bg-[#0F1420] border border-slate-800 space-y-2 font-mono text-xs">
              <div className="flex items-center justify-between text-sky-400 font-bold">
                <span className="flex items-center gap-1.5">
                  <Layers className="w-4 h-4" />
                  Task Intent &amp; Scope
                </span>
                <span className="text-[10px] text-slate-500 uppercase">{data.taskScope.taskType}</span>
              </div>
              <div className="grid grid-cols-3 gap-2 text-[11px]">
                <div className="p-2 rounded bg-[#090D15] border border-slate-800/80">
                  <span className="text-slate-500 block text-[10px]">Domain:</span>
                  <span className="text-slate-200 font-bold">{data.taskScope.domain || 'Generic'}</span>
                </div>
                <div className="p-2 rounded bg-[#090D15] border border-slate-800/80">
                  <span className="text-slate-500 block text-[10px]">Entity:</span>
                  <span className="text-slate-200 font-bold">{data.taskScope.entity || 'None'}</span>
                </div>
                <div className="p-2 rounded bg-[#090D15] border border-slate-800/80">
                  <span className="text-slate-500 block text-[10px]">Platform:</span>
                  <span className="text-slate-200 font-bold">{data.taskScope.platform || 'General'}</span>
                </div>
              </div>
            </div>
          )}

          {/* Results list */}
          <div className="space-y-3">
            <div className="flex items-center justify-between text-xs font-mono text-slate-400">
              <span>Assembled Context Items ({data.results.length}):</span>
              <span className={data.found ? 'text-emerald-400' : 'text-amber-400'}>
                {data.found ? 'Sufficient Knowledge' : 'Gaps Present'}
              </span>
            </div>

            {data.results.length === 0 ? (
              <div className="p-8 rounded-2xl bg-[#0F1420] border border-dashed border-slate-800 text-center space-y-2">
                <BookOpen className="w-8 h-8 text-slate-600 mx-auto" />
                <div className="text-xs font-mono text-slate-400">
                  Zero notes retrieved. No unrelated company notes were polluted into context.
                </div>
              </div>
            ) : (
              data.results.map((r, i) => (
                <div key={i} className="p-4 rounded-xl bg-[#0F1420] border border-slate-800 space-y-2">
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="font-bold text-white">{r.sourceNote ? r.sourceNote.split('/').pop() : 'Obsidian Vault'}</span>
                    <div className="flex items-center gap-2">
                      <span className="text-purple-300 font-bold px-2 py-0.5 rounded bg-purple-500/10 border border-purple-500/20 text-[10px]">
                        {r.approvalStatus}
                      </span>
                      <span className="text-emerald-400 font-bold">{(r.relevance * 100).toFixed(0)}% Relevance</span>
                    </div>
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed font-sans whitespace-pre-line">{r.content}</p>
                  <div className="text-[10px] font-mono text-slate-500 pt-1 border-t border-slate-800/60">
                    Source: {r.sourceNote}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
