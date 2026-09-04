'use client';

import React from 'react';
import { Terminal } from 'lucide-react';
import { OperationTimeline } from '@/components/OperationTimeline';

export default function EventsPage() {
  return (
    <div className="space-y-6">
      <div className="p-5 rounded-2xl bg-[#0F1420] border border-slate-800 shadow-xl space-y-1">
        <h1 className="text-base font-bold text-white tracking-wide">
          Real-Time Operations Event Stream
        </h1>
        <p className="text-xs text-slate-400 font-mono">
          Structured audit stream for memory layer calls
        </p>
      </div>

      <OperationTimeline events={[]} />
    </div>
  );
}
