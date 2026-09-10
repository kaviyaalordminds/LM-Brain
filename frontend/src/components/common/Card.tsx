import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  title?: React.ReactNode;
  subtitle?: React.ReactNode;
  headerAction?: React.ReactNode;
  footer?: React.ReactNode;
  badge?: React.ReactNode;
  icon?: React.ReactNode;
  variant?: 'default' | 'elevated' | 'bordered' | 'accent' | 'subtle';
}

export const Card: React.FC<CardProps> = ({
  children,
  className = '',
  title,
  subtitle,
  headerAction,
  footer,
  badge,
  icon,
  variant = 'default',
}) => {
  const variantStyles = {
    default: 'bg-[#111827] border-slate-800/80 shadow-sm',
    elevated: 'bg-[#131C2E] border-slate-800 shadow-md shadow-black/40',
    bordered: 'bg-[#0F172A]/70 border-slate-700/80',
    accent: 'bg-[#111827] border-indigo-900/50 shadow-sm shadow-indigo-950/20',
    subtle: 'bg-[#0B0F19] border-slate-800/60',
  };

  return (
    <div className={`rounded-xl border ${variantStyles[variant]} overflow-hidden ${className}`}>
      {(title || subtitle || headerAction || icon || badge) && (
        <div className="px-5 py-4 border-b border-slate-800/70 flex items-center justify-between gap-3 bg-slate-900/30">
          <div className="flex items-center gap-3 min-w-0">
            {icon && <span className="text-slate-400 shrink-0">{icon}</span>}
            <div className="min-w-0">
              {title && (
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-semibold text-slate-100 tracking-tight truncate">{title}</h3>
                  {badge && <span className="shrink-0">{badge}</span>}
                </div>
              )}
              {subtitle && <p className="text-xs text-slate-400 mt-0.5 truncate">{subtitle}</p>}
            </div>
          </div>
          {headerAction && <div className="shrink-0 flex items-center gap-2">{headerAction}</div>}
        </div>
      )}
      <div className="p-5">{children}</div>
      {footer && (
        <div className="px-5 py-3 border-t border-slate-800/70 bg-slate-900/40 text-xs text-slate-400">
          {footer}
        </div>
      )}
    </div>
  );
};
