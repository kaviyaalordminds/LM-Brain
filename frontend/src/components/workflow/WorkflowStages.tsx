'use client';

import React from 'react';
import {
  FileText,
  Eye,
  Settings,
  Database,
  Calendar,
  Layers,
  ShieldCheck,
  Users,
  Activity,
  CheckSquare,
  AlertTriangle,
  RotateCcw,
  Sparkles
} from 'lucide-react';
import { cn } from '@/lib/utils/cn';

interface WorkflowStagesProps {
  currentStep: number;
}

export function WorkflowStages({ currentStep }: WorkflowStagesProps) {
  // 12 key stages of the LOCKED company architecture
  const stages = [
    { id: 'input', name: 'Input Parse', icon: FileText, desc: 'Accept instructions/files' },
    { id: 'perception', name: 'Perception', icon: Eye, desc: 'Identify system requirements & goals' },
    { id: 'orchestrator', name: 'Master Orchestrator', icon: Settings, desc: 'Initialize task context state' },
    { id: 'memory', name: 'Obsidian Vault', icon: Database, desc: 'Query company guidelines & standards' },
    { id: 'planner', name: 'Planner', icon: Calendar, desc: 'Draft steps & dependency list' },
    { id: 'capability', name: 'Capability Manager', icon: Layers, desc: 'Select Specialist Agents & Twins' },
    { id: 'security', name: 'Guardrail & Security', icon: ShieldCheck, desc: 'Evaluate permission boundaries' },
    { id: 'workforce', name: 'Workforce Hub', icon: Users, desc: 'Spawn and assign active workers' },
    { id: 'execution', name: 'Execution', icon: Activity, desc: 'Write code files & run scripts' },
    { id: 'verification', name: 'Verification', icon: CheckSquare, desc: 'Run unit & integration tests' },
    { id: 'reflection', name: 'Reflection / Re-Plan', icon: AlertTriangle, desc: 'Fix failures & update planner steps' },
    { id: 'success', name: 'Checkpoint & Sync', icon: Sparkles, desc: 'Write output back to Obsidian Memory' }
  ];

  const getStageStatus = (stageId: string): 'pending' | 'running' | 'completed' | 'failed' | 'retrying' => {
    if (currentStep === -1) return 'pending';

    switch (stageId) {
      case 'input':
        return currentStep >= 0 ? 'completed' : 'pending';
      case 'perception':
        return currentStep > 0 ? 'completed' : currentStep === 1 ? 'running' : 'pending';
      case 'orchestrator':
        return currentStep > 1 ? 'completed' : currentStep === 1 ? 'running' : 'pending';
      case 'memory':
        return currentStep > 2 ? 'completed' : currentStep === 2 ? 'running' : 'pending';
      case 'planner':
        if (currentStep === 15) return 'retrying';
        return currentStep > 3 ? 'completed' : currentStep === 3 ? 'running' : 'pending';
      case 'capability':
        return currentStep > 4 ? 'completed' : currentStep === 4 ? 'running' : 'pending';
      case 'security':
        return currentStep > 5 ? 'completed' : currentStep === 5 ? 'running' : 'pending';
      case 'workforce':
        return currentStep >= 19 ? 'completed' : (currentStep >= 6 && currentStep <= 8) ? 'running' : currentStep > 8 ? 'completed' : 'pending';
      case 'execution':
        if (currentStep === 16) return 'retrying';
        return currentStep > 16 ? 'completed' : (currentStep >= 9 && currentStep <= 12) ? 'running' : currentStep > 12 ? 'completed' : 'pending';
      case 'verification':
        if (currentStep === 13) return 'failed';
        if (currentStep === 17) return 'retrying';
        return currentStep >= 18 ? 'completed' : currentStep === 12 ? 'running' : 'pending';
      case 'reflection':
        if (currentStep === 13) return 'failed';
        if (currentStep === 14) return 'running';
        return currentStep > 14 ? 'completed' : 'pending';
      case 'success':
        return currentStep === 21 || currentStep === 22 ? 'completed' : currentStep === 20 ? 'running' : 'pending';
      default:
        return 'pending';
    }
  };

  return (
    <div className="space-y-3 select-none">
      <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
        Workforce Execution Pipeline
      </h3>
      
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-2">
        {stages.map((stage) => {
          const status = getStageStatus(stage.id);
          const Icon = stage.icon;

          return (
            <div
              key={stage.id}
              className={cn(
                "border rounded-lg p-2.5 flex flex-col justify-between min-h-[90px] transition-all duration-300 relative overflow-hidden",
                status === 'pending' && "bg-[#070b13]/55 border-slate-900 text-slate-600",
                status === 'running' && "bg-indigo-950/20 border-indigo-500/50 text-indigo-300 premium-glow-indigo animate-pulse-slow",
                status === 'completed' && "bg-[#0c1322] border-slate-800 text-slate-300",
                status === 'failed' && "bg-rose-950/20 border-rose-500/50 text-rose-300 premium-glow-rose",
                status === 'retrying' && "bg-amber-950/20 border-amber-500/50 text-amber-300 animate-pulse"
              )}
            >
              {/* Top Row: Icon + status dot */}
              <div className="flex items-start justify-between">
                <div className={cn(
                  "p-1 rounded-md border",
                  status === 'pending' && "bg-slate-900 border-slate-800 text-slate-500",
                  status === 'running' && "bg-indigo-950 border-indigo-500/30 text-indigo-400",
                  status === 'completed' && "bg-slate-900 border-slate-800 text-indigo-400",
                  status === 'failed' && "bg-rose-950 border-rose-500/30 text-rose-400",
                  status === 'retrying' && "bg-amber-950 border-amber-500/30 text-amber-400"
                )}>
                  <Icon className="h-4 w-4" />
                </div>
                
                {/* Status indicator tag */}
                <span className={cn(
                  "h-1.5 w-1.5 rounded-full",
                  status === 'pending' && "bg-slate-700",
                  status === 'running' && "bg-indigo-400 animate-ping",
                  status === 'completed' && "bg-emerald-400",
                  status === 'failed' && "bg-rose-500",
                  status === 'retrying' && "bg-amber-400 animate-pulse"
                )}></span>
              </div>

              {/* Bottom text */}
              <div className="mt-2">
                <h4 className="text-[11px] font-bold truncate leading-none">
                  {stage.name}
                </h4>
                <span className="text-[9px] text-slate-500 block truncate mt-0.5" title={stage.desc}>
                  {stage.desc}
                </span>
              </div>

              {/* Reflection Failure Overlay visual hook */}
              {stage.id === 'reflection' && status === 'failed' && (
                <div className="absolute inset-0 bg-rose-950/10 flex items-center justify-center pointer-events-none">
                  <div className="w-full h-0.5 bg-rose-500/50 absolute top-1/2"></div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
