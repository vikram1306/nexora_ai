'use client';

import React, { useState, useEffect } from 'react';
import {
  Search,
  X,
  BrainCircuit,
  BarChart3,
  UploadCloud,
  Activity,
  ShieldCheck,
  Sparkles,
  Database,
  ArrowRight
} from 'lucide-react';

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectTab: (tab: 'overview' | 'query' | 'ingest' | 'sentinel' | 'governance') => void;
  onExecutePresetQuery: (prompt: string) => void;
  onTriggerSentinelScan: () => void;
}

export function CommandPalette({
  isOpen,
  onClose,
  onSelectTab,
  onExecutePresetQuery,
  onTriggerSentinelScan,
}: CommandPaletteProps) {
  const [search, setSearch] = useState('');

  // Global Ctrl+K keyboard shortcut listener
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        if (isOpen) {
          onClose();
        } else {
          // Open palette
          const event = new CustomEvent('open-command-palette');
          window.dispatchEvent(event);
        }
      } else if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const quickPresets = [
    {
      label: 'Analyze Q3 Revenue and Operating EBITDA Margins',
      desc: 'Multi-agent correlation across Sales and Finance departments',
      prompt: 'What was our total revenue and EBITDA margin for Q3, and what are the growth drivers?',
    },
    {
      label: 'Evaluate Marketing ROI and CAC across Acquisition Channels',
      desc: 'Decomposes Marketing efficiency and Sales conversion velocity',
      prompt: 'Analyze our marketing spend efficiency, CAC trends, and lead conversion rates.',
    },
    {
      label: 'Review Headcount Growth vs Employee Turnover',
      desc: 'HR domain intelligence on retention and salary distributions',
      prompt: 'Review our current headcount, attrition rate, and salary distribution by department.',
    },
    {
      label: 'Audit Operations Logistics and Fulfillment Bottlenecks',
      desc: 'Operations Agent fulfillment latency and cost per unit analysis',
      prompt: 'What are our operational fulfillment delays and inventory turnover rates?',
    },
  ];

  const navigationItems = [
    { tab: 'overview', label: 'Go to Executive Overview', icon: BarChart3 },
    { tab: 'query', label: 'Go to AI Command Center', icon: BrainCircuit },
    { tab: 'ingest', label: 'Go to Enterprise Ingestion', icon: UploadCloud },
    { tab: 'sentinel', label: 'Go to Sentinel AI Anomaly Center', icon: Activity },
    { tab: 'governance', label: 'Go to Responsible AI Governance', icon: ShieldCheck },
  ] as const;

  const filteredPresets = quickPresets.filter((p) =>
    p.label.toLowerCase().includes(search.toLowerCase()) ||
    p.desc.toLowerCase().includes(search.toLowerCase())
  );

  const filteredNav = navigationItems.filter((n) =>
    n.label.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-start justify-center pt-20 px-4 animate-in fade-in duration-200">
      <div className="bg-obsidian-900 border border-accent-cyan/30 rounded-2xl max-w-2xl w-full shadow-2xl overflow-hidden">
        {/* Search Input Bar */}
        <div className="flex items-center gap-3 px-4 py-3.5 border-b border-white/10">
          <Search className="w-5 h-5 text-accent-cyan flex-shrink-0" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search commands, navigate tabs, or ask an executive query..."
            autoFocus
            className="w-full bg-transparent text-sm text-white placeholder-neutral-500 focus:outline-none font-sans"
          />
          <button
            onClick={onClose}
            className="text-neutral-400 hover:text-white p-1 rounded-lg hover:bg-white/5 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Results List */}
        <div className="p-3 max-h-[60vh] overflow-y-auto space-y-4">
          {/* Navigation Section */}
          <div>
            <div className="text-[10px] font-mono uppercase text-neutral-400 px-3 py-1 font-semibold">
              Navigation
            </div>
            <div className="space-y-1 mt-1">
              {filteredNav.map((item) => {
                const Icon = item.icon;
                return (
                  <button
                    key={item.tab}
                    onClick={() => {
                      onSelectTab(item.tab);
                      onClose();
                    }}
                    className="w-full flex items-center gap-3 px-3 py-2 rounded-xl text-xs text-neutral-300 hover:text-white hover:bg-white/5 transition-colors text-left"
                  >
                    <Icon className="w-4 h-4 text-accent-cyan" />
                    <span>{item.label}</span>
                    <ArrowRight className="w-3.5 h-3.5 ml-auto text-neutral-500" />
                  </button>
                );
              })}
            </div>
          </div>

          {/* Quick Queries Section */}
          <div>
            <div className="text-[10px] font-mono uppercase text-neutral-400 px-3 py-1 font-semibold">
              Executive AI Intelligence Queries
            </div>
            <div className="space-y-1 mt-1">
              {filteredPresets.map((preset, idx) => (
                <button
                  key={idx}
                  onClick={() => {
                    onExecutePresetQuery(preset.prompt);
                    onClose();
                  }}
                  className="w-full p-3 rounded-xl bg-obsidian-850 hover:bg-white/5 border border-white/5 hover:border-accent-cyan/30 transition-all text-left group"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-white group-hover:text-accent-cyan transition-colors flex items-center gap-2">
                      <Sparkles className="w-3.5 h-3.5 text-accent-cyan" /> {preset.label}
                    </span>
                    <span className="text-[10px] font-mono text-neutral-400">Run Query ↵</span>
                  </div>
                  <div className="text-[11px] text-neutral-400 mt-1">{preset.desc}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Quick Actions */}
          <div>
            <div className="text-[10px] font-mono uppercase text-neutral-400 px-3 py-1 font-semibold">
              Automated System Actions
            </div>
            <div className="space-y-1 mt-1">
              <button
                onClick={() => {
                  onTriggerSentinelScan();
                  onClose();
                }}
                className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs text-neutral-300 hover:text-white hover:bg-accent-rose/10 transition-colors text-left border border-white/5 hover:border-accent-rose/30"
              >
                <Activity className="w-4 h-4 text-accent-rose" />
                <div>
                  <div className="font-semibold text-white">Trigger Sentinel AI Scan</div>
                  <div className="text-[10px] text-neutral-400">
                    Immediately audit ingested memory for z-score statistical anomalies
                  </div>
                </div>
              </button>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-4 py-2.5 bg-obsidian-950 border-t border-white/5 flex items-center justify-between text-[11px] font-mono text-neutral-500">
          <span>Navigate with mouse or keyboard</span>
          <span>Press ESC to dismiss</span>
        </div>
      </div>
    </div>
  );
}

