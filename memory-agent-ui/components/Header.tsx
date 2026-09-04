'use client';

import React, { useState, useEffect } from 'react';
import { usePathname } from 'next/navigation';
import { Activity, RefreshCw, Database, Server, ShieldCheck } from 'lucide-react';
import { checkBackendHealth } from '@/lib/api';
import { MEMORY_AGENT_API_URL } from '@/lib/config';

export const Header: React.FC = () => {
  const pathname = usePathname();
  const [online, setOnline] = useState<boolean | null>(null);
  const [checking, setChecking] = useState<boolean>(false);

  const testHealth = async () => {
    setChecking(true);
    const res = await checkBackendHealth();
    setOnline(res.online);
    setChecking(false);
  };

  useEffect(() => {
    testHealth();
    const interval = setInterval(testHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  const getPageTitle = (path: string) => {
    switch (path) {
      case '/': return 'Command Center & Status Overview';
      case '/knowledge/vault': return 'Obsidian Knowledge Base (Source of Truth)';
      case '/knowledge/search': return 'Internal Knowledge Search (BM25 + Semantic)';
      case '/knowledge/retrieval': return 'Knowledge Retrieval & Evidence Attribution';
      case '/knowledge/context': return 'Task Knowledge Context Inspector';
      case '/research': return 'Controlled Web Research (Jina Engine)';
      case '/research/sources': return 'Discovered Sources & Evidence Provenance';
      case '/operations/store': return 'Memory Store & Approved Write-Back';
      case '/operations/validation': return 'Deterministic Evidence Validation Layer';
      case '/operations/history': return 'Memory Operations Audit History';
      case '/system/health': return 'System Health & Component Status';
      case '/system/events': return 'Real-Time Event Stream & Logging';
      case '/system/settings': return 'Service Configuration & Environment';
      default: return 'Memory Agent Control Plane';
    }
  };

  return (
    <header className="h-16 px-6 border-b border-slate-800/80 bg-[#0B0F17]/80 backdrop-blur-md flex items-center justify-between sticky top-0 z-30">
      <div>
        <h2 className="text-sm font-bold text-white uppercase tracking-wider font-sans">
          {getPageTitle(pathname)}
        </h2>
        <p className="text-[11px] text-slate-400 font-mono">
          Endpoint: <span className="text-sky-400">{MEMORY_AGENT_API_URL}</span>
        </p>
      </div>

      <div className="flex items-center gap-3">
        {/* Backend Status Pill */}
        <div
          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-mono font-medium border transition-all ${
            online === true
              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
              : online === false
              ? 'bg-rose-500/10 text-rose-400 border-rose-500/20'
              : 'bg-slate-800 text-slate-400 border-slate-700'
          }`}
        >
          <span
            className={`w-2 h-2 rounded-full ${
              online === true
                ? 'bg-emerald-400 animate-pulse'
                : online === false
                ? 'bg-rose-400'
                : 'bg-slate-400'
            }`}
          />
          <span>
            {online === true
              ? 'MEMORY AGENT ONLINE'
              : online === false
              ? 'BACKEND OFFLINE'
              : 'CHECKING...'}
          </span>
        </div>

        {/* Refresh Button */}
        <button
          onClick={testHealth}
          disabled={checking}
          className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-white hover:border-slate-700 transition-colors"
          title="Refresh Backend Status"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${checking ? 'animate-spin text-sky-400' : ''}`} />
        </button>
      </div>
    </header>
  );
};
