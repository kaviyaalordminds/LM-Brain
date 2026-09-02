'use client';

import React, { useState, useEffect } from 'react';
import { Header } from '@/components/layout/Header';
import { modelService } from '@/lib/api/modelService';
import { Model } from '@/lib/types';
import { Cpu, Search, Sparkles, AlertTriangle, Eye, Layers } from 'lucide-react';
import { cn } from '@/lib/utils/cn';

export default function Page() {
  const [models, setModels] = useState<Model[]>([]);
  const [search, setSearch] = useState('');
  const [activeCategory, setActiveCategory] = useState<Model['type'] | 'all'>('all');
  const [loading, setLoading] = useState(true);

  const fetchModels = async () => {
    const m = await modelService.getModels();
    setModels(m);
    setLoading(false);
  };

  useEffect(() => {
    fetchModels();
  }, []);

  const handleToggleLoad = async (id: string) => {
    // Update local state temporarily for loading transition
    setModels(prev => prev.map(m => m.id === id ? { ...m, status: m.status === 'loaded' ? 'unloaded' : 'loading' } : m));
    
    // Fire service call
    await modelService.toggleModelLoad(id);
    
    // Refresh models list after a delay
    setTimeout(() => {
      fetchModels();
    }, 1600);
  };

  const getStatusColor = (status: Model['status']) => {
    switch (status) {
      case 'loaded': return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20';
      case 'loading': return 'text-indigo-400 bg-indigo-500/10 border-indigo-500/20 animate-pulse';
      case 'unloaded': return 'text-slate-400 bg-slate-800 border-slate-700';
      case 'available': return 'text-slate-300 bg-slate-900 border-slate-800';
      case 'unavailable': return 'text-rose-500 bg-rose-500/10 border-rose-500/20';
      default: return 'text-slate-400 bg-slate-800';
    }
  };

  const filteredModels = models.filter(m => {
    const matchesSearch = m.name.toLowerCase().includes(search.toLowerCase());
    const matchesCategory = activeCategory === 'all' || m.type === activeCategory;
    return matchesSearch && matchesCategory;
  });

  const categories: (Model['type'] | 'all')[] = [
    'all',
    'reasoning',
    'coding',
    'speech-to-text',
    'vision',
    'image',
    'video',
    'text-to-speech',
    'embeddings',
    'reranking'
  ];

  return (
    <div className="flex flex-col min-h-full pb-10">
      <Header
        title="Local AI Models"
        subtitle="Manage locally compiled LLM, Vision, STT, and TTS inference engines."
      />

      <div className="flex-1 px-6 py-6 space-y-6 max-w-6xl mx-auto w-full select-none">
        
        {/* Resource monitor info */}
        <div className="bg-[#0c1322] border border-slate-800 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <span className="font-bold text-slate-200 text-xs block">Local Hardware Allocation</span>
            <p className="text-[11px] text-slate-400 font-mono leading-normal max-w-xl">
              Platform inference runs completely local-first. Models loaded are loaded into RTX VRAM buffers. Maintain VRAM bounds to prevent process crashing.
            </p>
          </div>

          <div className="bg-slate-900 border border-slate-850 px-4 py-2 rounded-lg font-mono text-[11px] text-right shrink-0">
            <span className="text-slate-500 block">System VRAM Load:</span>
            <span className="text-slate-200 font-bold text-xs">54.2 GB / 80 GB</span>
          </div>
        </div>

        {/* Filters and search */}
        <div className="flex flex-col gap-3 justify-between items-stretch">
          <div className="relative max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search local models directory..."
              className="w-full bg-[#0c1322] border border-slate-800 rounded-lg pl-9 pr-4 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div className="flex items-center gap-1.5 overflow-x-auto scrollbar-none bg-[#0c1322] border border-slate-800 p-1 rounded-lg">
            {categories.map(cat => (
              <button
                key={cat}
                onClick={() => setActiveCategory(cat)}
                className={cn(
                  "px-3 py-1.5 rounded text-[9px] uppercase font-bold tracking-wider transition-colors shrink-0",
                  activeCategory === cat ? "bg-slate-800 text-slate-100" : "text-slate-500 hover:text-slate-300"
                )}
              >
                {cat.replace('-', ' ')}
              </button>
            ))}
          </div>
        </div>

        {/* Model cards */}
        {loading ? (
          <div className="h-64 flex items-center justify-center font-mono text-xs text-slate-500">
            Checking device model index...
          </div>
        ) : filteredModels.length === 0 ? (
          <div className="h-64 flex flex-col items-center justify-center border border-dashed border-slate-800 rounded-xl text-slate-500 font-mono text-xs gap-2">
            <Cpu className="h-6 w-6 text-slate-700" />
            <span>No models found matching selected category.</span>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredModels.map(model => (
              <div
                key={model.id}
                className="border border-slate-800 bg-[#0c1322] rounded-xl p-4 flex flex-col justify-between min-h-[160px]"
              >
                <div className="space-y-3">
                  <div className="flex justify-between items-start gap-2">
                    <div>
                      <h4 className="text-xs font-bold text-slate-200 truncate max-w-[150px]">{model.name}</h4>
                      <span className="text-[9px] text-indigo-400 font-mono uppercase tracking-wider block mt-0.5">{model.type}</span>
                    </div>

                    <span className={cn(
                      "text-[9px] font-mono font-bold uppercase border px-2 py-0.5 rounded-full shrink-0",
                      getStatusColor(model.status)
                    )}>
                      {model.status}
                    </span>
                  </div>

                  <div className="grid grid-cols-3 gap-1 font-mono text-[9px] text-slate-500 bg-[#060a12] p-2 border border-slate-900 rounded">
                    <div>
                      <span className="block text-slate-600">PARAMS</span>
                      <span className="text-slate-300 font-bold">{model.parameters}</span>
                    </div>
                    <div>
                      <span className="block text-slate-600">QUANT</span>
                      <span className="text-slate-300 font-bold">{model.quantization}</span>
                    </div>
                    <div>
                      <span className="block text-slate-600">VRAM</span>
                      <span className="text-slate-300 font-bold">{model.vram}</span>
                    </div>
                  </div>
                </div>

                <div className="pt-3 mt-3 border-t border-slate-900 flex justify-between items-center text-[10px] font-mono">
                  <span className="text-slate-500">Host: Local GGUF</span>
                  
                  {model.status !== 'unavailable' && (
                    <button
                      onClick={() => handleToggleLoad(model.id)}
                      disabled={model.status === 'loading'}
                      className={cn(
                        "font-bold uppercase tracking-wider px-2.5 py-1 rounded transition-colors text-[9px]",
                        model.status === 'loaded' 
                          ? "bg-rose-950/20 text-rose-400 hover:bg-rose-900/20 border border-rose-900/30" 
                          : "bg-slate-900 text-slate-300 hover:bg-slate-800 border border-slate-800"
                      )}
                    >
                      {model.status === 'loaded' ? 'Unload Model' : model.status === 'loading' ? 'Loading...' : 'Load Model'}
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

      </div>
    </div>
  );
}
