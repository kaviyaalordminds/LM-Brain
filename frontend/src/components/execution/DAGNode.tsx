'use client';

import React from 'react';
import { PlanStep, StepLifecycle } from '../../lib/types';
import { getStatusTheme } from '../../lib/utils/formatters';
import { Badge } from '../ui/Badge';
import { Bot, ArrowRight, AlertTriangle, ShieldCheck, CheckCircle2, Clock } from 'lucide-react';

interface DAGNodeProps {
  step: PlanStep;
  status: StepLifecycle;
  attemptNumber?: number;
  isSelected?: boolean;
  onClick?: () => void;
  error?: string | null;
}

export const DAGNode: React.FC<DAGNodeProps> = ({
  step,
  status,
  attemptNumber,
  isSelected,
  onClick,
  error,
}) => {
  const theme = getStatusTheme(status);

  return (
    <div
      onClick={onClick}
      className={`group cursor-pointer relative p-3 rounded-lg border transition-all duration-150 text-left w-64 ${
        isSelected
          ? 'bg-space-800 border-sky-500 shadow-lg ring-1 ring-sky-500/50'
          : 'bg-space-900 hover:bg-space-850 border-space-800 hover:border-space-700'
      }`}
    >
      {/* Active pulse aura when running */}
      {status === 'RUNNING' && (
        <span className="absolute -top-1 -right-1 flex h-3 w-3">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
          <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500" />
        </span>
      )}

      {/* Header: Specialist + Step ID */}
      <div className="flex items-center justify-between gap-2 mb-1.5">
        <div className="flex items-center gap-1.5 overflow-hidden">
          <Bot className="w-3.5 h-3.5 text-slate-400 shrink-0" />
          <span className="text-[11px] font-mono-tech font-bold text-slate-200 truncate uppercase">
            {step.specialist}
          </span>
        </div>
        <Badge status={status} size="sm" />
      </div>

      {/* Step ID tag */}
      <div className="text-[10px] text-slate-500 font-mono-tech mb-2">
        {step.step_id}
      </div>

      {/* Description */}
      <p className="text-[11px] text-slate-300 line-clamp-2 mb-2 leading-relaxed">
        {step.description}
      </p>

      {/* Metadata footer */}
      <div className="flex items-center justify-between pt-2 border-t border-space-800/80 text-[10px] font-mono-tech text-slate-500">
        <div className="flex items-center gap-2">
          {attemptNumber !== undefined && attemptNumber > 0 && (
            <span className={status === 'FAILED' ? 'text-rose-400' : 'text-slate-400'}>
              Att: {attemptNumber}
            </span>
          )}
          {step.dependencies?.length > 0 && (
            <span title={`Depends on: ${step.dependencies.join(', ')}`}>
              Deps: {step.dependencies.length}
            </span>
          )}
        </div>

        {status === 'FAILED' && error && (
          <span className="text-rose-400 truncate max-w-[100px]" title={error}>
            {error.includes('MODEL_UNAVAILABLE') ? 'NO MODEL' : 'FAILED'}
          </span>
        )}
      </div>
    </div>
  );
};
