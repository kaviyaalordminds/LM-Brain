import React, { useState } from 'react';
import {
  CheckCircle2,
  Clock,
  Filter,
  History,
  RotateCcw,
  Search,
  Sparkles,
  XCircle,
} from 'lucide-react';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { Card } from '../components/common/Card';
import { PageId } from '../components/layout/Sidebar';
import { mockRuns } from '../mock';
import { OrchestrationStatus, WorkflowRun } from '../types';

interface RunsHistoryPageProps {
  onNavigate: (page: PageId) => void;
  onSelectRun: (run: WorkflowRun) => void;
}

export const RunsHistoryPage: React.FC<RunsHistoryPageProps> = ({
  onNavigate,
  onSelectRun,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');

  const filteredRuns = mockRuns.filter((r) => {
    const matchesSearch = r.runId.toLowerCase().includes(searchTerm.toLowerCase()) ||
      r.userGoal.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'ALL' || r.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-xl md:text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <History className="w-5 h-5 text-indigo-400" />
            Autonomous Runs History
          </h1>
          <p className="text-xs md:text-sm text-slate-400">
            Immutable audit record of all autonomous executions, verifications, and bounded failure recoveries.
          </p>
        </div>

        <Button
          variant="primary"
          size="md"
          icon={<Sparkles className="w-4 h-4" />}
          onClick={() => onNavigate('new-work')}
        >
          Submit New Run
        </Button>
      </div>

      {/* Filters and Search Bar */}
      <div className="p-4 rounded-xl border border-slate-800 bg-[#111827] flex flex-wrap items-center justify-between gap-4 text-xs">
        <div className="relative flex-1 min-w-[240px]">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by Run ID or requirement goal..."
            className="w-full bg-[#080C14] border border-slate-700/80 rounded-lg pl-9 pr-4 py-2 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 font-sans"
          />
        </div>

        <div className="flex items-center gap-2 font-mono">
          <span className="text-slate-400">Status:</span>
          {['ALL', 'COMPLETED', 'FAILED'].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
                statusFilter === st
                  ? 'bg-indigo-600 text-white'
                  : 'bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800'
              }`}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      {/* Runs Table */}
      <Card
        title="Execution Timeline Records"
        subtitle={`Showing ${filteredRuns.length} of ${mockRuns.length} recorded autonomous runs`}
        icon={<History className="w-4 h-4 text-indigo-400" />}
      >
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 uppercase tracking-wider">
                <th className="pb-3 font-semibold">RUN ID</th>
                <th className="pb-3 font-semibold">REQUIREMENT GOAL</th>
                <th className="pb-3 font-semibold">STATUS</th>
                <th className="pb-3 font-semibold">DURATION</th>
                <th className="pb-3 font-semibold">RECOVERY</th>
                <th className="pb-3 font-semibold">VERIFICATION</th>
                <th className="pb-3 font-semibold text-right">ACTION</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {filteredRuns.map((run) => (
                <tr key={run.runId} className="hover:bg-slate-900/40 transition-colors">
                  <td className="py-4 font-bold text-indigo-300">{run.runId}</td>
                  <td className="py-4 font-sans text-slate-200 max-w-md">
                    <div className="font-medium truncate">{run.userGoal.split('\n')[0]}</div>
                    <div className="text-[11px] text-slate-500 font-mono mt-0.5">
                      Started: {run.startedAt}
                    </div>
                  </td>
                  <td className="py-4">
                    {run.status === 'COMPLETED' ? (
                      <Badge variant="success" size="sm" dot>COMPLETED</Badge>
                    ) : run.status === 'FAILED' ? (
                      <Badge variant="danger" size="sm" dot>FAILED — BOUNDED</Badge>
                    ) : (
                      <Badge variant="warning" size="sm" dot>{run.status}</Badge>
                    )}
                  </td>
                  <td className="py-4 text-slate-300">{run.durationSeconds}s</td>
                  <td className="py-4">
                    {run.recoveryHistory.length > 0 ? (
                      <Badge variant="warning" size="sm">
                        {run.recoveryHistory.length} Attempt{run.recoveryHistory.length > 1 ? 's' : ''}
                      </Badge>
                    ) : (
                      <span className="text-slate-500">0</span>
                    )}
                  </td>
                  <td className="py-4">
                    {run.status === 'COMPLETED' ? (
                      <span className="text-emerald-400 font-semibold flex items-center gap-1">
                        <CheckCircle2 className="w-3.5 h-3.5" /> VERIFIED
                      </span>
                    ) : (
                      <span className="text-rose-400 font-semibold flex items-center gap-1">
                        <XCircle className="w-3.5 h-3.5" /> BLOCKED
                      </span>
                    )}
                  </td>
                  <td className="py-4 text-right">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        onSelectRun(run);
                        onNavigate('live-run');
                      }}
                    >
                      Open Timeline
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};
