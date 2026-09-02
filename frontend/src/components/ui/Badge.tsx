import React from 'react';
import { getStatusTheme } from '../../lib/utils/formatters';

interface BadgeProps {
  status?: string | null;
  label?: string;
  size?: 'sm' | 'md';
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({ status, label, size = 'sm', className = '' }) => {
  const theme = getStatusTheme(status);
  const text = label || theme.label;
  const sizeClasses = size === 'sm' ? 'px-2 py-0.5 text-[10px]' : 'px-2.5 py-1 text-xs';

  return (
    <span
      className={`inline-flex items-center gap-1.5 font-mono-tech uppercase font-medium rounded border ${theme.bg} ${theme.text} ${theme.border} ${sizeClasses} ${className}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${theme.dot}`} />
      {text}
    </span>
  );
};
