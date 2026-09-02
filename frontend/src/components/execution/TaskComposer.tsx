'use client';

import React, { useState } from 'react';
import { Play, Sparkles, Loader2, AlertCircle } from 'lucide-react';
import { orchestratorApi } from '../../lib/api/orchestrator';

interface TaskComposerProps {
  onExecutionCreated: (executionId: string) => void;
  className?: string;
}

const SAMPLE_INTENTS = [
  'Build a full-stack user authentication module with password hashing and JWT',
  'Design and implement database schema migration with index analysis',
  'Implement automated end-to-end testing suite for API endpoints',
  'Audit infrastructure security configurations and generate compliance report',
];

export const TaskComposer: React.FC<TaskComposerProps> = ({
  onExecutionCreated,
  className = '',
}) => {
  const [requestText, setRequestText] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const text = requestText.trim();
    if (!text || isSubmitting) return;

    setIsSubmitting(true);
    setError(null);

    try {
      const res = await orchestratorApi.createExecution(text, {
        source: 'web_control_center',
        client_timestamp: new Date().toISOString(),
      });
      setRequestText('');
      onExecutionCreated(res.execution_id);
    } catch (err: any) {
      setError(err?.message || 'Failed to trigger execution');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className={`bg-space-900 border border-space-800 rounded-lg p-4 shadow-md ${className}`}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-emerald-400" />
          <h2 className="text-xs font-semibold font-mono-tech uppercase tracking-wider text-slate-100">
            Dispatch Autonomous Task
          </h2>
        </div>
        <span className="text-[10px] text-slate-500 font-mono-tech">
          Target: Master Orchestrator (127.0.0.1:8000)
        </span>
      </div>

      <form onSubmit={handleSubmit} className="space-y-3">
        <div className="relative">
          <textarea
            rows={3}
            value={requestText}
            onChange={(e) => setRequestText(e.target.value)}
            placeholder="Describe the objective for the multi-agent workforce (e.g. Build a secure user registration API)..."
            className="w-full bg-space-950 border border-space-750 focus:border-emerald-500/80 rounded-md p-3 text-xs text-slate-100 placeholder-slate-500 font-mono-tech resize-none leading-relaxed transition-colors"
            disabled={isSubmitting}
          />
        </div>

        {error && (
          <div className="flex items-center gap-2 p-2.5 rounded bg-rose-950/40 border border-rose-800/60 text-rose-300 text-xs font-mono-tech">
            <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
            <span>{error}</span>
          </div>
        )}

        {/* Action button & sample intents */}
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex flex-wrap items-center gap-1.5 text-[10px] font-mono-tech text-slate-400">
            <span className="text-slate-500">Presets:</span>
            {SAMPLE_INTENTS.map((intent, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => setRequestText(intent)}
                className="px-2 py-0.5 rounded bg-space-850 hover:bg-space-800 text-slate-300 hover:text-slate-100 border border-space-750 hover:border-space-700 transition-colors"
              >
                #{idx + 1}
              </button>
            ))}
          </div>

          <button
            type="submit"
            disabled={!requestText.trim() || isSubmitting}
            className="flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:bg-space-800 disabled:text-slate-500 disabled:cursor-not-allowed text-slate-950 font-mono-tech font-bold text-xs rounded transition-all shadow-sm"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span>DISPATCHING...</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>EXECUTE</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
