import React, { useState } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  Filter,
  RefreshCw,
  ScrollText,
  Search,
  ShieldCheck,
  Zap,
} from 'lucide-react';
import { Badge } from '../components/common/Badge';
import { Card } from '../components/common/Card';
import { CodeBlock } from '../components/common/CodeBlock';
import { mockAuditEvents } from '../mock';
import { AuditEvent } from '../types';

export const AuditPage: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedEventType, setSelectedEventType] = useState<string>('ALL');

  const eventTypes = [
    'ALL',
    'ORCHESTRATION_STARTED',
    'PERCEPTION_COMPLETED',
    'KNOWLEDGE_RETRIEVED',
    'REASONING_COMPLETED',
    'PLAN_VALIDATED',
    'CAPABILITY_SELECTED',
    'SPECIALIST_DELEGATED',
    'EXECUTION_COMPLETED',
    'OBSERVATION_RECORDED',
    'VERIFICATION_COMPLETED',
    'MEMORY_WRITEBACK_COMPLETED',
    'ORCHESTRATION_COMPLETED',
  ];

  const filteredEvents = mockAuditEvents.filter((e) => {
    const matchesSearch =
      e.eventType.toLowerCase().includes(searchTerm.toLowerCase()) ||
      JSON.stringify(e.payload).toLowerCase().includes(searchTerm.toLowerCase());
    const matchesType = selectedEventType === 'ALL' || e.eventType === selectedEventType;
    return matchesSearch && matchesType;
  });

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="space-y-1">
        <h1 className="text-xl md:text-2xl font-bold text-white tracking-tight flex items-center gap-2">
          <ScrollText className="w-5 h-5 text-indigo-400" />
          System & Security Audit Log
        </h1>
        <p className="text-xs md:text-sm text-slate-400">
          Immutable, structured event log recording lifecycle state transitions with automatic credential scrubbing.
        </p>
      </div>

      {/* Audit Policy Banner */}
      <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 flex items-start gap-3 text-xs text-slate-300 font-mono">
        <ShieldCheck className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <span className="font-bold text-slate-200">
            AuditLogger Security Redaction Policy (AuditLogger._scrub_sensitive_data)
          </span>
          <p className="text-slate-400 leading-relaxed font-sans">
            All passwords, tokens, API secrets, and raw authentication credentials are automatically scrubbed and replaced with <code className="text-amber-400">[REDACTED]</code> prior to persistence.
          </p>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="p-4 rounded-xl border border-slate-800 bg-[#111827] flex flex-wrap items-center justify-between gap-4 text-xs">
        <div className="relative flex-1 min-w-[240px]">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search payload fields or event types..."
            className="w-full bg-[#080C14] border border-slate-700/80 rounded-lg pl-9 pr-3 py-2 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 font-sans"
          />
        </div>

        <div className="flex items-center gap-2 font-mono">
          <span className="text-slate-400">Event:</span>
          <select
            value={selectedEventType}
            onChange={(e) => setSelectedEventType(e.target.value)}
            className="bg-[#080C14] border border-slate-700 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-indigo-500 font-mono text-xs"
          >
            {eventTypes.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Audit Events Timeline List */}
      <div className="space-y-3">
        {filteredEvents.map((evt, idx) => (
          <div
            key={evt.eventId || idx}
            className="p-4 rounded-xl border border-slate-800 bg-[#111827] space-y-2 text-xs font-mono shadow-sm"
          >
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-2.5">
                <span className="w-6 h-6 rounded bg-indigo-950/80 border border-indigo-800/60 text-indigo-300 flex items-center justify-center font-bold text-[10px]">
                  {idx + 1}
                </span>
                <span className="font-bold text-slate-100 tracking-wide text-sm">
                  {evt.eventType}
                </span>
              </div>
              <div className="flex items-center gap-3 text-slate-400 text-[11px]">
                <span className="flex items-center gap-1">
                  <Clock className="w-3.5 h-3.5 text-slate-500" />
                  {evt.timestamp}
                </span>
                <Badge variant="default" size="sm">{evt.eventId}</Badge>
              </div>
            </div>

            <CodeBlock
              code={JSON.stringify(evt.payload, null, 2)}
              language="json"
              title="Scrubbed Audit Payload"
              maxHeight="max-h-48"
            />
          </div>
        ))}
      </div>
    </div>
  );
};
