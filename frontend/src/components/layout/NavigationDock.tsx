'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  Activity,
  Layers,
  Cpu,
  Users,
  Box,
  Brain,
  ListTree,
  Settings,
} from 'lucide-react';

export const NAV_ITEMS = [
  { id: '1', name: 'Control Center', path: '/', icon: Activity },
  { id: '2', name: 'Workspace', path: '/execution', icon: Layers },
  { id: '3', name: 'Planner', path: '/planner', icon: Cpu },
  { id: '4', name: 'Specialists', path: '/specialists', icon: Users },
  { id: '5', name: 'Artifacts', path: '/artifacts', icon: Box },
  { id: '6', name: 'Memory', path: '/memory', icon: Brain },
  { id: '7', name: 'Events', path: '/events', icon: ListTree },
  { id: '8', name: 'System', path: '/settings', icon: Settings },
];

export const NavigationDock: React.FC = () => {
  const pathname = usePathname();

  return (
    <nav aria-label="Main Navigation" className="flex items-center gap-1 bg-space-900/90 border border-space-800 p-1 rounded-lg backdrop-blur-md shadow-lg">
      {NAV_ITEMS.map((item) => {
        const isActive =
          item.path === '/'
            ? pathname === '/'
            : pathname.startsWith(item.path);
        const Icon = item.icon;

        return (
          <Link
            key={item.id}
            href={item.path}
            className={`group relative flex items-center gap-1.5 px-3 py-1.5 text-xs font-mono-tech rounded transition-all ${
              isActive
                ? 'bg-space-800 text-slate-100 font-semibold border border-space-700 shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-space-850/80 border border-transparent'
            }`}
          >
            <Icon className={`w-3.5 h-3.5 transition-colors ${isActive ? 'text-emerald-400' : 'text-slate-400 group-hover:text-slate-200'}`} />
            <span className="hidden md:inline">{item.name}</span>
            <span className="hidden lg:inline text-[9px] text-slate-600 group-hover:text-slate-400 font-mono">
              {item.id}
            </span>
          </Link>
        );
      })}
    </nav>
  );
};
