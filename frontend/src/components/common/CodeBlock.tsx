import React, { useState } from 'react';
import { Check, Copy } from 'lucide-react';

interface CodeBlockProps {
  code: string;
  language?: string;
  title?: string;
  className?: string;
  maxHeight?: string;
}

export const CodeBlock: React.FC<CodeBlockProps> = ({
  code,
  language = 'text',
  title,
  className = '',
  maxHeight = 'max-h-80',
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className={`rounded-lg border border-slate-800 bg-[#080C14] overflow-hidden text-xs font-mono ${className}`}>
      {title && (
        <div className="px-3.5 py-2 border-b border-slate-800/80 bg-slate-900/60 flex items-center justify-between text-slate-400">
          <span className="truncate font-medium text-slate-300">{title}</span>
          <div className="flex items-center gap-2">
            <span className="text-[10px] uppercase tracking-wider text-slate-500 font-semibold">{language}</span>
            <button
              onClick={handleCopy}
              className="p-1 hover:text-slate-200 transition-colors rounded hover:bg-slate-800"
              title="Copy code"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            </button>
          </div>
        </div>
      )}
      <pre className={`p-3.5 overflow-x-auto overflow-y-auto text-slate-300 leading-relaxed ${maxHeight}`}>
        <code>{code}</code>
      </pre>
    </div>
  );
};
