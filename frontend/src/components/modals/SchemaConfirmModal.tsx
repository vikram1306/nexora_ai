'use client';

import React, { useState } from 'react';
import { CheckCircle2, RefreshCw, X, ShieldAlert, Sparkles } from 'lucide-react';
import { SchemaAnalysisResult } from '@/lib/api';

interface SchemaConfirmModalProps {
  proposal: SchemaAnalysisResult;
  onConfirm: (confirmedMapping: Record<string, string>) => void;
  onCancel: () => void;
  isConfirming: boolean;
}

export function SchemaConfirmModal({
  proposal,
  onConfirm,
  onCancel,
  isConfirming,
}: SchemaConfirmModalProps) {
  const [mapping, setMapping] = useState<Record<string, string>>(() => {
    const initial: Record<string, string> = {};
    proposal.proposed_mappings.forEach((item) => {
      initial[item.user_column] = item.proposed_canonical;
    });
    return initial;
  });

  const handleSelectChange = (col: string, val: string) => {
    setMapping((prev) => ({ ...prev, [col]: val }));
  };

  const handleConfirm = () => {
    onConfirm(mapping);
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
      <div className="bg-obsidian-900 border border-accent-cyan/30 rounded-2xl p-6 max-w-3xl w-full space-y-5 shadow-2xl overflow-y-auto max-h-[85vh] animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-white/10 pb-4">
          <div>
            <span className="text-xs font-mono uppercase px-2.5 py-0.5 rounded bg-accent-cyan/10 text-accent-cyan border border-accent-cyan/30 font-semibold">
              AI Schema Intelligence Engine
            </span>
            <h3 className="text-xl font-serif font-bold text-white mt-1">
              Verify Schema Mapping for {proposal.filename}
            </h3>
            <p className="text-xs text-neutral-400 mt-0.5">
              Department:{' '}
              <span className="uppercase text-accent-emerald font-semibold">
                {proposal.department}
              </span>{' '}
              | {proposal.total_columns} Columns Profiled
            </p>
          </div>
          <button
            onClick={onCancel}
            className="text-neutral-400 hover:text-white p-1 rounded-lg hover:bg-white/5 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="space-y-3">
          <div className="text-xs text-neutral-300">
            Confirm or fine-tune the AI-suggested canonical column associations before persisting to
            relational SQL memory and vector store:
          </div>

          <div className="divide-y divide-white/5 border border-white/10 rounded-xl overflow-hidden bg-obsidian-850">
            <div className="grid grid-cols-12 px-4 py-2.5 text-[10px] font-mono uppercase text-neutral-400 bg-white/5">
              <div className="col-span-4">CSV Column & Samples</div>
              <div className="col-span-3">AI Confidence</div>
              <div className="col-span-5">Canonical Target Field</div>
            </div>

            {proposal.proposed_mappings.map((item, idx) => (
              <div
                key={idx}
                className="grid grid-cols-12 px-4 py-3 items-center text-xs gap-2 hover:bg-white/[0.02] transition-colors"
              >
                <div className="col-span-4">
                  <div className="font-semibold text-white">{item.user_column}</div>
                  <div className="text-[10px] text-neutral-400 truncate font-mono">
                    Sample: {item.sample_values.join(', ') || 'N/A'}
                  </div>
                </div>

                <div className="col-span-3">
                  <span
                    className={`inline-block px-2 py-0.5 rounded text-[10px] font-mono font-semibold ${
                      item.confidence >= 0.85
                        ? 'bg-accent-emerald/10 text-accent-emerald border border-accent-emerald/30'
                        : 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                    }`}
                  >
                    {Math.round(item.confidence * 100)}% Match
                  </span>
                </div>

                <div className="col-span-5">
                  <select
                    value={mapping[item.user_column] || item.proposed_canonical}
                    onChange={(e) => handleSelectChange(item.user_column, e.target.value)}
                    className="w-full px-3 py-1.5 rounded-lg bg-obsidian-950 border border-white/20 text-white text-xs focus:outline-none focus:border-accent-cyan"
                  >
                    {item.available_options.map((opt) => (
                      <option key={opt} value={opt}>
                        {opt === 'ignore' ? '🚫 Ignore Column' : `🎯 Mapped to: ${opt}`}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-end gap-3 pt-4 border-t border-white/10">
          <button
            type="button"
            onClick={onCancel}
            disabled={isConfirming}
            className="px-4 py-2 rounded-xl bg-white/5 hover:bg-white/10 text-neutral-300 text-xs font-semibold transition-all disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleConfirm}
            disabled={isConfirming}
            className="px-6 py-2.5 rounded-xl bg-accent-cyan text-obsidian-950 font-bold text-xs hover:brightness-110 transition-all flex items-center gap-2 shadow-lg shadow-accent-cyan/20 disabled:opacity-50"
          >
            {isConfirming ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" /> Ingesting Verified Schema...
              </>
            ) : (
              <>
                <CheckCircle2 className="w-4 h-4" /> Confirm & Ingest Verified Schema
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

