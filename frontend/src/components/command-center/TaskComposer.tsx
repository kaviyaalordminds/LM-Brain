'use client';

import React, { useState } from 'react';
import { Mic, Upload, Play, Square, Loader2, FileCode, CheckCircle } from 'lucide-react';
import { cn } from '@/lib/utils/cn';

interface TaskComposerProps {
  onStart: (query: string, mode: 'basic' | 'advanced') => void;
  isPlaying: boolean;
  onReset: () => void;
}

export function TaskComposer({ onStart, isPlaying, onReset }: TaskComposerProps) {
  const [query, setQuery] = useState('');
  const [mode, setMode] = useState<'basic' | 'advanced'>('advanced');
  const [micState, setMicState] = useState<'ready' | 'listening' | 'recording' | 'transcribing'>('ready');
  const [attachedFiles, setAttachedFiles] = useState<{ name: string; size: string }[]>([]);

  // Simulation voice trigger
  const handleMicClick = () => {
    if (micState === 'ready') {
      setMicState('listening');
      setTimeout(() => {
        setMicState('recording');
      }, 1500);
    } else if (micState === 'recording') {
      setMicState('transcribing');
      setTimeout(() => {
        setMicState('ready');
        setQuery('Create a complete company landing website.');
      }, 2000);
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      setAttachedFiles([{ name: file.name, size: `${(file.size / 1024).toFixed(1)} KB` }]);
    }
  };

  const handleTrigger = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || isPlaying) return;
    onStart(query, mode);
  };

  return (
    <div className="bg-[#0c1322] border border-slate-800 rounded-xl p-4 premium-glow-indigo">
      <form onSubmit={handleTrigger} className="space-y-4">
        {/* Input Text Box */}
        <div className="relative">
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={isPlaying}
            placeholder="What would you like the workforce to accomplish?"
            className="w-full h-28 bg-[#060a12] border border-slate-800 rounded-lg p-3 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500/70 focus:ring-1 focus:ring-indigo-500/50 resize-none font-mono"
          />
          
          {/* File Upload preview */}
          {attachedFiles.length > 0 && (
            <div className="absolute bottom-3 left-3 flex items-center gap-2 bg-slate-900 border border-indigo-500/30 px-2 py-1 rounded text-[11px] font-mono text-indigo-400">
              <FileCode className="h-3.5 w-3.5" />
              <span>{attachedFiles[0].name} ({attachedFiles[0].size})</span>
              <button 
                type="button" 
                onClick={() => setAttachedFiles([])}
                className="text-slate-400 hover:text-slate-200 ml-1 font-sans font-bold"
              >
                &times;
              </button>
            </div>
          )}
        </div>

        {/* Form Controls */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pt-1">
          
          {/* Mode Selector */}
          <div className="flex items-center gap-1.5 bg-[#060a12] border border-slate-800 p-1 rounded-lg">
            <button
              type="button"
              disabled={isPlaying}
              onClick={() => setMode('basic')}
              className={cn(
                "px-3 py-1.5 rounded-md text-xs font-semibold uppercase tracking-wider transition-colors",
                mode === 'basic' 
                  ? "bg-slate-800 text-slate-100" 
                  : "text-slate-500 hover:text-slate-300"
              )}
            >
              Basic Task Mode
            </button>
            <button
              type="button"
              disabled={isPlaying}
              onClick={() => setMode('advanced')}
              className={cn(
                "px-3 py-1.5 rounded-md text-xs font-semibold uppercase tracking-wider transition-colors",
                mode === 'advanced' 
                  ? "bg-indigo-600 text-white shadow shadow-indigo-500/30" 
                  : "text-slate-500 hover:text-slate-300"
              )}
            >
              Advanced Project Mode
            </button>
          </div>

          {/* Quick Buttons */}
          <div className="flex items-center gap-3">
            {/* File upload hidden input */}
            <label className={cn(
              "flex items-center justify-center p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:bg-slate-800 hover:text-slate-200 cursor-pointer transition-colors focus-ring",
              isPlaying && "opacity-50 cursor-not-allowed"
            )}>
              <Upload className="h-4.5 w-4.5" />
              <input 
                type="file" 
                onChange={handleFileUpload} 
                disabled={isPlaying} 
                className="hidden" 
              />
            </label>

            {/* Voice Control Button */}
            <button
              type="button"
              disabled={isPlaying}
              onClick={handleMicClick}
              className={cn(
                "flex items-center justify-center p-2 rounded-lg transition-colors border focus-ring relative",
                micState === 'listening' && "bg-amber-950/40 text-amber-400 border-amber-500/40 animate-pulse",
                micState === 'recording' && "bg-rose-950/40 text-rose-400 border-rose-500/40 animate-pulse",
                micState === 'transcribing' && "bg-blue-950/40 text-blue-400 border-blue-500/40",
                micState === 'ready' && "bg-slate-900 border-slate-800 text-slate-400 hover:bg-slate-800 hover:text-slate-200"
              )}
            >
              {micState === 'transcribing' ? (
                <Loader2 className="h-4.5 w-4.5 animate-spin" />
              ) : (
                <Mic className="h-4.5 w-4.5" />
              )}
              {micState !== 'ready' && (
                <span className="absolute bottom-full mb-1.5 left-1/2 -translate-x-1/2 bg-slate-950 border border-slate-800 text-[9px] uppercase px-1.5 py-0.5 rounded shadow z-50 whitespace-nowrap font-mono">
                  {micState}
                </span>
              )}
            </button>

            {/* Launch button */}
            {isPlaying ? (
              <button
                type="button"
                onClick={onReset}
                className="flex items-center gap-1.5 bg-rose-950/50 border border-rose-500/40 text-rose-400 hover:bg-rose-900/50 hover:text-rose-200 text-xs py-2 px-4 rounded-lg font-bold transition-all focus-ring uppercase tracking-wider"
              >
                <Square className="h-4 w-4 fill-current" /> Stop Workforce
              </button>
            ) : (
              <button
                type="submit"
                disabled={!query.trim()}
                className={cn(
                  "flex items-center gap-1.5 text-xs py-2 px-4 rounded-lg font-bold transition-all focus-ring uppercase tracking-wider",
                  query.trim()
                    ? "bg-indigo-600 hover:bg-indigo-500 text-white shadow shadow-indigo-500/30"
                    : "bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-900"
                )}
              >
                <Play className="h-4 w-4 fill-current" /> Start Workforce
              </button>
            )}
          </div>

        </div>
      </form>
    </div>
  );
}
