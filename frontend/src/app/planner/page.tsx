'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { orchestratorApi } from '@/lib/api/orchestrator';
import { Plan, PlanStep } from '@/lib/types';
import { Badge } from '@/components/ui/Badge';
import { CodeBlock } from '@/components/ui/CodeBlock';
import { EmptyState } from '@/components/ui/EmptyState';
import { Cpu, Bot, ShieldCheck, Database, Search, ArrowRight, Layers, RefreshCw } from 'lucide-react';

export default function PlannerViewPage() {
  const [executions, setExecutions] = useState<any[]>([]);
  const [selectedPlanId, setSelectedPlanId] = useState<string | null>(null);
  const [plan, setPlan] = useState<Plan | null>(null);
  const [selectedStepId, setSelectedStepId] = useState<string | null>(null);

  useEffect(() => {
    orchestratorApi.listExecutions().then((list) => {
      setExecutions(list);
      const withPlan = list.find((e) => e.plan_id);
      if (withPlan && withPlan.plan_id) {
        setSelectedPlanId(withPlan.plan_id);
      }

    });
  }, []);

  useEffect(() => {
    if (!selectedPlanId) return;
    orchestratorApi.getPlan(selectedPlanId).then(setPlan);
  }, [selectedPlanId]);

  // Selected step details
  const selectedStep = useMemo(() => {
    if (!plan || !selectedStepId) return plan?.steps?.[0] || null;
    return plan.steps.find((s) => s.step_id === selectedStepId) || null;
  }, [plan, selectedStepId]);

  return (
    <div className="space-y-6 font-mono-tech">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-4 bg-space-900 border border-space-800 rounded-lg shadow-md">
        <div className="flex items-center gap-3">
          <Cpu className="w-5 h-5 text-cyan-400" />
          <div>
            <h1 className="text-xs font-bold text-slate-100 uppercase tracking-wider">
              Planner Agent Decompositions
            </h1>
            <div className="text-[11px] text-slate-400">
              Service: Planner Agent (127.0.0.1:8002) | Real DAG generation & dependency resolution
            </div>
          </div>
        </div>

        {/* Plan Selector */}
        <div className="flex items-center gap-2 text-xs">
          <span className="text-slate-500">Plan:</span>
          <select
            value={selectedPlanId || ''}
            onChange={(e) => {
              setSelectedPlanId(e.target.value);
              setSelectedStepId(null);
            }}
            className="bg-space-950 border border-space-750 text-slate-200 rounded px-2.5 py-1 focus:outline-none"
          >
            {executions
              .filter((e) => e.plan_id)
              .map((e) => (
                <option key={e.plan_id} value={e.plan_id}>
                  {e.plan_id} (v{e.plan_version}) - {e.user_request.slice(0, 35)}...
                </option>
              ))}
          </select>
        </div>
      </div>

      {!plan ? (
        <EmptyState
          title="No Plan Data Available"
          description="Submit a task from the Control Center to trigger real decomposition by the Planner Agent."
          icon={<Cpu className="w-5 h-5 text-cyan-400" />}
        />
      ) : (
        <div className="space-y-6">
          {/* Plan Meta Card */}
          <div className="p-4 bg-space-900 border border-space-800 rounded-lg space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-space-800">
              <span className="text-xs font-bold text-cyan-400">PLAN: {plan.plan_id}</span>
              <span className="text-[11px] text-slate-400">Version {plan.plan_version}</span>
            </div>
            <div>
              <div className="text-[10px] text-slate-500 uppercase">Normalized User Intent:</div>
              <p className="text-xs text-slate-200 font-sans mt-0.5 leading-relaxed">
                {plan.user_intent || 'Intent decomposed into discrete dependency steps.'}
              </p>
            </div>
          </div>

          {/* Steps & Inspector Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Steps List (cols 1) */}
            <div className="space-y-2 bg-space-900 border border-space-800 rounded-lg p-3 max-h-[500px] overflow-y-auto">
              <div className="text-[11px] text-slate-400 uppercase tracking-wider pb-2 border-b border-space-800">
                Plan Steps ({plan.steps?.length || 0})
              </div>

              {plan.steps?.map((s, idx) => {
                const isSelected = selectedStep?.step_id === s.step_id;
                return (
                  <div
                    key={s.step_id}
                    onClick={() => setSelectedStepId(s.step_id)}
                    className={`p-3 rounded border transition-all cursor-pointer text-left ${
                      isSelected
                        ? 'bg-space-800 border-sky-500 shadow-sm'
                        : 'bg-space-950 hover:bg-space-850 border-space-800'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-bold text-slate-200 uppercase">
                        {idx + 1}. {s.specialist}
                      </span>
                      <span className="text-[9px] px-1.5 py-0.2 rounded bg-space-850 text-slate-400 border border-space-750">
                        {s.step_id}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400 font-sans line-clamp-2 leading-relaxed">
                      {s.description}
                    </p>
                    {s.dependencies?.length > 0 && (
                      <div className="text-[10px] text-slate-500 mt-1.5">
                        Depends on: {s.dependencies.join(', ')}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Step Specification (cols 2) */}
            <div className="md:col-span-2 bg-space-900 border border-space-800 rounded-lg p-4 space-y-4">
              {selectedStep ? (
                <>
                  <div className="flex items-center justify-between pb-3 border-b border-space-800">
                    <div>
                      <h2 className="text-xs font-bold text-slate-100 uppercase">
                        STEP: {selectedStep.step_id}
                      </h2>
                      <div className="text-[11px] text-emerald-400 font-bold uppercase mt-0.5">
                        Specialist: {selectedStep.specialist}
                      </div>
                    </div>
                    <Badge status={selectedStep.status || 'READY'} size="sm" />
                  </div>

                  <div className="p-3 bg-space-950 border border-space-800 rounded text-xs">
                    <span className="text-[10px] text-slate-500 uppercase block mb-1">Task Instruction</span>
                    <p className="text-slate-200 font-sans leading-relaxed">{selectedStep.description}</p>
                  </div>

                  {/* Requirements Grid */}
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-[11px]">
                    <div className="p-2.5 bg-space-950 border border-space-800 rounded">
                      <span className="text-slate-500 block text-[10px]">Dependencies</span>
                      <span className="text-slate-300">
                        {selectedStep.dependencies?.length ? selectedStep.dependencies.join(', ') : 'None'}
                      </span>
                    </div>
                    <div className="p-2.5 bg-space-950 border border-space-800 rounded">
                      <span className="text-slate-500 block text-[10px]">Memory Context</span>
                      <span className={selectedStep.memory_requirement ? 'text-emerald-400' : 'text-slate-400'}>
                        {selectedStep.memory_requirement ? 'Required' : 'Optional'}
                      </span>
                    </div>
                    <div className="p-2.5 bg-space-950 border border-space-800 rounded">
                      <span className="text-slate-500 block text-[10px]">Web Research</span>
                      <span className={selectedStep.research_requirement ? 'text-emerald-400' : 'text-slate-400'}>
                        {selectedStep.research_requirement ? 'Required' : 'Optional'}
                      </span>
                    </div>
                  </div>

                  {/* Verification Criteria */}
                  {selectedStep.verification_requirements && (
                    <div className="space-y-1">
                      <div className="text-[10px] text-slate-500 uppercase">Result Verification Policy</div>
                      <CodeBlock
                        code={
                          typeof selectedStep.verification_requirements === 'string'
                            ? selectedStep.verification_requirements
                            : JSON.stringify(selectedStep.verification_requirements, null, 2)
                        }
                        language="json"
                        title="Verification Constraints"
                      />
                    </div>
                  )}
                </>
              ) : null}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
