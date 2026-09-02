'use client';

import React, { useState, useEffect } from 'react';
import { orchestratorApi } from '@/lib/api/orchestrator';
import { TrustBadge } from '@/components/memory/TrustBadge';
import { Brain, Database, ShieldCheck, Search, FileText, CheckCircle2, Clock, AlertTriangle } from 'lucide-react';

export default function MemoryKnowledgePage() {
  const [memoryStatus, setMemoryStatus] = useState<string>('Checking...');
  const [activeTab, setActiveTab] = useState<'vault' | 'evidence' | 'trust'>('trust');

  useEffect(() => {
    orchestratorApi.checkReady().then((res) => {
      setMemoryStatus(res.dependencies?.memory === 'up' ? 'CONNECTED' : 'STANDBY');
    }).catch(() => setMemoryStatus('OFFLINE'));
  }, []);

  return (
    <div className="space-y-6 font-mono-tech">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-4 bg-space-900 border border-space-800 rounded-lg shadow-md">
        <div className="flex items-center gap-3">
          <Brain className="w-5 h-5 text-purple-400" />
          <div>
            <h1 className="text-xs font-bold text-slate-100 uppercase tracking-wider">
              Memory Agent & Knowledge Vault
            </h1>
            <div className="text-[11px] text-slate-400">
              Service: Memory Agent (Port 8001) | Obsidian Local Vault & Controlled Research
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs">
          <span className="text-slate-500">Service Status:</span>
          <span className={`px-2 py-0.5 rounded border text-[10px] ${
            memoryStatus === 'CONNECTED'
              ? 'bg-emerald-950/60 border-emerald-800 text-emerald-300'
              : 'bg-space-950 border-space-750 text-slate-400'
          }`}>
            {memoryStatus}
          </span>
        </div>
      </div>

      {/* Trust Philosophy Callout */}
      <div className="p-4 bg-space-900 border border-purple-900/40 rounded-lg space-y-2">
        <div className="flex items-center gap-2 text-xs font-bold text-purple-300">
          <ShieldCheck className="w-4 h-4 text-purple-400" />
          <span>ZERO-TRUST MEMORY ARCHITECTURE</span>
        </div>
        <p className="text-xs text-slate-300 font-sans leading-relaxed">
          The Memory Agent enforces strict cryptographic and evidence verification before contextual write.
          Context retrieved from external research is explicitly marked as <strong>RETRIEVED</strong> and is <strong>NEVER</strong> treated as trusted until validated against the Obsidian vault and approved.
        </p>
      </div>

      {/* Trust States Taxonomy */}
      <div className="bg-space-900 border border-space-800 rounded-lg p-5 space-y-4">
        <div className="text-xs font-bold text-slate-200 uppercase tracking-wider pb-2 border-b border-space-800">
          Memory Trust States & Verification Rules
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          <div className="p-3 bg-space-950 border border-space-800 rounded space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-200">APPROVED</span>
              <TrustBadge state="APPROVED" size="sm" />
            </div>
            <p className="text-[11px] text-slate-400 font-sans leading-relaxed">
              Cryptographically or authoritatively verified knowledge approved for persistence in the enterprise Obsidian vault.
            </p>
          </div>

          <div className="p-3 bg-space-950 border border-space-800 rounded space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-200">VALIDATED</span>
              <TrustBadge state="VALIDATED" size="sm" />
            </div>
            <p className="text-[11px] text-slate-400 font-sans leading-relaxed">
              Evidence that satisfies schema verification, consistency checks, and source citations without contradiction.
            </p>
          </div>

          <div className="p-3 bg-space-950 border border-space-800 rounded space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-200">RETRIEVED</span>
              <TrustBadge state="RETRIEVED" size="sm" />
            </div>
            <p className="text-[11px] text-slate-400 font-sans leading-relaxed">
              Freshly collected context from web research or local markdown search, pending policy audit.
            </p>
          </div>

          <div className="p-3 bg-space-950 border border-space-800 rounded space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-200">PENDING</span>
              <TrustBadge state="PENDING" size="sm" />
            </div>
            <p className="text-[11px] text-slate-400 font-sans leading-relaxed">
              Context currently queued in the ValidationLayer for verification against existing documentation.
            </p>
          </div>

          <div className="p-3 bg-space-950 border border-space-800 rounded space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-200">UNVERIFIED</span>
              <TrustBadge state="UNVERIFIED" size="sm" />
            </div>
            <p className="text-[11px] text-slate-400 font-sans leading-relaxed">
              Raw outputs or untrusted external inputs. Must not be used for critical architectural decisions.
            </p>
          </div>

          <div className="p-3 bg-space-950 border border-space-800 rounded space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-200">REJECTED</span>
              <TrustBadge state="REJECTED" size="sm" />
            </div>
            <p className="text-[11px] text-slate-400 font-sans leading-relaxed">
              Contradictory, hallucinated, or policy-violating information rejected by the MemoryWriter.
            </p>
          </div>
        </div>
      </div>

      {/* Vault Structure Info */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-space-900 border border-space-800 rounded-lg p-4 space-y-3">
          <div className="flex items-center gap-2 text-xs font-bold text-slate-200">
            <Database className="w-4 h-4 text-purple-400" />
            <span>LOCAL OBSIDIAN VAULT</span>
          </div>
          <p className="text-xs text-slate-400 font-sans leading-relaxed">
            Local Obsidian Adapter indexes markdown documentation across software, web architecture, reliability, and production engineering.
          </p>
          <div className="text-[11px] text-slate-500 font-mono">
            Adapter Mode: <span className="text-slate-300">Local / Real Markdown Vault</span>
          </div>
        </div>

        <div className="bg-space-900 border border-space-800 rounded-lg p-4 space-y-3">
          <div className="flex items-center gap-2 text-xs font-bold text-slate-200">
            <Search className="w-4 h-4 text-cyan-400" />
            <span>RESEARCH PROVIDER</span>
          </div>
          <p className="text-xs text-slate-400 font-sans leading-relaxed">
            Jina Reader / Mock research provider parses technical RFCs and documentation under controlled rate limits.
          </p>
          <div className="text-[11px] text-slate-500 font-mono">
            Provider: <span className="text-slate-300">Jina Research Provider / Local Fallback</span>
          </div>
        </div>
      </div>
    </div>
  );
}
