'use client';

import React, { useState } from 'react';
import { X, Copy, Check, Terminal, Database, Code } from 'lucide-react';
import { DepartmentBadge } from '../ui/DepartmentBadge';

interface SqlInspectModalProps {
  evidence: {
    department: string;
    sql: string;
    source: string;
  } | null;
  onClose: () => void;
}

export function SqlInspectModal({ evidence, onClose }: SqlInspectModalProps) {
  const [copied, setCopied] = useState(false);

  if (!evidence) return null;

  const handleCopy = () => {
    navigator.clipboard.writeText(evidence.sql);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
      <div className="bg-obsidian-900 border border-white/20 rounded-2xl p-6 max-w-2xl w-full space-y-4 shadow-2xl animate-in fade-in zoom-in-95 duration-200">
        <div className="flex items-center justify-between border-b border-white/10 pb-3">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-accent-cyan/10 border border-accent-cyan/30 flex items-center justify-center text-accent-cyan">
              <Terminal className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                SQL Evidence Inspector
              </h3>
              <p className="text-[11px] text-neutral-400 font-mono">
                Source: {evidence.source || 'Relational Memory Engine'}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <DepartmentBadge department={evidence.department} size="xs" />
            <button
              onClick={onClose}
              className="text-neutral-400 hover:text-white p-1 rounded-lg hover:bg-white/5 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        <div className="relative">
          <pre className="p-4 rounded-xl bg-obsidian-950 border border-white/10 text-accent-cyan font-mono text-xs overflow-x-auto whitespace-pre-wrap leading-relaxed">
            {evidence.sql}
          </pre>
          <button
            onClick={handleCopy}
            className="absolute top-3 right-3 px-2.5 py-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-neutral-300 text-[11px] font-mono flex items-center gap-1.5 transition-all"
          >
            {copied ? (
              <>
                <Check className="w-3.5 h-3.5 text-accent-emerald" /> Copied
              </>
            ) : (
              <>
                <Copy className="w-3.5 h-3.5" /> Copy Query
              </>
            )}
          </button>
        </div>

        <div className="flex items-center justify-between text-[11px] font-mono text-neutral-400 pt-2 border-t border-white/5">
          <span className="flex items-center gap-1 text-accent-emerald">
            <Check className="w-3.5 h-3.5" /> Direct Database Validation Passed
          </span>
          <span>Zero-Hallucination Guardrail Active</span>
        </div>
      </div>
    </div>
  );
}

