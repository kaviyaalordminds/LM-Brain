'use client';

import React, { useState, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { Search, Loader2, Sparkles, Zap, ArrowRight, CheckCircle2, Globe, ShieldCheck, BookPlus } from 'lucide-react';
import { SearchResults } from '@/components/SearchResults';
import { searchMemory } from '@/lib/api';
import { SearchResponse, MemoryResult } from '@/lib/types';

const SAMPLE_QUERIES = [
  {
    label: 'E-Commerce Platform Architecture',
    query: 'Create a creative website for e-commerce',
    desc: 'Auto-detects gap -> Auto Jina research -> writes to Obsidian -> returns full specs',
  },
  {
    label: 'Instagram Ads Campaign Specs',
    query: 'Create creative ads for Instagram',
    desc: 'Auto-detects gap -> Auto Jina research -> writes to Obsidian -> returns ad guidelines',
  },
  {
    label: 'Lordminds Brand Guidelines',
    query: 'Lordminds company profile and design principles',
    desc: 'Entity: Lordminds -> immediately retrieves internal company notes from vault',
  },
  {
    label: 'AI Heuristic Search',
    query: 'Heuristic Search in Artificial Intelligence',
    desc: 'Domain: AI -> immediately retrieves 20 AI lecture notes from vault',
  },
];

function SearchPageContent() {
  const searchParams = useSearchParams();
  const initialQuery = searchParams.get('q') || 'Create a creative website for e-commerce';

  const [query, setQuery] = useState(initialQuery);
  const [taskId, setTaskId] = useState('');
  const [context, setContext] = useState('');
  const [autoResearch, setAutoResearch] = useState(true);
  const [response, setResponse] = useState<SearchResponse | null>(null);
  const [hasSearched, setHasSearched] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);
  const [isAutoResolving, setIsAutoResolving] = useState<boolean>(false);
  const [autoResolveStep, setAutoResolveStep] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (searchParams.get('q')) {
      const q = searchParams.get('q')!;
      setQuery(q);
      executeSearch(q, false);
    }
  }, [searchParams]);

  const executeSearch = async (q: string, forceAutoResearch: boolean) => {
    if (!q.trim() || loading) return;
    setLoading(true);
    setError(null);
    if (forceAutoResearch) {
      setIsAutoResolving(true);
      setAutoResolveStep('Searching Obsidian & evaluating requirement gaps...');
    }

    try {
      if (forceAutoResearch) {
        setAutoResolveStep('Dispatching Jina Live Web Research & validating evidence...');
      }
      const res = await searchMemory(q, taskId || undefined, context || undefined, undefined, forceAutoResearch || autoResearch);
      setResponse(res);
      setHasSearched(true);
      if (forceAutoResearch) {
        setAutoResolveStep('Knowledge successfully validated and written into Obsidian vault!');
      }
    } catch (err: any) {
      setError(err.message || 'Search failed');
      setResponse(null);
    }
    setLoading(false);
    setIsAutoResolving(false);
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    executeSearch(query, autoResearch);
  };

  const handleSelectSample = (sampleQ: string) => {
    setQuery(sampleQ);
    executeSearch(sampleQ, autoResearch);
  };

  const handleAutoResolveGap = (q: string) => {
    executeSearch(q, true);
  };

  return (
    <div className="space-y-6">
      {/* Search Input Box */}
      <div className="p-5 rounded-2xl bg-[#0F1420] border border-slate-800 shadow-xl space-y-4">
        <div>
          <h1 className="text-base font-bold text-white tracking-wide flex items-center gap-2">
            <span>Autonomous Knowledge Search &amp; Ingestion</span>
            <span className="text-[10px] font-mono px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-bold">
              Autonomous Gap Resolution Active
            </span>
          </h1>
          <p className="text-xs text-slate-400 font-mono mt-1">
            If knowledge is missing from Obsidian, the system automatically triggers Jina research, validates evidence, and saves it directly to Obsidian.
          </p>
        </div>

        <form onSubmit={handleSearch} className="space-y-3">
          <div className="relative">
            <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-3.5" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Enter client query (e.g. Create a creative website for e-commerce)..."
              className="w-full bg-[#090D15] border border-slate-800 rounded-xl pl-10 pr-4 py-3 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sky-500 font-mono"
            />
          </div>

          {/* Auto-Resolve Mode Toggle */}
          <div className="flex items-center justify-between p-3 rounded-xl bg-[#0B0F19] border border-slate-800/80">
            <div className="flex items-center gap-2">
              <Zap className="w-4 h-4 text-amber-400 shrink-0" />
              <div className="text-xs font-mono">
                <span className="text-white font-bold block">Auto-Resolve Gaps via Jina Research &rarr; Obsidian</span>
                <span className="text-[11px] text-slate-400">
                  Automatically research, validate, and write missing domain knowledge directly into Obsidian.
                </span>
              </div>
            </div>
            <label className="relative inline-flex items-center cursor-pointer shrink-0">
              <input
                type="checkbox"
                checked={autoResearch}
                onChange={(e) => setAutoResearch(e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-slate-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-emerald-500"></div>
            </label>
          </div>

          {/* Quick preset chips */}
          <div className="space-y-1.5 pt-1">
            <div className="text-[10px] font-mono text-slate-500 flex items-center gap-1">
              <Sparkles className="w-3 h-3 text-purple-400" />
              <span>Quick Test Scenarios:</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {SAMPLE_QUERIES.map((sq, i) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => handleSelectSample(sq.query)}
                  className={`p-2.5 rounded-xl text-left border transition-all text-xs font-mono flex flex-col justify-between ${
                    query === sq.query
                      ? 'bg-purple-950/20 border-purple-500/40 text-white'
                      : 'bg-[#0B0F19] border-slate-800/80 hover:border-slate-700 text-slate-300'
                  }`}
                >
                  <span className="font-semibold text-sky-300 flex items-center justify-between">
                    <span>{sq.label}</span>
                    <ArrowRight className="w-3 h-3 opacity-60" />
                  </span>
                  <span className="text-[10px] text-slate-500 truncate mt-1">{sq.query}</span>
                </button>
              ))}
            </div>
          </div>

          <div className="flex gap-3 pt-2">
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="flex-1 flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-sky-500 via-indigo-600 to-purple-600 hover:from-sky-400 hover:to-purple-500 text-white text-xs font-bold shadow-lg shadow-sky-500/20 disabled:opacity-50 transition-all font-sans"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Executing Autonomous Knowledge Pipeline...</span>
                </>
              ) : (
                <>
                  <Zap className="w-4 h-4 text-amber-300" />
                  <span>Search &amp; Auto-Enrich Obsidian</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Real-time Status Card when auto resolving */}
      {isAutoResolving && (
        <div className="p-4 rounded-xl bg-gradient-to-r from-sky-950/40 to-purple-950/40 border border-sky-500/30 text-xs font-mono text-sky-300 flex items-center gap-3 animate-pulse">
          <Loader2 className="w-5 h-5 animate-spin text-sky-400 shrink-0" />
          <div>
            <div className="font-bold text-white">Autonomous Agent Active:</div>
            <div className="text-[11px] text-sky-300">{autoResolveStep}</div>
          </div>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-xs text-rose-400 font-mono">
          Error: {error}
        </div>
      )}

      {/* Results Component */}
      {hasSearched && response && (
        <SearchResults
          results={response.results || []}
          found={response.found}
          query={query}
          taskScope={response.taskScope}
          knowledgeGaps={response.knowledgeGaps}
          rejectedCandidates={response.rejectedCandidates}
          vaultScanStats={response.vaultScanStats}
          onAutoResolveGap={handleAutoResolveGap}
          isAutoResolving={isAutoResolving}
        />
      )}
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-xs font-mono text-slate-500">Loading Search...</div>}>
      <SearchPageContent />
    </Suspense>
  );
}
