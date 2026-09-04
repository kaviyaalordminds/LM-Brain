'use client';

import React from 'react';

interface StatusCardProps {
  title: string;
  value: string | number;
  subtext: string;
  status: 'online' | 'offline' | 'warning' | 'neutral';
  icon: React.ElementType;
}

export const StatusCard: React.FC<StatusCardProps> = ({
  title,
  value,
  subtext,
  status,
  icon: Icon,
}) => {
  let statusBadge = 'bg-slate-800 text-slate-400 border-slate-700';
  let dotColor = 'bg-slate-400';

  if (status === 'online') {
    statusBadge = 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
    dotColor = 'bg-emerald-400';
  } else if (status === 'offline') {
    statusBadge = 'bg-rose-500/10 text-rose-400 border-rose-500/20';
    dotColor = 'bg-rose-400';
  } else if (status === 'warning') {
    statusBadge = 'bg-amber-500/10 text-amber-400 border-amber-500/20';
    dotColor = 'bg-amber-400';
  }

  return (
    <div className="p-4 rounded-2xl bg-[#0F1420] border border-slate-800/90 shadow-xl flex flex-col justify-between">
      <div className="flex items-start justify-between gap-2 mb-3">
        <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider font-semibold">
          {title}
        </span>
        <div className="w-7 h-7 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-center text-slate-400">
          <Icon className="w-3.5 h-3.5" />
        </div>
      </div>

      <div>
        <div className="flex items-center gap-2 mb-1">
          <span className={`w-2 h-2 rounded-full ${dotColor}`} />
          <span className="text-lg font-bold text-white font-sans tracking-tight">{value}</span>
        </div>
        <p className="text-[11px] text-slate-400 font-mono truncate">{subtext}</p>
      </div>
    </div>
  );
};
