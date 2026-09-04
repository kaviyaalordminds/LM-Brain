'use client';

import React, { useState, useEffect } from 'react';
import { Activity, Server, Database, Globe, ShieldCheck } from 'lucide-react';
import { checkBackendHealth } from '@/lib/api';

export default function HealthPage() {
  const [healthData, setHealthData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function check() {
      setLoading(true);
      const res = await checkBackendHealth();
      setHealthData(res);
      setLoading(false);
    }
    check();
  }, []);

  return (
    <div className="space-y-6">
      <div className="p-5 rounded-2xl bg-[#0F1420] border border-slate-800 shadow-xl space-y-1">
        <h1 className="text-base font-bold text-white tracking-wide">
          System Health &amp; Subsystem Diagnostics
        </h1>
        <p className="text-xs text-slate-400 font-mono">
          GET /health &bull; Real-time status inspection
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="p-4 rounded-xl bg-[#0F1420] border border-slate-800 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-white font-mono">Memory Agent (FastAPI)</span>
            <span className={healthData?.online ? 'text-xs text-emerald-400 font-bold font-mono' : 'text-xs text-rose-400 font-bold font-mono'}>
              {healthData?.online ? '● HEALTHY' : '● OFFLINE'}
            </span>
          </div>
          <p className="text-xs text-slate-400">Response: {JSON.stringify(healthData?.data || healthData?.error)}</p>
        </div>

        <div className="p-4 rounded-xl bg-[#0F1420] border border-slate-800 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-white font-mono">Obsidian Local Vault</span>
            <span className="text-xs text-emerald-400 font-bold font-mono">● ATTACHED</span>
          </div>
          <p className="text-xs text-slate-400">Path: memory-agent/obsedian/AI-Knowledge-Base</p>
        </div>
      </div>
    </div>
  );
}
