'use client';

import React, { useState, useEffect } from 'react';
import { Header } from '@/components/layout/Header';
import { toolService } from '@/lib/api/toolService';
import { Tool } from '@/lib/types';
import { Terminal, Search, ShieldCheck, AlertTriangle, Play, ToggleLeft, ToggleRight, Layers } from 'lucide-react';
import { cn } from '@/lib/utils/cn';

export default function Page() {
  const [tools, setTools] = useState<Tool[]>([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);

  const fetchTools = async () => {
    const t = await toolService.getTools();
    setTools(t);
    setLoading(false);
  };

  useEffect(() => {
    fetchTools();
  }, []);

  const handleToggleTool = async (id: string) => {
    await toolService.toggleToolStatus(id);
    fetchTools();
  };

  const filteredTools = tools.filter(t => {
    return t.name.toLowerCase().includes(search.toLowerCase()) || 
           t.description.toLowerCase().includes(search.toLowerCase());
  });

  const getPermissionColor = (level: Tool['permissionLevel']) => {
    switch (level) {
      case 'admin': return 'text-rose-400 bg-rose-500/10 border-rose-500/20';
      case 'write': return 'text-indigo-400 bg-indigo-500/10 border-indigo-500/20';
      case 'read': return 'text-slate-400 bg-slate-900 border-slate-800';
      default: return 'text-slate-400 bg-slate-800';
    }
  };

  return (
    <div className="flex flex-col min-h-full pb-10">
      <Header
        title="Capabilities Registry"
        subtitle="Configure shell terminal, file edits, and network capability permissions."
      />

      <div className="flex-1 px-6 py-6 space-y-6 max-w-6xl mx-auto w-full select-none">
        
        {/* Security Warning box */}
        <div className="bg-[#0c1322] border border-slate-800 rounded-xl p-4 flex gap-3 text-xs leading-relaxed text-slate-350">
          <ShieldCheck className="h-5 w-5 text-indigo-400 shrink-0" />
          <div className="space-y-1">
            <span className="font-bold text-slate-200 block">Agent Capabilities Guardrail Isolation</span>
            <p className="text-slate-400 font-mono text-[11px]">
              Agents access these tools strictly within the folder structure `C:\Lordminds\Multiagent\scratch`. Admin permission tools (like terminal command execution) trigger an instant security gate assessment.
            </p>
          </div>
        </div>

        {/* Search */}
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search tools registry..."
            className="w-full bg-[#0c1322] border border-slate-800 rounded-lg pl-9 pr-4 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
          />
        </div>

        {/* Tools list */}
        {loading ? (
          <div className="h-64 flex items-center justify-center font-mono text-xs text-slate-500">
            Checking device tool definitions...
          </div>
        ) : filteredTools.length === 0 ? (
          <div className="h-64 flex flex-col items-center justify-center border border-dashed border-slate-800 rounded-xl text-slate-500 font-mono text-xs gap-2">
            <Terminal className="h-6 w-6 text-slate-700" />
            <span>No tools matching criteria.</span>
          </div>
        ) : (
          <div className="space-y-3">
            {filteredTools.map(tool => (
              <div
                key={tool.id}
                className="border border-slate-800 bg-[#0c1322] rounded-xl p-4 flex flex-col md:flex-row md:items-center justify-between gap-4"
              >
                {/* Left side details */}
                <div className="flex-1 space-y-1">
                  <div className="flex items-center gap-2">
                    <h4 className="text-xs font-bold text-slate-200 font-mono">{tool.name}</h4>
                    <span className={cn(
                      "text-[9px] font-mono font-bold uppercase border px-2 py-0.5 rounded-full shrink-0",
                      getPermissionColor(tool.permissionLevel)
                    )}>
                      {tool.permissionLevel}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 leading-normal max-w-2xl font-mono">
                    {tool.description}
                  </p>
                  
                  {/* Authorized agents list */}
                  <div className="flex flex-wrap gap-1.5 pt-2">
                    <span className="text-[9px] text-slate-500 font-mono self-center">Access:</span>
                    {tool.agentAccess.map(a => (
                      <span key={a} className="text-[9px] bg-slate-900 border border-slate-850 px-1.5 py-0.5 rounded text-indigo-400 capitalize font-mono">
                        {a.replace('agent-', '').replace('twin-', '')}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Right side controls */}
                <div className="flex items-center justify-end gap-4 shrink-0 font-mono text-xs select-none">
                  <div className="text-right">
                    <span className="text-[9px] text-slate-500 block">STATUS:</span>
                    <span className={cn(
                      "text-[10px] font-bold uppercase",
                      tool.status === 'active' ? "text-emerald-400" : "text-slate-500"
                    )}>{tool.status}</span>
                  </div>

                  <button
                    onClick={() => handleToggleTool(tool.id)}
                    className="text-slate-400 hover:text-slate-200 transition-colors focus-ring"
                    aria-label={tool.status === 'active' ? "Disable tool" : "Enable tool"}
                  >
                    {tool.status === 'active' ? (
                      <ToggleRight className="h-7 w-7 text-indigo-500" />
                    ) : (
                      <ToggleLeft className="h-7 w-7 text-slate-600" />
                    )}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

      </div>
    </div>
  );
}
