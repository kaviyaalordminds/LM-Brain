'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  Database,
  Search,
  FileCheck2,
  Sparkles,
  Globe,
  Share2,
  HardDriveDownload,
  ShieldCheck,
  History,
  Activity,
  Terminal,
  Settings,
  Cpu,
  FolderTree,
  ExternalLink
} from 'lucide-react';

interface NavItem {
  name: string;
  href: string;
  icon: React.ElementType;
}

interface NavSection {
  title: string;
  items: NavItem[];
}

const NAV_SECTIONS: NavSection[] = [
  {
    title: 'CORE',
    items: [
      { name: 'Overview', href: '/', icon: LayoutDashboard },
    ],
  },
  {
    title: 'KNOWLEDGE',
    items: [
      { name: 'Obsidian Vault', href: '/knowledge/vault', icon: FolderTree },
      { name: 'Search', href: '/knowledge/search', icon: Search },
      { name: 'Retrieval', href: '/knowledge/retrieval', icon: FileCheck2 },
      { name: 'Knowledge Context', href: '/knowledge/context', icon: Sparkles },
    ],
  },
  {
    title: 'RESEARCH',
    items: [
      { name: 'Research', href: '/research', icon: Globe },
      { name: 'Sources', href: '/research/sources', icon: Share2 },
    ],
  },
  {
    title: 'MEMORY OPERATIONS',
    items: [
      { name: 'Store', href: '/operations/store', icon: HardDriveDownload },
      { name: 'Validation', href: '/operations/validation', icon: ShieldCheck },
      { name: 'History', href: '/operations/history', icon: History },
    ],
  },
  {
    title: 'SYSTEM',
    items: [
      { name: 'Health', href: '/system/health', icon: Activity },
      { name: 'Events', href: '/system/events', icon: Terminal },
      { name: 'Settings', href: '/system/settings', icon: Settings },
    ],
  },
];

export const Sidebar: React.FC = () => {
  const pathname = usePathname();

  return (
    <aside className="w-64 bg-[#090D15] border-r border-slate-800/80 flex flex-col shrink-0 min-h-screen select-none">
      {/* Product Branding */}
      <div className="p-5 border-b border-slate-800/80">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-sky-500/20 to-indigo-500/20 border border-sky-500/30 flex items-center justify-center text-sky-400 shadow-[0_0_12px_rgba(56,189,248,0.2)]">
            <Cpu className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-sm font-bold text-white tracking-wide flex items-center gap-1.5">
              MEMORY AGENT
              <span className="text-[9px] px-1.5 py-0.2 rounded font-mono bg-sky-500/10 text-sky-400 border border-sky-500/20">
                PROD
              </span>
            </h1>
            <p className="text-[10px] text-slate-400 font-mono mt-0.5">Control Plane &bull; :8001</p>
          </div>
        </div>
      </div>

      {/* Navigation Links */}
      <div className="flex-1 px-3 py-4 space-y-6 overflow-y-auto">
        {NAV_SECTIONS.map((sec) => (
          <div key={sec.title} className="space-y-1">
            <div className="px-3 text-[10px] font-mono uppercase tracking-wider text-slate-500 font-bold">
              {sec.title}
            </div>
            <div className="space-y-0.5">
              {sec.items.map((item) => {
                const Icon = item.icon;
                const isActive = pathname === item.href;

                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                      isActive
                        ? 'bg-sky-500/15 text-sky-300 border border-sky-500/30 font-semibold shadow-sm'
                        : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
                    }`}
                  >
                    <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-sky-400' : 'text-slate-500'}`} />
                    <span>{item.name}</span>
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {/* Provenance Badge */}
      <div className="p-4 border-t border-slate-800/80 bg-[#0B0F17]/60">
        <div className="p-2.5 rounded-xl bg-slate-950/80 border border-slate-800/80 space-y-1.5 text-[10px] font-mono">
          <div className="flex items-center justify-between text-slate-400">
            <span className="flex items-center gap-1">
              <Database className="w-3 h-3 text-purple-400" />
              <span>Obsidian:</span>
            </span>
            <span className="text-purple-300 font-bold">SOURCE OF TRUTH</span>
          </div>
          <div className="flex items-center justify-between text-slate-400">
            <span className="flex items-center gap-1">
              <Cpu className="w-3 h-3 text-sky-400" />
              <span>Memory:</span>
            </span>
            <span className="text-sky-300 font-bold">CONTROL PLANE</span>
          </div>
        </div>
      </div>
    </aside>
  );
};
