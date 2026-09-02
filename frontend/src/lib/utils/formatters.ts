import { ExecutionStatus, StepLifecycle, EventType } from '../types';

export function truncateId(id?: string | null, length: number = 8): string {
  if (!id) return '---';
  if (id.length <= length) return id;
  return `${id.slice(0, length)}...`;
}

export function formatTimestamp(isoString?: string | null): string {
  if (!isoString) return '--:--:--';
  try {
    const d = new Date(isoString);
    if (isNaN(d.getTime())) return isoString;
    const hours = d.getHours().toString().padStart(2, '0');
    const mins = d.getMinutes().toString().padStart(2, '0');
    const secs = d.getSeconds().toString().padStart(2, '0');
    const ms = d.getMilliseconds().toString().padStart(3, '0');
    return `${hours}:${mins}:${secs}.${ms}`;
  } catch {
    return isoString;
  }
}

export function formatDuration(startedAt?: string | null, completedAt?: string | null): string {
  if (!startedAt) return '0.0s';
  try {
    const start = new Date(startedAt).getTime();
    const end = completedAt ? new Date(completedAt).getTime() : Date.now();
    const diffMs = Math.max(0, end - start);
    if (diffMs < 1000) return `${diffMs}ms`;
    const secs = (diffMs / 1000).toFixed(1);
    if (Number(secs) < 60) return `${secs}s`;
    const mins = Math.floor(Number(secs) / 60);
    const remSecs = (Number(secs) % 60).toFixed(0);
    return `${mins}m ${remSecs}s`;
  } catch {
    return '--';
  }
}

export function getStatusTheme(status?: ExecutionStatus | StepLifecycle | string | null): {
  bg: string;
  text: string;
  border: string;
  dot: string;
  label: string;
} {
  const s = (status || '').toUpperCase();
  switch (s) {
    case 'RUNNING':
      return {
        bg: 'bg-emerald-950/40',
        text: 'text-emerald-400',
        border: 'border-emerald-700/60',
        dot: 'bg-emerald-400 animate-pulse',
        label: 'RUNNING',
      };
    case 'COMPLETED':
      return {
        bg: 'bg-emerald-950/30',
        text: 'text-emerald-300',
        border: 'border-emerald-800/40',
        dot: 'bg-emerald-400',
        label: 'COMPLETED',
      };
    case 'PLANNING':
    case 'PLANNED':
      return {
        bg: 'bg-cyan-950/40',
        text: 'text-cyan-400',
        border: 'border-cyan-700/60',
        dot: 'bg-cyan-400 animate-pulse',
        label: s,
      };
    case 'DISPATCHED':
    case 'QUEUED':
    case 'READY':
      return {
        bg: 'bg-sky-950/40',
        text: 'text-sky-400',
        border: 'border-sky-800/50',
        dot: 'bg-sky-400',
        label: s,
      };
    case 'VERIFYING':
      return {
        bg: 'bg-purple-950/40',
        text: 'text-purple-400',
        border: 'border-purple-700/60',
        dot: 'bg-purple-400 animate-pulse',
        label: 'VERIFYING',
      };
    case 'PAUSED':
    case 'RECOVERING':
    case 'RETRY_SCHEDULED':
      return {
        bg: 'bg-amber-950/40',
        text: 'text-amber-400',
        border: 'border-amber-700/60',
        dot: 'bg-amber-400 animate-pulse',
        label: s,
      };
    case 'BLOCKED':
      return {
        bg: 'bg-orange-950/40',
        text: 'text-orange-400',
        border: 'border-orange-800/60',
        dot: 'bg-orange-400',
        label: 'BLOCKED',
      };
    case 'FAILED':
      return {
        bg: 'bg-rose-950/40',
        text: 'text-rose-400',
        border: 'border-rose-800/60',
        dot: 'bg-rose-400',
        label: 'FAILED',
      };
    case 'CANCELLED':
    case 'SKIPPED':
      return {
        bg: 'bg-slate-900',
        text: 'text-slate-400',
        border: 'border-slate-800',
        dot: 'bg-slate-500',
        label: s,
      };
    default:
      return {
        bg: 'bg-space-850',
        text: 'text-slate-400',
        border: 'border-space-800',
        dot: 'bg-slate-500',
        label: s || 'PENDING',
      };
  }
}

export function getEventSeverity(eventType: EventType | string): 'info' | 'warning' | 'error' | 'success' {
  const t = eventType.toUpperCase();
  if (t.includes('FAILED')) return 'error';
  if (t.includes('RETRY') || t.includes('BLOCKED') || t.includes('PAUSED')) return 'warning';
  if (t.includes('COMPLETED') || t.includes('PASSED')) return 'success';
  return 'info';
}
