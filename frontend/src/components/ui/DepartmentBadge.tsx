'use client';

import React from 'react';

interface DepartmentBadgeProps {
  department: string;
  size?: 'xs' | 'sm' | 'md';
}

const DEPARTMENT_THEMES: Record<
  string,
  { label: string; bg: string; text: string; border: string }
> = {
  sales: {
    label: 'Sales Agent',
    bg: 'bg-emerald-500/10',
    text: 'text-emerald-400',
    border: 'border-emerald-500/30',
  },
  finance: {
    label: 'Finance Agent',
    bg: 'bg-cyan-500/10',
    text: 'text-cyan-400',
    border: 'border-cyan-500/30',
  },
  hr: {
    label: 'HR Agent',
    bg: 'bg-purple-500/10',
    text: 'text-purple-400',
    border: 'border-purple-500/30',
  },
  marketing: {
    label: 'Marketing Agent',
    bg: 'bg-amber-500/10',
    text: 'text-amber-400',
    border: 'border-amber-500/30',
  },
  operations: {
    label: 'Operations Agent',
    bg: 'bg-rose-500/10',
    text: 'text-rose-400',
    border: 'border-rose-500/30',
  },
  planner: {
    label: 'Planner Synthesizer',
    bg: 'bg-blue-500/10',
    text: 'text-blue-400',
    border: 'border-blue-500/30',
  },
};

export function DepartmentBadge({ department, size = 'sm' }: DepartmentBadgeProps) {
  const deptKey = department.toLowerCase().trim();
  const theme = DEPARTMENT_THEMES[deptKey] || {
    label: department.toUpperCase(),
    bg: 'bg-white/10',
    text: 'text-white',
    border: 'border-white/20',
  };

  const sizeClasses = {
    xs: 'text-[9px] px-1.5 py-0.5',
    sm: 'text-[10px] px-2 py-0.5',
    md: 'text-xs px-2.5 py-1',
  };

  return (
    <span
      className={`inline-flex items-center font-mono font-semibold uppercase rounded-md border tracking-wider ${theme.bg} ${theme.text} ${theme.border} ${sizeClasses[size]}`}
    >
      {theme.label}
    </span>
  );
}

