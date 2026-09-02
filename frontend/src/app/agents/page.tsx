'use client';

import React, { useState, useEffect } from 'react';
import { Header } from '@/components/layout/Header';
import { useSimulation } from '@/lib/context/SimulationContext';
import { agentService } from '@/lib/api/agentService';
import { SpecialistAgent } from '@/lib/types';
import { Search, SlidersHorizontal, User, Cpu, Terminal, ShieldAlert } from 'lucide-react';
import { cn } from '@/lib/utils/cn';

export default function Page() {
  const { agents, setSelectedAgentId, selectedAgentId } = useSimulation();
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState<'all' | 'active' | 'idle' | 'completed' | 'failed'>('all');

  const getStatusColor = (status: SpecialistAgent['status']) => {
    switch (status) {
      case 'running':
      case 'retry':
        return 'text-indigo-400 bg-indigo-500/10 border-indigo-500/20 animate-pulse';
      case 'complete':
        return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20';
      case 'failed':
      case 'reflect':
        return 'text-rose-400 bg-rose-500/10 border-rose-500/20';
      case 'ready':
      case 'local':
        return 'text-emerald-500 bg-slate-900 border-slate-800';
      case 'offline':
        return 'text-slate-500 bg-slate-850 border-slate-800';
      case 'coming_online':
        return 'text-amber-500 bg-amber-500/10 border-amber-500/20';
      default:
        return 'text-slate-400 bg-slate-800';
    }
  };

  const isAgentActive = (status: SpecialistAgent['status']) => {
    return ['spawn', 'assign', 'running', 'verify', 'reflect', 'retry'].includes(status);
  };

  const isAgentIdle = (status: SpecialistAgent['status']) => {
    return ['ready', 'local', 'offline', 'coming_online'].includes(status);
  };

  const filteredAgents = agents.filter(agent => {
    const matchesSearch = agent.name.toLowerCase().includes(search.toLowerCase()) || 
                          agent.capability.toLowerCase().includes(search.toLowerCase());
    
    if (filter === 'all') return matchesSearch;
    if (filter === 'active') return matchesSearch && isAgentActive(agent.status);
    if (filter === 'idle') return matchesSearch && isAgentIdle(agent.status);
    if (filter === 'completed') return matchesSearch && agent.status === 'complete';
    if (filter === 'failed') return matchesSearch && agent.status === 'failed';
    return matchesSearch;
  });

  return (
    <div className="flex flex-col min-h-full pb-10">
      <Header
        title="Specialist Agents"
        subtitle="Review specialist capability parameters, run logs, and active LLM models."
      />

      <div className="flex-1 px-6 py-6 space-y-6 max-w-6xl mx-auto w-full select-none">
        
        {/* Search and filters */}
        <div className="flex flex-col sm:flex-row gap-3 justify-between items-stretch sm:items-center">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by agent name or capability..."
              className="w-full bg-[#0c1322] border border-slate-800 rounded-lg pl-9 pr-4 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div className="flex items-center gap-1.5 bg-[#0c1322] border border-slate-800 p-1 rounded-lg">
            {(['all', 'active', 'idle', 'completed', 'failed'] as const).map(f => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={cn(
                  "px-3 py-1.5 rounded text-[10px] uppercase font-bold tracking-wider transition-colors shrink-0",
                  filter === f ? "bg-slate-800 text-slate-100" : "text-slate-500 hover:text-slate-300"
                )}
              >
                {f}
              </button>
            ))}
          </div>
        </div>

        {/* Info label about details */}
        <p className="text-[11px] font-mono text-slate-500">
          💡 Click an agent card below to open its identity logs and manual configuration specs in the Right Panel.
        </p>

        {/* Agents Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
          {filteredAgents.map(agent => {
            const isSelected = selectedAgentId === agent.id;
            return (
              <div
                key={agent.id}
                onClick={() => setSelectedAgentId(agent.id)}
                className={cn(
                  "border rounded-xl p-4 bg-[#0c1322] hover:bg-slate-900/30 cursor-pointer flex flex-col justify-between min-h-[140px] transition-all duration-150 focus-ring",
                  isSelected ? "border-indigo-500 ring-1 ring-indigo-500/30" : "border-slate-800 hover:border-slate-750"
                )}
              >
                <div className="space-y-3">
                  <div className="flex justify-between items-start gap-2">
                    <div className="flex items-center gap-2">
                      <div className="h-7 w-7 rounded bg-indigo-500/10 flex items-center justify-center text-indigo-400">
                        <User className="h-4 w-4" />
                      </div>
                      <div>
                        <h4 className="text-xs font-bold text-slate-200">{agent.name}</h4>
                        <span className="text-[9px] text-slate-500 font-mono block">Cap: {agent.capability}</span>
                      </div>
                    </div>

                    <span className={cn(
                      "text-[9px] font-mono font-bold uppercase border px-2 py-0.5 rounded-full shrink-0",
                      getStatusColor(agent.status)
                    )}>
                      {agent.status}
                    </span>
                  </div>

                  {agent.currentTask && (
                    <div className="text-[11px] font-mono text-slate-400 border-l border-slate-800 pl-2 py-0.5 truncate">
                      Task: {agent.currentTask}
                    </div>
                  )}
                </div>

                <div className="space-y-2.5 pt-3 mt-3 border-t border-slate-900">
                  <div className="flex justify-between text-[9px] font-mono text-slate-500">
                    <span className="flex items-center gap-1"><Cpu className="h-3 w-3" /> {agent.model.split(' ')[0]}</span>
                    <span>Prog: {agent.progress}%</span>
                  </div>
                  {/* Progress bar */}
                  <div className="bg-slate-950 h-1 rounded-full overflow-hidden">
                    <div className="bg-indigo-500 h-full transition-all duration-300" style={{ width: `${agent.progress}%` }}></div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

      </div>
    </div>
  );
}
