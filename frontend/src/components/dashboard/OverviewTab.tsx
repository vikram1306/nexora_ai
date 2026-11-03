'use client';

import React from 'react';
import { motion } from 'framer-motion';
import {
  DollarSign,
  TrendingUp,
  Users,
  Activity,
  Sparkles,
  ArrowRight,
  Database,
  ShieldCheck,
  Building,
  CheckCircle2,
  AlertTriangle,
  ChevronRight,
  Info
} from 'lucide-react';
import { StatCard } from '../ui/StatCard';
import { GlassCard } from '../ui/GlassCard';
import { DepartmentBadge } from '../ui/DepartmentBadge';

interface OverviewTabProps {
  onSwitchTab: (tab: 'overview' | 'query' | 'ingest' | 'sentinel' | 'governance') => void;
  onExecutePresetQuery?: (prompt: string) => void;
  datasetsCount: number;
  alertsCount: number;
  decisionsCount: number;
  governanceRate: number;
}

export function OverviewTab({
  onSwitchTab,
  onExecutePresetQuery,
  datasetsCount,
  alertsCount,
  decisionsCount,
  governanceRate,
}: OverviewTabProps) {
  const departments = [
    {
      dept: 'sales',
      agent: 'Sales Agent',
      focus: 'Revenue Velocity, Regional Pipelines & ARR',
      status: 'Active & Synchronized',
      latency: '24ms',
    },
    {
      dept: 'finance',
      agent: 'Finance Agent',
      focus: 'EBITDA Margins, Cost Structure & Variances',
      status: 'Active & Synchronized',
      latency: '18ms',
    },
    {
      dept: 'hr',
      agent: 'HR Agent',
      focus: 'Headcount Scaling, Retention & Compensation',
      status: 'Active & Synchronized',
      latency: '31ms',
    },
    {
      dept: 'marketing',
      agent: 'Marketing Agent',
      focus: 'Channel CAC, ROAS & Conversion Funnels',
      status: 'Active & Synchronized',
      latency: '22ms',
    },
    {
      dept: 'operations',
      agent: 'Operations Agent',
      focus: 'Fulfillment Delays & Inventory Velocity',
      status: 'Active & Synchronized',
      latency: '27ms',
    },
  ];

  const quickQuestions = [
    'What was our total revenue and EBITDA margin for Q3, and what are the growth drivers?',
    'Analyze our marketing spend efficiency, CAC trends, and lead conversion rates.',
    'Review our current headcount, attrition rate, and salary distribution by department.',
    'Identify any supply chain bottlenecks or fulfillment delays affecting customer margins.',
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="space-y-8"
    >
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-serif font-bold text-white tracking-tight">
            Executive Operating Dashboard
          </h1>
          <p className="text-neutral-400 text-sm font-light mt-1">
            Real-time multi-agent intelligence, zero-hallucination verification, and enterprise dataset metrics.
          </p>
        </div>
        <button
          onClick={() => onSwitchTab('query')}
          className="px-5 py-2.5 rounded-xl bg-accent-cyan text-obsidian-950 font-semibold text-sm flex items-center justify-center gap-2 shadow-lg shadow-accent-cyan/20 hover:brightness-110 transition-all self-start sm:self-auto"
        >
          <Sparkles className="w-4 h-4" /> Ask Executive Query
        </button>
      </div>

      {/* Onboarding Notice if No Datasets Yet */}
      {datasetsCount === 0 && (
        <div className="p-4 rounded-xl bg-accent-cyan/10 border border-accent-cyan/30 text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2.5 text-accent-cyan font-medium">
            <Info className="w-4 h-4 flex-shrink-0" />
            <span>
              <strong>New Organization Workspace:</strong> You haven&apos;t uploaded any CSV datasets to your tenant yet. Go to <strong>Enterprise Ingestion</strong> to upload your own data or sample CSVs from <code className="px-1.5 py-0.5 rounded bg-black/40 text-accent-cyan font-mono">sample_datasets/</code>.
            </span>
          </div>
          <button
            onClick={() => onSwitchTab('ingest')}
            className="px-3.5 py-1.5 rounded-lg bg-accent-cyan text-obsidian-950 font-bold text-xs hover:brightness-110 whitespace-nowrap self-start sm:self-auto"
          >
            Upload Datasets →
          </button>
        </div>
      )}

      {/* KPI Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Annual Recurring Revenue"
          value={datasetsCount > 0 ? "$24.8M" : "$0.00"}
          subValue={datasetsCount > 0 ? "Target: $26.0M" : "Awaiting Ingestion"}
          trend={datasetsCount > 0 ? { value: "+18.4% MoM", positive: true } : undefined}
          icon={DollarSign}
          glow="cyan"
        />
        <StatCard
          label="Operating EBITDA Margin"
          value={datasetsCount > 0 ? "41.2%" : "0.0%"}
          subValue={datasetsCount > 0 ? "320 bps expansion" : "Awaiting Ingestion"}
          trend={datasetsCount > 0 ? { value: "+3.8% Margin", positive: true } : undefined}
          icon={TrendingUp}
          glow="emerald"
        />
        <StatCard
          label="Active Enterprise Headcount"
          value={datasetsCount > 0 ? "342" : "0"}
          subValue={datasetsCount > 0 ? "96.2% Retention Rate" : "Awaiting HR Dataset"}
          trend={datasetsCount > 0 ? { value: "+14 Hires", positive: true } : undefined}
          icon={Users}
          glow="none"
        />
        <StatCard
          label="Blended Customer CAC"
          value={datasetsCount > 0 ? "$412" : "$0"}
          subValue={datasetsCount > 0 ? "LTV/CAC: 4.8x" : "Awaiting Marketing Dataset"}
          trend={datasetsCount > 0 ? { value: "-12.4% Efficient", positive: true } : undefined}
          icon={Activity}
          glow="none"
        />
      </div>

      {/* Bento Grid: Agent Orchestration + Sentinel Radar */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: 5 Department Agents & Quick Inquiries */}
        <div className="lg:col-span-2 space-y-6">
          {/* Department Agents Telemetry */}
          <GlassCard className="p-6 space-y-5">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-serif font-bold text-white flex items-center gap-2">
                  <Building className="w-4 h-4 text-accent-cyan" /> Specialized Multi-Agent Network
                </h3>
                <p className="text-xs text-neutral-400 mt-0.5">
                  5 autonomous domain agents connected to relational SQL memory and ChromaDB semantic vectors.
                </p>
              </div>
              <span className="text-[11px] font-mono text-accent-emerald flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-accent-emerald/10 border border-accent-emerald/20">
                <span className="w-2 h-2 rounded-full bg-accent-emerald animate-pulse" />
                All 5 Online
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {departments.map((d) => (
                <div
                  key={d.dept}
                  className="p-4 rounded-xl bg-obsidian-850/80 border border-white/5 hover:border-white/15 transition-all flex flex-col justify-between"
                >
                  <div className="flex items-center justify-between mb-2">
                    <DepartmentBadge department={d.dept} size="xs" />
                    <span className="text-[10px] font-mono text-neutral-500">
                      p95 {d.latency}
                    </span>
                  </div>
                  <div className="text-xs text-neutral-300 font-light mb-2">{d.focus}</div>
                  <div className="text-[10px] font-mono text-accent-emerald flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3" /> {d.status}
                  </div>
                </div>
              ))}

              <div
                onClick={() => onSwitchTab('ingest')}
                className="p-4 rounded-xl bg-obsidian-850/40 border border-dashed border-white/10 hover:border-accent-cyan/40 hover:bg-accent-cyan/5 transition-all flex flex-col justify-center items-center text-center cursor-pointer group"
              >
                <Database className="w-5 h-5 text-accent-cyan mb-1.5 group-hover:scale-110 transition-transform" />
                <span className="text-xs font-semibold text-white">Ingest New Dataset</span>
                <span className="text-[10px] text-neutral-400 font-mono mt-0.5">
                  {datasetsCount} Datasets Active in Memory
                </span>
              </div>
            </div>
          </GlassCard>

          {/* Prompt Suggestions */}
          <GlassCard className="p-6 space-y-4">
            <h3 className="text-base font-serif font-bold text-white flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-accent-cyan" /> Suggested Executive Inquiries
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              {quickQuestions.map((q, idx) => (
                <button
                  key={idx}
                  onClick={() => {
                    if (onExecutePresetQuery) onExecutePresetQuery(q);
                    else onSwitchTab('query');
                  }}
                  className="p-3 rounded-xl bg-obsidian-850 hover:bg-white/5 border border-white/5 hover:border-accent-cyan/30 text-left transition-all group flex items-start justify-between gap-2"
                >
                  <span className="text-xs text-neutral-300 group-hover:text-white leading-relaxed">
                    {q}
                  </span>
                  <ChevronRight className="w-3.5 h-3.5 text-neutral-500 group-hover:text-accent-cyan group-hover:translate-x-0.5 transition-all flex-shrink-0 mt-0.5" />
                </button>
              ))}
            </div>
          </GlassCard>
        </div>

        {/* Right Col: Sentinel Alerts & Human Governance Widget */}
        <div className="space-y-6">
          {/* Sentinel AI Widget */}
          <GlassCard glow="rose" className="p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Activity className="w-4 h-4 text-accent-rose" />
                <h3 className="text-base font-serif font-bold text-white">Sentinel AI Radar</h3>
              </div>
              <button
                onClick={() => onSwitchTab('sentinel')}
                className="text-xs font-mono text-accent-rose hover:underline flex items-center gap-1"
              >
                View All <ArrowRight className="w-3 h-3" />
              </button>
            </div>

            <p className="text-xs text-neutral-400 font-light">
              Continuous background daemon scanning ingested datasets for z-score statistical anomalies (&gt;2.5σ).
            </p>

            <div className="p-4 rounded-xl bg-obsidian-850 border border-white/5 space-y-3">
              <div className="flex items-center justify-between text-xs">
                <span className="text-neutral-300 font-medium">Anomaly Detection Status</span>
                <span className="text-accent-emerald font-mono font-semibold">Active & Armed</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-neutral-400">Unacknowledged Alerts</span>
                <span
                  className={`font-mono font-bold px-2 py-0.5 rounded text-[10px] ${
                    alertsCount > 0
                      ? 'bg-accent-rose/20 text-accent-rose border border-accent-rose/30'
                      : 'bg-white/10 text-neutral-400'
                  }`}
                >
                  {alertsCount} Active
                </span>
              </div>
            </div>

            <button
              onClick={() => onSwitchTab('sentinel')}
              className="w-full py-2.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-xs font-semibold text-neutral-200 transition-all text-center block"
            >
              Open Sentinel AI Anomaly Center
            </button>
          </GlassCard>

          {/* Responsible AI Trust & Governance Card */}
          <GlassCard glow="cyan" className="p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-accent-cyan" />
                <h3 className="text-base font-serif font-bold text-white">Responsible AI Trust</h3>
              </div>
              <button
                onClick={() => onSwitchTab('governance')}
                className="text-xs font-mono text-accent-cyan hover:underline flex items-center gap-1"
              >
                Audit Log <ArrowRight className="w-3 h-3" />
              </button>
            </div>

            <p className="text-xs text-neutral-400 font-light">
              Human-in-the-Loop decision governance ensures executive authorization before any AI strategic recommendation is executed.
            </p>

            <div className="grid grid-cols-2 gap-3">
              <div className="p-3 rounded-xl bg-obsidian-850 border border-white/5 text-center">
                <div className="text-xl font-bold font-mono text-accent-emerald">
                  {governanceRate}%
                </div>
                <div className="text-[10px] text-neutral-400 font-mono mt-1">Acceptance Rate</div>
              </div>
              <div className="p-3 rounded-xl bg-obsidian-850 border border-white/5 text-center">
                <div className="text-xl font-bold font-mono text-white">
                  {decisionsCount}
                </div>
                <div className="text-[10px] text-neutral-400 font-mono mt-1">Logged Actions</div>
              </div>
            </div>

            <button
              onClick={() => onSwitchTab('governance')}
              className="w-full py-2.5 rounded-xl bg-accent-cyan/10 hover:bg-accent-cyan/20 border border-accent-cyan/30 text-xs font-semibold text-accent-cyan transition-all text-center block"
            >
              Review Human Decision Audit Trail
            </button>
          </GlassCard>
        </div>
      </div>
    </motion.div>
  );
}
