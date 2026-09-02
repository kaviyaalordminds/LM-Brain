'use client';

import React from 'react';
import { useSimulation } from '@/lib/context/SimulationContext';
import {
  X,
  User,
  Shield,
  Layers,
  Cpu,
  Settings,
  HelpCircle,
  FileText,
  AlertTriangle,
  Play,
  RotateCcw,
  CheckCircle,
  StopCircle
} from 'lucide-react';
import { mockModels } from '@/lib/mock';

export function RightPanel() {
  const {
    agents,
    twins,
    activeProject,
    selectedAgentId,
    setSelectedAgentId,
    selectedTwinId,
    setSelectedTwinId,
    selectedProjectId,
    setSelectedProjectId
  } = useSimulation();

  const selectedAgent = agents.find(a => a.id === selectedAgentId);
  const selectedTwin = twins.find(t => t.id === selectedTwinId);

  // Close context panels helper
  const closeAll = () => {
    setSelectedAgentId(null);
    setSelectedTwinId(null);
    setSelectedProjectId(null);
  };

  return (
    <aside className="w-80 border-l border-slate-800 bg-[#070b13] flex flex-col overflow-hidden shrink-0 select-none">
      {/* Panel Header */}
      <div className="h-16 border-b border-slate-800 px-4 flex items-center justify-between bg-[#090d16]">
        <div className="flex items-center gap-2">
          <Shield className="h-4 w-4 text-indigo-400" />
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-200">
            {selectedAgent ? 'Agent Specs' : selectedTwin ? 'Twin Decisions' : 'Guardrail Status'}
          </span>
        </div>
        {(selectedAgent || selectedTwin) && (
          <button
            onClick={closeAll}
            className="text-slate-400 hover:text-slate-200 hover:bg-slate-800 p-1 rounded-md transition-colors focus-ring"
            aria-label="Close detail panel"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* Panel Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {selectedAgent ? (
          /* Agent Details Panel */
          <div className="space-y-5">
            <div className="flex items-start gap-3">
              <div className="h-10 w-10 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 shrink-0">
                <User className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-100">{selectedAgent.name}</h3>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 border border-slate-700 text-slate-300 font-mono inline-block mt-1">
                  {selectedAgent.capability}
                </span>
              </div>
            </div>

            <div className="space-y-3 bg-slate-900/60 border border-slate-800/80 rounded-lg p-3 text-xs font-mono">
              <div className="flex justify-between">
                <span className="text-slate-400">Current Status:</span>
                <span className="text-indigo-400 font-bold uppercase">{selectedAgent.status}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Task Progress:</span>
                <span className="text-slate-200 font-bold">{selectedAgent.progress}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Model Assigned:</span>
                <span className="text-indigo-300 font-bold truncate max-w-[120px]" title={selectedAgent.model}>{selectedAgent.model}</span>
              </div>
              <div className="space-y-1 pt-1 border-t border-slate-800">
                <span className="text-slate-400 block mb-1">Capabilities:</span>
                <div className="flex flex-wrap gap-1">
                  {selectedAgent.tools.map(tool => (
                    <span key={tool} className="text-[9px] bg-slate-800 px-1.5 py-0.5 rounded text-slate-400">
                      {tool}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">Activity Log</span>
              <div className="bg-[#04080e] border border-slate-800 rounded p-2 text-[10px] font-mono text-slate-300 leading-normal min-h-[80px]">
                {selectedAgent.lastActivity || 'Waiting for commands...'}
              </div>
            </div>

            {/* Termination command */}
            <div className="pt-4 border-t border-slate-800">
              <button
                className="w-full bg-rose-950/40 border border-rose-500/30 text-rose-400 hover:bg-rose-900/40 text-xs py-2 rounded font-semibold transition-colors flex items-center justify-center gap-1.5 focus-ring"
                onClick={() => alert('Agent termination request issued. (Mock action)')}
              >
                <StopCircle className="h-4 w-4" />
                Terminate Agent
              </button>
            </div>
          </div>
        ) : selectedTwin ? (
          /* Executive Twin Panel */
          <div className="space-y-5">
            <div className="flex items-start gap-3">
              <div className="h-10 w-10 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 shrink-0">
                <Layers className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-100">{selectedTwin.name}</h3>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 border border-slate-700 text-slate-300 font-mono inline-block mt-1">
                  {selectedTwin.role} Twin
                </span>
              </div>
            </div>

            <div className="space-y-1">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">Scope of Responsibilities</span>
              <ul className="space-y-1 text-xs text-slate-300 list-disc list-inside">
                {selectedTwin.responsibilities.map((resp, i) => (
                  <li key={i} className="leading-relaxed">{resp}</li>
                ))}
              </ul>
            </div>

            <div className="space-y-3 bg-slate-900/60 border border-slate-800/80 rounded-lg p-3 text-xs font-mono">
              <div className="flex justify-between">
                <span className="text-slate-400">Status:</span>
                <span className="text-indigo-400 font-bold uppercase">{selectedTwin.status}</span>
              </div>
              {selectedTwin.currentAssignment && (
                <div className="space-y-1 pt-1 border-t border-slate-800">
                  <span className="text-slate-400 block">Current Assignment:</span>
                  <span className="text-slate-200 block text-[11px] leading-relaxed">{selectedTwin.currentAssignment}</span>
                </div>
              )}
              {selectedTwin.activationReason && (
                <div className="space-y-1 pt-1 border-t border-slate-800">
                  <span className="text-slate-400 block">Activation Trigger:</span>
                  <span className="text-slate-200 block text-[11px] leading-relaxed">{selectedTwin.activationReason}</span>
                </div>
              )}
            </div>

            {selectedTwin.recommendations.length > 0 && (
              <div className="space-y-2">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">Strategic Decisions</span>
                <div className="bg-slate-900/80 border border-slate-800 p-2.5 rounded text-xs text-indigo-300 leading-normal font-mono">
                  {selectedTwin.recommendations[0]}
                </div>
              </div>
            )}

            <div className="space-y-2">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">Operations Logs</span>
              <div className="bg-[#04080e] border border-slate-800 rounded p-2 text-[10px] font-mono text-slate-300 leading-normal space-y-1 max-h-40 overflow-y-auto">
                {selectedTwin.activityLog.map((log, i) => (
                  <div key={i} className="border-b border-slate-900/50 pb-1 last:border-0">{log}</div>
                ))}
              </div>
            </div>
          </div>
        ) : (
          /* Default Guardrail Audit Panel */
          <div className="space-y-5 text-xs">
            <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-3 space-y-3">
              <h4 className="font-bold text-slate-200 flex items-center gap-1.5">
                <Shield className="h-4 w-4 text-emerald-400" /> Security Checkpoints
              </h4>
              <p className="text-[11px] text-slate-400 leading-normal">
                Every action spawned by the orchestrator goes through automated filesystem, process sandbox, and sensitive secrets scans.
              </p>
            </div>

            <div className="space-y-3">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">Active Security Rules</span>
              <div className="space-y-2 font-mono text-[11px]">
                <div className="flex items-center justify-between border-b border-slate-900 pb-2">
                  <span className="text-slate-300">File IO Isolation</span>
                  <span className="text-emerald-400 font-bold bg-emerald-500/10 px-1.5 py-0.5 rounded">PASSED</span>
                </div>
                <div className="flex items-center justify-between border-b border-slate-900 pb-2">
                  <span className="text-slate-300">Credentials Protection</span>
                  <span className="text-emerald-400 font-bold bg-emerald-500/10 px-1.5 py-0.5 rounded">SECURE</span>
                </div>
                <div className="flex items-center justify-between border-b border-slate-900 pb-2">
                  <span className="text-slate-300">Port Binding Restrict</span>
                  <span className="text-indigo-400 font-bold bg-indigo-500/10 px-1.5 py-0.5 rounded">MONITOR</span>
                </div>
                <div className="flex items-center justify-between border-b border-slate-900 pb-2">
                  <span className="text-slate-300">Internet Access Gate</span>
                  <span className="text-amber-500 font-bold bg-amber-500/10 px-1.5 py-0.5 rounded">BLOCKED</span>
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">Sensitive-Data Check</span>
              <div className="bg-slate-950 border border-slate-800 p-2.5 rounded font-mono text-[10px] text-slate-400 leading-relaxed">
                <span className="text-slate-500">[Audit Logs]</span> No external JWT credentials or database keys detected in the active buffer directory. Workspace sandboxed at: <code className="text-indigo-400">C:\Lordminds\Multiagent\scratch</code>.
              </div>
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}
