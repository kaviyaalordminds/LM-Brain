import React from 'react';
import { Cpu, Database, Play, ShieldAlert, Sparkles, Terminal } from 'lucide-react';
import { ExecutionMode } from '../../hooks/useRunExecution';

interface DemoBannerProps {
  executionMode?: ExecutionMode;
  onToggleMode?: (mode: ExecutionMode) => void;
  pythonAvailable?: boolean;
}

export const DemoBanner: React.FC<DemoBannerProps> = ({
  executionMode = 'LOCAL',
  onToggleMode,
  pythonAvailable = true,
}) => {
  const isLocal = executionMode === 'LOCAL';

  return (
    <div className={`border-b px-4 py-2 text-xs flex flex-wrap items-center justify-between gap-3 text-slate-300 select-none transition-colors ${
      isLocal
        ? 'bg-gradient-to-r from-emerald-950/40 via-indigo-950/30 to-slate-900 border-emerald-800/40'
        : 'bg-gradient-to-r from-amber-950/40 via-indigo-950/30 to-slate-900 border-amber-900/40'
    }`}>
      <div className="flex items-center gap-2.5 flex-wrap">
        <span className="flex h-2 w-2 relative">
          <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${isLocal ? 'bg-emerald-400' : 'bg-amber-400'}`}></span>
          <span className={`relative inline-flex rounded-full h-2 w-2 ${isLocal ? 'bg-emerald-500' : 'bg-amber-500'}`}></span>
        </span>
        <span className={`font-semibold tracking-wide font-mono uppercase ${isLocal ? 'text-emerald-400' : 'text-amber-400'}`}>
          ● {isLocal ? 'LOCAL BACKEND MODE (Real LocalRunner)' : 'DEMO MODE (Simulator)'}
        </span>
        <span className="text-slate-500">|</span>
        <span className="text-slate-400">
          Target:{' '}
          <span className="text-slate-200 font-mono font-medium">
            {isLocal ? 'Vite Dev Bridge -> Python LocalRunner -> MasterOrchestrator' : 'Offline Stateful Demo Store'}
          </span>
        </span>

        {onToggleMode && (
          <div className="flex items-center gap-1 bg-slate-950/70 p-0.5 rounded border border-slate-700/80 font-mono text-[11px] ml-2">
            <button
              type="button"
              onClick={() => onToggleMode('LOCAL')}
              className={`px-2 py-0.5 rounded transition-all ${
                isLocal
                  ? 'bg-emerald-600 text-white font-bold shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              LOCAL BACKEND
            </button>
            <button
              type="button"
              onClick={() => onToggleMode('DEMO')}
              className={`px-2 py-0.5 rounded transition-all ${
                !isLocal
                  ? 'bg-amber-600 text-white font-bold shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              DEMO MODE
            </button>
          </div>
        )}
      </div>

      <div className="flex items-center gap-4 text-xs font-mono">
        <span className="flex items-center gap-1.5 text-emerald-400/90">
          <Database className="w-3.5 h-3.5" />
          Authoritative Knowledge: <strong className="font-semibold">Obsidian Vault</strong>
        </span>
        <span className="hidden md:flex items-center gap-1.5 text-indigo-300/80">
          <Terminal className="w-3.5 h-3.5" />
          SecurityGuard: <strong className="font-semibold">Enforced</strong>
        </span>
      </div>
    </div>
  );
};
