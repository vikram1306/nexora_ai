'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import {
  BrainCircuit,
  Activity,
  Database,
  UploadCloud,
  TrendingUp,
  CheckCircle2,
  BarChart3,
  Sparkles,
  ArrowRight,
  RefreshCw,
  Building,
  AlertCircle,
  FileSpreadsheet,
  Layers,
  Users,
  Code,
  Download,
  Terminal,
  Cpu,
  ChevronRight
} from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

export default function ExecutiveDashboard() {
  const [activeTab, setActiveTab] = useState<'overview' | 'query' | 'ingest' | 'sentinel'>('overview');
  const [queryInput, setQueryInput] = useState('');
  const [isExecuting, setIsExecuting] = useState(false);
  const [queryResult, setQueryResult] = useState<any>(null);
  const [apiError, setApiError] = useState('');
  const [activeSqlModal, setActiveSqlModal] = useState<string | null>(null);

  // Authentication State
  const [token, setToken] = useState<string | null>(null);

  // Ollama Status State
  const [ollamaStatus, setOllamaStatus] = useState<{ status: string; active_llm: string }>({
    status: 'checking',
    active_llm: 'Checking Local Ollama...'
  });

  // File Upload & Datasets List State
  const [selectedDept, setSelectedDept] = useState('sales');
  const [fileToUpload, setFileToUpload] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState('');
  const [uploadedDatasets, setUploadedDatasets] = useState<any[]>([]);

  // Sentinel Alerts State
  const [alerts, setAlerts] = useState<any[]>([]);

  // Get API Base URL
  const getApiUrl = () => {
    return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';
  };

  // Auto-Authenticate Demo CEO Token & Check Ollama Status on mount
  useEffect(() => {
    async function ensureAuth() {
      const apiUrl = getApiUrl();
      try {
        const res = await fetch(`${apiUrl}/api/v1/auth/register`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            company_name: "Acme Global Enterprise",
            email: "ceo@acme.com",
            password: "Password123!",
            full_name: "Jane Doe",
            role: "CEO"
          })
        });

        if (res.ok) {
          const data = await res.json();
          setToken(data.access_token);
        } else {
          const loginRes = await fetch(`${apiUrl}/api/v1/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              email: "ceo@acme.com",
              password: "Password123!"
            })
          });
          if (loginRes.ok) {
            const loginData = await loginRes.json();
            setToken(loginData.access_token);
          }
        }

        // Check Ollama status
        const oRes = await fetch(`${apiUrl}/api/v1/query/ollama-status`);
        if (oRes.ok) {
          const oData = await oRes.json();
          setOllamaStatus(oData);
        }
      } catch (err) {
        console.warn("Backend API not reachable at", apiUrl);
      }
    }
    ensureAuth();
  }, []);

  // Fetch Datasets List
  const fetchDatasets = async () => {
    if (!token) return;
    try {
      const res = await fetch(`${getApiUrl()}/api/v1/ingest/datasets`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setUploadedDatasets(data);
      }
    } catch (e) {
      console.warn("Could not fetch datasets list");
    }
  };

  // Fetch Sentinel Alerts
  const fetchAlerts = async () => {
    if (!token) return;
    try {
      const res = await fetch(`${getApiUrl()}/api/v1/sentinel/alerts`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setAlerts(data);
      }
    } catch (e) {
      console.warn("Could not fetch alerts");
    }
  };

  useEffect(() => {
    fetchDatasets();
    fetchAlerts();
  }, [token, activeTab]);

  // Real CSV Upload Handler
  const handleFileUpload = async () => {
    if (!fileToUpload) {
      setApiError('Please select a CSV file first.');
      return;
    }
    if (!token) {
      setApiError('Authenticating with backend server... Please try again in a second.');
      return;
    }

    setIsUploading(true);
    setUploadSuccess('');
    setApiError('');

    const formData = new FormData();
    formData.append('department', selectedDept);
    formData.append('file', fileToUpload);

    try {
      const res = await fetch(`${getApiUrl()}/api/v1/ingest/upload`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      });

      if (res.ok) {
        const data = await res.json();
        setUploadSuccess(`Successfully ingested '${data.name}' (${data.row_count} rows) into ${selectedDept.toUpperCase()} Enterprise Memory!`);
        setFileToUpload(null);
        fetchDatasets();
        fetch(`${getApiUrl()}/api/v1/sentinel/trigger`, {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${token}` }
        });
      } else {
        const errData = await res.json();
        setApiError(errData.detail || 'Failed to upload CSV file.');
      }
    } catch (err: any) {
      setApiError(`Could not connect to backend server at ${getApiUrl()}. Make sure your backend server is running on port 8080.`);
    } finally {
      setIsUploading(false);
    }
  };

  // Real AI Query Handler
  const handleExecuteQuery = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!queryInput.trim()) return;

    setIsExecuting(true);
    setQueryResult(null);
    setApiError('');

    try {
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const res = await fetch(`${getApiUrl()}/api/v1/query/execute`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ prompt: queryInput })
      });

      if (res.ok) {
        const data = await res.json();
        setQueryResult(data);
      } else {
        const errData = await res.json();
        setApiError(errData.detail || 'Query execution failed');
      }
    } catch (err: any) {
      setApiError(`Could not reach backend API at ${getApiUrl()}. Please check if your backend server is running.`);
    } finally {
      setIsExecuting(false);
    }
  };

  // Export Executive Intelligence Report as Text/File
  const handleExportReport = () => {
    if (!queryResult) return;
    const textContent = `
====================================================
NEXORA AI - EXECUTIVE INTELLIGENCE REPORT
====================================================
Query Prompt: ${queryResult.prompt}
Intent: ${queryResult.intent}
Response Validator Score: ${Math.round(queryResult.confidence_score * 100)}% Verified

EXECUTIVE SUMMARY:
----------------------------------------------------
${queryResult.executive_summary}

STRATEGIC RECOMMENDATIONS:
----------------------------------------------------
${queryResult.strategic_recommendations.map((r: any, i: number) => `${i+1}. [${r.target_department}] ${r.title}\n   Action: ${r.action_item}\n   Impact: ${r.expected_impact}`).join('\n\n')}

INVOLVED DEPARTMENT AGENTS & SQL LOGS:
----------------------------------------------------
${queryResult.department_outputs.map((d: any) => `* Department: ${d.department.toUpperCase()}\n  SQL Query Executed: ${d.sql_executed}\n  Confidence: ${d.confidence_score}`).join('\n\n')}
====================================================
Generated by Nexora AI Enterprise Operating System
`;
    const element = document.createElement("a");
    const file = new Blob([textContent], { type: 'text/plain' });
    element.href = URL.createObjectURL(file);
    element.download = `Nexora_Executive_Report_${Date.now()}.txt`;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  // Render Formatted Executive Summary Section Cards
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
          const contentLines = lines.slice(1).filter(l => l.trim().length > 0);

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
              <h4 className={`text-sm font-mono font-bold uppercase tracking-wider mb-3 flex items-center gap-2 ${
                isEbitda ? 'text-accent-cyan' : isLlama ? 'text-accent-emerald' : 'text-white'
              }`}>
                <ChevronRight className="w-4 h-4" /> {title}
              </h4>

              <div className="space-y-2">
                {contentLines.map((line, lIdx) => {
                  const cleaned = line.replace(/^•\s*/, '').trim();
                  if (!cleaned) return null;

                  return (
                    <div key={lIdx} className="flex items-start gap-2 text-xs text-neutral-200 leading-relaxed">
                      <span className="text-accent-cyan font-bold">•</span>
                      <span dangerouslySetInnerHTML={{
                        __html: cleaned.replace(/\*\*(.*?)\*\*/g, '<strong class="text-white font-semibold">$1</strong>')
                      }} />
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
    <div className="min-h-screen bg-obsidian-950 text-white flex flex-col font-sans">
      {/* Top Header */}
      <header className="glass-panel border-b border-white/10 px-8 py-4 flex items-center justify-between sticky top-0 z-40">
        <div className="flex items-center gap-4">
          <Link href="/" className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-accent-cyan to-accent-emerald flex items-center justify-center font-bold text-obsidian-950">
              N
            </div>
            <span className="font-bold text-lg">NEXORA AI</span>
          </Link>
          <span className="text-white/20">|</span>
          <div className="flex items-center gap-2 text-xs font-mono text-neutral-400 bg-obsidian-850 px-3 py-1.5 rounded-lg border border-white/5">
            <Building className="w-3.5 h-3.5 text-accent-cyan" />
            Acme Global Enterprise (CEO Portal)
          </div>
          {/* Ollama LLM Connection Badge */}
          <div className={`hidden lg:flex items-center gap-1.5 px-3 py-1 rounded-full border text-[11px] font-mono ${
            ollamaStatus.status === 'online' ? 'bg-accent-emerald/10 text-accent-emerald border-accent-emerald/30' : 'bg-obsidian-850 text-neutral-400 border-white/10'
          }`}>
            <Cpu className="w-3 h-3 text-accent-cyan" />
            <span>{ollamaStatus.active_llm}</span>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center gap-1 bg-obsidian-850 p-1 rounded-xl border border-white/10 text-xs font-medium">
          <button
            onClick={() => setActiveTab('overview')}
            className={`px-4 py-2 rounded-lg transition-all flex items-center gap-2 ${activeTab === 'overview' ? 'bg-white text-obsidian-950 font-semibold shadow' : 'text-neutral-400 hover:text-white'}`}
          >
            <BarChart3 className="w-3.5 h-3.5" /> Overview
          </button>
          <button
            onClick={() => setActiveTab('query')}
            className={`px-4 py-2 rounded-lg transition-all flex items-center gap-2 ${activeTab === 'query' ? 'bg-white text-obsidian-950 font-semibold shadow' : 'text-neutral-400 hover:text-white'}`}
          >
            <BrainCircuit className="w-3.5 h-3.5" /> AI Command Center
          </button>
          <button
            onClick={() => setActiveTab('ingest')}
            className={`px-4 py-2 rounded-lg transition-all flex items-center gap-2 ${activeTab === 'ingest' ? 'bg-white text-obsidian-950 font-semibold shadow' : 'text-neutral-400 hover:text-white'}`}
          >
            <UploadCloud className="w-3.5 h-3.5" /> Memory Ingestion
          </button>
          <button
            onClick={() => setActiveTab('sentinel')}
            className={`px-4 py-2 rounded-lg transition-all flex items-center gap-2 relative ${activeTab === 'sentinel' ? 'bg-white text-obsidian-950 font-semibold shadow' : 'text-neutral-400 hover:text-white'}`}
          >
            <Activity className="w-3.5 h-3.5 text-accent-rose" /> Sentinel AI
            {alerts.filter(a => !a.acknowledged).length > 0 && (
              <span className="w-2 h-2 rounded-full bg-accent-rose animate-ping absolute top-1 right-1" />
            )}
          </button>
        </div>

        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-accent-cyan/10 border border-accent-cyan/30 text-accent-cyan flex items-center justify-center font-bold text-xs">
            JD
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 p-8 max-w-7xl mx-auto w-full">
        {apiError && (
          <div className="mb-6 p-4 rounded-xl bg-accent-rose/10 border border-accent-rose/30 text-accent-rose text-xs flex items-center gap-3">
            <AlertCircle className="w-4 h-4" />
            <span>{apiError}</span>
          </div>
        )}

        {/* TAB 1: EXECUTIVE OVERVIEW */}
        {activeTab === 'overview' && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-8">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-serif font-bold">Executive Operating Dashboard</h1>
                <p className="text-neutral-400 text-sm font-light mt-1">
                  Real-time multi-agent intelligence and enterprise dataset metrics.
                </p>
              </div>
              <button 
                onClick={() => setActiveTab('query')}
                className="px-5 py-2.5 rounded-xl bg-accent-cyan text-obsidian-950 font-semibold text-sm flex items-center gap-2 shadow-lg shadow-accent-cyan/20 hover:brightness-110 transition-all"
              >
                <Sparkles className="w-4 h-4" /> Ask Executive Query
              </button>
            </div>

            {/* Department Agent Status Cards */}
            <div className="p-8 rounded-2xl glass-panel border border-white/10">
              <h2 className="text-xl font-serif font-bold mb-6 flex items-center gap-3">
                <BrainCircuit className="w-5 h-5 text-accent-cyan" />
                Active Department AI Agents Status
              </h2>

              <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                {['Sales', 'Finance', 'HR', 'Marketing', 'Operations'].map((dept) => (
                  <div key={dept} className="p-4 rounded-xl bg-obsidian-850 border border-white/5 flex flex-col justify-between">
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-sm font-semibold">{dept} Agent</span>
                      <span className="w-2.5 h-2.5 rounded-full bg-accent-emerald animate-pulse" />
                    </div>
                    <div className="text-xs text-neutral-400 font-mono mb-2">Pydantic Standard JSON</div>
                    <div className="text-[11px] text-accent-emerald bg-accent-emerald/10 px-2 py-0.5 rounded border border-accent-emerald/20 inline-block w-fit">
                      Status: Active
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        )}

        {/* TAB 2: AI COMMAND CENTER */}
        {activeTab === 'query' && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-8">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-serif font-bold">AI Executive Command Center</h1>
                <p className="text-neutral-400 text-sm font-light mt-1">
                  Execute data-driven multi-agent queries with zero hallucinations and verified evidence.
                </p>
              </div>

              {queryResult && (
                <button
                  onClick={handleExportReport}
                  className="px-4 py-2 rounded-xl bg-white/10 hover:bg-white/20 border border-white/15 text-white text-xs font-semibold flex items-center gap-2 transition-all"
                >
                  <Download className="w-3.5 h-3.5 text-accent-cyan" /> Export Executive Report (.TXT)
                </button>
              )}
            </div>

            <form onSubmit={handleExecuteQuery} className="relative">
              <input
                type="text"
                value={queryInput}
                onChange={(e) => setQueryInput(e.target.value)}
                placeholder="e.g. What is our total sales revenue and top performing region?"
                className="w-full px-6 py-5 rounded-2xl glass-panel border border-white/20 text-white placeholder-neutral-500 focus:outline-none focus:border-accent-cyan text-base shadow-2xl pr-36"
              />
              <button
                type="submit"
                disabled={isExecuting}
                className="absolute right-3 top-3 bottom-3 px-6 rounded-xl bg-white text-obsidian-950 font-semibold text-sm hover:bg-neutral-200 transition-all flex items-center gap-2 shadow-lg disabled:opacity-50"
              >
                {isExecuting ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" /> Reasoning...
                  </>
                ) : (
                  <>
                    Execute <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </form>

            {/* Query Output Display */}
            {queryResult && (
              <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
                {/* Confidence & Involved Agents Banner */}
                <div className="p-4 rounded-xl glass-panel border border-white/10 space-y-3">
                  <div className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-3">
                      <span className="font-semibold text-neutral-300">Intent:</span>
                      <span className="px-2.5 py-1 rounded bg-accent-cyan/10 text-accent-cyan border border-accent-cyan/30 font-mono">
                        {queryResult.intent}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <CheckCircle2 className="w-4 h-4 text-accent-emerald" />
                      <span className="text-neutral-300 font-semibold">Response Validator Score:</span>
                      <span className="text-accent-emerald font-bold font-mono">
                        {Math.round(queryResult.confidence_score * 100)}% Verified
                      </span>
                    </div>
                  </div>

                  {/* Involved Agents & View Generated SQL Query Buttons */}
                  {queryResult.department_outputs && queryResult.department_outputs.length > 0 && (
                    <div className="pt-2 border-t border-white/5 flex items-center gap-2 flex-wrap">
                      <span className="text-xs font-semibold text-neutral-400 flex items-center gap-1.5 mr-2">
                        <Users className="w-3.5 h-3.5 text-accent-cyan" /> Involved Department Agents:
                      </span>
                      {queryResult.department_outputs.map((out: any, idx: number) => (
                        <div
                          key={idx}
                          className="inline-flex items-center gap-2 px-3 py-1 rounded-lg bg-obsidian-850 border border-accent-cyan/30 text-xs font-medium text-white shadow-sm"
                        >
                          <span className="w-2 h-2 rounded-full bg-accent-emerald animate-pulse" />
                          <span className="uppercase font-mono text-[11px] text-accent-cyan">{out.department} Agent</span>
                          <button
                            onClick={() => setActiveSqlModal(activeSqlModal === out.department ? null : out.department)}
                            className="ml-1 px-1.5 py-0.5 rounded bg-white/10 hover:bg-accent-cyan/20 text-[10px] text-neutral-300 flex items-center gap-1 transition-all"
                          >
                            <Terminal className="w-3 h-3 text-accent-cyan" /> View SQL
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Expanded Raw SQL Inspector Code Box */}
                {activeSqlModal && (
                  <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} className="p-4 rounded-xl bg-obsidian-850 border border-accent-cyan/40 space-y-2">
                    <div className="flex items-center justify-between text-xs font-mono text-accent-cyan">
                      <span className="flex items-center gap-2">
                        <Code className="w-4 h-4" /> Raw SQL Executed by {activeSqlModal.toUpperCase()} Agent
                      </span>
                      <button onClick={() => setActiveSqlModal(null)} className="text-neutral-400 hover:text-white">Close</button>
                    </div>
                    <pre className="p-3 rounded bg-obsidian-950 border border-white/10 text-xs font-mono text-accent-emerald overflow-x-auto">
                      {queryResult.department_outputs.find((d: any) => d.department === activeSqlModal)?.sql_executed || '-- SQL Code Logged'}
                    </pre>
                  </motion.div>
                )}

                {/* Structured Executive Intelligence Synthesis Section Cards */}
                <div className="p-6 rounded-2xl glass-panel border border-white/10 space-y-4">
                  <h3 className="text-lg font-serif font-bold text-accent-cyan flex items-center gap-2">
                    <BrainCircuit className="w-5 h-5" /> Executive Intelligence Synthesis
                  </h3>
                  {renderFormattedSummary(queryResult.executive_summary)}
                </div>

                {/* Recharts Chart Visualization */}
                {queryResult.chart_config && queryResult.chart_config.data && queryResult.chart_config.data.length > 0 && (
                  <div className="p-6 rounded-2xl glass-panel border border-white/10">
                    <h3 className="text-sm font-semibold text-neutral-300 mb-4">{queryResult.chart_config.title}</h3>
                    <div className="h-64 w-full">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={queryResult.chart_config.data}>
                          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                          <XAxis dataKey="name" stroke="#8A8F98" fontSize={11} />
                          <YAxis stroke="#8A8F98" fontSize={11} />
                          <Tooltip contentStyle={{ backgroundColor: '#0E0E12', borderColor: '#2A2A36' }} />
                          <Bar dataKey="value" fill="#00E5FF" radius={[4, 4, 0, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                )}

                {/* Strategic Recommendations */}
                {queryResult.strategic_recommendations && queryResult.strategic_recommendations.length > 0 && (
                  <div className="p-6 rounded-2xl glass-panel border border-white/10 space-y-4">
                    <h3 className="text-lg font-serif font-bold flex items-center gap-2 text-accent-emerald">
                      <Sparkles className="w-5 h-5" /> Strategic Intelligence Recommendations
                    </h3>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {queryResult.strategic_recommendations.map((rec: any, idx: number) => (
                        <div key={idx} className="p-5 rounded-xl bg-obsidian-850 border border-white/5">
                          <div className="flex items-center justify-between mb-2">
                            <span className="font-semibold text-white text-sm">{rec.title}</span>
                            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-accent-emerald/10 text-accent-emerald border border-accent-emerald/20">
                              {rec.expected_impact}
                            </span>
                          </div>
                          <p className="text-xs text-neutral-300 font-light mb-3">{rec.action_item}</p>
                          <div className="text-[11px] text-neutral-500 font-mono">
                            Evidence: {rec.supporting_evidence[0] || 'Verified via memory engine'}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </motion.div>
            )}
          </motion.div>
        )}

        {/* TAB 3: DATA INGESTION & DATASET LIST */}
        {activeTab === 'ingest' && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-8">
            <div>
              <h1 className="text-3xl font-serif font-bold">Enterprise Memory Ingestion</h1>
              <p className="text-neutral-400 text-sm font-light mt-1">
                Upload CSV department datasets. Automatic schema profiling, KPI extraction, and ChromaDB vector indexing.
              </p>
            </div>

            {/* Datasets Active in Enterprise Memory */}
            <div className="p-6 rounded-2xl glass-panel border border-white/10 space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-serif font-bold flex items-center gap-2 text-accent-cyan">
                  <Database className="w-5 h-5" /> Active Ingested Datasets in Memory ({uploadedDatasets.length})
                </h2>
                <button
                  onClick={fetchDatasets}
                  className="px-3 py-1.5 rounded-lg bg-obsidian-850 hover:bg-white/10 border border-white/10 text-xs text-neutral-300 transition-all flex items-center gap-1.5"
                >
                  <RefreshCw className="w-3.5 h-3.5" /> Refresh List
                </button>
              </div>

              {uploadedDatasets.length === 0 ? (
                <div className="p-6 rounded-xl bg-obsidian-850/50 border border-white/5 text-center text-xs text-neutral-400">
                  No uploaded datasets stored in memory yet. Use the upload box below to ingest your CSV datasets.
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="border-b border-white/10 text-neutral-400 font-mono uppercase text-[10px]">
                        <th className="py-3 px-4">Dataset Name</th>
                        <th className="py-3 px-4">Department Tag</th>
                        <th className="py-3 px-4">Row Count</th>
                        <th className="py-3 px-4">Extracted Primary KPI</th>
                        <th className="py-3 px-4">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5">
                      {uploadedDatasets.map((ds: any) => (
                        <tr key={ds.id} className="hover:bg-white/5 transition-colors">
                          <td className="py-3 px-4 font-semibold text-white flex items-center gap-2">
                            <FileSpreadsheet className="w-4 h-4 text-accent-cyan" />
                            {ds.name}
                          </td>
                          <td className="py-3 px-4 font-mono uppercase text-accent-emerald">{ds.department}</td>
                          <td className="py-3 px-4 font-mono">{ds.row_count} rows</td>
                          <td className="py-3 px-4 text-neutral-300 font-mono">
                            {ds.schema_info?.kpis_extracted?.primary_metric || 'Analyzed & Profiled'}
                          </td>
                          <td className="py-3 px-4">
                            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-accent-emerald/10 text-accent-emerald border border-accent-emerald/30 font-semibold text-[10px]">
                              <span className="w-1.5 h-1.5 rounded-full bg-accent-emerald animate-pulse" /> Indexed & Active
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* Upload Box */}
            <div className="p-8 rounded-2xl glass-panel border border-white/10 max-w-2xl mx-auto space-y-6">
              <h2 className="text-lg font-serif font-bold flex items-center gap-2">
                <UploadCloud className="w-5 h-5 text-accent-cyan" /> Upload New Department Dataset
              </h2>

              <div>
                <label className="block text-xs font-semibold uppercase text-neutral-400 mb-2">Target Department</label>
                <select
                  value={selectedDept}
                  onChange={(e) => setSelectedDept(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl bg-obsidian-850 border border-white/15 text-white text-sm focus:outline-none focus:border-accent-cyan"
                >
                  <option value="sales">Sales Department</option>
                  <option value="finance">Finance Department</option>
                  <option value="hr">HR Department</option>
                  <option value="marketing">Marketing Department</option>
                  <option value="operations">Operations Department</option>
                </select>
              </div>

              <div className="border-2 border-dashed border-white/15 rounded-2xl p-8 text-center hover:border-accent-cyan/50 transition-all cursor-pointer relative">
                <UploadCloud className="w-10 h-10 text-accent-cyan mx-auto mb-3" />
                <p className="text-sm font-medium text-white mb-1">
                  {fileToUpload ? fileToUpload.name : 'Click or select CSV file to ingest'}
                </p>
                <p className="text-xs text-neutral-500">Supports CSV files up to 100MB</p>
                <input
                  type="file"
                  accept=".csv"
                  onChange={(e) => setFileToUpload(e.target.files?.[0] || null)}
                  className="mt-4 text-xs text-neutral-400 mx-auto block cursor-pointer"
                />
              </div>

              <button
                onClick={handleFileUpload}
                disabled={isUploading}
                className="w-full py-4 rounded-xl bg-white text-obsidian-950 font-semibold text-sm hover:bg-neutral-200 transition-all shadow-lg flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {isUploading ? <RefreshCw className="w-4 h-4 animate-spin" /> : 'Run Ingestion Pipeline'}
              </button>

              {uploadSuccess && (
                <div className="p-4 rounded-xl bg-accent-emerald/10 border border-accent-emerald/30 text-accent-emerald text-xs flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4" /> {uploadSuccess}
                </div>
              )}
            </div>
          </motion.div>
        )}

        {/* TAB 4: SENTINEL AI */}
        {activeTab === 'sentinel' && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-8">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-serif font-bold flex items-center gap-3">
                  <Activity className="w-7 h-7 text-accent-rose" /> Sentinel AI Anomaly Center
                </h1>
                <p className="text-neutral-400 text-sm font-light mt-1">
                  Continuous background daemon monitoring metrics and conducting automated root-cause analysis.
                </p>
              </div>
            </div>

            <div className="space-y-4">
              {alerts.length === 0 ? (
                <div className="p-8 rounded-2xl glass-panel border border-white/10 text-center text-neutral-400 text-sm font-light">
                  No active anomaly alerts detected yet. Upload CSV datasets to trigger Sentinel AI continuous background analysis.
                </div>
              ) : (
                alerts.map((alert) => (
                  <div
                    key={alert.id}
                    className={`p-6 rounded-2xl glass-panel border transition-all ${
                      alert.severity === 'HIGH' || alert.severity === 'CRITICAL' ? 'border-accent-rose/40 bg-accent-rose/5' : 'border-white/10'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <span className={`px-2.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                          alert.severity === 'HIGH' || alert.severity === 'CRITICAL' ? 'bg-accent-rose/20 text-accent-rose border border-accent-rose/30' : 'bg-accent-amber/20 text-accent-amber border border-accent-amber/30'
                        }`}>
                          {alert.severity} SEVERITY
                        </span>
                        <span className="text-xs text-neutral-400 font-mono">Target Role: {alert.target_role}</span>
                      </div>
                    </div>

                    <h3 className="text-lg font-bold text-white mb-2">{alert.title}</h3>
                    <p className="text-xs text-neutral-300 mb-3">{alert.description}</p>
                    
                    <div className="p-3 rounded-lg bg-obsidian-850 border border-white/5 text-xs text-neutral-400 font-mono">
                      <span className="text-accent-cyan font-semibold">Root Cause:</span> {alert.root_cause}
                    </div>
                  </div>
                ))
              )}
            </div>
          </motion.div>
        )}
      </main>
    </div>
  );
}
