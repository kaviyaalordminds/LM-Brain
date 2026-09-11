import React from 'react';
import {
  AlertTriangle,
  ArrowDown,
  Brain,
  CheckCircle2,
  Cpu,
  Eye,
  FileCheck2,
  Layers,
  RefreshCw,
  RotateCcw,
  ShieldAlert,
  Sparkles,
  Terminal,
  XCircle,
} from 'lucide-react';
import { RecoveryEvent, RecoverySubStep } from '../../types';
import { Badge } from '../common/Badge';

interface RecoveryTimelineProps {
  recoveryEvent: RecoveryEvent;
}

const STEP_ORDER: RecoverySubStep[] = [
  'FAILURE',
  'OBSERVATION',
  'DIAGNOSIS',
  'REFLECTION',
  'REPLAN',
  'RETRY',
  'VALIDATION',
  'VERIFICATION',
  'COMPLETED',
];

export const RecoveryTimeline: React.FC<RecoveryTimelineProps> = ({ recoveryEvent }) => {
  const isRecovered = recoveryEvent.status === 'RECOVERED' || recoveryEvent.activeStep === 'COMPLETED';
  const isExhausted = recoveryEvent.status === 'EXHAUSTED';
  const currentStepKey = recoveryEvent.activeStep || (isRecovered ? 'COMPLETED' : isExhausted ? 'VERIFICATION' : 'FAILURE');
  const currentStepIndex = STEP_ORDER.indexOf(currentStepKey);

  const getStepStatus = (stepKey: RecoverySubStep): 'completed' | 'active' | 'waiting' | 'failed' => {
    if (isRecovered) return 'completed';
    const stepIdx = STEP_ORDER.indexOf(stepKey);
    if (stepIdx < currentStepIndex) return 'completed';
    if (stepIdx === currentStepIndex) {
      if (isExhausted) return 'failed';
      return 'active';
    }
    return 'waiting';
  };

  const stepsConfig: {
    key: RecoverySubStep;
    label: string;
    subtext: string;
    icon: React.ComponentType<{ className?: string }>;
  }[] = [
    {
      key: 'FAILURE',
      label: 'EXECUTION FAILURE',
      subtext: recoveryEvent.triggerError || 'Sandboxed step execution failed validation checks.',
      icon: XCircle,
    },
    {
      key: 'OBSERVATION',
      label: 'OBSERVATION / QA',
      subtext: recoveryEvent.failureObserved || 'Empirical failure output captured in evidence set.',
      icon: Eye,
    },
    {
      key: 'DIAGNOSIS',
      label: 'DIAGNOSIS',
      subtext: recoveryEvent.diagnosis || 'Root cause identified. Corrective action required.',
      icon: Brain,
    },
    {
      key: 'REFLECTION',
      label: 'REFLECTION / RECOVERY',
      subtext: 'Bounded recovery strategy determined within maximum attempt limits.',
      icon: RefreshCw,
    },
    {
      key: 'REPLAN',
      label: 'RE-PLAN',
      subtext: recoveryEvent.replannedGoal
        ? `Corrective plan generated: ${recoveryEvent.replannedGoal} (${recoveryEvent.replanStepCount} steps)`
        : 'Generated corrected DAG steps.',
      icon: Layers,
    },
    {
      key: 'RETRY',
      label: 'SPECIALIST RETRY',
      subtext: 'Specialist re-executes task with corrected parameters in sandbox.',
      icon: Terminal,
    },
    {
      key: 'VALIDATION',
      label: 'VALIDATION',
      subtext: isRecovered
        ? 'Project coherence and validation checks verified successfully.'
        : isExhausted
        ? 'Validation could not pass within allowed attempts.'
        : 'Running build and project coherence validation in sandbox...',
      icon: ShieldAlert,
    },
    {
      key: 'VERIFICATION',
      label: 'VERIFICATION',
      subtext: isRecovered
        ? 'All success criteria confirmed. Safe to commit to memory.'
        : isExhausted
        ? 'Verification blocked due to exhausted retry bounds.'
        : 'Evaluating empirical evidence checklist...',
      icon: FileCheck2,
    },
  ];

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-xs font-mono font-bold text-amber-400 uppercase tracking-wider flex items-center gap-1.5">
          <RefreshCw className="w-3.5 h-3.5" />
          Autonomous Recovery Timeline (Attempt {recoveryEvent.attempt} of {recoveryEvent.maxAttempts})
        </span>
        <Badge
          variant={isRecovered ? 'success' : isExhausted ? 'danger' : 'warning'}
          size="sm"
          dot={!isRecovered && !isExhausted}
        >
          {recoveryEvent.status}
        </Badge>
      </div>

      <div className="relative pl-6 space-y-3.5 before:absolute before:left-2.5 before:top-3 before:bottom-3 before:w-0.5 before:bg-slate-800">
        {stepsConfig.map((step, idx) => {
          const Icon = step.icon;
          const status = getStepStatus(step.key);

          let badgeVariant: 'default' | 'primary' | 'success' | 'danger' | 'warning' = 'default';
          let badgeText = '○ WAITING';
          let iconColor = 'text-slate-500 bg-slate-900 border-slate-800';
          let cardStyle = 'bg-slate-950/40 border-slate-900 text-slate-500 opacity-60';

          if (status === 'active') {
            badgeVariant = 'warning';
            badgeText = '● ACTIVE';
            iconColor = 'text-amber-300 bg-amber-950 ring-2 ring-amber-400 border-amber-500';
            cardStyle = 'recovering-stage-card border-amber-500 text-amber-100 shadow-xl opacity-100 ring-2 ring-amber-400/80';
          } else if (status === 'completed') {
            badgeVariant = 'success';
            badgeText = '✓ COMPLETED';
            iconColor = 'text-emerald-400 bg-emerald-950 border-emerald-800';
            cardStyle = 'bg-slate-900/90 border-emerald-900/60 text-slate-200 opacity-90';
          } else if (status === 'failed') {
            badgeVariant = 'danger';
            badgeText = '❌ FAILED';
            iconColor = 'text-rose-400 bg-rose-950 border-rose-800';
            cardStyle = 'bg-rose-950/40 border-rose-700 text-rose-200 opacity-100';
          }

          return (
            <div key={step.key} className="relative group">
              <div
                className={`absolute -left-6 top-1.5 w-5 h-5 rounded-full border flex items-center justify-center text-[10px] ${iconColor}`}
              >
                <Icon className="w-3 h-3" />
              </div>

              <div className={`p-3.5 rounded-xl border transition-all text-xs ${cardStyle}`}>
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-[10px] text-slate-400 font-bold">
                      Sub-step {idx + 1}
                    </span>
                    <strong className="text-white font-sans text-xs tracking-tight">
                      {step.label}
                    </strong>
                  </div>
                  <Badge variant={badgeVariant} size="sm" dot={status === 'active'}>
                    {badgeText}
                  </Badge>
                </div>
                <p className="text-slate-300 font-sans text-[11px] mt-1 leading-relaxed">
                  {step.subtext}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
