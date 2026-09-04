'use client';

import React from 'react';
import { Settings, Server } from 'lucide-react';
import { MEMORY_AGENT_API_URL, OBSIDIAN_VAULT_PATH } from '@/lib/config';

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <div className="p-5 rounded-2xl bg-[#0F1420] border border-slate-800 shadow-xl space-y-1">
        <h1 className="text-base font-bold text-white tracking-wide">
          Service Configuration &amp; Environment
        </h1>
        <p className="text-xs text-slate-400 font-mono">
          Active endpoint bindings and environment variables
        </p>
      </div>

      <div className="p-5 rounded-2xl bg-[#0F1420] border border-slate-800 space-y-4 font-mono text-xs">
        <div>
          <label className="text-[10px] text-slate-500 uppercase block mb-1">Memory Agent API URL:</label>
          <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 text-sky-400 font-bold">
            {MEMORY_AGENT_API_URL}
          </div>
        </div>
        <div>
          <label className="text-[10px] text-slate-500 uppercase block mb-1">Obsidian Vault Local Path:</label>
          <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 text-purple-400">
            {OBSIDIAN_VAULT_PATH}
          </div>
        </div>
      </div>
    </div>
  );
}
