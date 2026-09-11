import React from 'react';
import { Bot, ChevronRight, Cpu, ShieldCheck, Terminal } from 'lucide-react';
import { PageId } from './Sidebar';
import { ExecutionMode } from '../../hooks/useRunExecution';

interface HeaderProps {
  currentPage: PageId;
  activeRunId?: string;
  onNavigate: (page: PageId) => void;
  executionMode?: ExecutionMode;
  onToggleMode?: (mode: ExecutionMode) => void;
}

export const Header: React.FC<HeaderProps> = ({
  currentPage,
  activeRunId,
  onNavigate,
  executionMode = 'LOCAL',
}) => {
  const isLocal = executionMode === 'LOCAL';

  const getPageTitle = (page: PageId) => {
    switch (page) {
      case 'overview':
        return 'Workforce Overview';
      case 'new-work':
        return 'Submit New Work';
      case 'live-run':
        return activeRunId ? `Live Orchestration Run (${activeRunId})` : 'Live Run Control';
      case 'runs':
        return 'Autonomous Runs History';
      case 'workforce':
        return 'Specialist Workforce & Executive Twins';
      case 'knowledge':
        return 'Company Knowledge & Obsidian Vault';
      case 'evidence':
        return 'Empirical Evidence Vault';
      case 'audit':
        return 'Security & Execution Audit Timeline';
      case 'security':
        return 'Security Boundaries & Guardrails';
      case 'architecture':
        return 'Visual Architecture & Flow Map';
    }
  };

  return (
    <header className="h-14 border-b border-slate-800 bg-[#0E1526]/80 backdrop-blur px-6 flex items-center justify-between shrink-0 select-none">
      <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
        <span className="text-slate-300 font-semibold cursor-pointer hover:text-white" onClick={() => onNavigate('overview')}>
          LM-Brain
        </span>
        <ChevronRight className="w-3.5 h-3.5 text-slate-600" />
        <span className="text-indigo-400 font-medium">{getPageTitle(currentPage)}</span>
      </div>

      <div className="flex items-center gap-3 text-xs font-mono">
        <div className={`hidden sm:flex items-center gap-2 px-2.5 py-1 rounded border ${
          isLocal
            ? 'bg-emerald-950/60 border-emerald-700/80 text-emerald-300'
            : 'bg-amber-950/60 border-amber-700/80 text-amber-300'
        }`}>
          <Terminal className="w-3.5 h-3.5" />
          <span>Mode: <strong className="font-bold">{isLocal ? 'LOCAL PYTHON RUNNER' : 'DEMO SIMULATOR'}</strong></span>
        </div>
        <div className="hidden sm:flex items-center gap-2 px-2.5 py-1 rounded bg-slate-900 border border-slate-800 text-slate-300">
          <Cpu className="w-3.5 h-3.5 text-indigo-400" />
          <span>Brain: <strong className="text-slate-100">Master Orchestrator</strong></span>
        </div>
        <div className="flex items-center gap-2 px-2.5 py-1 rounded bg-emerald-950/40 border border-emerald-800/60 text-emerald-300">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
          <span>SecurityGuard: <strong className="text-emerald-200">Active</strong></span>
        </div>
      </div>
    </header>
  );
};
