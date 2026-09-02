'use client';

import React from 'react';
import { TrustState } from '../../lib/types';
import { ShieldCheck, ShieldAlert, Clock, CheckCircle2, XCircle, Search } from 'lucide-react';

interface TrustBadgeProps {
  state: TrustState | string;
  size?: 'sm' | 'md';
}

export const TrustBadge: React.FC<TrustBadgeProps> = ({ state, size = 'sm' }) => {
  const s = (state || 'UNVERIFIED').toUpperCase();

  let bg = 'bg-slate-900 border-slate-700 text-slate-400';
  let Icon = Clock;

  switch (s) {
    case 'APPROVED':
      bg = 'bg-emerald-950/60 border-emerald-700 text-emerald-300';
      Icon = CheckCircle2;
      break;
    case 'VALIDATED':
      bg = 'bg-cyan-950/60 border-cyan-700 text-cyan-300';
      Icon = ShieldCheck;
      break;
    case 'RETRIEVED':
      bg = 'bg-sky-950/60 border-sky-800 text-sky-400';
      Icon = Search;
      break;
    case 'REJECTED':
      bg = 'bg-rose-950/60 border-rose-800 text-rose-300';
      Icon = XCircle;
      break;
    case 'PENDING':
      bg = 'bg-amber-950/60 border-amber-800 text-amber-300';
      Icon = Clock;
      break;
    default:
      bg = 'bg-space-900 border-space-800 text-slate-400';
      Icon = ShieldAlert;
      break;
  }

  const sizeClass = size === 'sm' ? 'px-2 py-0.5 text-[10px]' : 'px-2.5 py-1 text-xs';

  return (
    <span className={`inline-flex items-center gap-1.5 font-mono-tech uppercase font-bold rounded border ${bg} ${sizeClass}`}>
      <Icon className="w-3 h-3" />
      <span>{s}</span>
    </span>
  );
};
