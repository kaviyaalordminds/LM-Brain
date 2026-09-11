import React from 'react';
import {
  AlertCircle,
  AlertTriangle,
  ArrowRight,
  Brain,
  CheckCircle2,
  Cpu,
  Layers,
  RefreshCw,
  RotateCcw,
  ShieldAlert,
  Sparkles,
  Terminal,
  Zap,
} from 'lucide-react';
import { RecoveryEvent } from '../../types';
import { Badge } from '../common/Badge';
import { Button } from '../common/Button';
import { RecoveryTimeline } from './RecoveryTimeline';

interface FailureRecoveryPanelProps {
  recoveryHistory?: RecoveryEvent[];
  onTriggerControlledFailure?: () => void;
  onTriggerRepeatedFailure?: () => void;
  isExecuting?: boolean;
}

export const FailureRecoveryPanel: React.FC<FailureRecoveryPanelProps> = ({
  recoveryHistory = [],
  onTriggerControlledFailure,
  onTriggerRepeatedFailure,
  isExecuting = false,
}) => {
  const hasRecovery = recoveryHistory.length > 0;
  const latestEvent = recoveryHistory[recoveryHistory.length - 1];

  return (
    <div className="rounded-2xl border border-slate-800 bg-[#0F172A] p-5 shadow-xl space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800/80 pb-3">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-amber-950/60 border border-amber-700/60 text-amber-400">
            <RefreshCw className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white tracking-tight flex items-center gap-2">
              Autonomous Failure & Bounded Recovery Subsystem
            </h3>
            <p className="text-xs text-slate-400">
              Deterministic Failure Observation &bull; Root Cause Diagnosis &bull; Bounded Re-Planning
            </p>
          </div>
        </div>

        {hasRecovery && latestEvent && (
          <div className="flex items-center gap-2 font-mono text-xs">
            <span className="text-slate-400">Attempts:</span>
            <span className="text-amber-300 font-bold bg-amber-950/80 px-2 py-1 rounded border border-amber-700/60">
              {latestEvent.attempt} / {latestEvent.maxAttempts}
            </span>
          </div>
        )}
      </div>

      {/* Failure/Recovery Banner */}
      {hasRecovery ? (
        <div className="space-y-4">
          <div className="p-4 rounded-xl bg-gradient-to-r from-amber-950/40 via-amber-900/20 to-slate-900 border border-amber-600/50 flex flex-wrap items-start justify-between gap-3">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
                <strong className="text-amber-200 text-xs font-bold uppercase tracking-wider font-mono">
                  Autonomous Recovery Active
                </strong>
                <Badge variant="warning" size="sm">
                  ATTEMPT {latestEvent.attempt} OF {latestEvent.maxAttempts}
                </Badge>
              </div>
              <p className="text-xs text-slate-300 font-sans">
                {latestEvent.triggerError}
              </p>
            </div>
            <div className="text-[11px] font-mono text-slate-400 bg-slate-950/60 px-2.5 py-1.5 rounded border border-slate-800">
              Status: <strong className="text-white">{latestEvent.status}</strong>
            </div>
          </div>

          {/* Render Timeline for Each Recovery Event */}
          <div className="space-y-4 pt-2">
            {recoveryHistory.map((ev, idx) => (
              <RecoveryTimeline key={`rec_${idx}`} recoveryEvent={ev} />
            ))}
          </div>
        </div>
      ) : (
        <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800/80 flex flex-wrap items-center justify-between gap-4 text-xs">
          <div className="flex items-center gap-2 text-slate-400">
            <ShieldAlert className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>
              Autonomous execution operating nominally. No runtime failures or sandbox violations detected.
            </span>
          </div>

          {(onTriggerControlledFailure || onTriggerRepeatedFailure) && (
            <div className="flex flex-wrap items-center gap-2 shrink-0">
              {onTriggerControlledFailure && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={onTriggerControlledFailure}
                  disabled={isExecuting}
                  className="border-amber-800/60 text-amber-300 hover:bg-amber-950/40 text-xs"
                >
                  Simulate Recoverable Failure (1/3)
                </Button>
              )}
              {onTriggerRepeatedFailure && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={onTriggerRepeatedFailure}
                  disabled={isExecuting}
                  className="border-rose-800/60 text-rose-300 hover:bg-rose-950/40 text-xs"
                >
                  Simulate Exhausted Retries (3/3)
                </Button>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
