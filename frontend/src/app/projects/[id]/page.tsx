'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { Header } from '@/components/layout/Header';
import { projectService } from '@/lib/api/projectService';
import { Project, SpecialistAgent, ExecutiveTwin } from '@/lib/types';
import { use } from 'react';
import {
  ArrowLeft,
  BookOpen,
  Calendar,
  Layers,
  Activity,
  CheckSquare,
  FileCode,
  Volume2,
  Database,
  Info,
  Clock,
  ExternalLink,
  ShieldCheck,
  AlertTriangle
} from 'lucide-react';
import { cn } from '@/lib/utils/cn';

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function Page({ params }: PageProps) {
  const resolvedParams = use(params);
  const projectId = resolvedParams.id;

  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'requirements' | 'plan' | 'workforce' | 'execution' | 'verification' | 'artifacts' | 'walkthrough' | 'memory'>('overview');
  const [activeArtifactIndex, setActiveArtifactIndex] = useState(0);
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);

  useEffect(() => {
    const fetch = async () => {
      const p = await projectService.getProjectById(projectId);
      if (p) setProject(p);
      setLoading(false);
    };
    fetch();
  }, [projectId]);

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center font-mono text-xs text-slate-500">
        Querying database schemas...
      </div>
    );
  }

  if (!project) {
    return (
      <div className="p-6 text-center space-y-4">
        <p className="text-sm font-mono text-slate-400">Workspace directory not found.</p>
        <Link href="/projects" className="text-xs text-indigo-400 hover:underline">
          Return to Registry
        </Link>
      </div>
    );
  }

  const tabs = [
    { id: 'overview', name: 'Overview' },
    { id: 'requirements', name: 'Requirements' },
    { id: 'plan', name: 'Plan Steps' },
    { id: 'workforce', name: 'Workforce' },
    { id: 'execution', name: 'Execution Log' },
    { id: 'verification', name: 'Verification' },
    { id: 'artifacts', name: 'Artifacts' },
    { id: 'walkthrough', name: 'Walkthrough' },
    { id: 'memory', name: 'Memory' },
  ] as const;

  return (
    <div className="flex flex-col min-h-full pb-10 select-none">
      <Header
        title={`Project: ${project.name}`}
        subtitle={`Workspace status analysis and logs partition.`}
      />

      <div className="flex-1 px-6 py-6 space-y-6 max-w-6xl mx-auto w-full">
        {/* Back Link */}
        <Link href="/projects" className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-indigo-400 font-mono transition-colors">
          <ArrowLeft className="h-3.5 w-3.5" /> Back to Registry
        </Link>

        {/* Project Header block */}
        <div className="bg-[#0c1322] border border-slate-800 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h2 className="text-base font-bold text-slate-200">{project.name}</h2>
            <span className="text-[10px] font-mono text-slate-500 block mt-1">
              Started: {project.startTime ? new Date(project.startTime).toLocaleString() : 'N/A'} | Phase: {project.currentPhase || 'N/A'}
            </span>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-xs font-mono text-slate-400">Status:</span>
            <span className="text-xs font-mono font-bold uppercase border px-2.5 py-1 rounded bg-indigo-500/10 border-indigo-500/20 text-indigo-400">
              {project.status}
            </span>
          </div>
        </div>

        {/* Tab Selector */}
        <div className="border-b border-slate-800 flex items-center gap-1 overflow-x-auto scrollbar-none">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                "px-4 py-2 text-xs font-bold font-sans uppercase tracking-wider transition-colors border-b-2 focus:outline-none shrink-0",
                activeTab === tab.id 
                  ? "border-indigo-500 text-indigo-400 font-semibold" 
                  : "border-transparent text-slate-500 hover:text-slate-300"
              )}
            >
              {tab.name}
            </button>
          ))}
        </div>

        {/* Tab content panel */}
        <div className="bg-[#0c1322]/40 border border-slate-800/80 rounded-xl p-5 min-h-[350px]">
          
          {/* 1. Overview */}
          {activeTab === 'overview' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs leading-relaxed">
              <div className="space-y-4">
                <div className="space-y-1">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">Description</h3>
                  <p className="text-slate-300 font-mono">{project.description}</p>
                </div>
                
                <div className="space-y-1 pt-2">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">Success Criteria</h3>
                  <ul className="space-y-1 text-slate-400 list-disc list-inside">
                    {project.successCriteria.map((c, i) => (
                      <li key={i}>{c}</li>
                    ))}
                  </ul>
                </div>
              </div>

              <div className="space-y-4">
                <div className="space-y-1">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">Project Constraints</h3>
                  <ul className="space-y-1 text-slate-400 list-disc list-inside font-mono text-[11px]">
                    {project.constraints.map((c, i) => (
                      <li key={i}>{c}</li>
                    ))}
                  </ul>
                </div>

                <div className="space-y-1 pt-2">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">Project Metrics</h3>
                  <div className="grid grid-cols-2 gap-3 font-mono text-[11px] bg-slate-900 border border-slate-800 p-2.5 rounded">
                    <div>
                      <span className="text-slate-500 block">Progress:</span>
                      <span className="text-slate-200 font-bold">{project.progress}%</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block">Twin Count:</span>
                      <span className="text-slate-200 font-bold">{project.twins.length} Active</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* 2. Requirements */}
          {activeTab === 'requirements' && (
            <div className="space-y-4 text-xs font-mono">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">Perception Requirements Checklist</h3>
              <div className="space-y-2 max-w-2xl">
                {project.requirements.map(req => (
                  <div key={req.id} className="flex items-start gap-3 bg-slate-900/50 border border-slate-800/80 p-3 rounded-lg">
                    {req.status === 'satisfied' ? (
                      <span className="text-[10px] bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 font-bold px-2 py-0.5 rounded uppercase">Satisfied</span>
                    ) : (
                      <span className="text-[10px] bg-slate-800 border border-slate-700 text-slate-400 font-bold px-2 py-0.5 rounded uppercase">Pending</span>
                    )}
                    <div className="space-y-0.5">
                      <p className="text-slate-200 text-xs leading-normal">{req.text}</p>
                      <span className="text-[9px] text-slate-500">Category: {req.category}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 3. Plan */}
          {activeTab === 'plan' && (
            <div className="space-y-4 text-xs font-mono">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">Orchestrator Planned Steps</h3>
              <div className="space-y-2.5 max-w-3xl">
                {project.plan.map((step, idx) => (
                  <div key={step.id} className="border border-slate-800 bg-[#060a12] rounded p-3 flex gap-4">
                    <div className="text-indigo-400 font-bold text-sm select-none">{idx + 1}.</div>
                    <div className="flex-1 space-y-1">
                      <div className="flex justify-between items-center">
                        <span className="font-bold text-slate-200 text-xs">{step.title}</span>
                        <span className="text-[9px] font-bold uppercase text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-1.5 py-0.5 rounded">{step.status}</span>
                      </div>
                      <p className="text-[11px] text-slate-400 leading-normal">{step.description}</p>
                      {step.dependencies.length > 0 && (
                        <span className="text-[9px] text-indigo-400 block pt-1">Dependencies: {step.dependencies.join(', ')}</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 4. Workforce */}
          {activeTab === 'workforce' && (
            <div className="space-y-6 text-xs">
              <div className="space-y-3">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">Executive Digital Twins Involved</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {project.twins.map(twinId => (
                    <div key={twinId} className="border border-slate-800 bg-[#060a12] p-3 rounded-lg flex justify-between items-center">
                      <div>
                        <span className="font-bold text-slate-200 block text-xs">{twinId === 'twin-cto' ? 'CTO Twin' : 'CMO Twin'}</span>
                        <span className="text-[10px] text-slate-500 font-mono">Scope: Engineering / Branding Strategy</span>
                      </div>
                      <span className="text-[9px] font-mono font-bold uppercase bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 px-2 py-0.5 rounded-full">Activated</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="space-y-3 pt-2">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">Specialist Agents Deployed</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  {project.agents.map(agentId => (
                    <div key={agentId} className="border border-slate-800 bg-[#060a12] p-3 rounded-lg flex flex-col justify-between min-h-[80px]">
                      <div>
                        <span className="font-bold text-slate-200 block text-xs capitalize">{agentId.replace('agent-', '')} Agent</span>
                        <span className="text-[9px] text-slate-500 font-mono">Capability: Code / Graphics</span>
                      </div>
                      <span className="text-[9px] font-mono text-emerald-400 block mt-3">Status: Terminated (Success)</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* 5. Execution */}
          {activeTab === 'execution' && (
            <div className="space-y-4 text-xs font-mono">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">Simulated Execution Activity Feed</h3>
              <div className="bg-[#05080f] border border-slate-900 p-3 rounded-lg h-72 overflow-y-auto space-y-2 text-[10px] leading-relaxed">
                <div>[09:00:00] Perception identified software-development intent.</div>
                <div>[09:00:02] Guidelines retrieved from Obsidian memory.</div>
                <div>[09:00:05] CTO Twin activated engineering decision schema.</div>
                <div>[09:00:10] Frontend Agent spawned. Writing React interface.</div>
                <div>[09:01:45] Testing Agent reported Contact form middleware verification fail.</div>
                <div>[09:01:47] Reflection triggered: auto-configuring bypass.</div>
                <div>[09:02:14] Verification passed: 100% tests successful.</div>
                <div>[09:02:25] Vault synchronized. State written to Obsidian.</div>
              </div>
            </div>
          )}

          {/* 6. Verification */}
          {activeTab === 'verification' && (
            <div className="space-y-4 text-xs font-mono">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">Automated Verification Outcomes</h3>
              {project.verificationResult ? (
                <div className="space-y-4">
                  <div className="flex items-center gap-3">
                    <span className="text-[10px] bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 font-bold px-2 py-0.5 rounded uppercase">Passed</span>
                    <span className="text-slate-400">Duration: {project.verificationResult.duration}</span>
                  </div>
                  
                  <div className="bg-[#05080f] border border-slate-900 p-3 rounded-lg space-y-1.5 text-[10px] text-slate-300 leading-normal max-w-3xl">
                    {project.verificationResult.logs.map((log, i) => (
                      <div key={i}>{log}</div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="text-slate-500">No verification result recorded for this project.</div>
              )}
            </div>
          )}

          {/* 7. Artifacts */}
          {activeTab === 'artifacts' && (
            <div className="grid grid-cols-1 md:grid-cols-12 gap-6 text-xs font-mono">
              {/* File list */}
              <div className="md:col-span-4 space-y-2">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">Created Artifacts</h3>
                {project.artifacts && project.artifacts.map((art, idx) => (
                  <button
                    key={art.id}
                    onClick={() => setActiveArtifactIndex(idx)}
                    className={cn(
                      "w-full text-left p-2.5 rounded border transition-colors flex items-center gap-2",
                      activeArtifactIndex === idx 
                        ? "bg-slate-900 border-indigo-500/40 text-indigo-300" 
                        : "bg-[#060a12] border-slate-800 hover:bg-slate-900/30 text-slate-400"
                    )}
                  >
                    <FileCode className="h-4 w-4 text-indigo-400" />
                    <div className="min-w-0">
                      <span className="font-bold block truncate">{art.name}</span>
                      <span className="text-[9px] text-slate-500 truncate block">{art.path}</span>
                    </div>
                  </button>
                ))}
              </div>

              {/* Code viewer */}
              <div className="md:col-span-8 space-y-2">
                {project.artifacts && project.artifacts[activeArtifactIndex] ? (
                  <>
                    <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">File Preview: {project.artifacts[activeArtifactIndex].name}</h3>
                    <div className="bg-slate-950 border border-slate-900 rounded-lg p-3 text-[10px] text-slate-300 overflow-x-auto whitespace-pre leading-relaxed h-72">
                      <code>{project.artifacts[activeArtifactIndex].content}</code>
                    </div>
                  </>
                ) : (
                  <div className="h-full flex items-center justify-center text-slate-600">No artifacts generated.</div>
                )}
              </div>
            </div>
          )}

          {/* 8. Walkthrough */}
          {activeTab === 'walkthrough' && (
            <div className="space-y-5 text-xs font-mono max-w-3xl">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div>
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">Project Walkthrough Summary</h3>
                  <p className="text-[10px] text-slate-500 mt-1">Aggregated changes of all execution units.</p>
                </div>
                <button
                  onClick={() => setIsPlayingAudio(!isPlayingAudio)}
                  className="bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-slate-200 border border-slate-850 px-3 py-1.5 rounded flex items-center gap-1.5"
                >
                  <Volume2 className="h-4 w-4" />
                  {isPlayingAudio ? "Playing walkthrough guide..." : "Play Audio Walkthrough"}
                </button>
              </div>

              <div className="space-y-4">
                <div className="bg-[#060a12] p-3 border border-slate-800 rounded">
                  <h4 className="font-bold text-slate-300 mb-1 text-xs">Technical Output Summary</h4>
                  <p className="text-slate-400 leading-relaxed text-[11px]">
                    Created custom Next.js landing portal matching corporate guideline context. Setup local SQLite database schemas, and structured secure POST email messaging submission route.
                  </p>
                </div>

                <div className="bg-amber-950/10 border border-amber-500/20 p-3 rounded text-[11px] text-amber-300">
                  <span className="font-bold block mb-1">Self-Correction Report:</span>
                  Authentication session checking unit tests failed initially. Reflection logic auto-applied process-env testing bypass checking to enable compilation.
                </div>
              </div>
            </div>
          )}

          {/* 9. Memory */}
          {activeTab === 'memory' && (
            <div className="space-y-4 text-xs font-mono">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">Local Obsidian Sync Status</h3>
              <div className="bg-slate-900 border border-slate-800 p-3.5 rounded-lg max-w-xl space-y-3">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2 text-[11px]">
                  <span className="text-slate-400">Obsidian Vault Status:</span>
                  <span className="text-emerald-400 font-bold bg-emerald-500/10 px-1.5 py-0.5 rounded">CONNECTED</span>
                </div>
                <div className="flex items-center justify-between border-b border-slate-800 pb-2 text-[11px]">
                  <span className="text-slate-400">Vault Location:</span>
                  <span className="text-slate-200">C:/Users/Anshif/Obsidian/Lordminds</span>
                </div>
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-slate-400">Last Sync:</span>
                  <span className="text-slate-300">2026-08-31 09:02:25</span>
                </div>
              </div>

              <div className="space-y-2">
                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Decisions Written to Memory</span>
                <div className="bg-slate-950 border border-slate-900 p-3 rounded max-w-2xl">
                  <p className="text-[11px] text-slate-400 leading-normal">
                    <span className="text-indigo-400 font-bold">Decision:</span> Local SQLite stack chosen. Auto-applied test token bypass logic. Brand alignment validated by CMO Twin recommendation templates.
                  </p>
                </div>
              </div>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}
