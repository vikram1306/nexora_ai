'use client';

import React from 'react';
import { LucideIcon, TrendingUp, TrendingDown } from 'lucide-react';
import { GlassCard } from './GlassCard';

interface StatCardProps {
  label: string;
  value: string | number;
  subValue?: string;
  trend?: {
    value: string;
    positive: boolean;
  };
  icon: LucideIcon;
  glow?: 'cyan' | 'emerald' | 'rose' | 'amber' | 'none';
}

export function StatCard({
  label,
  value,
  subValue,
  trend,
  icon: Icon,
  glow = 'none',
}: StatCardProps) {
  return (
    <GlassCard glow={glow} className="p-5 flex flex-col justify-between">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-mono uppercase text-neutral-400 tracking-wider">
          {label}
        </span>
        <div className="w-8 h-8 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center text-white">
          <Icon className="w-4 h-4 text-neutral-300" />
        </div>
      </div>

      <div>
        <div className="text-2xl lg:text-3xl font-bold font-mono tracking-tight text-white">
          {value}
        </div>
        <div className="flex items-center justify-between mt-2 text-xs">
          {subValue && <span className="text-neutral-400 font-light">{subValue}</span>}
          {trend && (
            <span
              className={`inline-flex items-center gap-1 font-mono font-semibold ${
                trend.positive ? 'text-accent-emerald' : 'text-accent-rose'
              }`}
            >
              {trend.positive ? (
                <TrendingUp className="w-3.5 h-3.5" />
              ) : (
                <TrendingDown className="w-3.5 h-3.5" />
              )}
              {trend.value}
            </span>
          )}
        </div>
      </div>
    </GlassCard>
  );
}

