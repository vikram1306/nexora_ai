'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { Header } from '@/components/layout/Header';
import { Sidebar } from '@/components/layout/Sidebar';
import { CommandPalette } from '@/components/layout/CommandPalette';
import { OverviewTab } from '@/components/dashboard/OverviewTab';
import { QueryTab } from '@/components/dashboard/QueryTab';
import { IngestTab } from '@/components/dashboard/IngestTab';
import { SentinelTab } from '@/components/dashboard/SentinelTab';
import { GovernanceTab } from '@/components/dashboard/GovernanceTab';
import {
  ingestApi,
  sentinelApi,
  queryApi,
  DatasetItem,
  SentinelAlertItem,
  GovernanceStats
} from '@/lib/api';
import { useAuth } from '@/context/AuthContext';

export default function DashboardPage() {
  const router = useRouter();
  const { token, isAuthenticated, isLoading: authLoading } = useAuth();

  const [activeTab, setActiveTab] = useState<'overview' | 'query' | 'ingest' | 'sentinel' | 'governance'>('overview');
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false);
  const [presetQuery, setPresetQuery] = useState('');

  // Core Data State
  const [datasets, setDatasets] = useState<DatasetItem[]>([]);
  const [alerts, setAlerts] = useState<SentinelAlertItem[]>([]);
  const [governanceStats, setGovernanceStats] = useState<GovernanceStats | null>(null);
  const [decisionsHistory, setDecisionsHistory] = useState<any[]>([]);
  const [ollamaStatus, setOllamaStatus] = useState<{ status: string; active_llm: string }>({
    status: 'checking',
    active_llm: 'Verifying Ollama...',
  });

  // If not authenticated, redirect to /login so the user can sign in or register explicitly
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [authLoading, isAuthenticated, router]);

  // Ollama status check
  useEffect(() => {
    async function checkOllama() {
      try {
        const data = await queryApi.checkOllamaStatus();
        setOllamaStatus(data);
      } catch (err) {
        setOllamaStatus({
          status: 'offline',
          active_llm: 'Deterministic Multi-Agent Engine',
        });
      }
    }
    checkOllama();
  }, []);

  // Fetch Datasets
  const fetchDatasets = useCallback(async () => {
    if (!token) return;
    try {
      const data = await ingestApi.getDatasets();
      setDatasets(data);
    } catch (err) {
      console.warn('Could not fetch datasets list');
    }
  }, [token]);

  // Fetch Sentinel Alerts
  const fetchAlerts = useCallback(async () => {
    if (!token) return;
    try {
      const data = await sentinelApi.getAlerts();
      setAlerts(data);
    } catch (err) {
      console.warn('Could not fetch sentinel alerts');
    }
  }, [token]);

  // Fetch Governance Stats & Decisions
  const fetchGovernance = useCallback(async () => {
    if (!token) return;
    try {
      const [stats, history] = await Promise.all([
        queryApi.getGovernanceStats().catch(() => null),
        queryApi.listDecisions(50).catch(() => []),
      ]);
      if (stats) setGovernanceStats(stats);
      if (history) setDecisionsHistory(history);
    } catch (err) {
      console.warn('Could not fetch governance stats');
    }
  }, [token]);

  // Refresh data on token change or tab navigation
  useEffect(() => {
    if (token) {
      fetchDatasets();
      fetchAlerts();
      fetchGovernance();
    }
  }, [token, activeTab, fetchDatasets, fetchAlerts, fetchGovernance]);

  // Handle Ctrl+K custom event trigger
  useEffect(() => {
    const handleOpen = () => setIsCommandPaletteOpen(true);
    window.addEventListener('open-command-palette', handleOpen);
    return () => window.removeEventListener('open-command-palette', handleOpen);
  }, []);

  const handleExecutePresetQuery = (prompt: string) => {
    setPresetQuery(prompt);
    setActiveTab('query');
  };

  const handleTriggerSentinelScan = async () => {
    setActiveTab('sentinel');
    try {
      await sentinelApi.triggerScan();
      fetchAlerts();
    } catch (err) {
      console.warn('Trigger scan error', err);
    }
  };

  const unackAlertsCount = alerts.filter((a) => !a.acknowledged).length;

  if (authLoading) {
    return (
      <div className="min-h-screen bg-obsidian-950 text-white flex flex-col items-center justify-center font-sans">
        <div className="w-8 h-8 border-2 border-accent-cyan border-t-transparent rounded-full animate-spin mb-3" />
        <p className="text-xs font-mono text-neutral-400">Loading Executive Session...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null; // Will redirect in useEffect
  }

  return (
    <div className="min-h-screen bg-obsidian-950 text-white flex flex-col font-sans selection:bg-accent-cyan/30 selection:text-accent-cyan">
      {/* Executive Top Header */}
      <Header
        activeTab={activeTab}
        onTabChange={setActiveTab}
        onOpenCommandPalette={() => setIsCommandPaletteOpen(true)}
        ollamaStatus={ollamaStatus}
        unacknowledgedAlertsCount={unackAlertsCount}
        decisionsCount={governanceStats?.total_decisions || 0}
      />

      {/* Main Workspace: Sidebar + Dynamic Tab View */}
      <div className="flex-1 flex overflow-hidden">
        <Sidebar
          activeTab={activeTab}
          onTabChange={setActiveTab}
          unacknowledgedAlertsCount={unackAlertsCount}
          decisionsCount={governanceStats?.total_decisions || 0}
        />

        <main className="flex-1 p-6 md:p-8 max-w-7xl mx-auto w-full overflow-y-auto">
          {activeTab === 'overview' && (
            <OverviewTab
              onSwitchTab={setActiveTab}
              onExecutePresetQuery={handleExecutePresetQuery}
              datasetsCount={datasets.length}
              alertsCount={unackAlertsCount}
              decisionsCount={governanceStats?.total_decisions || 0}
              governanceRate={governanceStats?.acceptance_rate_pct || 94.2}
            />
          )}

          {activeTab === 'query' && (
            <QueryTab
              initialPrompt={presetQuery}
              onDecisionLogged={fetchGovernance}
            />
          )}

          {activeTab === 'ingest' && (
            <IngestTab
              datasets={datasets}
              onRefreshDatasets={fetchDatasets}
              onDatasetUploaded={fetchDatasets}
            />
          )}

          {activeTab === 'sentinel' && (
            <SentinelTab
              alerts={alerts}
              onRefreshAlerts={fetchAlerts}
              onAlertAcknowledged={fetchAlerts}
            />
          )}

          {activeTab === 'governance' && (
            <GovernanceTab
              stats={governanceStats}
              decisions={decisionsHistory}
              onRefresh={fetchGovernance}
            />
          )}
        </main>
      </div>

      {/* Global Command Palette (Ctrl+K) */}
      <CommandPalette
        isOpen={isCommandPaletteOpen}
        onClose={() => setIsCommandPaletteOpen(false)}
        onSelectTab={setActiveTab}
        onExecutePresetQuery={handleExecutePresetQuery}
        onTriggerSentinelScan={handleTriggerSentinelScan}
      />
    </div>
  );
}
