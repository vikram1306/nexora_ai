'use client';

import React from 'react';
import { ShieldCheck, ShieldAlert, CheckCircle2 } from 'lucide-react';

interface ConfidenceMeterProps {
  score: number; // 0.0 to 1.0 or 0 to 100
  showLabel?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export function ConfidenceMeter({ score, showLabel = true, size = 'md' }: ConfidenceMeterProps) {
  // Normalize to 0-100
  const normalized = score > 1 ? Math.min(Math.round(score), 100) : Math.round(score * 100);

  const getTier = (pct: number) => {
    if (pct >= 90) {
      return {
        label: 'Zero-Hallucination Verified',
        color: 'text-accent-emerald',
        bg: 'bg-accent-emerald',
        badgeBg: 'bg-accent-emerald/10',
        border: 'border-accent-emerald/30',
        icon: CheckCircle2,
      };
    }
    if (pct >= 75) {
      return {
        label: 'High Confidence Alignment',
        color: 'text-accent-cyan',
        bg: 'bg-accent-cyan',
        badgeBg: 'bg-accent-cyan/10',
        border: 'border-accent-cyan/30',
        icon: ShieldCheck,
      };
    }
    return {
      label: 'Review Recommended',
      color: 'text-amber-400',
      bg: 'bg-amber-400',
      badgeBg: 'bg-amber-400/10',
      border: 'border-amber-400/30',
      icon: ShieldAlert,
    };
  };

  const tier = getTier(normalized);
  const Icon = tier.icon;

  return (
    <div className="space-y-1.5">
      {showLabel && (
        <div className="flex items-center justify-between text-xs">
          <div className="flex items-center gap-1.5 font-medium">
            <Icon className={`w-3.5 h-3.5 ${tier.color}`} />
            <span className={tier.color}>{tier.label}</span>
          </div>
          <span className={`font-mono font-bold ${tier.color}`}>{normalized}%</span>
        </div>
      )}

      {/* Progress track */}
      <div className="w-full bg-white/10 rounded-full h-1.5 overflow-hidden">
        <div
          className={`h-full transition-all duration-500 ease-out ${tier.bg}`}
          style={{ width: `${normalized}%` }}
        />
      </div>
    </div>
  );
}

