import React, { useState } from 'react';
import { Copy, Check } from 'lucide-react';

interface CodeBlockProps {
  code: string;
  language?: string;
  title?: string;
  maxHeight?: string;
}

export const CodeBlock: React.FC<CodeBlockProps> = ({
  code,
  language = 'json',
  title,
  maxHeight = 'max-h-80',
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // ignore
    }
  };

  return (
    <div className="rounded-md border border-space-800 bg-space-950 overflow-hidden text-xs font-mono-tech">
      <div className="flex items-center justify-between px-3 py-1.5 bg-space-900 border-b border-space-800">
        <div className="flex items-center gap-2 text-slate-400">
          <span className="w-2 h-2 rounded-full bg-space-700" />
          <span className="text-[11px] uppercase tracking-wider">{title || language}</span>
        </div>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1 text-[11px] text-slate-400 hover:text-slate-200 transition-colors px-1.5 py-0.5 rounded hover:bg-space-800"
          title="Copy code"
        >
          {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
          <span>{copied ? 'Copied' : 'Copy'}</span>
        </button>
      </div>
      <div className={`p-3 overflow-auto ${maxHeight} text-slate-300 leading-relaxed`}>
        <pre className="whitespace-pre-wrap break-all">{code}</pre>
      </div>
    </div>
  );
};
