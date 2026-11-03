'use client';

import React from 'react';

interface GlassCardProps {
  children: React.ReactNode;
  className?: string;
  glow?: 'cyan' | 'emerald' | 'rose' | 'amber' | 'none';
  onClick?: () => void;
}

export function GlassCard({
  children,
  className = '',
  glow = 'none',
  onClick,
}: GlassCardProps) {
  const glowStyles = {
    cyan: 'hover:border-accent-cyan/40 hover:shadow-lg hover:shadow-accent-cyan/5',
    emerald: 'hover:border-accent-emerald/40 hover:shadow-lg hover:shadow-accent-emerald/5',
    rose: 'hover:border-accent-rose/40 hover:shadow-lg hover:shadow-accent-rose/5',
    amber: 'hover:border-accent-amber/40 hover:shadow-lg hover:shadow-accent-amber/5',
    none: 'hover:border-white/15',
  };

  return (
    <div
      onClick={onClick}
      className={`glass-panel rounded-2xl border border-white/10 transition-all duration-300 ${glowStyles[glow]} ${className}`}
    >
      {children}
    </div>
  );
}

