'use client';

import React from 'react';
import { SpecialistInfo, DispatchAttempt } from '../../lib/types';
import { Bot, Cpu, Database, Shield, Wrench, Globe, Image, Terminal, Network, AlertCircle, CheckCircle2 } from 'lucide-react';
import { Badge } from '../ui/Badge';

export const ALL_10_SPECIALISTS: SpecialistInfo[] = [
  {
    id: 'web_dev',
    name: 'Web Development',
    category: 'BUILD',
    description: 'Builds modern responsive web applications, interactive UI surfaces, and frontend integrations.',
    defaultModel: 'claude-3-5-sonnet',
    modelStatus: 'NOT CONFIGURED',
    state: 'IDLE',
    capabilities: ['React', 'Next.js', 'Tailwind', 'State Management', 'Accessibility'],
  },
  {
    id: 'backend',
    name: 'Backend Engineering',
    category: 'BUILD',
    description: 'Implements server architectures, asynchronous microservices, business logic, and API routes.',
    defaultModel: 'claude-3-5-sonnet',
    modelStatus: 'NOT CONFIGURED',
    state: 'IDLE',
    capabilities: ['FastAPI', 'Python', 'Node.js', 'AsyncIO', 'Authentication'],
  },
  {
    id: 'api_integration',
    name: 'API Integration',
    category: 'BUILD',
    description: 'Connects external web services, protocols, webhook handlers, and third-party APIs.',
    defaultModel: 'gpt-4o',
    modelStatus: 'NOT CONFIGURED',
    state: 'IDLE',
    capabilities: ['REST', 'GraphQL', 'Webhooks', 'OAuth', 'Rate Limiting'],
  },
  {
    id: 'image_gen',
    name: 'Image Generation',
    category: 'BUILD',
    description: 'Generates creative visual assets, branding elements, and multimodal diagrams.',
    defaultModel: 'dall-e-3',
    modelStatus: 'NOT CONFIGURED',
    state: 'IDLE',
    capabilities: ['Asset Generation', 'SVG Icons', 'Diagrams', 'Visual Mockups'],
  },
  {
    id: 'database',
    name: 'Database Specialist',
    category: 'DATA',
    description: 'Architects schemas, executes migrations, analyzes query indexes, and ensures consistency.',
    defaultModel: 'claude-3-5-sonnet',
    modelStatus: 'NOT CONFIGURED',
    state: 'IDLE',
    capabilities: ['SQLite', 'PostgreSQL', 'Migrations', 'Indexing', 'Query Optimization'],
  },
  {
    id: 'research',
    name: 'Research & Evidence',
    category: 'DATA',
    description: 'Gathers external evidence, parses technical documentation, and cross-references facts.',
    defaultModel: 'gpt-4o',
    modelStatus: 'NOT CONFIGURED',
    state: 'IDLE',
    capabilities: ['Jina Reader', 'Web Search', 'Technical RFCs', 'Evidence Synthesis'],
  },
  {
    id: 'ai_ml',
    name: 'AI / ML Specialist',
    category: 'DATA',
    description: 'Manages model prompts, embeddings, vector indexing, and inference optimization.',
    defaultModel: 'claude-3-5-sonnet',
    modelStatus: 'NOT CONFIGURED',
    state: 'IDLE',
    capabilities: ['Prompt Engineering', 'Embeddings', 'Context Compression', 'Evaluation'],
  },
  {
    id: 'testing',
    name: 'Testing & QA',
    category: 'QUALITY',
    description: 'Writes unit, integration, and E2E test suites with coverage assertions and fuzzing.',
    defaultModel: 'claude-3-5-sonnet',
    modelStatus: 'NOT CONFIGURED',
    state: 'IDLE',
    capabilities: ['PyTest', 'Jest', 'Integration Verification', 'Contract Tests'],
  },
  {
    id: 'security',
    name: 'Security & Audit',
    category: 'QUALITY',
    description: 'Audits code for vulnerabilities, secret leakage, auth bypass, and compliance breaches.',
    defaultModel: 'claude-3-5-sonnet',
    modelStatus: 'NOT CONFIGURED',
    state: 'IDLE',
    capabilities: ['Vulnerability Scan', 'Secret Detection', 'Permission Review', 'SAST'],
  },
  {
    id: 'devops',
    name: 'DevOps & Infra',
    category: 'QUALITY',
    description: 'Configures CI/CD pipelines, containerization, environment variables, and deployment scripts.',
    defaultModel: 'claude-3-5-sonnet',
    modelStatus: 'NOT CONFIGURED',
    state: 'IDLE',
    capabilities: ['Docker', 'CI/CD Pipelines', 'Environment Guardrails', 'Logging'],
  },
];

interface WorkforceMapProps {
  attempts?: DispatchAttempt[];
  activeSpecialistId?: string | null;
  onSelectSpecialist?: (id: string) => void;
  className?: string;
}

export const WorkforceMap: React.FC<WorkforceMapProps> = ({
  attempts = [],
  activeSpecialistId,
  onSelectSpecialist,
  className = '',
}) => {
  // Map attempts to specialists
  const specialistStats = React.useMemo(() => {
    const stats: Record<string, { attemptsCount: number; lastError?: string | null; lastStatus?: string }> = {};
    ALL_10_SPECIALISTS.forEach((s) => {
      const specAttempts = attempts.filter(
        (a) =>
          a.specialist_id?.toLowerCase() === s.id.toLowerCase() ||
          a.specialist_id?.toLowerCase() === s.name.toLowerCase() ||
          a.step_id?.toLowerCase().includes(s.id.toLowerCase())
      );
      const latest = specAttempts[specAttempts.length - 1];
      stats[s.id] = {
        attemptsCount: specAttempts.length,
        lastError: latest?.error,
        lastStatus: latest?.status,
      };
    });
    return stats;
  }, [attempts]);

  const categories = ['BUILD', 'DATA', 'QUALITY'] as const;

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Top Architecture Hierarchy Banner */}
      <div className="flex flex-col items-center justify-center p-4 bg-space-900 border border-space-800 rounded-lg text-center font-mono-tech">
        <div className="flex items-center gap-2 text-xs font-bold text-slate-100 uppercase tracking-wider mb-1">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          Master Orchestrator
          <span className="text-slate-600">→</span>
          Planner Agent (Port 8002)
          <span className="text-slate-600">→</span>
          10 Autonomous Specialists
        </div>
        <div className="text-[11px] text-slate-400">
          Dispatched concurrently via real DAG Engine with Result Verification & Failure Policies
        </div>
      </div>

      {/* 3 Clusters */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {categories.map((cat) => {
          const specialists = ALL_10_SPECIALISTS.filter((s) => s.category === cat);
          return (
            <div key={cat} className="bg-space-900/90 border border-space-800 rounded-lg p-4 flex flex-col gap-3">
              <div className="flex items-center justify-between pb-2 border-b border-space-800 font-mono-tech">
                <span className="text-xs font-bold text-slate-200 tracking-wider">
                  {cat} SPECIALISTS
                </span>
                <span className="text-[10px] text-slate-500">{specialists.length} AGENTS</span>
              </div>

              <div className="space-y-2.5">
                {specialists.map((spec) => {
                  const stat = specialistStats[spec.id] || { attemptsCount: 0 };
                  const isSelected = activeSpecialistId === spec.id;

                  return (
                    <div
                      key={spec.id}
                      onClick={() => onSelectSpecialist?.(spec.id)}
                      className={`p-3 rounded-md border transition-all cursor-pointer text-left ${
                        isSelected
                          ? 'bg-space-800 border-sky-500 shadow-md ring-1 ring-sky-500/50'
                          : 'bg-space-950 hover:bg-space-850 border-space-800 hover:border-space-750'
                      }`}
                    >
                      <div className="flex items-center justify-between gap-1 mb-1">
                        <span className="text-xs font-bold text-slate-100 font-mono-tech truncate">
                          {spec.name}
                        </span>
                        <span className="text-[9px] font-mono-tech px-1.5 py-0.2 rounded bg-rose-950/60 border border-rose-900/60 text-rose-300">
                          {spec.modelStatus}
                        </span>
                      </div>

                      <p className="text-[11px] text-slate-400 line-clamp-2 leading-relaxed mb-2 font-sans">
                        {spec.description}
                      </p>

                      <div className="flex items-center justify-between pt-2 border-t border-space-850/80 text-[10px] font-mono-tech text-slate-500">
                        <span>Attempts: {stat.attemptsCount}</span>
                        {stat.lastError && (
                          <span className="text-rose-400 truncate max-w-[120px]" title={stat.lastError}>
                            {stat.lastError.includes('MODEL_UNAVAILABLE') ? 'MODEL_UNAVAILABLE' : 'ERR'}
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
