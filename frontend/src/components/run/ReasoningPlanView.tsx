import React from 'react';
import { Brain, CheckCircle2, ShieldAlert, Sparkles, Tag, Target } from 'lucide-react';
import { ReasoningPlan } from '../../types';
import { Badge } from '../common/Badge';
import { Card } from '../common/Card';

interface ReasoningPlanViewProps {
  plan?: ReasoningPlan;
  mode?: string;
  planStatus?: string;
}

export const ReasoningPlanView: React.FC<ReasoningPlanViewProps> = ({
  plan,
  mode = 'DEVELOP',
  planStatus = 'VALIDATED',
}) => {
  if (!plan) {
    return (
      <Card
        title="Reasoning Engine — Structured Plan"
        subtitle="Declarative capability plan synthesized by Reasoning Service"
        icon={<Brain className="w-4 h-4 text-indigo-400" />}
      >
        <div className="py-8 text-center text-xs text-slate-500 font-mono">
          Awaiting perception normalization & knowledge context to synthesize structured plan...
        </div>
      </Card>
    );
  }

  return (
    <Card
      title="Structured Reasoning Plan (Safe Contract)"
      subtitle="Declarative capability roadmap — Raw chain-of-thought scrubbed by security policy"
      icon={<Brain className="w-4 h-4 text-indigo-400" />}
      badge={<Badge variant="primary" size="sm">CONFIDENCE: {Math.round(plan.confidence * 100)}%</Badge>}
    >
      <div className="space-y-4">
        {/* Metadata Summary Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
          <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800">
            <span className="text-[10px] text-slate-500 uppercase block">Reasoning Mode</span>
            <span className="font-bold text-indigo-300 text-sm">{mode}</span>
          </div>
          <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800">
            <span className="text-[10px] text-slate-500 uppercase block">Plan Status</span>
            <span className="font-bold text-emerald-400 text-sm flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5" />
              {planStatus}
            </span>
          </div>
          <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800">
            <span className="text-[10px] text-slate-500 uppercase block">Risk Assessment</span>
            <span className="font-bold text-slate-200 text-sm">LOW</span>
          </div>
          <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800">
            <span className="text-[10px] text-slate-500 uppercase block">Total Plan Steps</span>
            <span className="font-bold text-slate-200 text-sm">{plan.steps.length} Bounded Steps</span>
          </div>
        </div>

        {/* Required Capabilities Pills */}
        <div className="p-3 rounded-lg bg-[#0B0F19] border border-slate-800 flex flex-wrap items-center gap-2">
          <span className="text-xs text-slate-400 font-mono font-medium mr-1 flex items-center gap-1.5">
            <Tag className="w-3.5 h-3.5 text-indigo-400" />
            Required Capabilities:
          </span>
          {plan.requiredCapabilities.map((cap) => (
            <span
              key={cap}
              className="text-xs font-mono px-2 py-0.5 rounded bg-indigo-950/70 text-indigo-300 border border-indigo-800/60"
            >
              {cap}
            </span>
          ))}
        </div>

        {/* Structured Step Table */}
        <div className="border border-slate-800 rounded-lg overflow-hidden">
          <div className="bg-slate-900/90 px-4 py-2 text-xs font-mono font-semibold text-slate-400 border-b border-slate-800 flex items-center justify-between">
            <span>Machine-Validatable Step Specifications</span>
            <span className="text-[11px] text-slate-500">Execution Boundary Guarded</span>
          </div>
          <div className="divide-y divide-slate-800/80 bg-[#0E1526]/50">
            {plan.steps.map((step, idx) => (
              <div key={step.stepId} className="p-3.5 hover:bg-slate-900/50 transition-colors flex items-start gap-3">
                <span className="w-7 h-7 rounded-md bg-indigo-950/80 border border-indigo-800/60 text-indigo-300 flex items-center justify-center text-xs font-mono font-bold shrink-0">
                  {String(idx + 1).padStart(2, '0')}
                </span>
                <div className="flex-1 min-w-0 space-y-1">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <span className="text-xs font-semibold text-slate-200">{step.objective}</span>
                    <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-800">
                      Capability: {step.requiredCapability}
                    </span>
                  </div>
                  {step.verificationRequirement && (
                    <div className="text-[11px] font-mono text-slate-400 flex items-center gap-1.5">
                      <Target className="w-3 h-3 text-emerald-400 shrink-0" />
                      <span>Verification Rule: {step.verificationRequirement}</span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </Card>
  );
};
