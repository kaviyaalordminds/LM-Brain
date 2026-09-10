import React from 'react';
import { OrchestrationStatus, StageStatus } from '../../types';

interface StatusIndicatorProps {
  status: OrchestrationStatus | StageStatus;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
  className?: string;
}

export const StatusIndicator: React.FC<StatusIndicatorProps> = ({
  status,
  size = 'md',
  showLabel = true,
  className = '',
}) => {
  let color = 'bg-slate-400';
  let pulse = false;
  let label = status;
  let textColor = 'text-slate-300';

  switch (status) {
    case 'COMPLETED':
      color = 'bg-emerald-500';
      textColor = 'text-emerald-400';
      label = 'COMPLETED';
      break;
    case 'RUNNING':
    case 'PERCEIVING':
    case 'PLANNING':
    case 'VALIDATING':
    case 'SELECTING_CAPABILITIES':
    case 'EXECUTING':
    case 'OBSERVING':
    case 'VERIFYING':
      color = 'bg-indigo-500';
      textColor = 'text-indigo-400';
      pulse = true;
      label = status === 'RUNNING' ? 'RUNNING' : status;
      break;
    case 'RECOVERING':
    case 'REPLANNING':
      color = 'bg-amber-500';
      textColor = 'text-amber-400';
      pulse = true;
      label = 'RECOVERING';
      break;
    case 'FAILED':
      color = 'bg-rose-500';
      textColor = 'text-rose-400';
      label = 'FAILED';
      break;
    case 'BLOCKED':
      color = 'bg-orange-500';
      textColor = 'text-orange-400';
      label = 'BLOCKED';
      break;
    case 'WAITING':
    case 'RECEIVED':
      color = 'bg-slate-500';
      textColor = 'text-slate-400';
      label = 'WAITING';
      break;
    case 'SKIPPED':
      color = 'bg-slate-600';
      textColor = 'text-slate-500';
      label = 'SKIPPED';
      break;
    case 'PARTIAL':
      color = 'bg-amber-400';
      textColor = 'text-amber-300';
      label = 'PARTIAL';
      break;
  }

  const dotSizes = {
    sm: 'w-1.5 h-1.5',
    md: 'w-2 h-2',
    lg: 'w-2.5 h-2.5',
  };

  const textSizes = {
    sm: 'text-xs',
    md: 'text-xs font-mono font-medium',
    lg: 'text-sm font-mono font-semibold',
  };

  return (
    <div className={`inline-flex items-center gap-2 ${className}`}>
      <span className="relative flex items-center justify-center">
        {pulse && (
          <span className={`absolute inline-flex h-full w-full rounded-full ${color} opacity-75 animate-ping`} />
        )}
        <span className={`relative inline-flex rounded-full ${color} ${dotSizes[size]}`} />
      </span>
      {showLabel && <span className={`${textColor} ${textSizes[size]}`}>{label}</span>}
    </div>
  );
};
