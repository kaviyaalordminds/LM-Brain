import React from 'react';
import {
  AlertOctagon,
  AlertTriangle,
  ArrowDown,
  CheckCircle2,
  Play,
  RefreshCw,
  RotateCcw,
  ShieldAlert,
  Sparkles,
  XCircle,
} from 'lucide-react';
import { RecoveryEvent } from '../../types';
import { Badge } from '../common/Badge';
import { Button } from '../common/Button';
import { Card } from '../common/Card';

interface RecoverySimulationPanelProps {
  recoveryHistory: RecoveryEvent[];
  onTriggerControlledFailure?: () => void;
  onTriggerRepeatedFailure?: () => void;
  isExecuting?: boolean;
}

export const RecoverySimulationPanel: React.FC<RecoverySimulationPanelProps> = ({
  recoveryHistory = [],
  onTriggerControlledFailure,
  onTriggerRepeatedFailure,
  isExecuting = false,
}) => {
  return (
    <Card
      title="Autonomous Failure Diagnosis & Bounded Recovery Demo"
      subtitle="The workforce recovers autonomously using Reflection & Re-planning within strict bounded limits"
      icon={<RotateCcw className="w-4 h-4 text-amber-400" />}
      badge={<Badge variant="warning" size="sm">DEMO CONTROLS</Badge>}
    >
      <div className="space-y-4">
        {/* Interactive Simulation Triggers */}
        <div className="p-3.5 rounded-lg bg-[#080C14] border border-amber-900/40 flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="space-y-0.5">
            <span className="font-bold text-amber-400 font-mono flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5" />
              Interactive Recovery Testing Controls
            </span>
            <p className="text-slate-400 text-[11px]">
              Trigger controlled failure scenarios to witness live autonomous diagnosis, re-planning, and bounded termination.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={onTriggerControlledFailure}
              disabled={isExecuting}
              icon={<RotateCcw className="w-3.5 h-3.5 text-amber-400" />}
              className="border-amber-800/60 hover:bg-amber-950/40 text-amber-200"
            >
              SIMULATE CONTROLLED FAILURE
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={onTriggerRepeatedFailure}
              disabled={isExecuting}
              icon={<AlertOctagon className="w-3.5 h-3.5 text-rose-400" />}
              className="border-rose-800/60 hover:bg-rose-950/40 text-rose-200"
            >
              SIMULATE REPEATED FAILURE
            </Button>
          </div>
        </div>

        {/* Visual Recovery Timeline (if active or occurred) */}
        {recoveryHistory.length > 0 && (
          <div className="space-y-3 pt-2">
            <div className="text-xs font-mono font-semibold text-slate-300 flex items-center justify-between">
              <span>Autonomous Recovery Progression</span>
              <span className="text-slate-500">
                Budget: {recoveryHistory.length} / 3 Attempts Used
              </span>
            </div>

            <div className="space-y-3">
              {recoveryHistory.map((rec, idx) => (
                <div
                  key={idx}
                  className={`p-4 rounded-lg border text-xs font-mono space-y-3 ${
                    rec.status === 'RECOVERED'
                      ? 'bg-emerald-950/20 border-emerald-800/50'
                      : rec.status === 'EXHAUSTED'
                      ? 'bg-rose-950/20 border-rose-800/50'
                      : 'bg-amber-950/20 border-amber-800/50'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-200 flex items-center gap-1.5">
                      <RefreshCw className="w-3.5 h-3.5 text-amber-400 animate-spin" />
                      Recovery Attempt {rec.attempt} / {rec.maxAttempts}
                    </span>
                    {rec.status === 'RECOVERED' ? (
                      <Badge variant="success" size="sm" dot>RECOVERED</Badge>
                    ) : rec.status === 'EXHAUSTED' ? (
                      <Badge variant="danger" size="sm" dot>FAILED — BOUNDED (Budget Exhausted)</Badge>
                    ) : (
                      <Badge variant="warning" size="sm" dot>IN PROGRESS</Badge>
                    )}
                  </div>

                  {/* Visual Step-by-Step Flow */}
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-2 text-[11px] pt-1">
                    <div className="p-2 rounded bg-slate-900/90 border border-slate-800">
                      <span className="text-rose-400 font-bold block mb-1">1. FAILED</span>
                      <span className="text-slate-300 truncate block">{rec.triggerError}</span>
                    </div>
                    <div className="p-2 rounded bg-slate-900/90 border border-slate-800">
                      <span className="text-amber-400 font-bold block mb-1">2. OBSERVED</span>
                      <span className="text-slate-300 truncate block">{rec.failureObserved}</span>
                    </div>
                    <div className="p-2 rounded bg-slate-900/90 border border-slate-800">
                      <span className="text-indigo-400 font-bold block mb-1">3. DIAGNOSED</span>
                      <span className="text-slate-300 truncate block">{rec.diagnosis}</span>
                    </div>
                    <div className="p-2 rounded bg-slate-900/90 border border-slate-800">
                      <span className={rec.status === 'RECOVERED' ? 'text-emerald-400 font-bold block mb-1' : 'text-rose-400 font-bold block mb-1'}>
                        {rec.status === 'RECOVERED' ? '4. RECOVERED' : '4. BOUNDED'}
                      </span>
                      <span className="text-slate-300 truncate block">
                        {rec.status === 'RECOVERED' ? 'New plan verified & passed' : 'No infinite execution'}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </Card>
  );
};
