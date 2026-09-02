'use client';

import React, { useState, useEffect } from 'react';
import { useSystemHealth } from '@/hooks/useSystemHealth';
import { Settings, ShieldAlert, Database, Cpu, Brain, Bot, Key, CheckCircle2, AlertTriangle, ExternalLink } from 'lucide-react';

export default function SystemSettingsPage() {
  const health = useSystemHealth(4000);

  return (
    <div className="space-y-6 font-mono-tech">
      {/* Header */}
      <div className="flex items-center justify-between p-4 bg-space-900 border border-space-800 rounded-lg shadow-md">
        <div className="flex items-center gap-3">
          <Settings className="w-5 h-5 text-emerald-400" />
          <div>
            <h1 className="text-xs font-bold text-slate-100 uppercase tracking-wider">
              System Architecture & Runtime Configurations
            </h1>
            <div className="text-[11px] text-slate-400">
              Live operational telemetry, service endpoints, and honest model availability
            </div>
          </div>
        </div>

        <div className="text-[10px] text-slate-500">
          Last Health Ping: {health.lastChecked ? new Date(health.lastChecked).toLocaleTimeString() : '---'}
        </div>
      </div>

      {/* Model Providers Callout - HONESTLY NOT CONFIGURED */}
      <div className="p-4 bg-rose-950/40 border border-rose-800/80 rounded-lg space-y-2">
        <div className="flex items-center gap-2 text-xs font-bold text-rose-300">
          <Key className="w-4 h-4 text-rose-400" />
          <span>AI MODEL PROVIDERS: NOT CONFIGURED</span>
        </div>
        <p className="text-xs text-slate-300 font-sans leading-relaxed">
          No external LLM provider API keys (OpenAI, Anthropic, Google) are currently configured in this local runtime environment.
          When specialists are dispatched, the system produces honest <strong>MODEL_UNAVAILABLE</strong> failure events.
          This is an intentional system state, not a broken frontend.
        </p>
      </div>

      {/* Services Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Master Orchestrator */}
        <div className="bg-space-900 border border-space-800 rounded-lg p-4 space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-space-800">
            <div className="flex items-center gap-2 text-xs font-bold text-slate-200">
              <span className={`w-2.5 h-2.5 rounded-full ${health.master === 'UP' ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'}`} />
              <span>MASTER ORCHESTRATOR</span>
            </div>
            <span className={`text-[10px] px-2 py-0.5 rounded border ${
              health.master === 'UP' ? 'bg-emerald-950 text-emerald-300 border-emerald-800' : 'bg-rose-950 text-rose-300 border-rose-800'
            }`}>
              {health.master}
            </span>
          </div>
          <div className="space-y-1.5 text-[11px] text-slate-300">
            <div className="flex justify-between">
              <span className="text-slate-500">Host Port:</span>
              <span>http://127.0.0.1:8000</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Scheduler Concurrency:</span>
              <span>5 concurrent workers</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Task Timeout:</span>
              <span>300s</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Retry Limit:</span>
              <span>3 attempts</span>
            </div>
          </div>
        </div>

        {/* Planner Agent */}
        <div className="bg-space-900 border border-space-800 rounded-lg p-4 space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-space-800">
            <div className="flex items-center gap-2 text-xs font-bold text-slate-200">
              <Cpu className="w-4 h-4 text-cyan-400" />
              <span>PLANNER AGENT</span>
            </div>
            <span className={`text-[10px] px-2 py-0.5 rounded border ${
              health.planner === 'UP' ? 'bg-emerald-950 text-emerald-300 border-emerald-800' : 'bg-space-950 text-slate-400 border-space-750'
            }`}>
              {health.planner}
            </span>
          </div>
          <div className="space-y-1.5 text-[11px] text-slate-300">
            <div className="flex justify-between">
              <span className="text-slate-500">Endpoint:</span>
              <span>http://127.0.0.1:8002</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Engine:</span>
              <span>Topological DAG Decomposition</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Contracts:</span>
              <span>Validated Pydantic v2</span>
            </div>
          </div>
        </div>

        {/* Memory Agent */}
        <div className="bg-space-900 border border-space-800 rounded-lg p-4 space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-space-800">
            <div className="flex items-center gap-2 text-xs font-bold text-slate-200">
              <Brain className="w-4 h-4 text-purple-400" />
              <span>MEMORY AGENT</span>
            </div>
            <span className={`text-[10px] px-2 py-0.5 rounded border ${
              health.memory === 'UP' ? 'bg-emerald-950 text-emerald-300 border-emerald-800' : 'bg-space-950 text-slate-400 border-space-750'
            }`}>
              {health.memory}
            </span>
          </div>
          <div className="space-y-1.5 text-[11px] text-slate-300">
            <div className="flex justify-between">
              <span className="text-slate-500">Endpoint:</span>
              <span>http://127.0.0.1:8001</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Vault:</span>
              <span>Local Obsidian Adapter</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Research Provider:</span>
              <span>Jina Reader / Mock</span>
            </div>
          </div>
        </div>

        {/* Persistence Layer */}
        <div className="bg-space-900 border border-space-800 rounded-lg p-4 space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-space-800">
            <div className="flex items-center gap-2 text-xs font-bold text-slate-200">
              <Database className="w-4 h-4 text-slate-400" />
              <span>PERSISTENCE ENGINE</span>
            </div>
            <span className="text-[10px] px-2 py-0.5 rounded border bg-emerald-950 text-emerald-300 border-emerald-800">
              DURABLE
            </span>
          </div>
          <div className="space-y-1.5 text-[11px] text-slate-300">
            <div className="flex justify-between">
              <span className="text-slate-500">Database Engine:</span>
              <span>SQLite3 (WAL Mode)</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">File Path:</span>
              <span>orchestrator.db</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Audit Logging:</span>
              <span>Append-only Event Store</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
