'use client';

import React from 'react';
import Link from 'next/link';
import {
  Building,
  Cpu,
  Search,
  LogOut,
  ShieldCheck,
  Activity,
  BarChart3,
  BrainCircuit,
  UploadCloud,
  ChevronDown
} from 'lucide-react';
import { useAuth } from '@/context/AuthContext';

interface HeaderProps {
  activeTab: 'overview' | 'query' | 'ingest' | 'sentinel' | 'governance';
  onTabChange: (tab: 'overview' | 'query' | 'ingest' | 'sentinel' | 'governance') => void;
  onOpenCommandPalette: () => void;
  ollamaStatus: { status: string; active_llm: string };
  unacknowledgedAlertsCount: number;
  decisionsCount: number;
}

export function Header({
  activeTab,
  onTabChange,
  onOpenCommandPalette,
  ollamaStatus,
  unacknowledgedAlertsCount,
  decisionsCount,
}: HeaderProps) {
  const { user, logout } = useAuth();

  const getInitials = (name?: string) => {
    if (!name) return 'EX';
    return name
      .split(' ')
      .map((n) => n[0])
      .slice(0, 2)
      .join('')
      .toUpperCase();
  };

  return (
    <header className="glass-panel border-b border-white/10 px-6 py-3.5 flex items-center justify-between sticky top-0 z-40 backdrop-blur-xl">
      {/* Left: Brand & Tenant Context */}
      <div className="flex items-center gap-4">
        <Link href="/" className="flex items-center gap-2.5 group">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-accent-cyan to-accent-emerald flex items-center justify-center font-bold text-obsidian-950 text-base shadow-md shadow-accent-cyan/20 group-hover:scale-105 transition-transform">
            N
          </div>
          <span className="font-bold text-base tracking-tight text-white font-sans">
            NEXORA <span className="text-accent-cyan text-[11px] font-mono uppercase">AI</span>
          </span>
        </Link>

        <span className="text-white/20 hidden sm:inline">|</span>

        <div className="hidden sm:flex items-center gap-2 text-xs font-mono text-neutral-300 bg-obsidian-850 px-3 py-1.5 rounded-lg border border-white/5">
          <Building className="w-3.5 h-3.5 text-accent-cyan" />
          <span className="font-semibold text-white">
            {user?.tenant?.name || 'Acme Global Enterprise'}
          </span>
          <span className="text-neutral-500">•</span>
          <span className="text-accent-emerald font-semibold uppercase text-[10px] px-1.5 py-0.5 rounded bg-accent-emerald/10 border border-accent-emerald/20">
            {user?.role || 'CEO'}
          </span>
        </div>

        {/* Ollama LLM Connection Badge */}
        <div
          className={`hidden lg:flex items-center gap-1.5 px-3 py-1 rounded-full border text-[11px] font-mono transition-colors ${
            ollamaStatus.status === 'online'
              ? 'bg-accent-emerald/10 text-accent-emerald border-accent-emerald/30'
              : 'bg-obsidian-850 text-neutral-400 border-white/10'
          }`}
          title={ollamaStatus.status === 'online' ? 'Connected to local Ollama inference server' : 'Using built-in deterministic multi-agent engine'}
        >
          <Cpu className="w-3 h-3 text-accent-cyan" />
          <span>{ollamaStatus.active_llm}</span>
        </div>
      </div>

      {/* Middle: Quick Tab Navigation */}
      <nav className="hidden xl:flex items-center gap-1 bg-obsidian-850 p-1 rounded-xl border border-white/10 text-xs font-medium">
        <button
          onClick={() => onTabChange('overview')}
          className={`px-3.5 py-1.5 rounded-lg transition-all flex items-center gap-2 ${
            activeTab === 'overview'
              ? 'bg-white text-obsidian-950 font-semibold shadow'
              : 'text-neutral-400 hover:text-white'
          }`}
        >
          <BarChart3 className="w-3.5 h-3.5" /> Overview
        </button>
        <button
          onClick={() => onTabChange('query')}
          className={`px-3.5 py-1.5 rounded-lg transition-all flex items-center gap-2 ${
            activeTab === 'query'
              ? 'bg-white text-obsidian-950 font-semibold shadow'
              : 'text-neutral-400 hover:text-white'
          }`}
        >
          <BrainCircuit className="w-3.5 h-3.5" /> AI Command Center
        </button>
        <button
          onClick={() => onTabChange('ingest')}
          className={`px-3.5 py-1.5 rounded-lg transition-all flex items-center gap-2 ${
            activeTab === 'ingest'
              ? 'bg-white text-obsidian-950 font-semibold shadow'
              : 'text-neutral-400 hover:text-white'
          }`}
        >
          <UploadCloud className="w-3.5 h-3.5" /> Ingestion
        </button>
        <button
          onClick={() => onTabChange('sentinel')}
          className={`px-3.5 py-1.5 rounded-lg transition-all flex items-center gap-2 relative ${
            activeTab === 'sentinel'
              ? 'bg-white text-obsidian-950 font-semibold shadow'
              : 'text-neutral-400 hover:text-white'
          }`}
        >
          <Activity className="w-3.5 h-3.5 text-accent-rose" /> Sentinel AI
          {unacknowledgedAlertsCount > 0 && (
            <span className="w-2 h-2 rounded-full bg-accent-rose animate-ping absolute top-1 right-1" />
          )}
        </button>
        <button
          onClick={() => onTabChange('governance')}
          className={`px-3.5 py-1.5 rounded-lg transition-all flex items-center gap-2 ${
            activeTab === 'governance'
              ? 'bg-white text-obsidian-950 font-semibold shadow'
              : 'text-neutral-400 hover:text-white'
          }`}
        >
          <ShieldCheck className="w-3.5 h-3.5 text-accent-cyan" /> Governance
          {decisionsCount > 0 && (
            <span className="px-1.5 py-0.2 rounded-full bg-accent-cyan/20 text-accent-cyan text-[10px] font-mono">
              {decisionsCount}
            </span>
          )}
        </button>
      </nav>

      {/* Right: Command Bar Trigger & User Logout */}
      <div className="flex items-center gap-3">
        <button
          onClick={onOpenCommandPalette}
          className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-obsidian-850 hover:bg-white/5 border border-white/10 text-neutral-400 text-xs font-mono transition-all"
        >
          <Search className="w-3.5 h-3.5 text-accent-cyan" />
          <span className="text-neutral-300">Quick Commands</span>
          <kbd className="px-1.5 py-0.5 rounded bg-white/10 text-[10px] text-neutral-400 font-mono">
            Ctrl+K
          </kbd>
        </button>

        <div className="flex items-center gap-2.5 pl-2 border-l border-white/10">
          <div
            className="w-8 h-8 rounded-full bg-gradient-to-tr from-accent-cyan/20 to-accent-emerald/20 border border-accent-cyan/40 text-accent-cyan flex items-center justify-center font-bold text-xs font-mono shadow-sm"
            title={`${user?.full_name || 'Executive'} (${user?.role || 'CEO'})`}
          >
            {getInitials(user?.full_name)}
          </div>

          <button
            onClick={logout}
            title="Sign Out"
            className="p-1.5 rounded-lg text-neutral-400 hover:text-accent-rose hover:bg-accent-rose/10 transition-colors"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
}

