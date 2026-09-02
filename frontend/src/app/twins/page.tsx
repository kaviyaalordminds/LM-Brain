'use client';

import React, { useState } from 'react';
import { Header } from '@/components/layout/Header';
import { useSimulation } from '@/lib/context/SimulationContext';
import { ExecutiveTwin } from '@/lib/types';
import { Shield, Layers, Users, Zap, CheckCircle2, ChevronRight } from 'lucide-react';
import { cn } from '@/lib/utils/cn';

export default function Page() {
  const { twins, setSelectedTwinId, selectedTwinId } = useSimulation();

  const getStatusColor = (status: ExecutiveTwin['status']) => {
    switch (status) {
      case 'active':
      case 'planning':
      case 'reviewing':
        return 'text-indigo-400 bg-indigo-500/10 border-indigo-500/20 animate-pulse';
      case 'completed':
        return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20';
      case 'standby':
        return 'text-slate-400 bg-slate-900 border-slate-800';
      case 'escalated':
        return 'text-rose-400 bg-rose-500/10 border-rose-500/20';
      default:
        return 'text-slate-400 bg-slate-800';
    }
  };

  return (
    <div className="flex flex-col min-h-full pb-10">
      <Header
        title="Executive Digital Twins"
        subtitle="Strategic AI agents coordinating specialized workloads and ROI parameters."
      />

      <div className="flex-1 px-6 py-6 space-y-6 max-w-6xl mx-auto w-full select-none">
        
        {/* Info panel explaining activation */}
        <div className="bg-[#0c1322] border border-slate-800 rounded-xl p-4 flex gap-3 text-xs leading-relaxed text-slate-300">
          <Shield className="h-5 w-5 text-indigo-400 shrink-0" />
          <div className="space-y-1">
            <span className="font-bold text-slate-200 block">Strategic Activation Policy</span>
            <p className="text-slate-400 font-mono text-[11px]">
              Executive Twins are NOT active permanently. They trigger dynamically only when the Capability Manager identifies requirements that involve high-level architecture decisions, ROI thresholds, operational workflows, or brand guidelines.
            </p>
          </div>
        </div>

        {/* Info label about details */}
        <p className="text-[11px] font-mono text-slate-500">
          💡 Click any Twin card below to inspect active decisions, activation triggers, and delegated specialist agents in the Right Panel.
        </p>

        {/* Twins List */}
        <div className="space-y-4">
          {twins.map(twin => {
            const isSelected = selectedTwinId === twin.id;
            return (
              <div
                key={twin.id}
                onClick={() => setSelectedTwinId(twin.id)}
                className={cn(
                  "border rounded-xl p-4 bg-[#0c1322] hover:bg-slate-900/30 cursor-pointer transition-all duration-150 focus-ring flex flex-col md:flex-row md:items-center justify-between gap-4",
                  isSelected ? "border-indigo-500 ring-1 ring-indigo-500/30" : "border-slate-800"
                )}
              >
                {/* Left block: Role and responsibilities */}
                <div className="flex items-start gap-3 flex-1">
                  <div className="h-9 w-9 rounded-lg bg-indigo-500/10 flex items-center justify-center text-indigo-400 shrink-0 border border-slate-800">
                    <Layers className="h-5 w-5" />
                  </div>

                  <div className="space-y-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <h3 className="text-sm font-bold text-slate-100">{twin.name}</h3>
                      <span className="text-[9px] font-mono text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20">
                        {twin.role}
                      </span>
                    </div>
                    
                    {/* Responsibilities bullet points */}
                    <div className="text-[11px] text-slate-400 leading-normal font-mono max-w-xl truncate">
                      Scope: {twin.responsibilities.join(' • ')}
                    </div>
                  </div>
                </div>

                {/* Middle block: Status and current assignment */}
                <div className="flex items-center gap-4 text-xs font-mono shrink-0">
                  {twin.currentAssignment && (
                    <div className="hidden lg:block text-right">
                      <span className="text-[10px] text-slate-500 block">CURRENT TASK:</span>
                      <span className="text-slate-300 font-bold max-w-[200px] truncate block">{twin.currentAssignment}</span>
                    </div>
                  )}

                  <span className={cn(
                    "text-[9px] font-mono font-bold uppercase border px-2.5 py-1 rounded-full shrink-0",
                    getStatusColor(twin.status)
                  )}>
                    {twin.status}
                  </span>

                  <ChevronRight className="h-4 w-4 text-slate-500" />
                </div>
              </div>
            );
          })}
        </div>

      </div>
    </div>
  );
}
