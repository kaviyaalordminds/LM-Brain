import React from 'react';
import { Terminal } from 'lucide-react';

interface EmptyStateProps {
  title: string;
  description: string;
  action?: React.ReactNode;
  icon?: React.ReactNode;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  action,
  icon,
  className = '',
}) => {
  return (
    <div
      className={`flex flex-col items-center justify-center p-8 text-center border border-dashed border-space-800 rounded-lg bg-space-900/40 ${className}`}
    >
      <div className="w-10 h-10 rounded-md bg-space-850 border border-space-750 flex items-center justify-center text-slate-400 mb-3">
        {icon || <Terminal className="w-5 h-5" />}
      </div>
      <h3 className="text-sm font-semibold text-slate-200 font-mono-tech mb-1">{title}</h3>
      <p className="text-xs text-slate-400 max-w-sm mb-4 leading-normal">{description}</p>
      {action && <div>{action}</div>}
    </div>
  );
};
