import React from 'react';
import {
  Activity,
  Bot,
  BrainCircuit,
  Database,
  FileCheck2,
  FolderGit2,
  GitFork,
  History,
  Layers,
  LayoutDashboard,
  PlusCircle,
  ScrollText,
  ShieldCheck,
  Workflow,
} from 'lucide-react';

export type PageId =
  | 'overview'
  | 'new-work'
  | 'live-run'
  | 'runs'
  | 'workforce'
  | 'knowledge'
  | 'evidence'
  | 'audit'
  | 'security'
  | 'architecture';

interface SidebarProps {
  currentPage: PageId;
  onNavigate: (page: PageId) => void;
  activeRunId?: string;
  isRunActive?: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentPage,
  onNavigate,
  activeRunId,
  isRunActive = false,
}) => {
  const navItems = [
    { id: 'overview' as PageId, label: 'Overview', icon: LayoutDashboard },
    { id: 'new-work' as PageId, label: 'New Work', icon: PlusCircle, badge: 'Hero' },
    { id: 'runs' as PageId, label: 'Runs History', icon: History },
    { id: 'workforce' as PageId, label: 'Workforce', icon: Bot },
    { id: 'knowledge' as PageId, label: 'Company Knowledge', icon: Database, badge: 'Obsidian' },
    { id: 'evidence' as PageId, label: 'Evidence Vault', icon: FileCheck2 },
    { id: 'audit' as PageId, label: 'Audit Log', icon: ScrollText },
    { id: 'security' as PageId, label: 'Security & Boundaries', icon: ShieldCheck },
    { id: 'architecture' as PageId, label: 'Architecture Map', icon: GitFork },
  ];

  return (
    <aside className="w-64 bg-[#0D1322] border-r border-slate-800/90 flex flex-col h-screen shrink-0 select-none">
      {/* Brand Header */}
      <div className="p-5 border-b border-slate-800/80">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-indigo-500 to-indigo-700 flex items-center justify-center shadow-md shadow-indigo-950/60 border border-indigo-400/30">
            <BrainCircuit className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-base font-bold text-white tracking-tight flex items-center gap-1.5">
              LM-BRAIN
            </h1>
            <p className="text-[11px] font-medium text-slate-400 tracking-wide uppercase">
              Autonomous AI Workforce
            </p>
          </div>
        </div>
      </div>

      {/* Active Run Shortcut (if any) */}
      {activeRunId && (
        <div className="px-3 pt-3">
          <button
            onClick={() => onNavigate('live-run')}
            className={`w-full text-left p-2.5 rounded-lg border transition-all ${
              currentPage === 'live-run'
                ? 'bg-indigo-950/80 border-indigo-500/80 text-white shadow-sm shadow-indigo-900/40'
                : 'bg-slate-900/70 border-slate-800 text-slate-300 hover:border-slate-700'
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="text-[10px] uppercase font-mono font-semibold tracking-wider text-indigo-400 flex items-center gap-1.5">
                <Activity className={`w-3 h-3 ${isRunActive ? 'animate-spin text-indigo-400' : 'text-slate-400'}`} />
                {isRunActive ? 'Active Live Run' : 'Current Run View'}
              </span>
              <span className="text-xs font-mono font-bold text-slate-200">{activeRunId}</span>
            </div>
            <div className="text-xs text-slate-400 truncate mt-1">Live Control & Pipeline</div>
          </button>
        </div>
      )}

      {/* Main Navigation */}
      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
        <div className="px-3 pb-2 text-[10px] font-mono font-bold tracking-widest text-slate-500 uppercase">
          Workforce Control
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentPage === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                isActive
                  ? 'bg-indigo-600/20 text-indigo-200 border border-indigo-500/40 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <div className="flex items-center gap-2.5">
                <Icon className={`w-4 h-4 ${isActive ? 'text-indigo-400' : 'text-slate-400'}`} />
                <span>{item.label}</span>
              </div>
              {item.badge && (
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700 font-mono">
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* System Footer Status */}
      <div className="p-4 border-t border-slate-800/80 bg-[#0B0F19]/60">
        <div className="rounded-lg bg-slate-900/90 border border-slate-800 p-3 space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-400 font-mono text-[11px]">System Status</span>
            <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-400 font-mono">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              Operational
            </span>
          </div>
          <div className="text-[10px] text-slate-400 font-mono flex items-center justify-between">
            <span>Control Loop:</span>
            <span className="text-slate-300">Bounded (20 Max)</span>
          </div>
          <div className="text-[10px] text-slate-400 font-mono flex items-center justify-between">
            <span>Recovery Budget:</span>
            <span className="text-slate-300">3 Attempts</span>
          </div>
        </div>
      </div>
    </aside>
  );
};
