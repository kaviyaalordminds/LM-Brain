'use client';

import React, { useState, useMemo } from 'react';
import { ExecutionEvent } from '../../lib/types';
import { formatTimestamp, getEventSeverity } from '../../lib/utils/formatters';
import { Search, ChevronDown, ChevronRight, Activity, Filter, AlertCircle, CheckCircle2, AlertTriangle, Info } from 'lucide-react';

interface LiveEventStreamProps {
  events: ExecutionEvent[];
  className?: string;
  maxHeight?: string;
  title?: string;
}

export const LiveEventStream: React.FC<LiveEventStreamProps> = ({
  events,
  className = '',
  maxHeight = 'max-h-96',
  title = 'Live Event Stream',
}) => {
  const [filterType, setFilterType] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [expandedEventId, setExpandedEventId] = useState<string | null>(null);

  const eventTypes = useMemo(() => {
    const types = new Set(events.map((e) => e.event_type));
    return ['ALL', ...Array.from(types)];
  }, [events]);

  const filteredEvents = useMemo(() => {
    return events.filter((e) => {
      const matchesType = filterType === 'ALL' || e.event_type === filterType;
      const matchesSearch =
        !searchQuery ||
        e.event_type.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (e.step_id && e.step_id.toLowerCase().includes(searchQuery.toLowerCase())) ||
        JSON.stringify(e.payload).toLowerCase().includes(searchQuery.toLowerCase());
      return matchesType && matchesSearch;
    });
  }, [events, filterType, searchQuery]);

  return (
    <div className={`bg-space-900 border border-space-800 rounded-lg overflow-hidden flex flex-col shadow-md ${className}`}>
      {/* Header with Title & Event Count */}
      <div className="flex flex-wrap items-center justify-between p-3 bg-space-850 border-b border-space-800 gap-2">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-emerald-400" />
          <h3 className="text-xs font-bold font-mono-tech uppercase tracking-wider text-slate-100">
            {title}
          </h3>
          <span className="text-[10px] font-mono-tech px-2 py-0.5 rounded bg-space-800 text-slate-400 border border-space-750">
            {filteredEvents.length} / {events.length}
          </span>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-2">
          <div className="relative flex items-center bg-space-950 border border-space-800 rounded px-2 py-1">
            <Search className="w-3 h-3 text-slate-500 mr-1.5" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Filter events..."
              className="bg-transparent text-[11px] text-slate-200 placeholder-slate-500 font-mono-tech focus:outline-none w-28 sm:w-36"
            />
          </div>

          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="bg-space-950 border border-space-800 rounded px-2 py-1 text-[11px] font-mono-tech text-slate-300 focus:outline-none"
          >
            {eventTypes.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Events List */}
      <div className={`overflow-y-auto p-2 space-y-1.5 ${maxHeight}`}>
        {filteredEvents.length === 0 ? (
          <div className="text-center py-8 text-xs font-mono-tech text-slate-500">
            No events recorded yet
          </div>
        ) : (
          filteredEvents.map((evt) => {
            const severity = getEventSeverity(evt.event_type);
            const isExpanded = expandedEventId === evt.event_id;

            let badgeClass = 'text-slate-400 bg-space-800/80 border-space-700';
            let Icon = Info;
            if (severity === 'error') {
              badgeClass = 'text-rose-400 bg-rose-950/40 border-rose-800/60';
              Icon = AlertCircle;
            } else if (severity === 'warning') {
              badgeClass = 'text-amber-400 bg-amber-950/40 border-amber-800/60';
              Icon = AlertTriangle;
            } else if (severity === 'success') {
              badgeClass = 'text-emerald-400 bg-emerald-950/40 border-emerald-800/60';
              Icon = CheckCircle2;
            }

            return (
              <div
                key={evt.event_id}
                className="rounded border border-space-800/80 bg-space-950 hover:bg-space-850/60 transition-colors text-xs font-mono-tech"
              >
                <div
                  onClick={() => setExpandedEventId(isExpanded ? null : evt.event_id)}
                  className="p-2 flex items-center justify-between cursor-pointer gap-2"
                >
                  <div className="flex items-center gap-2 truncate">
                    <button className="text-slate-500 hover:text-slate-300">
                      {isExpanded ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
                    </button>
                    <span className={`px-1.5 py-0.5 rounded text-[10px] border flex items-center gap-1 ${badgeClass}`}>
                      <Icon className="w-2.5 h-2.5" />
                      {evt.event_type}
                    </span>
                    {evt.step_id && (
                      <span className="text-[11px] text-slate-300 truncate">
                        {evt.step_id}
                      </span>
                    )}
                  </div>

                  <span className="text-[10px] text-slate-500 shrink-0">
                    {formatTimestamp(evt.timestamp)}
                  </span>
                </div>

                {/* Expanded Payload view */}
                {isExpanded && (
                  <div className="px-3 pb-3 pt-1 border-t border-space-850/80">
                    <div className="text-[10px] text-slate-500 mb-1">Payload:</div>
                    <pre className="p-2 rounded bg-space-900 border border-space-800 text-[11px] text-slate-300 overflow-x-auto whitespace-pre-wrap">
                      {JSON.stringify(evt.payload, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
