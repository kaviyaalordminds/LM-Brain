'use client';

import React, { useState, useEffect } from 'react';
import { orchestratorApi } from '@/lib/api/orchestrator';
import { WorkforceMap, ALL_10_SPECIALISTS } from '@/components/specialists/WorkforceMap';
import { DispatchAttempt } from '@/lib/types';
import { Users, Bot, Shield, AlertCircle, RefreshCw } from 'lucide-react';

export default function SpecialistWorkforcePage() {
  const [attempts, setAttempts] = useState<DispatchAttempt[]>([]);
  const [selectedSpecialistId, setSelectedSpecialistId] = useState<string | null>(null);

  useEffect(() => {
    // Load attempts from recent executions
    orchestratorApi.listExecutions().then(async (executions) => {
      const allAttempts: DispatchAttempt[] = [];
      for (const ex of executions.slice(0, 5)) {
        try {
          const atts = await orchestratorApi.getExecutionAttempts(ex.execution_id);
          allAttempts.push(...atts);
        } catch {
          // ignore
        }
      }
      setAttempts(allAttempts);
    });
  }, []);

  const selectedSpec = ALL_10_SPECIALISTS.find((s) => s.id === selectedSpecialistId) || null;

  return (
    <div className="space-y-6 font-mono-tech">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-4 bg-space-900 border border-space-800 rounded-lg shadow-md">
        <div className="flex items-center gap-3">
          <Users className="w-5 h-5 text-emerald-400" />
          <div>
            <h1 className="text-xs font-bold text-slate-100 uppercase tracking-wider">
              Autonomous Specialist Workforce
            </h1>
            <div className="text-[11px] text-slate-400">
              10 Domain-Specific Specialists in Build, Data, and Quality Layers
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs">
          <span className="text-[10px] px-2 py-0.5 rounded bg-rose-950/60 border border-rose-900/60 text-rose-300">
            Model Status: NOT CONFIGURED (Honest System State)
          </span>
        </div>
      </div>

      {/* Specialist Details Drawer if selected */}
      {selectedSpec && (
        <div className="p-4 bg-space-900 border border-sky-600/60 rounded-lg space-y-3 animate-fade-in">
          <div className="flex items-center justify-between pb-2 border-b border-space-800">
            <div className="flex items-center gap-2">
              <Bot className="w-4 h-4 text-emerald-400" />
              <span className="text-xs font-bold text-slate-100 uppercase">{selectedSpec.name}</span>
              <span className="text-[10px] px-1.5 py-0.2 rounded bg-space-800 text-slate-400">
                {selectedSpec.category}
              </span>
            </div>
            <button
              onClick={() => setSelectedSpecialistId(null)}
              className="text-[10px] text-slate-500 hover:text-slate-300"
            >
              DISMISS
            </button>
          </div>

          <p className="text-xs text-slate-300 font-sans leading-relaxed">
            {selectedSpec.description}
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-[11px]">
            <div className="p-2.5 bg-space-950 border border-space-800 rounded">
              <span className="text-slate-500 block text-[10px]">Assigned Model</span>
              <span className="text-slate-200">{selectedSpec.defaultModel}</span>
            </div>
            <div className="p-2.5 bg-space-950 border border-space-800 rounded">
              <span className="text-slate-500 block text-[10px]">Runtime Availability</span>
              <span className="text-rose-400 font-bold">{selectedSpec.modelStatus}</span>
            </div>
            <div className="p-2.5 bg-space-950 border border-space-800 rounded">
              <span className="text-slate-500 block text-[10px]">Capabilities</span>
              <span className="text-slate-300">{selectedSpec.capabilities.join(', ')}</span>
            </div>
          </div>
        </div>
      )}

      {/* Workforce Map Grid */}
      <WorkforceMap
        attempts={attempts}
        activeSpecialistId={selectedSpecialistId}
        onSelectSpecialist={setSelectedSpecialistId}
      />
    </div>
  );
}
