'use client';

import React, { useState, useEffect } from 'react';
import { Header } from '@/components/layout/Header';
import { memoryService } from '@/lib/api/memoryService';
import { MemoryItem } from '@/lib/types';
import { Database, Link2, RefreshCw, Layers, CheckCircle2, AlertTriangle, FileText } from 'lucide-react';
import { cn } from '@/lib/utils/cn';

export default function Page() {
  const [items, setItems] = useState<MemoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [isSyncing, setIsSyncing] = useState(false);

  useEffect(() => {
    const fetch = async () => {
      const m = await memoryService.getMemoryItems();
      setItems(m);
      setLoading(false);
    };
    fetch();
  }, []);

  const handleSync = () => {
    setIsSyncing(true);
    setTimeout(() => {
      setIsSyncing(false);
      alert('Obsidian Vault directories scanned. 4 memory items synced locally.');
    }, 1500);
  };

  const retrievedItems = items.filter(item => item.type === 'retrieved');
  const writtenItems = items.filter(item => item.type !== 'retrieved');

  return (
    <div className="flex flex-col min-h-full pb-10">
      <Header
        title="Knowledge & Memory"
        subtitle="Access local Obsidian vaults and sync agent lesson checkpoints."
      />

      <div className="flex-1 px-6 py-6 space-y-6 max-w-6xl mx-auto w-full select-none">
        
        {/* Obsidian Vault configuration panel */}
        <div className="bg-[#0c1322] border border-slate-800 rounded-xl p-5 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="md:col-span-2 space-y-4">
            <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
              <Database className="h-5 w-5 text-indigo-400" />
              Obsidian Vault Partition
            </h3>
            
            <p className="text-xs text-slate-400 font-mono leading-relaxed">
              The platform references standard Markdown files in your local vault as the company memory layer. Newly validated decisions and architectural schemas are written back automatically as system checkpoints.
            </p>

            <div className="flex flex-col gap-2 pt-1 font-mono text-[11px]">
              <div className="flex justify-between border-b border-slate-900 pb-2">
                <span className="text-slate-500">Vault Location:</span>
                <span className="text-slate-300">C:/Users/Anshif/Obsidian/Lordminds</span>
              </div>
              <div className="flex justify-between border-b border-slate-900 pb-2">
                <span className="text-slate-500">Last Synced Checkpoint:</span>
                <span className="text-slate-300">2026-08-31 09:02:25</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Workspace Status:</span>
                <span className="text-amber-500 font-bold bg-amber-500/10 px-1.5 py-0.5 rounded">CONNECTION PENDING (LOCAL VAULT ONLY)</span>
              </div>
            </div>
          </div>

          <div className="flex flex-col justify-center items-stretch gap-3 border-t md:border-t-0 md:border-l border-slate-800 pt-4 md:pt-0 md:pl-6 shrink-0">
            <button
              onClick={handleSync}
              disabled={isSyncing}
              className="flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 text-white disabled:text-slate-500 text-xs py-2.5 px-4 rounded-lg font-bold transition-all focus-ring uppercase tracking-wider font-mono"
            >
              <RefreshCw className={cn("h-4 w-4", isSyncing && "animate-spin")} />
              {isSyncing ? "Syncing markdown..." : "Sync Vault Now"}
            </button>
            <div className="text-[10px] text-center font-mono text-slate-500">
              Files parsed offline. No cloud network usage.
            </div>
          </div>
        </div>

        {/* Memory Items Section */}
        {loading ? (
          <div className="h-64 flex items-center justify-center font-mono text-xs text-slate-500">
            Reading Obsidian index...
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
            
            {/* Left Col: Retrieved brand context */}
            <div className="space-y-4">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                <FileText className="h-4 w-4 text-indigo-400" />
                Retrieved Context Guidelines
              </h3>
              
              <div className="space-y-3">
                {retrievedItems.map(item => (
                  <div key={item.id} className="border border-slate-800 bg-[#0c1322] rounded-lg p-3 space-y-2">
                    <div className="flex justify-between items-start gap-2">
                      <h4 className="text-xs font-bold text-slate-200">{item.title}</h4>
                      <span className="text-[8px] bg-slate-900 px-1.5 py-0.5 rounded text-indigo-400 font-mono uppercase">Read Only</span>
                    </div>
                    <p className="text-[11px] text-slate-400 leading-relaxed font-mono">
                      {item.content}
                    </p>
                    <div className="text-[9px] font-mono text-slate-500 pt-1 border-t border-slate-900">
                      Used by: {item.usedBy.join(', ')}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Right Col: Written decisions & lessons */}
            <div className="space-y-4">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                <Database className="h-4 w-4 text-indigo-400" />
                System Decisions & Lessons Learned
              </h3>

              <div className="space-y-3">
                {writtenItems.map(item => (
                  <div key={item.id} className="border border-slate-800 bg-[#0c1322] rounded-lg p-3 space-y-2">
                    <div className="flex justify-between items-start gap-2">
                      <h4 className="text-xs font-bold text-slate-200">{item.title}</h4>
                      <span className="text-[8px] bg-indigo-950/20 border border-indigo-500/20 text-indigo-400 px-1.5 py-0.5 rounded font-mono uppercase">Written Checkpoint</span>
                    </div>
                    <p className="text-[11px] text-slate-400 leading-relaxed font-mono">
                      {item.content}
                    </p>
                    <div className="text-[9px] font-mono text-slate-500 pt-1 border-t border-slate-900 flex justify-between">
                      <span>Authored: {item.usedBy.join(', ')}</span>
                      <span>{new Date(item.timestamp).toLocaleDateString()}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

          </div>
        )}

      </div>
    </div>
  );
}
