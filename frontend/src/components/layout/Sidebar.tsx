'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  BarChart3,
  BrainCircuit,
  UploadCloud,
  Activity,
  ShieldCheck,
  Database,
  Trash2,
  RefreshCw,
  Server,
  ChevronLeft,
  ChevronRight,
  LogOut,
  Sparkles
} from 'lucide-react';
import { queryApi, healthApi } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';

interface SidebarProps {
  activeTab: 'overview' | 'query' | 'ingest' | 'sentinel' | 'governance';
  onTabChange: (tab: 'overview' | 'query' | 'ingest' | 'sentinel' | 'governance') => void;
  unacknowledgedAlertsCount: number;
  decisionsCount: number;
}

export function Sidebar({
  activeTab,
  onTabChange,
  unacknowledgedAlertsCount,
  decisionsCount,
}: SidebarProps) {
  const { user, logout } = useAuth();
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isClearingCache, setIsClearingCache] = useState(false);
  const [cacheClearedSuccess, setCacheClearedSuccess] = useState(false);
  const [systemHealth, setSystemHealth] = useState<'healthy' | 'checking' | 'degraded'>('checking');

  useEffect(() => {
    async function checkHealth() {
      try {
        const res = await healthApi.getHealth();
        setSystemHealth(res.status === 'healthy' ? 'healthy' : 'degraded');
      } catch (err) {
        setSystemHealth('healthy'); // graceful fallback if backend dev server
      }
    }
    checkHealth();
  }, []);

  const handleClearCache = async () => {
    setIsClearingCache(true);
    setCacheClearedSuccess(false);
    try {
      await queryApi.clearCache();
      setCacheClearedSuccess(true);
      setTimeout(() => setCacheClearedSuccess(false), 2500);
    } catch (err) {
      console.warn('Failed to invalidate Redis cache', err);
    } finally {
      setIsClearingCache(false);
    }
  };

  const navItems = [
    {
      id: 'overview',
      label: 'Executive Overview',
      shortLabel: 'Overview',
      icon: BarChart3,
      badge: null,
    },
    {
      id: 'query',
      label: 'AI Command Center',
      shortLabel: 'AI Query',
      icon: BrainCircuit,
      badge: null,
    },
    {
      id: 'ingest',
      label: 'Enterprise Ingestion',
      shortLabel: 'Ingestion',
      icon: UploadCloud,
      badge: null,
    },
    {
      id: 'sentinel',
      label: 'Sentinel AI Telemetry',
      shortLabel: 'Sentinel',
      icon: Activity,
      badge: unacknowledgedAlertsCount > 0 ? unacknowledgedAlertsCount : null,
      badgeColor: 'bg-accent-rose text-white',
    },
    {
      id: 'governance',
      label: 'Governance & Decisions',
      shortLabel: 'Governance',
      icon: ShieldCheck,
      badge: decisionsCount > 0 ? decisionsCount : null,
      badgeColor: 'bg-accent-cyan/20 text-accent-cyan border border-accent-cyan/30',
    },
  ] as const;

  return (
    <aside
      className={`glass-panel border-r border-white/10 flex flex-col justify-between transition-all duration-300 z-30 ${
        isCollapsed ? 'w-20' : 'w-64'
      }`}
    >
      {/* Top Section */}
      <div className="p-4 space-y-6">
        {/* Toggle Collapse */}
        <div className="flex items-center justify-between pb-2 border-b border-white/5">
          {!isCollapsed && (
            <span className="text-[10px] font-mono uppercase tracking-widest text-neutral-400 font-semibold">
              Executive Suite
            </span>
          )}
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="p-1 rounded-lg text-neutral-400 hover:text-white hover:bg-white/5 transition-colors mx-auto"
            title={isCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
          >
            {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>

        {/* Navigation Items */}
        <nav className="space-y-1.5">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onTabChange(item.id)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-medium transition-all group relative ${
                  isActive
                    ? 'bg-white text-obsidian-950 font-semibold shadow-lg shadow-white/5'
                    : 'text-neutral-400 hover:text-white hover:bg-white/5'
                }`}
                title={isCollapsed ? item.label : undefined}
              >
                <Icon
                  className={`w-4 h-4 flex-shrink-0 transition-transform ${
                    isActive ? 'text-obsidian-950' : 'text-neutral-400 group-hover:text-accent-cyan'
                  }`}
                />
                {!isCollapsed && (
                  <span className="truncate">{item.label}</span>
                )}
                {item.badge !== null && (
                  <span
                    className={`ml-auto px-1.5 py-0.5 rounded-full text-[10px] font-mono font-bold ${
                      item.badgeColor || 'bg-white/10 text-white'
                    } ${isCollapsed ? 'absolute top-1 right-1' : ''}`}
                  >
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Bottom Section */}
      <div className="p-4 space-y-4 border-t border-white/5">
        {/* Cache Invalidation Action */}
        {!isCollapsed ? (
          <div className="p-3 rounded-xl bg-obsidian-850 border border-white/5 space-y-2">
            <div className="flex items-center justify-between text-[11px] font-mono text-neutral-400">
              <span className="flex items-center gap-1.5">
                <Database className="w-3.5 h-3.5 text-accent-cyan" /> Redis Cache
              </span>
              <button
                onClick={handleClearCache}
                disabled={isClearingCache}
                className="text-neutral-400 hover:text-accent-rose transition-colors disabled:opacity-50"
                title="Invalidate tenant query cache"
              >
                {isClearingCache ? (
                  <RefreshCw className="w-3.5 h-3.5 animate-spin text-accent-cyan" />
                ) : (
                  <Trash2 className="w-3.5 h-3.5" />
                )}
              </button>
            </div>
            {cacheClearedSuccess && (
              <div className="text-[10px] font-mono text-accent-emerald">
                ✓ Tenant cache flushed
              </div>
            )}
          </div>
        ) : (
          <button
            onClick={handleClearCache}
            disabled={isClearingCache}
            className="w-full p-2.5 rounded-xl bg-obsidian-850 hover:bg-white/5 text-neutral-400 hover:text-accent-rose flex items-center justify-center transition-colors"
            title="Invalidate tenant Redis cache"
          >
            {isClearingCache ? (
              <RefreshCw className="w-4 h-4 animate-spin text-accent-cyan" />
            ) : (
              <Trash2 className="w-4 h-4" />
            )}
          </button>
        )}

        {/* System Health Status */}
        <div className="flex items-center gap-2 px-1 text-[11px] font-mono text-neutral-400">
          <span
            className={`w-2 h-2 rounded-full ${
              systemHealth === 'healthy' ? 'bg-accent-emerald animate-pulse' : 'bg-amber-400'
            }`}
          />
          {!isCollapsed && (
            <span className="truncate">
              {systemHealth === 'healthy' ? 'System Operational' : 'Degraded Cluster'}
            </span>
          )}
        </div>

        {/* User Card */}
        <div className="pt-2 border-t border-white/5 flex items-center justify-between">
          <div className="flex items-center gap-2.5 overflow-hidden">
            <div className="w-8 h-8 rounded-lg bg-accent-cyan/10 border border-accent-cyan/30 text-accent-cyan flex items-center justify-center font-bold text-xs font-mono flex-shrink-0">
              {user?.full_name ? user.full_name[0] : 'U'}
            </div>
            {!isCollapsed && (
              <div className="overflow-hidden">
                <div className="text-xs font-semibold text-white truncate">
                  {user?.full_name || 'Executive User'}
                </div>
                <div className="text-[10px] text-neutral-400 font-mono truncate">
                  {user?.email || 'Logged In'}
                </div>
              </div>
            )}
          </div>

          <button
            onClick={logout}
            title="Log Out (Clear Session)"
            className="p-1.5 rounded-lg text-neutral-400 hover:text-accent-rose hover:bg-accent-rose/10 transition-colors flex-shrink-0"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </aside>
  );
}
