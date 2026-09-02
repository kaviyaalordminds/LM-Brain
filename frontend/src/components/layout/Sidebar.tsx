'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  Terminal,
  FolderKanban,
  Users,
  Layers,
  Activity,
  Database,
  Cpu,
  Settings,
  Menu,
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
  Zap
} from 'lucide-react';
import { cn } from '@/lib/utils/cn';

interface SidebarProps {
  isCollapsed: boolean;
  setIsCollapsed: (collapsed: boolean) => void;
}

export function Sidebar({ isCollapsed, setIsCollapsed }: SidebarProps) {
  const pathname = usePathname();

  const navItems = [
    { name: 'Command Center', href: '/', icon: Terminal },
    { name: 'Projects', href: '/projects', icon: FolderKanban },
    { name: 'Specialist Agents', href: '/agents', icon: Users },
    { name: 'Executive Twins', href: '/twins', icon: Layers },
    { name: 'Activity Log', href: '/activity', icon: Activity },
    { name: 'Knowledge / Memory', href: '/memory', icon: Database },
    { name: 'Model Inventory', href: '/models', icon: Cpu },
    { name: 'Settings', href: '/settings', icon: Settings },
  ];

  return (
    <aside
      className={cn(
        "flex flex-col border-r border-slate-800 bg-[#070b13] transition-all duration-300 ease-in-out select-none",
        isCollapsed ? "w-16" : "w-64"
      )}
    >
      {/* Top Brand Logo */}
      <div className="flex h-16 items-center justify-between px-4 border-b border-slate-800">
        <Link href="/" className="flex items-center gap-3 overflow-hidden">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-gradient-to-tr from-indigo-600 to-blue-500 text-white shadow-lg shadow-indigo-500/20">
            <Zap className="h-5 w-5" />
          </div>
          {!isCollapsed && (
            <div className="flex flex-col">
              <span className="text-sm font-semibold tracking-wider text-slate-100 uppercase">
                Lordminds
              </span>
              <span className="text-[10px] text-indigo-400 font-mono tracking-tight uppercase leading-none">
                AI Workforce
              </span>
            </div>
          )}
        </Link>
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="rounded-md p-1.5 text-slate-400 hover:bg-slate-800 hover:text-slate-100 transition-colors focus-ring"
          aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {isCollapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </button>
      </div>

      {/* Nav Links */}
      <nav className="flex-1 space-y-1 px-2 py-4">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "group flex items-center rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-150 focus-ring relative",
                isActive
                  ? "bg-slate-800/80 text-white border-l-2 border-indigo-500"
                  : "text-slate-400 hover:bg-slate-900 hover:text-slate-200"
              )}
              title={isCollapsed ? item.name : undefined}
            >
              <Icon className={cn("h-5 w-5 shrink-0 transition-transform duration-200 group-hover:scale-105", isCollapsed ? "mx-auto" : "mr-3")} />
              {!isCollapsed && <span>{item.name}</span>}
              {isCollapsed && (
                <div className="absolute left-full ml-2 hidden rounded-md bg-slate-950 border border-slate-800 px-2 py-1 text-xs text-slate-100 shadow-md group-hover:block z-50 whitespace-nowrap">
                  {item.name}
                </div>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Bottom Status bar widgets */}
      <div className="border-t border-slate-800 p-4 space-y-3 bg-[#05080f] overflow-hidden shrink-0">
        {!isCollapsed ? (
          <>
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-400">Environment</span>
              <span className="flex items-center gap-1.5 font-mono text-[10px] text-emerald-400 font-semibold bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                LOCAL HOST
              </span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-400">Security Gate</span>
              <span className="flex items-center gap-1 text-indigo-400">
                <ShieldCheck className="h-3.5 w-3.5" /> Secure
              </span>
            </div>
            <div className="flex items-center gap-3 pt-2">
              <div className="h-8 w-8 rounded-full bg-slate-800 flex items-center justify-center text-xs font-semibold text-indigo-300">
                IN
              </div>
              <div className="flex flex-col min-w-0">
                <span className="text-xs font-medium text-slate-200 truncate">Intern Developer</span>
                <span className="text-[10px] text-slate-500 truncate">Phase: Frontend Found.</span>
              </div>
            </div>
          </>
        ) : (
          <div className="flex flex-col gap-3 items-center">
            <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" title="System status: Local Online"></span>
            <span title="Security Gate status: Active">
              <ShieldCheck className="h-4 w-4 text-indigo-400" />
            </span>
            <div className="h-6 w-6 rounded-full bg-slate-800 flex items-center justify-center text-[10px] font-semibold text-indigo-300">
              IN
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}
