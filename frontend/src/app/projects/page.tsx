'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { Header } from '@/components/layout/Header';
import { projectService } from '@/lib/api/projectService';
import { Project } from '@/lib/types';
import {
  FolderKanban,
  Search,
  SlidersHorizontal,
  CheckCircle,
  XCircle,
  Play,
  RotateCcw,
  Clock,
  Layers,
  Users
} from 'lucide-react';
import { cn } from '@/lib/utils/cn';

export default function Page() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState<Project['status'] | 'all'>('all');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetch = async () => {
      const p = await projectService.getProjects();
      setProjects(p);
      setLoading(false);
    };
    fetch();
  }, []);

  const getStatusColor = (status: Project['status']) => {
    switch (status) {
      case 'completed': return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20';
      case 'running': return 'text-indigo-400 bg-indigo-500/10 border-indigo-500/20 animate-pulse';
      case 'planning': return 'text-amber-500 bg-amber-500/10 border-amber-500/20';
      case 'verification': return 'text-blue-400 bg-blue-500/10 border-blue-500/20';
      case 'needs_review': return 'text-rose-400 bg-rose-500/10 border-rose-500/20';
      case 'failed': return 'text-rose-600 bg-rose-950/20 border-rose-900/30';
      default: return 'text-slate-400 bg-slate-800';
    }
  };

  const getStatusLabel = (status: Project['status']) => {
    if (status === 'needs_review') return 'Needs Review';
    return status;
  };

  const filteredProjects = projects.filter(p => {
    const matchesSearch = p.name.toLowerCase().includes(search.toLowerCase()) || 
                          p.description.toLowerCase().includes(search.toLowerCase());
    const matchesFilter = filter === 'all' || p.status === filter;
    return matchesSearch && matchesFilter;
  });

  return (
    <div className="flex flex-col min-h-full pb-10">
      <Header
        title="Project Registry"
        subtitle="Manage complex workspaces, execution logs, and output history."
      />

      <div className="flex-1 px-6 py-6 space-y-6 max-w-6xl mx-auto w-full select-none">
        
        {/* Filters and search */}
        <div className="flex flex-col sm:flex-row gap-3 justify-between items-stretch sm:items-center">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search projects by title or description..."
              className="w-full bg-[#0c1322] border border-slate-800 rounded-lg pl-9 pr-4 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div className="flex items-center gap-1.5 overflow-x-auto scrollbar-none bg-[#0c1322] border border-slate-800 p-1 rounded-lg">
            {(['all', 'planning', 'running', 'verification', 'completed', 'needs_review', 'failed'] as const).map(f => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={cn(
                  "px-3 py-1.5 rounded text-[10px] uppercase font-bold tracking-wider transition-colors shrink-0",
                  filter === f ? "bg-slate-800 text-slate-100" : "text-slate-500 hover:text-slate-300"
                )}
              >
                {f === 'needs_review' ? 'Review' : f}
              </button>
            ))}
          </div>
        </div>

        {/* Loading state */}
        {loading ? (
          <div className="h-64 flex items-center justify-center font-mono text-xs text-slate-500">
            Scanning project tables...
          </div>
        ) : filteredProjects.length === 0 ? (
          <div className="h-64 flex flex-col items-center justify-center border border-dashed border-slate-800 rounded-xl text-slate-500 font-mono text-xs gap-2">
            <FolderKanban className="h-6 w-6 text-slate-700" />
            <span>No workspace directories matched filter criteria.</span>
          </div>
        ) : (
          /* Grid of projects */
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredProjects.map(project => (
              <Link
                key={project.id}
                href={`/projects/${project.id}`}
                className="border border-slate-800 hover:border-indigo-500/40 bg-[#0c1322] hover:bg-slate-900/30 rounded-xl p-4 flex flex-col justify-between transition-all duration-150 focus-ring"
              >
                <div className="space-y-3">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <h3 className="text-sm font-bold text-slate-100 hover:text-indigo-400 transition-colors">
                        {project.name}
                      </h3>
                      <span className="text-[9px] font-mono text-slate-500 block uppercase mt-0.5">
                        Mode: {project.mode} Mode
                      </span>
                    </div>

                    <span className={cn(
                      "text-[9px] font-mono font-bold uppercase border px-2 py-0.5 rounded-full shrink-0",
                      getStatusColor(project.status)
                    )}>
                      {getStatusLabel(project.status)}
                    </span>
                  </div>

                  <p className="text-xs text-slate-400 leading-normal line-clamp-2">
                    {project.description}
                  </p>
                </div>

                <div className="space-y-4 pt-4 mt-4 border-t border-slate-900">
                  {/* Progress bar */}
                  <div className="flex items-center justify-between text-[10px] font-mono">
                    <span className="text-slate-500">Task Completion:</span>
                    <span className="text-slate-300 font-bold">{project.progress}%</span>
                  </div>
                  <div className="bg-slate-950 h-1 rounded-full overflow-hidden">
                    <div className="bg-indigo-500 h-full transition-all duration-300" style={{ width: `${project.progress}%` }}></div>
                  </div>

                  {/* Agents list and details */}
                  <div className="flex items-center justify-between text-[9px] font-mono text-slate-500">
                    <div className="flex items-center gap-1">
                      <Layers className="h-3.5 w-3.5 text-indigo-400" />
                      <span>{project.twins.length} Twins</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Users className="h-3.5 w-3.5 text-indigo-400" />
                      <span>{project.agents.length} Specialists</span>
                    </div>
                    <span className="text-indigo-400 font-bold hover:text-indigo-300">
                      View details &rarr;
                    </span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}

      </div>
    </div>
  );
}
