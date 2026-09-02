'use client';

import React from 'react';
import {
  Code,
  Image,
  Sparkles,
  FileImage,
  Mic,
  Music,
  UserCheck,
  Paintbrush,
  Presentation,
  FileText,
  FileSpreadsheet,
  PenTool,
  Send,
  CloudLightning,
  MessagesSquare,
  Play,
  CheckCircle,
  Clock
} from 'lucide-react';
import { SpecialistAgent } from '@/lib/types';
import { cn } from '@/lib/utils/cn';

interface BasicModeViewProps {
  agents: SpecialistAgent[];
  onTriggerAgent: (agentName: string, query: string) => void;
}

export function BasicModeView({ agents, onTriggerAgent }: BasicModeViewProps) {
  // Map capabilities to icons
  const getIcon = (cap: string) => {
    switch (cap) {
      case 'Web Development': return Code;
      case 'Poster': return Image;
      case 'Logo / Branding': return Sparkles;
      case 'Image Generation': return FileImage;
      case 'Image Enhancement': return Sparkles;
      case 'Audio Transcription': return Mic;
      case 'Audio Generation': return Music;
      case 'Voice Processing / Cloning': return UserCheck;
      case 'Graphic Design': return Paintbrush;
      case 'PPT': return Presentation;
      case 'Document': return FileText;
      case 'Spreadsheet': return FileSpreadsheet;
      case 'Content Creation': return PenTool;
      case 'Deployment': return CloudLightning;
      case 'Communication': return MessagesSquare;
      case 'Software Development': return Code;
      default: return Code;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ready': return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20';
      case 'local': return 'text-indigo-400 bg-indigo-500/10 border-indigo-500/20';
      case 'offline': return 'text-slate-500 bg-slate-800/10 border-slate-700/20';
      case 'coming_online': return 'text-amber-500 bg-amber-500/10 border-amber-500/20';
      default: return 'text-slate-400 bg-slate-900/50';
    }
  };

  const getStatusLabel = (status: string) => {
    if (status === 'ready') return 'Ready';
    if (status === 'local') return 'Local';
    if (status === 'offline') return 'Offline';
    if (status === 'coming_online') return 'Syncing';
    return status;
  };

  // 15 Capabilities specified in requirements:
  const capabilitiesList = [
    { cap: 'Web Development', name: 'Frontend Agent', desc: 'Build responsive Next.js/HTML applications.', status: 'ready' },
    { cap: 'Poster', name: 'Poster Agent', desc: 'Generate poster visual layouts & concepts.', status: 'ready' },
    { cap: 'Logo / Branding', name: 'Logo / Branding Agent', desc: 'Synthesize logo assets and color codes.', status: 'coming_online' },
    { cap: 'Image Generation', name: 'Image Agent', desc: 'Create illustrations and marketing vectors.', status: 'ready' },
    { cap: 'Image Enhancement', name: 'Vision Agent', desc: 'Enlarge or restore visual details.', status: 'ready' },
    { cap: 'Audio Transcription', name: 'Audio Transcription Agent', desc: 'Whisper-powered audio files transcription.', status: 'ready' },
    { cap: 'Audio Generation', name: 'Audio Generation Agent', desc: 'Synthesize audio clips and backdrops.', status: 'ready' },
    { cap: 'Voice Processing / Cloning', name: 'Voice Cloning Agent', desc: 'Clone verified speaker parameters.', status: 'offline' },
    { cap: 'Graphic Design', name: 'Design Agent', desc: 'Combine shapes, layers, and text blocks.', status: 'ready' },
    { cap: 'PPT', name: 'PPT Agent', desc: 'Compile project outlines into slide decks.', status: 'coming_online' },
    { cap: 'Document', name: 'Document Agent', desc: 'Write standard marketing briefs and documents.', status: 'ready' },
    { cap: 'Spreadsheet', name: 'Spreadsheet Agent', desc: 'Inject formulas and format data spreadsheets.', status: 'ready' },
    { cap: 'Content Creation', name: 'Content Agent', desc: 'Draft copy outlines and social media posts.', status: 'ready' },
    { cap: 'Deployment', name: 'Deployment Agent', desc: 'Configure local server scripts and routing.', status: 'ready' },
    { cap: 'Communication', name: 'Communication Agent', desc: 'Compose responses or validate inbox logs.', status: 'local' },
    { cap: 'Software Development', name: 'Software Agent', desc: 'Build complete software projects from requirements through implementation, testing, verification and deployment.', status: 'ready' }
  ];

  const handleCardClick = (cap: string, agentName: string) => {
    const q = prompt(`Enter instructions for ${agentName} (${cap}):`, `Generate a basic ${cap.toLowerCase()} request...`);
    if (q) {
      onTriggerAgent(agentName, q);
    }
  };

  return (
    <div className="space-y-6 select-none">
      {/* Overview header */}
      <div>
        <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">
          Specialist Capability Registry
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
          {capabilitiesList.map((item) => {
            const Icon = getIcon(item.cap);
            const isSelectable = item.status !== 'offline';
            return (
              <div
                key={item.cap}
                onClick={() => isSelectable && handleCardClick(item.cap, item.name)}
                className={cn(
                  "border border-slate-800 bg-[#0c1322] rounded-lg p-3 flex flex-col justify-between transition-all duration-150 relative",
                  isSelectable
                    ? "hover:border-indigo-500/40 hover:bg-slate-900/50 cursor-pointer"
                    : "opacity-60 cursor-not-allowed"
                )}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="h-8 w-8 rounded-lg bg-slate-900 flex items-center justify-center text-indigo-400 shrink-0 border border-slate-800">
                    <Icon className="h-4 w-4" />
                  </div>
                  <span className={cn(
                    "text-[9px] font-mono font-bold uppercase border px-2 py-0.5 rounded-full shrink-0",
                    getStatusColor(item.status)
                  )}>
                    {getStatusLabel(item.status)}
                  </span>
                </div>
                <div className="mt-3">
                  <h4 className="text-xs font-bold text-slate-200">{item.cap}</h4>
                  <p className="text-[10px] text-slate-400 mt-1 leading-normal">
                    {item.desc}
                  </p>
                </div>
                <div className="mt-3 pt-2 border-t border-slate-900 flex items-center justify-between text-[9px] font-mono text-slate-500">
                  <span>Worker: {item.name}</span>
                  {isSelectable && (
                    <span className="text-indigo-400 flex items-center gap-1 hover:text-indigo-300 font-bold">
                      Launch <Play className="h-2.5 w-2.5 fill-current" />
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Recents split layout */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4">
        {/* Recent Tasks */}
        <div className="space-y-3">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
            Recent General Tasks
          </h3>
          <div className="bg-[#0c1322]/40 border border-slate-800 rounded-lg p-3 space-y-2.5">
            <div className="flex items-center justify-between border-b border-slate-900 pb-2 text-[11px] font-mono">
              <span className="text-slate-300 truncate max-w-[200px]">"Generate a marketing poster..."</span>
              <span className="text-emerald-400 font-bold bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/20 flex items-center gap-1">
                <CheckCircle className="h-3 w-3" /> Completed
              </span>
            </div>
            <div className="flex items-center justify-between border-b border-slate-900 pb-2 text-[11px] font-mono">
              <span className="text-slate-300 truncate max-w-[200px]">"Transcribe client audio note..."</span>
              <span className="text-emerald-400 font-bold bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/20 flex items-center gap-1">
                <CheckCircle className="h-3 w-3" /> Completed
              </span>
            </div>
            <div className="flex items-center justify-between text-[11px] font-mono">
              <span className="text-slate-300 truncate max-w-[200px]">"Summarize PDF release checklist..."</span>
              <span className="text-slate-500">2h ago</span>
            </div>
          </div>
        </div>

        {/* Recent Outputs */}
        <div className="space-y-3">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
            Recent Artifacts Generated
          </h3>
          <div className="bg-[#0c1322]/40 border border-slate-800 rounded-lg p-3 space-y-2.5">
            <div className="flex items-center justify-between border-b border-slate-900 pb-2 text-[11px] font-mono">
              <span className="text-slate-300 truncate">marketing_poster_v1.png</span>
              <span className="text-slate-500">18s run time</span>
            </div>
            <div className="flex items-center justify-between border-b border-slate-900 pb-2 text-[11px] font-mono">
              <span className="text-slate-300 truncate">meeting_transcript.md</span>
              <span className="text-slate-500">42s run time</span>
            </div>
            <div className="flex items-center justify-between text-[11px] font-mono">
              <span className="text-slate-300 truncate">launch_announcement.txt</span>
              <span className="text-slate-500 font-mono">6s run time</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
