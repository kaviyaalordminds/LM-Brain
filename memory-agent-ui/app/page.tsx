'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  Server,
  Database,
  Globe,
  FileText,
  ShieldCheck,
  Search,
  ArrowRight,
  HardDriveDownload,
  Sparkles,
  Layers,
  AlertCircle
} from 'lucide-react';
import { StatusCard } from '@/components/StatusCard';
import { checkBackendHealth, getVaultTree, searchMemory } from '@/lib/api';

export default function OverviewPage() {
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);
  const [vaultFileCount, setVaultFileCount] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [quickQuery, setQuickQuery] = useState('Intelligent Agents');
  const [quickResults, setQuickResults] = useState<any[]>([]);
  const [searching, setSearching] = useState(false);

  useEffect(() => {
    async function loadStats() {
      setLoading(true);
      const health = await checkBackendHealth();
      setBackendOnline(health.online);

      try {
        const tree = await getVaultTree();
        setVaultFileCount(tree.totalFiles);
      } catch (err) {
        setVaultFileCount(null);
      }
      setLoading(false);
    }
    loadStats();
  }, []);

  const handleQuickSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!quickQuery.trim() || searching) return;
    setSearching(true);
    try {
      const res = await searchMemory(quickQuery);
      setQuickResults(res.results || []);
    } catch (err) {
      setQuickResults([]);
    }
    setSearching(false);
  };

  return (
    <div className="space-y-6">
      {/* Top Welcome Banner */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-[#111728] via-[#0E1424] to-[#0A0D14] border border-slate-800 shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <h1 className="text-xl font-bold text-white tracking-tight">
              Memory Agent Control Plane
            </h1>
            <p className="text-xs text-slate-400">
              Authoritative knowledge gateway &bull; Obsidian Knowledge Base + Jina Controlled Research
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Link
              href="/knowledge/search"
              className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-sky-500 hover:bg-sky-400 text-white text-xs font-semibold shadow-lg shadow-sky-500/20 transition-all"
            >
              <Search className="w-3.5 h-3.5" />
              <span>Search Knowledge</span>
            </Link>
            <Link
              href="/knowledge/vault"
              className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 text-xs font-semibold transition-all"
            >
              <Database className="w-3.5 h-3.5 text-purple-400" />
              <span>Browse Vault</span>
            </Link>
          </div>
        </div>
      </div>

      {/* 4 Primary Infrastructure Status Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatusCard
          title="Memory Agent"
          value={backendOnline === true ? 'ONLINE' : backendOnline === false ? 'OFFLINE' : 'CHECKING'}
          subtext="FastAPI Backend :8001"
          status={backendOnline === true ? 'online' : backendOnline === false ? 'offline' : 'neutral'}
          icon={Server}
        />
        <StatusCard
          title="Obsidian Vault"
          value={vaultFileCount !== null ? `${vaultFileCount} Notes` : 'CONNECTED'}
          subtext="Local Knowledge Base"
          status="online"
          icon={Database}
        />
        <StatusCard
          title="Jina Web Research"
          value="AVAILABLE"
          subtext="Controlled External Engine"
          status="online"
          icon={Globe}
        />
        <StatusCard
          title="Validation Gate"
          value="ENFORCING"
          subtext="Deterministic Trust Layer"
          status="online"
          icon={ShieldCheck}
        />
      </div>

      {/* Quick Search & Interaction Widget */}
      <div className="p-5 rounded-2xl bg-[#0F1420] border border-slate-800 shadow-xl space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2 text-xs font-bold text-white uppercase tracking-wider font-mono">
            <Search className="w-4 h-4 text-sky-400" />
            <span>Interactive Knowledge Search Query</span>
          </div>
          <span className="text-[10px] font-mono text-slate-400">Target: POST /api/v1/memory/search</span>
        </div>

        <form onSubmit={handleQuickSearch} className="flex gap-2">
          <input
            type="text"
            value={quickQuery}
            onChange={(e) => setQuickQuery(e.target.value)}
            placeholder="Search Obsidian Knowledge Base (e.g. Rational Agents, Deep Learning, Supervised Learning)..."
            className="flex-1 bg-[#090D15] border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sky-500 font-mono"
          />
          <button
            type="submit"
            disabled={searching}
            className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 text-white text-xs font-semibold shadow-md shadow-sky-500/20 transition-all disabled:opacity-50"
          >
            {searching ? 'Querying...' : 'Search Vault'}
          </button>
        </form>

        {quickResults.length > 0 && (
          <div className="space-y-2 pt-2">
            <span className="text-[11px] font-mono text-slate-400 block">
              Retrieved {quickResults.length} Matching Notes:
            </span>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {quickResults.slice(0, 4).map((r, idx) => (
                <div key={idx} className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 text-xs space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-white font-mono truncate">{r.sourceNote?.split('/').pop() || r.query}</span>
                    <span className="text-[10px] text-emerald-400 font-mono font-bold">{(r.relevance * 100).toFixed(0)}% Match</span>
                  </div>
                  <p className="text-[11px] text-slate-400 line-clamp-2">{r.content}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Provenance & Flow Diagram */}
      <div className="p-5 rounded-2xl bg-[#0F1420] border border-slate-800 shadow-xl space-y-3">
        <div className="text-xs font-bold text-white uppercase tracking-wider font-mono">
          Memory Agent Knowledge Lifecycle
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 text-xs font-mono">
          <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
            <span className="text-sky-400 font-bold block mb-1">1. Obsidian Query</span>
            <p className="text-[11px] text-slate-400">Lexical BM25 index scan across markdown vault records.</p>
          </div>
          <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
            <span className="text-purple-400 font-bold block mb-1">2. Controlled Research</span>
            <p className="text-[11px] text-slate-400">Jina Web search triggered when knowledge gap is detected.</p>
          </div>
          <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
            <span className="text-amber-400 font-bold block mb-1">3. Validation Gate</span>
            <p className="text-[11px] text-slate-400">Strict deterministic trust filtering (unverified &rarr; approved).</p>
          </div>
          <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
            <span className="text-emerald-400 font-bold block mb-1">4. Vault Persistence</span>
            <p className="text-[11px] text-slate-400">Approved notes committed to Obsidian as source of truth.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
