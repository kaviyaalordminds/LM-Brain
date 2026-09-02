'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { Dialog } from '../ui/Dialog';
import { NAV_ITEMS } from '../layout/NavigationDock';
import {
  Search,
  Play,
  Pause,
  RotateCcw,
  XCircle,
  Activity,
  Cpu,
  Layers,
  Users,
  Box,
  Brain,
  ListTree,
  Settings,
} from 'lucide-react';
import { orchestratorApi } from '../../lib/api/orchestrator';

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  activeExecutionId?: string | null;
  onNewExecutionClick?: () => void;
}

export const CommandPalette: React.FC<CommandPaletteProps> = ({
  isOpen,
  onClose,
  activeExecutionId,
  onNewExecutionClick,
}) => {
  const router = useRouter();
  const [query, setQuery] = useState('');
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  const actions = useMemo(() => {
    const list = [
      {
        id: 'new_exec',
        title: 'New Execution Task',
        desc: 'Submit a new natural language task to Planner and Specialists',
        icon: Play,
        action: () => {
          onClose();
          onNewExecutionClick?.();
        },
      },
      ...NAV_ITEMS.map((item) => ({
        id: `nav_${item.id}`,
        title: `Navigate: ${item.name}`,
        desc: `Jump to ${item.name} (${item.path})`,
        icon: item.icon,
        action: () => {
          onClose();
          router.push(item.path);
        },
      })),
    ];

    if (activeExecutionId) {
      list.push(
        {
          id: 'pause_exec',
          title: `Pause Active Execution (${activeExecutionId.slice(0, 8)})`,
          desc: 'Temporarily halt execution scheduling',
          icon: Pause,
          action: async () => {
            try {
              await orchestratorApi.pauseExecution(activeExecutionId);
              setStatusMsg('Execution paused');
              setTimeout(onClose, 800);
            } catch (err: any) {
              setStatusMsg(`Error: ${err.message}`);
            }
          },
        },
        {
          id: 'resume_exec',
          title: `Resume Active Execution (${activeExecutionId.slice(0, 8)})`,
          desc: 'Continue paused workflow execution',
          icon: RotateCcw,
          action: async () => {
            try {
              await orchestratorApi.resumeExecution(activeExecutionId);
              setStatusMsg('Execution resumed');
              setTimeout(onClose, 800);
            } catch (err: any) {
              setStatusMsg(`Error: ${err.message}`);
            }
          },
        },
        {
          id: 'cancel_exec',
          title: `Cancel Active Execution (${activeExecutionId.slice(0, 8)})`,
          desc: 'Terminate running tasks and cancel downstream schedule',
          icon: XCircle,
          action: async () => {
            try {
              await orchestratorApi.cancelExecution(activeExecutionId);
              setStatusMsg('Execution cancelled');
              setTimeout(onClose, 800);
            } catch (err: any) {
              setStatusMsg(`Error: ${err.message}`);
            }
          },
        }
      );
    }

    return list;
  }, [activeExecutionId, onClose, onNewExecutionClick, router]);

  const filtered = useMemo(() => {
    const q = query.toLowerCase().trim();
    if (!q) return actions;
    return actions.filter(
      (a) => a.title.toLowerCase().includes(q) || a.desc.toLowerCase().includes(q)
    );
  }, [actions, query]);

  useEffect(() => {
    if (isOpen) {
      setQuery('');
      setStatusMsg(null);
    }
  }, [isOpen]);

  return (
    <Dialog isOpen={isOpen} onClose={onClose} title="Global Command Palette" maxWidth="max-w-xl">
      <div className="flex flex-col gap-3">
        {/* Search input */}
        <div className="relative flex items-center bg-space-950 border border-space-800 rounded-md px-3 py-2">
          <Search className="w-4 h-4 text-slate-400 mr-2" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type a command or page name..."
            className="w-full bg-transparent text-xs text-slate-100 placeholder-slate-500 font-mono-tech focus:outline-none"
            autoFocus
          />
          {query && (
            <button
              onClick={() => setQuery('')}
              className="text-[10px] text-slate-500 hover:text-slate-300 font-mono"
            >
              CLEAR
            </button>
          )}
        </div>

        {statusMsg && (
          <div className="p-2 text-xs font-mono-tech text-amber-300 bg-amber-950/40 border border-amber-800/60 rounded">
            {statusMsg}
          </div>
        )}

        {/* Action list */}
        <div className="max-h-80 overflow-y-auto space-y-1">
          {filtered.length === 0 ? (
            <div className="text-center py-6 text-xs text-slate-500 font-mono-tech">
              No matching commands
            </div>
          ) : (
            filtered.map((item) => {
              const Icon = item.icon;
              return (
                <button
                  key={item.id}
                  onClick={item.action}
                  className="w-full flex items-center justify-between p-2.5 rounded-md hover:bg-space-800 border border-transparent hover:border-space-700 transition-all text-left group"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-7 h-7 rounded bg-space-850 border border-space-750 flex items-center justify-center text-slate-400 group-hover:text-emerald-400 group-hover:border-emerald-500/40 transition-colors">
                      <Icon className="w-3.5 h-3.5" />
                    </div>
                    <div>
                      <div className="text-xs font-medium text-slate-200 group-hover:text-slate-100 font-mono-tech">
                        {item.title}
                      </div>
                      <div className="text-[11px] text-slate-400 leading-none mt-0.5">{item.desc}</div>
                    </div>
                  </div>
                  <span className="text-[10px] text-slate-600 group-hover:text-slate-400 font-mono">
                    ↵
                  </span>
                </button>
              );
            })
          )}
        </div>

        <div className="pt-2 border-t border-space-800/80 flex items-center justify-between text-[10px] text-slate-500 font-mono-tech">
          <span>Shortcuts: Press 1-8 for direct page jumps</span>
          <span>ESC to close</span>
        </div>
      </div>
    </Dialog>
  );
};
