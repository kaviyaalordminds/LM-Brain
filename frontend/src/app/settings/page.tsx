'use client';

import React, { useState } from 'react';
import { Header } from '@/components/layout/Header';
import { Settings, Cpu, Shield, Database, Layout, Eye, Radio, Settings2 } from 'lucide-react';
import { cn } from '@/lib/utils/cn';

export default function Page() {
  const [activeSection, setActiveSection] = useState<'general' | 'local_ai' | 'agents' | 'security' | 'obsidian'>('local_ai');

  // Local state form mock states
  const [modelServer, setModelServer] = useState('http://localhost:11434');
  const [maxAgents, setMaxAgents] = useState(8);
  const [agentTimeout, setAgentTimeout] = useState(300);
  const [retryLimit, setRetryLimit] = useState(3);
  const [obsidianPath, setObsidianPath] = useState('C:/Users/Anshif/Obsidian/Lordminds');
  const [requireVerification, setRequireVerification] = useState(true);
  const [blockSensitive, setBlockSensitive] = useState(true);

  const sections = [
    { id: 'general', name: 'General', icon: Settings },
    { id: 'local_ai', name: 'Local AI Server', icon: Cpu },
    { id: 'agents', name: 'Agent Lifecycle Config', icon: Settings2 },
    { id: 'security', name: 'Security & Guardrails', icon: Shield },
    { id: 'obsidian', name: 'Memory / Obsidian', icon: Database },
  ] as const;

  return (
    <div className="flex flex-col min-h-full pb-10">
      <Header
        title="Settings Workspace"
        subtitle="Manage local hardware VRAM limits, agent lifecycles, and Obsidian vaults."
      />

      <div className="flex-1 px-6 py-6 max-w-6xl mx-auto w-full select-none flex flex-col md:flex-row gap-6">
        
        {/* Navigation Sidebar (Left) */}
        <aside className="w-full md:w-56 shrink-0 space-y-1">
          {sections.map(sec => {
            const Icon = sec.icon;
            return (
              <button
                key={sec.id}
                onClick={() => setActiveSection(sec.id)}
                className={cn(
                  "w-full flex items-center gap-2.5 rounded-lg px-3 py-2 text-xs font-bold uppercase tracking-wider transition-all text-left focus-ring border",
                  activeSection === sec.id
                    ? "bg-slate-800 border-slate-700 text-indigo-400"
                    : "border-transparent text-slate-500 hover:text-slate-300 hover:bg-slate-900/30"
                )}
              >
                <Icon className="h-4.5 w-4.5 text-indigo-400" />
                <span>{sec.name}</span>
              </button>
            );
          })}
        </aside>

        {/* Configuration Body (Right) */}
        <div className="flex-1 bg-[#0c1322] border border-slate-800 rounded-xl p-5 md:p-6 min-h-[400px] text-xs font-mono">
          
          {/* General Section */}
          {activeSection === 'general' && (
            <div className="space-y-4 max-w-lg">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200 border-b border-slate-800 pb-2">General Workspace Preferences</h3>
              
              <div className="space-y-2">
                <label className="text-slate-400 block">Theme Mode</label>
                <select className="w-full bg-[#060a12] border border-slate-800 rounded p-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500">
                  <option value="dark">Dark-first Premium (Locked)</option>
                </select>
              </div>

              <div className="space-y-2">
                <label className="text-slate-400 block">Logging Telemetry Interval (ms)</label>
                <input
                  type="number"
                  defaultValue={2000}
                  className="w-full bg-[#060a12] border border-slate-800 rounded p-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                />
              </div>
            </div>
          )}

          {/* Local AI Server */}
          {activeSection === 'local_ai' && (
            <div className="space-y-4 max-w-lg">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200 border-b border-slate-800 pb-2">Local AI Inference Setup</h3>
              
              <div className="space-y-2">
                <label className="text-slate-400 block">Ollama / Model Server Address</label>
                <input
                  type="text"
                  value={modelServer}
                  onChange={(e) => setModelServer(e.target.value)}
                  className="w-full bg-[#060a12] border border-slate-800 rounded p-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3 pt-2">
                <div className="bg-[#060a12] p-2.5 border border-slate-900 rounded">
                  <span className="text-slate-500 block text-[10px]">GPU SCHEDULER:</span>
                  <span className="text-emerald-400 font-bold uppercase text-xs">Ollama Direct (Active)</span>
                </div>
                <div className="bg-[#060a12] p-2.5 border border-slate-900 rounded">
                  <span className="text-slate-500 block text-[10px]">VRAM ISOLATION:</span>
                  <span className="text-slate-200 font-bold uppercase text-xs">Enabled</span>
                </div>
              </div>

              <div className="bg-slate-900 border border-slate-850 p-3 rounded text-[11px] text-slate-400 leading-normal">
                ⚠️ Platform connects to the server offline using localhost bindings. Changing the server address triggers automatic capability recalculations.
              </div>
            </div>
          )}

          {/* Agent Lifecycle Config */}
          {activeSection === 'agents' && (
            <div className="space-y-4 max-w-lg">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200 border-b border-slate-800 pb-2">Orchestrator Lifecycle Configuration</h3>
              
              <div className="space-y-2">
                <label className="text-slate-400 block">Maximum Concurrent Agents Allowed</label>
                <input
                  type="number"
                  value={maxAgents}
                  onChange={(e) => setMaxAgents(Number(e.target.value))}
                  className="w-full bg-[#060a12] border border-slate-800 rounded p-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="space-y-2">
                <label className="text-slate-400 block">Agent Execution Timeout Limit (Seconds)</label>
                <input
                  type="number"
                  value={agentTimeout}
                  onChange={(e) => setAgentTimeout(Number(e.target.value))}
                  className="w-full bg-[#060a12] border border-slate-800 rounded p-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="space-y-2">
                <label className="text-slate-400 block">Agent Failure Retry Limit</label>
                <input
                  type="number"
                  value={retryLimit}
                  onChange={(e) => setRetryLimit(Number(e.target.value))}
                  className="w-full bg-[#060a12] border border-slate-800 rounded p-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="flex items-center justify-between pt-2">
                <label className="text-slate-400">Require Verification Before Code Commit</label>
                <input
                  type="checkbox"
                  checked={requireVerification}
                  onChange={(e) => setRequireVerification(e.target.checked)}
                  className="h-4 w-4 bg-slate-900 border-slate-800 rounded text-indigo-600 focus:ring-indigo-500"
                />
              </div>
            </div>
          )}

          {/* Security & Guardrails */}
          {activeSection === 'security' && (
            <div className="space-y-4 max-w-lg">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200 border-b border-slate-800 pb-2">Guardrails & Safety Rules</h3>
              
              <div className="flex items-center justify-between">
                <label className="text-slate-400">Block Sensitive Credentials scan failures</label>
                <input
                  type="checkbox"
                  checked={blockSensitive}
                  onChange={(e) => setBlockSensitive(e.target.checked)}
                  className="h-4 w-4 bg-slate-900 border-slate-800 rounded text-indigo-600 focus:ring-indigo-500"
                />
              </div>

              <div className="space-y-2">
                <label className="text-slate-400 block">Allowed Ports Boundary</label>
                <input
                  type="text"
                  defaultValue="3000, 3001, 8080"
                  className="w-full bg-[#060a12] border border-slate-800 rounded p-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="space-y-2">
                <label className="text-slate-400 block">Escalation Policy</label>
                <select className="w-full bg-[#060a12] border border-slate-800 rounded p-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500">
                  <option value="pause">Pause workforce & await User confirmation</option>
                  <option value="abort">Abort running session immediately</option>
                </select>
              </div>
            </div>
          )}

          {/* Memory / Obsidian */}
          {activeSection === 'obsidian' && (
            <div className="space-y-4 max-w-lg">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200 border-b border-slate-800 pb-2">Obsidian Vault Directory Configuration</h3>
              
              <div className="space-y-2">
                <label className="text-slate-400 block">Local Obsidian Vault Path</label>
                <input
                  type="text"
                  value={obsidianPath}
                  onChange={(e) => setObsidianPath(e.target.value)}
                  className="w-full bg-[#060a12] border border-slate-800 rounded p-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="flex justify-between border-t border-slate-900 pt-3">
                <span className="text-slate-500">Vault Folder Sync Status:</span>
                <span className="text-emerald-400 font-bold bg-emerald-500/10 px-1.5 py-0.5 rounded uppercase">Connected</span>
              </div>
            </div>
          )}

        </div>

      </div>
    </div>
  );
}
