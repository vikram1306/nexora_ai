'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  Activity,
  AlertTriangle,
  RefreshCw,
  CheckCircle2,
  ShieldAlert,
  ArrowRight,
  Filter,
  Check
} from 'lucide-react';
import { sentinelApi, SentinelAlertItem } from '@/lib/api';
import { GlassCard } from '../ui/GlassCard';

interface SentinelTabProps {
  alerts: SentinelAlertItem[];
  onRefreshAlerts: () => void;
  onAlertAcknowledged?: () => void;
}

export function SentinelTab({
  alerts,
  onRefreshAlerts,
  onAlertAcknowledged,
}: SentinelTabProps) {
  const [selectedSeverity, setSelectedSeverity] = useState<string>('ALL');
  const [showOnlyUnacknowledged, setShowOnlyUnacknowledged] = useState<boolean>(false);
  const [isScanning, setIsScanning] = useState<boolean>(false);
  const [acknowledgingId, setAcknowledgingId] = useState<string | null>(null);
  const [scanMessage, setScanMessage] = useState<string>('');

  const handleTriggerScan = async () => {
    setIsScanning(true);
    setScanMessage('');
    try {
      const results = await sentinelApi.triggerScan();
      setScanMessage(`Scan complete. ${results.length} anomalies audited.`);
      onRefreshAlerts();
      setTimeout(() => setScanMessage(''), 4000);
    } catch (err: any) {
      console.warn('Sentinel scan trigger error', err);
    } finally {
      setIsScanning(false);
    }
  };

  const handleAcknowledge = async (alertId: string) => {
    setAcknowledgingId(alertId);
    try {
      await sentinelApi.acknowledgeAlert(alertId);
      onRefreshAlerts();
      if (onAlertAcknowledged) onAlertAcknowledged();
    } catch (err) {
      console.error('Failed to acknowledge alert', err);
    } finally {
      setAcknowledgingId(null);
    }
  };

  const filteredAlerts = alerts.filter((a) => {
    if (selectedSeverity !== 'ALL' && a.severity !== selectedSeverity) {
      return false;
    }
    if (showOnlyUnacknowledged && a.acknowledged) {
      return false;
    }
    return true;
  });

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case 'CRITICAL':
        return 'bg-accent-rose/20 text-accent-rose border border-accent-rose/40';
      case 'HIGH':
        return 'bg-accent-rose/15 text-accent-rose border border-accent-rose/30';
      case 'MEDIUM':
        return 'bg-amber-500/15 text-amber-400 border border-amber-500/30';
      case 'LOW':
      default:
        return 'bg-blue-500/15 text-blue-400 border border-blue-500/30';
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="space-y-8"
    >
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-serif font-bold text-white tracking-tight flex items-center gap-3">
            <Activity className="w-8 h-8 text-accent-rose" /> Sentinel AI Anomaly Center
          </h1>
          <p className="text-neutral-400 text-sm font-light mt-1">
            Continuous background daemon monitoring metrics, calculating z-score variances (&gt;2.5σ), and conducting automated root-cause analysis.
          </p>
        </div>

        <button
          onClick={handleTriggerScan}
          disabled={isScanning}
          className="px-5 py-2.5 rounded-xl bg-accent-rose text-white font-bold text-xs hover:brightness-110 transition-all flex items-center gap-2 shadow-lg shadow-accent-rose/20 disabled:opacity-50 self-start sm:self-auto"
        >
          {isScanning ? (
            <RefreshCw className="w-4 h-4 animate-spin" />
          ) : (
            <ShieldAlert className="w-4 h-4" />
          )}
          Trigger Manual Sentinel Scan
        </button>
      </div>

      {scanMessage && (
        <div className="p-3.5 rounded-xl bg-accent-cyan/10 border border-accent-cyan/30 text-accent-cyan text-xs font-mono flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4" /> {scanMessage}
        </div>
      )}

      {/* Filter Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-xl bg-obsidian-850 border border-white/5">
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-[10px] font-mono uppercase text-neutral-500 mr-2 flex items-center gap-1">
            <Filter className="w-3 h-3" /> Severity:
          </span>
          {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map((sev) => (
            <button
              key={sev}
              onClick={() => setSelectedSeverity(sev)}
              className={`px-3 py-1 rounded-lg text-xs font-mono uppercase transition-all ${
                selectedSeverity === sev
                  ? 'bg-white text-obsidian-950 font-bold shadow'
                  : 'text-neutral-400 hover:text-white hover:bg-white/5'
              }`}
            >
              {sev}
            </button>
          ))}
        </div>

        <label className="flex items-center gap-2 text-xs text-neutral-300 cursor-pointer font-mono select-none">
          <input
            type="checkbox"
            checked={showOnlyUnacknowledged}
            onChange={(e) => setShowOnlyUnacknowledged(e.target.checked)}
            className="rounded bg-obsidian-950 border-white/20 text-accent-cyan focus:ring-0 cursor-pointer"
          />
          <span>Unacknowledged Only</span>
        </label>
      </div>

      {/* Alerts Feed */}
      <div className="space-y-4">
        {filteredAlerts.length === 0 ? (
          <GlassCard className="p-8 text-center text-neutral-400 text-sm font-light">
            No active anomalies matching the selected filters. Upload dataset CSVs or trigger a scan to inspect metrics.
          </GlassCard>
        ) : (
          filteredAlerts.map((alert) => (
            <GlassCard
              key={alert.id}
              glow={alert.severity === 'CRITICAL' || alert.severity === 'HIGH' ? 'rose' : 'none'}
              className="p-6 space-y-4"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div className="flex items-center gap-3">
                  <span
                    className={`px-2.5 py-0.5 rounded text-[10px] font-mono font-bold uppercase tracking-wider ${getSeverityBadge(
                      alert.severity
                    )}`}
                  >
                    {alert.severity} SEVERITY
                  </span>
                  <span className="text-xs text-neutral-400 font-mono">
                    Target Role: <strong className="text-neutral-200">{alert.target_role}</strong>
                  </span>
                  {alert.deviation_score && (
                    <span className="text-xs font-mono text-accent-rose font-semibold">
                      +{alert.deviation_score.toFixed(1)}σ Outlier
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-3">
                  <span className="text-[11px] font-mono text-neutral-500">
                    {new Date(alert.created_at).toLocaleString()}
                  </span>
                  {alert.acknowledged ? (
                    <span className="text-[10px] font-mono text-accent-emerald flex items-center gap-1 bg-accent-emerald/10 px-2 py-0.5 rounded border border-accent-emerald/20 font-semibold">
                      <Check className="w-3 h-3" /> Reviewed
                    </span>
                  ) : (
                    <button
                      onClick={() => handleAcknowledge(alert.id)}
                      disabled={acknowledgingId === alert.id}
                      className="px-3 py-1 rounded-lg bg-white/10 hover:bg-white/20 text-xs text-white font-mono flex items-center gap-1.5 transition-all disabled:opacity-50"
                    >
                      {acknowledgingId === alert.id ? (
                        <RefreshCw className="w-3 h-3 animate-spin" />
                      ) : (
                        <Check className="w-3 h-3 text-accent-emerald" />
                      )}
                      Acknowledge Alert
                    </button>
                  )}
                </div>
              </div>

              <div>
                <h3 className="text-lg font-bold text-white mb-1.5 font-sans">{alert.title}</h3>
                <p className="text-xs text-neutral-300 font-light leading-relaxed">
                  {alert.description}
                </p>
              </div>

              {/* Root Cause Panel */}
              {alert.root_cause && (
                <div className="p-3.5 rounded-xl bg-obsidian-850 border border-white/5 text-xs text-neutral-300 font-mono flex items-start gap-2">
                  <span className="text-accent-cyan font-bold flex-shrink-0">Root Cause:</span>
                  <span className="text-neutral-300">{alert.root_cause}</span>
                </div>
              )}
            </GlassCard>
          ))
        )}
      </div>
    </motion.div>
  );
}

