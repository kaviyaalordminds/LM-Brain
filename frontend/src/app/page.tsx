'use client';

import React, { useState } from 'react';
import { useSimulation } from '@/lib/context/SimulationContext';
import { Header } from '@/components/layout/Header';
import { TaskComposer } from '@/components/command-center/TaskComposer';
import { BasicModeView } from '@/components/command-center/BasicModeView';
import { AdvancedWorkspace } from '@/components/command-center/AdvancedWorkspace';
import { FolderKanban, Layers, ShieldCheck, Database, HelpCircle } from 'lucide-react';

export default function Page() {
  const {
    isPlaying,
    currentStep,
    progress,
    agents,
    startSimulation,
    resetSimulation
  } = useSimulation();

  const [activeTabMode, setActiveTabMode] = useState<'basic' | 'advanced'>('advanced');
  const [hasStartedAdvanced, setHasStartedAdvanced] = useState(false);
  const [activeQueryText, setActiveQueryText] = useState('');

  const handleStartWorkforce = (query: string, mode: 'basic' | 'advanced') => {
    setActiveQueryText(query);
    setActiveTabMode(mode);

    if (mode === 'advanced') {
      setHasStartedAdvanced(true);
      startSimulation();
    } else {
      // Basic Mode Mock Trigger
      alert(`General Task Triggered: "${query}" via Basic Mode.\nSpawned Specialist Agent.`);
    }
  };

  const handleTriggerBasicAgent = (agentName: string, query: string) => {
    alert(`Mock Prompt sent to ${agentName}:\n"${query}"\nResult will appear in recent artifacts shortly.`);
  };

  const handleStopWorkforce = () => {
    resetSimulation();
    setHasStartedAdvanced(false);
    setActiveQueryText('');
  };

  return (
    <div className="flex flex-col min-h-full pb-10">
      <Header
        title="Command Center"
        subtitle="Turn requirements into verified outcomes."
      />

      <div className="flex-1 px-6 py-6 space-y-6 max-w-6xl mx-auto w-full">
        
        {/* Composer Widget (Hide large composer when simulation is running to save workspace space) */}
        {!hasStartedAdvanced ? (
          <div className="space-y-6">
            
            <div className="space-y-1">
              <h2 className="text-2xl font-bold tracking-tight text-slate-100 uppercase">
                Autonomous AI Workforce
              </h2>
              <p className="text-xs font-mono text-slate-400">
                Self-hosted enterprise orchestrator for complex software engineering and campaigns.
              </p>
            </div>

            <TaskComposer
              onStart={handleStartWorkforce}
              isPlaying={isPlaying}
              onReset={handleStopWorkforce}
            />

            {/* Render sub-views depending on selector in composer */}
            <div className="pt-2">
              <BasicModeView
                agents={agents}
                onTriggerAgent={handleTriggerBasicAgent}
              />
            </div>

          </div>
        ) : (
          /* Active Advanced workspace view */
          <div className="space-y-6">
            
            {/* Minimal running header */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between bg-[#0c1322] border border-slate-800 rounded-xl p-4 gap-4">
              <div className="space-y-1">
                <span className="text-[10px] text-indigo-400 font-mono font-bold uppercase tracking-wider">
                  Active Advanced Project Task
                </span>
                <h2 className="text-sm font-bold font-mono text-slate-200">
                  "{activeQueryText}"
                </h2>
              </div>
              <button
                onClick={handleStopWorkforce}
                className="bg-rose-950/40 hover:bg-rose-900/40 border border-rose-500/30 text-rose-400 text-xs font-mono py-2 px-4 rounded font-bold transition-all focus-ring shrink-0 uppercase tracking-wider"
              >
                Stop Workforce
              </button>
            </div>

            <AdvancedWorkspace />

          </div>
        )}

      </div>
    </div>
  );
}
