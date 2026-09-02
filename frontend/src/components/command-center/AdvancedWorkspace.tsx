'use client';

import React, { useEffect, useRef, useState } from 'react';
import { useSimulation } from '@/lib/context/SimulationContext';
import { WorkflowStages } from '../workflow/WorkflowStages';
import {
  CheckCircle,
  XCircle,
  Play,
  Pause,
  SkipForward,
  RotateCcw,
  Calendar,
  Layers,
  FileCode,
  Volume2,
  Clock,
  ExternalLink,
  BookOpen,
  Settings,
  Eye,
  Terminal,
  Database
} from 'lucide-react';
import { cn } from '@/lib/utils/cn';

export function AdvancedWorkspace() {
  const {
    isPlaying,
    currentStep,
    simulatedEvents,
    progress,
    activeProject,
    agents,
    twins,
    setSelectedAgentId,
    setSelectedTwinId,
    startSimulation,
    pauseSimulation,
    stepForward,
    resetSimulation
  } = useSimulation();

  const [activeCodeTab, setActiveCodeTab] = useState<'layout' | 'database' | 'router'>('layout');
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const [audioProgress, setAudioProgress] = useState(0);
  const logEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll simulated activity log to bottom
  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [simulatedEvents]);

  // Audio simulator
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isPlayingAudio) {
      interval = setInterval(() => {
        setAudioProgress(p => {
          if (p >= 100) {
            setIsPlayingAudio(false);
            return 0;
          }
          return p + 2;
        });
      }, 200);
    }
    return () => clearInterval(interval);
  }, [isPlayingAudio]);

  if (!activeProject) {
    return (
      <div className="h-64 flex flex-col items-center justify-center border border-dashed border-slate-800 rounded-xl text-slate-500 font-mono text-xs gap-2 select-none">
        <Database className="h-6 w-6 text-slate-600 animate-pulse" />
        <span>Awaiting requirements deployment...</span>
      </div>
    );
  }

  // Code snippets for Walkthrough panel
  const codeFiles = {
    layout: `// filepath: src/app/layout.tsx
import '@/app/globals.css';
import Sidebar from '@/components/Sidebar';

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark bg-slate-950 text-slate-100">
      <body className="flex h-screen overflow-hidden">
        <Sidebar className="w-64 border-r border-slate-800" />
        <main className="flex-1 overflow-y-auto bg-slate-900/50">
          {children}
        </main>
      </body>
    </html>
  );
}`,
    database: `// filepath: src/lib/db.ts
import sqlite3 from 'sqlite3';

const DB_PATH = './data/workforce.db';

export function initializeDatabase() {
  const db = new sqlite3.Database(DB_PATH);
  db.serialize(() => {
    db.run(\`
      CREATE TABLE IF NOT EXISTS contacts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        message TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
      )
    \`);
  });
  return db;
}`,
    router: `// filepath: src/app/api/contact/route.ts
import { NextResponse } from 'next/server';
import { initializeDatabase } from '@/lib/db';

export async function POST(req: Request) {
  try {
    const { name, email, message } = await req.json();
    
    // Auth Token Protection Guardrail check
    const authHeader = req.headers.get('Authorization');
    if (process.env.NODE_ENV !== 'test' && !authHeader) {
      return NextResponse.json({ error: 'Unauthorized Session' }, { status: 401 });
    }

    const db = initializeDatabase();
    // Save contact query
    return NextResponse.json({ success: true, message: 'Message logged locally' });
  } catch (error) {
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}`
  };

  return (
    <div className="space-y-6">
      {/* Simulation Toolbar */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between bg-slate-900 border border-slate-800 rounded-lg p-3 gap-3 select-none">
        <div className="flex items-center gap-3">
          <div className="h-3 w-3 rounded-full bg-indigo-500 animate-ping"></div>
          <div>
            <span className="text-[10px] text-slate-400 font-mono block">PROJECT ID: simulated-project</span>
            <span className="text-xs font-bold text-slate-200 uppercase font-mono">
              Phase: {activeProject.currentPhase || 'Idle'}
            </span>
          </div>
        </div>

        {/* Playback Controls */}
        <div className="flex items-center gap-2">
          {isPlaying ? (
            <button
              onClick={pauseSimulation}
              className="flex items-center gap-1 bg-slate-800 hover:bg-slate-700 text-slate-100 text-xs py-1.5 px-3 rounded font-mono border border-slate-700 transition-colors focus-ring"
            >
              <Pause className="h-3.5 w-3.5" /> Pause
            </button>
          ) : (
            <button
              onClick={startSimulation}
              className="flex items-center gap-1 bg-indigo-600 hover:bg-indigo-500 text-white text-xs py-1.5 px-3 rounded font-mono shadow shadow-indigo-500/20 transition-colors focus-ring"
            >
              <Play className="h-3.5 w-3.5 fill-current" /> Play
            </button>
          )}

          <button
            onClick={stepForward}
            className="flex items-center gap-1 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs py-1.5 px-2.5 rounded font-mono border border-slate-700 transition-colors focus-ring"
            title="Step Forward"
          >
            <SkipForward className="h-3.5 w-3.5" /> Step
          </button>

          <button
            onClick={resetSimulation}
            className="flex items-center gap-1 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs py-1.5 px-2.5 rounded font-mono border border-slate-700 transition-colors focus-ring"
            title="Reset Simulation"
          >
            <RotateCcw className="h-3.5 w-3.5" /> Reset
          </button>
        </div>
      </div>

      {/* 12 Stages pipeline */}
      <WorkflowStages currentStep={currentStep} />

      {/* Grid Dashboard */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Requirements & Plan Panel (Left - 5 Cols) */}
        <div className="lg:col-span-5 space-y-6">
          
          {/* Requirement Panel */}
          <div className="bg-[#0c1322] border border-slate-800 rounded-lg p-4 space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <BookOpen className="h-4 w-4 text-indigo-400" /> Perception Requirements
            </h3>

            <div className="space-y-3 text-xs">
              <div className="bg-[#060a12] p-2.5 rounded border border-slate-900 font-mono">
                <span className="text-[10px] text-indigo-400 block mb-1">ORIGINAL REQUEST:</span>
                <p className="text-slate-300">"{activeProject.description}"</p>
              </div>

              {/* Obsidian retrieved guidelines */}
              <div className="bg-slate-900/50 p-2.5 rounded border border-slate-800 space-y-1 font-mono text-[11px]">
                <span className="text-[10px] text-amber-500 font-bold block">RETRIEVED BRAND GUIDELINES:</span>
                <p className="text-slate-400 leading-normal">
                  Vault query pulled brand specs. Primary dark palette with Indigo accents. Configured for local offline storage stack.
                </p>
              </div>

              {/* Requirement checkboxes */}
              <div className="space-y-2 pt-1">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Functional Requirements</span>
                <div className="space-y-1.5 font-mono text-[11px]">
                  {activeProject.requirements.map(req => (
                    <div key={req.id} className="flex items-start gap-2">
                      {req.status === 'satisfied' ? (
                        <CheckCircle className="h-3.5 w-3.5 text-emerald-400 shrink-0 mt-0.5" />
                      ) : req.status === 'failed' ? (
                        <XCircle className="h-3.5 w-3.5 text-rose-400 shrink-0 mt-0.5" />
                      ) : (
                        <div className="h-3.5 w-3.5 rounded border border-slate-700 shrink-0 mt-0.5"></div>
                      )}
                      <span className={cn(
                        req.status === 'satisfied' ? "text-slate-300 line-through decoration-slate-800" : "text-slate-400"
                      )}>{req.text}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Plan Panel */}
          <div className="bg-[#0c1322] border border-slate-800 rounded-lg p-4 space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <Calendar className="h-4 w-4 text-indigo-400" /> Orchestrator Planner Steps
            </h3>

            <div className="space-y-2.5 font-mono text-[11px]">
              {activeProject.plan.map((step, idx) => (
                <div
                  key={step.id}
                  className={cn(
                    "flex items-start gap-3 p-2 rounded border transition-colors",
                    step.status === 'completed' && "bg-[#060a12]/50 border-slate-900 text-slate-500",
                    step.status === 'running' && "bg-indigo-950/20 border-indigo-500/30 text-slate-200",
                    step.status === 'retrying' && "bg-amber-950/20 border-amber-500/30 text-amber-200",
                    step.status === 'failed' && "bg-rose-950/20 border-rose-500/30 text-rose-200",
                    step.status === 'pending' && "border-transparent text-slate-600"
                  )}
                >
                  <div className="font-bold text-slate-400 shrink-0">{idx + 1}.</div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-1.5">
                      <span className="font-semibold text-xs leading-none truncate">{step.title}</span>
                      <span className={cn(
                        "text-[9px] font-bold uppercase",
                        step.status === 'completed' && "text-emerald-400",
                        step.status === 'running' && "text-indigo-400 animate-pulse",
                        step.status === 'retrying' && "text-amber-500 animate-pulse",
                        step.status === 'failed' && "text-rose-500",
                        step.status === 'pending' && "text-slate-600"
                      )}>{step.status}</span>
                    </div>
                    <p className="text-[10px] text-slate-400 mt-1 leading-normal">{step.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

        </div>

        {/* Workforce & Log Feed (Right - 7 Cols) */}
        <div className="lg:col-span-7 space-y-6">
          
          {/* Workforce Panel */}
          <div className="bg-[#0c1322] border border-slate-800 rounded-lg p-4 space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <Layers className="h-4 w-4 text-indigo-400" /> Active Workforce Workers
            </h3>

            {/* Twins & Specialists grid */}
            <div className="space-y-3 select-none">
              
              {/* Executive Twins activated */}
              <div className="space-y-2">
                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Executive Strategy Layer</span>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {twins
                    .filter(t => t.status === 'active' || t.status === 'completed')
                    .map(twin => (
                      <div
                        key={twin.id}
                        onClick={() => setSelectedTwinId(twin.id)}
                        className="bg-slate-900/60 hover:bg-slate-900 border border-slate-800 rounded p-2.5 cursor-pointer flex items-center justify-between text-xs transition-colors focus-ring"
                      >
                        <div className="min-w-0">
                          <span className="font-bold text-slate-200 block truncate">{twin.name}</span>
                          <span className="text-[9px] text-slate-400 font-mono">Executive: {twin.role}</span>
                        </div>
                        <span className={cn(
                          "text-[9px] font-mono font-bold uppercase px-1.5 py-0.5 rounded border shrink-0",
                          twin.status === 'active' ? "text-indigo-400 bg-indigo-500/10 border-indigo-500/20 animate-pulse" : "text-slate-400 bg-slate-800 border-slate-700"
                        )}>
                          {twin.status}
                        </span>
                      </div>
                    ))}
                  {twins.filter(t => t.status === 'active' || t.status === 'completed').length === 0 && (
                    <div className="col-span-2 text-center py-2 text-[10px] text-slate-600 font-mono">
                      No Executive Twin active. Delegated to Specialist directly.
                    </div>
                  )}
                </div>
              </div>

              {/* Specialists spawned */}
              <div className="space-y-2">
                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Specialist Agents Execution Layer</span>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {agents
                    .filter(a => a.status !== 'ready' && a.status !== 'offline')
                    .map(agent => (
                      <div
                        key={agent.id}
                        onClick={() => setSelectedAgentId(agent.id)}
                        className="bg-slate-900/60 hover:bg-slate-900 border border-slate-800 rounded p-2.5 cursor-pointer flex flex-col justify-between min-h-[64px] transition-colors focus-ring"
                      >
                        <div className="flex items-start justify-between gap-1.5">
                          <div className="min-w-0">
                            <span className="font-bold text-slate-200 block truncate">{agent.name}</span>
                            <span className="text-[9px] text-slate-500 font-mono truncate block" title={agent.model}>{agent.model}</span>
                          </div>
                          <span className={cn(
                            "text-[8px] font-mono font-bold uppercase px-1.5 py-0.5 rounded shrink-0",
                            agent.status === 'spawn' && "text-slate-400 bg-slate-800",
                            agent.status === 'running' && "text-indigo-400 bg-indigo-500/10 border border-indigo-500/20 animate-pulse",
                            agent.status === 'failed' && "text-rose-500 bg-rose-500/10 border border-rose-500/20",
                            agent.status === 'reflect' && "text-amber-500 bg-amber-500/10 border border-amber-500/20",
                            agent.status === 'retry' && "text-amber-400 bg-amber-500/10 border border-amber-500/20 animate-pulse",
                            agent.status === 'complete' && "text-emerald-400 bg-emerald-500/10 border border-emerald-500/20",
                            agent.status === 'terminate' && "text-slate-600 bg-slate-950 border border-slate-900"
                          )}>
                            {agent.status}
                          </span>
                        </div>
                        {agent.status !== 'terminate' && (
                          <div className="mt-2 flex items-center gap-2">
                            <div className="flex-1 bg-slate-950 h-1 rounded-full overflow-hidden">
                              <div className="bg-indigo-500 h-full transition-all duration-300" style={{ width: `${agent.progress}%` }}></div>
                            </div>
                            <span className="text-[9px] font-bold text-slate-300 shrink-0 font-mono">{agent.progress}%</span>
                          </div>
                        )}
                      </div>
                    ))}
                  {agents.filter(a => a.status !== 'ready' && a.status !== 'offline').length === 0 && (
                    <div className="col-span-2 text-center py-4 text-[10px] text-slate-600 font-mono border border-dashed border-slate-900 rounded">
                      Workers offline. Trigger task in composer to spawn active workers.
                    </div>
                  )}
                </div>
              </div>

            </div>
          </div>

          {/* Activity Event Feed */}
          <div className="bg-[#0c1322] border border-slate-800 rounded-lg p-4 space-y-4 flex flex-col h-[280px]">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5 shrink-0">
              <Terminal className="h-4 w-4 text-indigo-400 animate-pulse" /> Live Workforce Stream Log
            </h3>
            
            <div className="flex-1 overflow-y-auto bg-slate-950 border border-slate-900 p-2.5 rounded space-y-2 font-mono text-[10px] leading-relaxed">
              {simulatedEvents.map((evt) => (
                <div key={evt.id} className="flex gap-2 items-start border-b border-slate-900/50 pb-1.5 last:border-none">
                  <span className="text-slate-600 shrink-0 select-none">
                    {new Date(evt.timestamp).toLocaleTimeString()}
                  </span>
                  <span className={cn(
                    "font-bold uppercase tracking-tighter text-[9px] border px-1 rounded shrink-0",
                    evt.type === 'error' && "text-rose-500 border-rose-500/20 bg-rose-500/5",
                    evt.type === 'warning' && "text-amber-500 border-amber-500/20 bg-amber-500/5",
                    evt.type === 'success' && "text-emerald-500 border-emerald-500/20 bg-emerald-500/5",
                    evt.type === 'info' && "text-indigo-400 border-indigo-500/20 bg-indigo-500/5"
                  )}>
                    {evt.component}
                  </span>
                  <span className={cn(
                    evt.type === 'error' && "text-rose-300",
                    evt.type === 'warning' && "text-amber-300 font-semibold",
                    evt.type === 'success' && "text-emerald-300",
                    evt.type === 'info' && "text-slate-300"
                  )}>
                    {evt.message}
                  </span>
                </div>
              ))}
              {simulatedEvents.length === 0 && (
                <div className="h-full flex items-center justify-center text-slate-600">
                  No active logs. Click "Start Workforce" to execute task.
                </div>
              )}
              <div ref={logEndRef}></div>
            </div>
          </div>

        </div>

      </div>

      {/* Final Walkthrough / Code outputs (Visible only when simulation completes - step 21/22) */}
      {(currentStep >= 21 || progress === 100) && (
        <div className="bg-[#0c1322] border border-emerald-500/30 rounded-lg p-5 space-y-6 premium-glow-emerald select-none animate-shimmer" style={{ backgroundSize: '200% auto' }}>
          
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between border-b border-slate-800 pb-3 gap-3">
            <div className="flex items-center gap-2.5">
              <CheckCircle className="h-5 w-5 text-emerald-400" />
              <div>
                <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wider">Final Result Walkthrough</h3>
                <p className="text-[10px] text-slate-400 font-mono">Workspace validated successfully. Project compilation passed.</p>
              </div>
            </div>

            {/* Play voice walkthrough */}
            <button
              onClick={() => setIsPlayingAudio(!isPlayingAudio)}
              className={cn(
                "flex items-center gap-1.5 text-xs py-1.5 px-3 rounded font-mono border transition-all focus-ring",
                isPlayingAudio 
                  ? "bg-emerald-950/40 text-emerald-400 border-emerald-500/40" 
                  : "bg-slate-900 border-slate-800 text-slate-400 hover:bg-slate-800 hover:text-slate-200"
              )}
            >
              <Volume2 className="h-4 w-4" />
              {isPlayingAudio ? `Voice: ${audioProgress}%` : "Play Audio Walkthrough"}
            </button>
          </div>

          {/* Quick Metrics */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs font-mono">
            <div className="bg-slate-900/60 p-2 border border-slate-800/80 rounded">
              <span className="text-slate-500 block">Total Runtime:</span>
              <span className="text-slate-200 font-bold text-sm">2m 14s</span>
            </div>
            <div className="bg-slate-900/60 p-2 border border-slate-800/80 rounded">
              <span className="text-slate-500 block">Workers Used:</span>
              <span className="text-slate-200 font-bold text-sm">5 Specialist Agents</span>
            </div>
            <div className="bg-slate-900/60 p-2 border border-slate-800/80 rounded">
              <span className="text-slate-500 block">Verification Tests:</span>
              <span className="text-emerald-400 font-bold text-sm">8 / 8 Passed</span>
            </div>
            <div className="bg-slate-900/60 p-2 border border-slate-800/80 rounded">
              <span className="text-slate-500 block">Obsidian Status:</span>
              <span className="text-emerald-400 font-bold text-sm uppercase">Synchronized</span>
            </div>
          </div>

          {/* Code Files Visualizer */}
          <div className="space-y-3">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">Created Codebase Files</span>
            <div className="bg-slate-950 border border-slate-850 rounded-lg overflow-hidden flex flex-col">
              
              {/* Tab Selector */}
              <div className="flex border-b border-slate-900 bg-[#090d16] text-[10px] font-mono">
                <button
                  onClick={() => setActiveCodeTab('layout')}
                  className={cn(
                    "px-4 py-2 border-r border-slate-900 transition-colors focus:outline-none",
                    activeCodeTab === 'layout' ? "bg-slate-950 text-indigo-400 border-b-2 border-b-indigo-500" : "text-slate-500 hover:bg-slate-900/30"
                  )}
                >
                  layout.tsx
                </button>
                <button
                  onClick={() => setActiveCodeTab('database')}
                  className={cn(
                    "px-4 py-2 border-r border-slate-900 transition-colors focus:outline-none",
                    activeCodeTab === 'database' ? "bg-slate-950 text-indigo-400 border-b-2 border-b-indigo-500" : "text-slate-500 hover:bg-slate-900/30"
                  )}
                >
                  db.ts
                </button>
                <button
                  onClick={() => setActiveCodeTab('router')}
                  className={cn(
                    "px-4 py-2 border-r border-slate-900 transition-colors focus:outline-none",
                    activeCodeTab === 'router' ? "bg-slate-950 text-indigo-400 border-b-2 border-b-indigo-500" : "text-slate-500 hover:bg-slate-900/30"
                  )}
                >
                  route.ts
                </button>
              </div>

              {/* Code display */}
              <div className="p-3 text-[10px] font-mono text-slate-300 bg-[#04070d] overflow-x-auto whitespace-pre leading-relaxed h-56 select-text">
                <code>{codeFiles[activeCodeTab]}</code>
              </div>
            </div>
          </div>

          {/* Verification failure reflection summary */}
          <div className="bg-amber-950/15 border border-amber-500/20 rounded p-3 text-xs font-mono text-amber-300 space-y-1.5">
            <div className="font-bold flex items-center gap-1.5">
              <span>⚠️ System Failure Recovery Checklist:</span>
            </div>
            <p className="text-[11px] leading-normal text-amber-400">
              During phase 3 execution, Testing Agent reported a verification failure on Contact submission due to missing session validation values. The Orchestrator automatically initiated Reflection: patched the API route to bypass authentication checks in test mode, updated the plan configuration, and re-executed code validation.
            </p>
          </div>

        </div>
      )}
    </div>
  );
}
