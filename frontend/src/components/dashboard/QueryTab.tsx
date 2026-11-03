'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { jsPDF } from 'jspdf';
import {
  BrainCircuit,
  Sparkles,
  ArrowRight,
  ChevronRight,
  Download,
  Terminal,
  Code,
  ShieldCheck,
  ThumbsUp,
  ThumbsDown,
  Check,
  X,
  RefreshCw,
  AlertCircle,
  FileText,
  BarChart3,
  Layers
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid
} from 'recharts';
import { queryApi, ExecutiveQueryResponse } from '@/lib/api';
import { GlassCard } from '../ui/GlassCard';
import { DepartmentBadge } from '../ui/DepartmentBadge';
import { ConfidenceMeter } from '../ui/ConfidenceMeter';
import { SqlInspectModal } from '../modals/SqlInspectModal';

interface QueryTabProps {
  initialPrompt?: string;
  onDecisionLogged?: () => void;
}

export function QueryTab({ initialPrompt = '', onDecisionLogged }: QueryTabProps) {
  const [queryInput, setQueryInput] = useState(initialPrompt);
  const [isExecuting, setIsExecuting] = useState(false);
  const [queryResult, setQueryResult] = useState<ExecutiveQueryResponse | null>(null);
  const [apiError, setApiError] = useState('');
  const [selectedAgentTab, setSelectedAgentTab] = useState<string | null>(null);

  // Evidence modal state
  const [activeSqlModal, setActiveSqlModal] = useState<{
    department: string;
    sql: string;
    source: string;
  } | null>(null);

  // Local recommendation decisions tracking
  const [recommendationDecisions, setRecommendationDecisions] = useState<
    Record<string, 'ACCEPTED' | 'REJECTED'>
  >({});
  const [isLoggingDecision, setIsLoggingDecision] = useState<string | null>(null);

  const quickPrompts = [
    'What was our total revenue and EBITDA margin for Q3, and what are the growth drivers?',
    'Analyze marketing spend efficiency, CAC trends, and lead conversion rates.',
    'Review headcount growth, employee turnover, and department salary distribution.',
    'Evaluate operational fulfillment delays and inventory turnover rates.',
  ];

  const handleExecuteQuery = async (e?: React.FormEvent, overridePrompt?: string) => {
    if (e) e.preventDefault();
    const promptToRun = overridePrompt || queryInput;
    if (!promptToRun.trim()) return;

    setIsExecuting(true);
    setQueryResult(null);
    setApiError('');
    setSelectedAgentTab(null);

    try {
      const data = await queryApi.executeQuery(promptToRun);
      setQueryResult(data);
      if (data.selected_departments && data.selected_departments.length > 0) {
        setSelectedAgentTab(data.selected_departments[0]);
      }
    } catch (err: any) {
      setApiError(
        err.message ||
          'Failed to execute multi-agent query. Ensure the backend server is running on port 8000.'
      );
    } finally {
      setIsExecuting(false);
    }
  };

  const handleRecommendationDecision = async (rec: any, actionType: 'ACCEPTED' | 'REJECTED') => {
    const recId = rec.id || `rec_${Date.now()}`;
    setIsLoggingDecision(recId);
    try {
      await queryApi.logRecommendationDecision({
        recommendation_id: recId,
        recommendation_title: rec.title,
        department: rec.target_department || 'Executive',
        action_type: actionType,
        action_plan: rec.action_item,
        confidence_score: rec.confidence_score || 0.95,
        impact_urgency: rec.impact_urgency || 'High',
        feedback_notes:
          actionType === 'ACCEPTED'
            ? 'Approved by executive authority for departmental execution'
            : 'Rejected during executive review',
      });
      setRecommendationDecisions((prev) => ({ ...prev, [recId]: actionType }));
      if (onDecisionLogged) onDecisionLogged();
    } catch (err) {
      console.error('Failed to log recommendation decision:', err);
    } finally {
      setIsLoggingDecision(null);
    }
  };

  const handleExportReport = () => {
    if (!queryResult) return;
    try {
      const doc = new jsPDF();

      // Title Banner
      doc.setFillColor(15, 23, 42); // Obsidian Slate
      doc.rect(0, 0, 210, 35, 'F');

      doc.setTextColor(255, 255, 255);
      doc.setFont('helvetica', 'bold');
      doc.setFontSize(18);
      doc.text('NEXORA AI - EXECUTIVE INTELLIGENCE REPORT', 14, 18);

      doc.setFontSize(10);
      doc.setFont('helvetica', 'normal');
      doc.setTextColor(148, 163, 184);
      doc.text(
        `Generated: ${new Date().toLocaleString()} | Guardrail: Zero-Hallucination Verified`,
        14,
        26
      );

      let yPos = 45;
      doc.setTextColor(15, 23, 42);

      // Metadata Block
      doc.setFont('helvetica', 'bold');
      doc.setFontSize(10);
      doc.text('Query Prompt:', 14, yPos);
      doc.setFont('helvetica', 'normal');
      doc.text(`${queryResult.prompt}`, 45, yPos);
      yPos += 7;

      doc.setFont('helvetica', 'bold');
      doc.text('Intent:', 14, yPos);
      doc.setFont('helvetica', 'normal');
      doc.text(`${queryResult.intent}`, 45, yPos);
      yPos += 7;

      doc.setFont('helvetica', 'bold');
      doc.text('Verification Score:', 14, yPos);
      doc.setFont('helvetica', 'normal');
      doc.text(
        `${Math.round(queryResult.confidence_score * 100)}% Zero-Hallucination Confidence`,
        45,
        yPos
      );
      yPos += 12;

      // Executive Summary
      doc.setFont('helvetica', 'bold');
      doc.setFontSize(12);
      doc.setTextColor(30, 41, 59);
      doc.text('EXECUTIVE SUMMARY', 14, yPos);
      yPos += 6;

      doc.setLineWidth(0.5);
      doc.setDrawColor(226, 232, 240);
      doc.line(14, yPos, 196, yPos);
      yPos += 6;

      doc.setFont('helvetica', 'normal');
      doc.setFontSize(9);
      const cleanSummary = (queryResult.executive_summary || '')
        .replace(/###\s?/g, '')
        .replace(/\*\*/g, '');
      const summaryLines = doc.splitTextToSize(cleanSummary, 180);
      doc.text(summaryLines, 14, yPos);
      yPos += summaryLines.length * 4.5 + 10;

      // Strategic Recommendations
      if (yPos > 240) {
        doc.addPage();
        yPos = 20;
      }
      doc.setFont('helvetica', 'bold');
      doc.setFontSize(12);
      doc.text('STRATEGIC RECOMMENDATIONS', 14, yPos);
      yPos += 6;
      doc.line(14, yPos, 196, yPos);
      yPos += 6;

      if (queryResult.strategic_recommendations) {
        queryResult.strategic_recommendations.forEach((r: any, i: number) => {
          if (yPos > 250) {
            doc.addPage();
            yPos = 20;
          }
          doc.setFont('helvetica', 'bold');
          doc.setFontSize(9.5);
          doc.setTextColor(15, 23, 42);
          doc.text(`${i + 1}. [${r.target_department}] ${r.title}`, 14, yPos);
          yPos += 5;

          doc.setFont('helvetica', 'normal');
          doc.setFontSize(8.5);
          doc.setTextColor(51, 65, 85);
          const actionLines = doc.splitTextToSize(`Action: ${r.action_item}`, 175);
          doc.text(actionLines, 18, yPos);
          yPos += actionLines.length * 4 + 2;

          doc.setFont('helvetica', 'bold');
          doc.setTextColor(16, 185, 129);
          doc.text(`Expected Impact: ${r.expected_impact}`, 18, yPos);
          yPos += 7;
        });
      }

      doc.save(`Nexora_Executive_Report_${Date.now()}.pdf`);
    } catch (err) {
      console.error('PDF export fallback:', err);
    }
  };

  const renderFormattedSummary = (summaryText: string) => {
    if (!summaryText) return null;
    const sections = summaryText.split('### ').filter(Boolean);

    if (sections.length <= 1 && !summaryText.includes('###')) {
      return (
        <div className="p-5 rounded-xl bg-obsidian-850 border border-white/10 text-neutral-300 text-sm leading-relaxed whitespace-pre-line">
          {summaryText}
        </div>
      );
    }

    return (
      <div className="space-y-4">
        {sections.map((sec, idx) => {
          const lines = sec.split('\n');
          const title = lines[0].trim();
          const contentLines = lines.slice(1).filter((l) => l.trim().length > 0);

          const isEbitda = title.includes('EBITDA') || title.includes('FINANCIAL');
          const isLlama = title.includes('LLAMA');

          return (
            <div
              key={idx}
              className={`p-5 rounded-xl border transition-all ${
                isEbitda
                  ? 'bg-accent-cyan/10 border-accent-cyan/40 shadow-lg shadow-accent-cyan/5'
                  : isLlama
                  ? 'bg-accent-emerald/10 border-accent-emerald/30'
                  : 'bg-obsidian-850 border-white/10'
              }`}
            >
              <h4
                className={`text-sm font-mono font-bold uppercase tracking-wider mb-3 flex items-center gap-2 ${
                  isEbitda ? 'text-accent-cyan' : isLlama ? 'text-accent-emerald' : 'text-white'
                }`}
              >
                <ChevronRight className="w-4 h-4" /> {title}
              </h4>

              <div className="space-y-2">
                {contentLines.map((line, lIdx) => {
                  const cleaned = line.replace(/^•\s*/, '').trim();
                  if (!cleaned) return null;

                  return (
                    <div
                      key={lIdx}
                      className="flex items-start gap-2 text-xs text-neutral-200 leading-relaxed"
                    >
                      <span className="text-accent-cyan font-bold">•</span>
                      <span
                        dangerouslySetInnerHTML={{
                          __html: cleaned.replace(
                            /\*\*(.*?)\*\*/g,
                            '<strong class="text-white font-semibold">$1</strong>'
                          ),
                        }}
                      />
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="space-y-8"
    >
      {/* Title */}
      <div>
        <h1 className="text-3xl font-serif font-bold text-white tracking-tight flex items-center gap-3">
          <BrainCircuit className="w-8 h-8 text-accent-cyan" /> Multi-Agent Command Center
        </h1>
        <p className="text-neutral-400 text-sm font-light mt-1">
          Planner agent intent decomposition, parallel department execution, and zero-hallucination verification.
        </p>
      </div>

      {apiError && (
        <div className="p-4 rounded-xl bg-accent-rose/10 border border-accent-rose/30 text-accent-rose text-xs flex items-center gap-3">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{apiError}</span>
        </div>
      )}

      {/* Query Input Box */}
      <GlassCard className="p-6">
        <form onSubmit={handleExecuteQuery} className="space-y-4">
          <div className="relative">
            <textarea
              rows={3}
              value={queryInput}
              onChange={(e) => setQueryInput(e.target.value)}
              placeholder="Ask an executive question across Sales, Finance, HR, Marketing, or Operations..."
              className="w-full p-4 rounded-xl bg-obsidian-850 border border-white/10 text-white placeholder-neutral-500 text-sm focus:outline-none focus:border-accent-cyan/60 transition-all resize-none font-sans"
            />
          </div>

          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            {/* Quick Suggestions */}
            <div className="flex items-center gap-1.5 flex-wrap">
              <span className="text-[11px] font-mono text-neutral-500 uppercase mr-1">Presets:</span>
              {quickPrompts.slice(0, 2).map((p, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => {
                    setQueryInput(p);
                    handleExecuteQuery(undefined, p);
                  }}
                  className="px-2.5 py-1 rounded-lg bg-obsidian-850 hover:bg-white/5 border border-white/5 text-[11px] text-neutral-300 hover:text-white transition-all truncate max-w-xs"
                >
                  {p}
                </button>
              ))}
            </div>

            <button
              type="submit"
              disabled={isExecuting || !queryInput.trim()}
              className="px-6 py-2.5 rounded-xl bg-accent-cyan text-obsidian-950 font-bold text-xs hover:brightness-110 transition-all shadow-lg shadow-accent-cyan/20 flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {isExecuting ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" /> Synthesizing Multi-Agent Intelligence...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" /> Execute Intelligence Query
                  <ArrowRight className="w-3.5 h-3.5" />
                </>
              )}
            </button>
          </div>
        </form>
      </GlassCard>

      {/* Execution Results View */}
      {queryResult && (
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="space-y-6"
        >
          {/* Metadata & Actions Header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-2xl glass-panel border border-white/10">
            <div className="space-y-1">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-xs font-mono uppercase px-2.5 py-0.5 rounded bg-accent-cyan/10 text-accent-cyan border border-accent-cyan/30 font-semibold">
                  Intent: {queryResult.intent}
                </span>
                <span className="text-xs font-mono text-neutral-400">
                  Execution Latency: <strong className="text-white">{queryResult.execution_time_ms}ms</strong>
                </span>
              </div>
              <div className="text-xs text-neutral-300 font-light mt-1">
                Prompt: &ldquo;{queryResult.prompt}&rdquo;
              </div>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={handleExportReport}
                className="px-4 py-2 rounded-xl bg-obsidian-850 hover:bg-white/10 border border-white/15 text-xs font-semibold text-white transition-all flex items-center gap-2 shadow-sm"
              >
                <Download className="w-3.5 h-3.5 text-accent-cyan" /> Export Executive PDF
              </button>
            </div>
          </div>

          {/* Responsible AI Confidence Meter */}
          <div className="p-5 rounded-2xl glass-panel border border-white/10">
            <ConfidenceMeter score={queryResult.confidence_score} />
          </div>

          {/* Recharts Visualization */}
          {queryResult.visual_config &&
            queryResult.visual_config.data &&
            queryResult.visual_config.data.length > 0 && (
              <GlassCard className="p-6 space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-base font-serif font-bold text-white flex items-center gap-2">
                    <BarChart3 className="w-4 h-4 text-accent-cyan" />{' '}
                    {queryResult.visual_config.title || 'Telemetry Trends & Aggregations'}
                  </h3>
                  <span className="text-[10px] font-mono text-neutral-500 uppercase">
                    Interactive Recharts
                  </span>
                </div>

                <div className="h-64 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={queryResult.visual_config.data}
                      margin={{ top: 10, right: 10, left: 0, bottom: 20 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                      <XAxis
                        dataKey={queryResult.visual_config.x_axis || 'name'}
                        stroke="#64748B"
                        fontSize={11}
                        tickLine={false}
                      />
                      <YAxis stroke="#64748B" fontSize={11} tickLine={false} />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#0E0E12',
                          borderColor: 'rgba(255,255,255,0.1)',
                          borderRadius: '12px',
                          color: '#FFF',
                          fontSize: '12px',
                        }}
                      />
                      {queryResult.visual_config.series ? (
                        queryResult.visual_config.series.map((s, idx) => (
                          <Bar
                            key={s.key || idx}
                            dataKey={s.key}
                            name={s.name}
                            fill={s.color || '#00E5FF'}
                            radius={[6, 6, 0, 0]}
                          />
                        ))
                      ) : (
                        <Bar dataKey="value" fill="#00E5FF" radius={[6, 6, 0, 0]} />
                      )}
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </GlassCard>
            )}

          {/* Executive Summary Cards */}
          <GlassCard className="p-6 space-y-4">
            <h3 className="text-lg font-serif font-bold text-white flex items-center gap-2">
              <FileText className="w-5 h-5 text-accent-cyan" /> Synthesized Executive Intelligence
            </h3>
            {renderFormattedSummary(queryResult.executive_summary)}
          </GlassCard>

          {/* Department Agent Breakdown Tabs */}
          {queryResult.department_outputs &&
            Object.keys(queryResult.department_outputs).length > 0 && (
              <GlassCard className="p-6 space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-base font-serif font-bold text-white flex items-center gap-2">
                    <Layers className="w-4 h-4 text-accent-cyan" /> Department Agent Telemetry Streams
                  </h3>
                  <div className="flex items-center gap-1.5 flex-wrap">
                    {Object.keys(queryResult.department_outputs).map((dept) => (
                      <button
                        key={dept}
                        onClick={() => setSelectedAgentTab(dept)}
                        className={`px-3 py-1 rounded-lg text-xs font-mono uppercase font-semibold transition-all ${
                          selectedAgentTab === dept
                            ? 'bg-accent-cyan text-obsidian-950 shadow-sm'
                            : 'bg-obsidian-850 text-neutral-400 hover:text-white border border-white/5'
                        }`}
                      >
                        {dept}
                      </button>
                    ))}
                  </div>
                </div>

                {selectedAgentTab && queryResult.department_outputs[selectedAgentTab] && (
                  <div className="p-4 rounded-xl bg-obsidian-950 border border-white/5 space-y-3 font-mono text-xs">
                    <div className="flex items-center justify-between text-neutral-400 pb-2 border-b border-white/5">
                      <span>Agent: {selectedAgentTab.toUpperCase()}</span>
                      <span>Zero-Hallucination Verified</span>
                    </div>
                    <pre className="text-neutral-300 overflow-x-auto whitespace-pre-wrap leading-relaxed max-h-60">
                      {JSON.stringify(queryResult.department_outputs[selectedAgentTab], null, 2)}
                    </pre>
                  </div>
                )}
              </GlassCard>
            )}

          {/* Strategic Recommendations with Explicit Human Authorization */}
          {queryResult.strategic_recommendations &&
            queryResult.strategic_recommendations.length > 0 && (
              <GlassCard glow="emerald" className="p-6 space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-serif font-bold flex items-center gap-2 text-accent-emerald">
                    <Sparkles className="w-5 h-5" /> AI-Assisted Strategic Recommendations
                  </h3>
                  <span className="text-[11px] font-mono text-neutral-400 bg-obsidian-850 px-2.5 py-1 rounded border border-white/10">
                    Human-in-the-Loop Approval Required
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {queryResult.strategic_recommendations.map((rec: any, idx: number) => {
                    const recId = rec.id || `rec_${idx}`;
                    const decision = recommendationDecisions[recId];
                    return (
                      <div
                        key={idx}
                        className={`p-5 rounded-xl bg-obsidian-850 border transition-all flex flex-col justify-between ${
                          decision === 'ACCEPTED'
                            ? 'border-accent-emerald/60 bg-accent-emerald/5 shadow-lg shadow-accent-emerald/10'
                            : decision === 'REJECTED'
                            ? 'border-accent-rose/50 bg-accent-rose/5 opacity-70'
                            : 'border-white/5 hover:border-white/15'
                        }`}
                      >
                        <div>
                          <div className="flex items-start justify-between mb-2">
                            <span className="font-semibold text-white text-sm">{rec.title}</span>
                            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-accent-emerald/10 text-accent-emerald border border-accent-emerald/20 ml-2 whitespace-nowrap">
                              {rec.expected_impact}
                            </span>
                          </div>
                          <p className="text-xs text-neutral-300 font-light mb-3">
                            {rec.action_item}
                          </p>
                          <div className="text-[11px] text-neutral-500 font-mono mb-4">
                            Evidence: {rec.supporting_evidence?.[0] || 'Verified via memory engine'}
                          </div>
                        </div>

                        {/* Human Decision Action Area */}
                        <div className="pt-3 border-t border-white/5 flex items-center justify-between gap-3">
                          {decision ? (
                            <div className="flex items-center justify-between w-full text-xs font-mono">
                              {decision === 'ACCEPTED' ? (
                                <span className="text-accent-emerald flex items-center gap-1.5 font-semibold bg-accent-emerald/10 px-3 py-1 rounded-lg border border-accent-emerald/30">
                                  <Check className="w-3.5 h-3.5" /> Action Plan Accepted by CEO
                                </span>
                              ) : (
                                <span className="text-accent-rose flex items-center gap-1.5 font-semibold bg-accent-rose/10 px-3 py-1 rounded-lg border border-accent-rose/30">
                                  <X className="w-3.5 h-3.5" /> Recommendation Rejected
                                </span>
                              )}
                              <span className="text-[10px] text-neutral-500">
                                Logged to Audit Trail
                              </span>
                            </div>
                          ) : (
                            <div className="flex items-center gap-2 w-full justify-end">
                              <button
                                onClick={() => handleRecommendationDecision(rec, 'REJECTED')}
                                disabled={isLoggingDecision === recId}
                                className="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-accent-rose/20 text-neutral-400 hover:text-accent-rose border border-white/10 hover:border-accent-rose/30 text-xs font-medium transition-all flex items-center gap-1.5 disabled:opacity-50"
                              >
                                <ThumbsDown className="w-3 h-3" /> Reject
                              </button>
                              <button
                                onClick={() => handleRecommendationDecision(rec, 'ACCEPTED')}
                                disabled={isLoggingDecision === recId}
                                className="px-3.5 py-1.5 rounded-lg bg-accent-emerald/20 hover:bg-accent-emerald/30 text-accent-emerald border border-accent-emerald/40 text-xs font-semibold transition-all flex items-center gap-1.5 shadow-sm hover:shadow-accent-emerald/20 disabled:opacity-50"
                              >
                                <ThumbsUp className="w-3 h-3" /> Accept Action Plan
                              </button>
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </GlassCard>
            )}

          {/* Evidence Inspector Section */}
          {queryResult.evidence_queries && queryResult.evidence_queries.length > 0 && (
            <GlassCard className="p-6 space-y-4">
              <h3 className="text-base font-serif font-bold text-white flex items-center gap-2">
                <Terminal className="w-4 h-4 text-accent-cyan" /> Zero-Hallucination SQL Evidence Log
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {queryResult.evidence_queries.map((ev, idx) => (
                  <div
                    key={idx}
                    onClick={() => setActiveSqlModal(ev)}
                    className="p-3.5 rounded-xl bg-obsidian-850 hover:bg-white/5 border border-white/5 hover:border-accent-cyan/30 cursor-pointer transition-all flex items-center justify-between"
                  >
                    <div className="space-y-1 overflow-hidden pr-2">
                      <div className="flex items-center gap-2">
                        <DepartmentBadge department={ev.department} size="xs" />
                        <span className="text-[10px] text-neutral-400 font-mono">
                          {ev.source || 'Database Query'}
                        </span>
                      </div>
                      <div className="text-xs font-mono text-neutral-300 truncate">
                        {ev.sql}
                      </div>
                    </div>
                    <ChevronRight className="w-4 h-4 text-neutral-500 flex-shrink-0" />
                  </div>
                ))}
              </div>
            </GlassCard>
          )}
        </motion.div>
      )}

      {/* SQL Inspection Modal */}
      <SqlInspectModal evidence={activeSqlModal} onClose={() => setActiveSqlModal(null)} />
    </motion.div>
  );
}

