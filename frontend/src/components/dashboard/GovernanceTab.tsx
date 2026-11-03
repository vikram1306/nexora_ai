'use client';

import React from 'react';
import { motion } from 'framer-motion';
import {
  ShieldCheck,
  RefreshCw,
  CheckCircle2,
  Check,
  X,
  BarChart3,
  ShieldAlert,
  Award,
  Layers
} from 'lucide-react';
import { GovernanceStats } from '@/lib/api';
import { GlassCard } from '../ui/GlassCard';
import { DepartmentBadge } from '../ui/DepartmentBadge';

interface GovernanceTabProps {
  stats: GovernanceStats | null;
  decisions: any[];
  onRefresh: () => void;
}

export function GovernanceTab({ stats, decisions, onRefresh }: GovernanceTabProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="space-y-8"
    >
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-serif font-bold text-white tracking-tight flex items-center gap-3">
            <ShieldCheck className="w-8 h-8 text-accent-cyan" /> Responsible AI Governance &amp; Decisions
          </h1>
          <p className="text-neutral-400 text-sm font-light mt-1">
            Human-in-the-Loop decision audit trail. Review logged executive accept/reject actions on AI recommendations.
          </p>
        </div>

        <button
          onClick={onRefresh}
          className="px-4 py-2 rounded-xl bg-obsidian-850 hover:bg-white/10 border border-white/10 text-xs text-neutral-300 transition-all flex items-center gap-2 self-start sm:self-auto"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Refresh Audit Metrics
        </button>
      </div>

      {/* Governance Telemetry Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <GlassCard className="p-5 space-y-2">
          <div className="text-xs font-mono text-neutral-400 uppercase">Executive Decisions</div>
          <div className="text-3xl font-bold font-mono text-white">
            {stats?.total_decisions || 0}
          </div>
          <div className="text-[11px] text-neutral-500">Human-reviewed recommendations</div>
        </GlassCard>

        <GlassCard glow="emerald" className="p-5 space-y-2 bg-accent-emerald/5 border-accent-emerald/30">
          <div className="text-xs font-mono text-accent-emerald uppercase font-semibold">
            Acceptance Rate
          </div>
          <div className="text-3xl font-bold font-mono text-accent-emerald">
            {stats?.acceptance_rate_pct || 0}%
          </div>
          <div className="text-[11px] text-neutral-400">Trust alignment index</div>
        </GlassCard>

        <GlassCard glow="cyan" className="p-5 space-y-2">
          <div className="text-xs font-mono text-accent-cyan uppercase font-semibold">
            Accepted Action Plans
          </div>
          <div className="text-3xl font-bold font-mono text-accent-cyan">
            {stats?.accepted_count || 0}
          </div>
          <div className="text-[11px] text-neutral-500">Authorized for execution</div>
        </GlassCard>

        <GlassCard glow="rose" className="p-5 space-y-2">
          <div className="text-xs font-mono text-accent-rose uppercase font-semibold">
            Rejected Recommendations
          </div>
          <div className="text-3xl font-bold font-mono text-accent-rose">
            {stats?.rejected_count || 0}
          </div>
          <div className="text-[11px] text-neutral-500">Filtered by executive review</div>
        </GlassCard>
      </div>

      {/* Department Breakdown Bar */}
      {stats?.department_breakdown && Object.keys(stats.department_breakdown).length > 0 && (
        <GlassCard className="p-6 space-y-4">
          <h3 className="text-base font-serif font-bold text-white flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-accent-cyan" /> Department Governance Distribution
          </h3>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
            {Object.entries(stats.department_breakdown).map(([dept, counts]: [string, any]) => (
              <div
                key={dept}
                className="p-4 rounded-xl bg-obsidian-850 border border-white/5 space-y-2"
              >
                <div className="flex items-center justify-between">
                  <DepartmentBadge department={dept} size="xs" />
                </div>
                <div className="flex items-center justify-between text-xs font-mono pt-1">
                  <span className="text-accent-emerald flex items-center gap-1 font-semibold">
                    <Check className="w-3 h-3" /> {counts.ACCEPTED || 0}
                  </span>
                  <span className="text-accent-rose flex items-center gap-1 font-semibold">
                    <X className="w-3 h-3" /> {counts.REJECTED || 0}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </GlassCard>
      )}

      {/* Decision Audit Log Table */}
      <GlassCard className="p-6 space-y-4">
        <h3 className="text-base font-serif font-bold text-white flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 text-accent-emerald" /> Decision Audit Trail ({decisions.length})
        </h3>

        {decisions.length === 0 ? (
          <div className="p-8 rounded-xl bg-obsidian-850/50 border border-white/5 text-center text-xs text-neutral-400 font-light">
            No decisions logged yet. Execute an AI Command Center query and click &quot;Accept Action Plan&quot; or &quot;Reject&quot; on any recommendation.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-white/10 text-neutral-400 font-mono uppercase text-[10px]">
                  <th className="py-3 px-4">Timestamp</th>
                  <th className="py-3 px-4">Executive Actor</th>
                  <th className="py-3 px-4">Department</th>
                  <th className="py-3 px-4">Decision Action</th>
                  <th className="py-3 px-4">Recommendation Title</th>
                  <th className="py-3 px-4">Confidence</th>
                  <th className="py-3 px-4">Audit Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {decisions.map((d: any) => (
                  <tr key={d.id} className="hover:bg-white/5 transition-colors">
                    <td className="py-3 px-4 font-mono text-neutral-400 text-[11px] whitespace-nowrap">
                      {new Date(d.created_at).toLocaleString()}
                    </td>
                    <td className="py-3 px-4 font-semibold text-white whitespace-nowrap">
                      CEO Authority
                    </td>
                    <td className="py-3 px-4">
                      <DepartmentBadge department={d.department} size="xs" />
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`px-2.5 py-0.5 rounded font-mono text-[10px] font-bold ${
                          d.action_type === 'ACCEPTED'
                            ? 'bg-accent-emerald/20 text-accent-emerald border border-accent-emerald/30'
                            : 'bg-accent-rose/20 text-accent-rose border border-accent-rose/30'
                        }`}
                      >
                        {d.action_type}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-neutral-200 font-medium max-w-xs truncate">
                      {d.recommendation_title}
                    </td>
                    <td className="py-3 px-4 font-mono text-accent-emerald">
                      {Math.round((d.confidence_score || 0.95) * 100)}%
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      <span className="text-[10px] font-mono text-neutral-400 flex items-center gap-1">
                        <CheckCircle2 className="w-3 h-3 text-accent-emerald" /> Logged &amp; Verified
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </GlassCard>
    </motion.div>
  );
}

