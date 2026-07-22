'use client';

import React from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { 
  ShieldCheck, 
  BrainCircuit, 
  Activity, 
  Database, 
  ArrowRight, 
  TrendingUp, 
  Sparkles, 
  Zap, 
  CheckCircle2, 
  Layers, 
  Cpu, 
  Lock,
  Server,
  BarChart3,
  Bot
} from 'lucide-react';

export default function LandingPage() {
  return (
    <div className="relative min-h-screen bg-obsidian-900 text-white overflow-hidden scroll-smooth">
      {/* Dynamic Background Glow */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[500px] bg-glow-radial pointer-events-none opacity-80 blur-3xl" />
      <div className="absolute top-1/3 right-0 w-[400px] h-[400px] bg-accent-violet/10 rounded-full blur-3xl pointer-events-none" />

      {/* Navigation Header */}
      <header className="sticky top-0 z-50 glass-panel border-b border-white/10 px-8 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-accent-cyan to-accent-emerald flex items-center justify-center font-bold text-obsidian-950 text-xl shadow-lg shadow-accent-cyan/20">
            N
          </div>
          <span className="font-bold tracking-tight text-xl font-sans">
            NEXORA <span className="text-accent-cyan text-sm font-semibold tracking-wider uppercase ml-1 px-2 py-0.5 rounded bg-accent-cyan/10 border border-accent-cyan/30">AI OS</span>
          </span>
        </div>

        <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-neutral-400">
          <a href="#features" className="hover:text-white transition-colors">Features</a>
          <a href="#architecture" className="hover:text-white transition-colors">Architecture</a>
          <a href="#sentinel" className="hover:text-white transition-colors">Sentinel AI</a>
          <a href="#pricing" className="hover:text-white transition-colors">Pricing</a>
        </nav>

        <div className="flex items-center gap-4">
          <Link 
            href="/dashboard" 
            className="px-5 py-2.5 rounded-lg font-medium text-sm bg-white text-obsidian-950 hover:bg-neutral-200 transition-all shadow-lg hover:shadow-white/20 flex items-center gap-2 group"
          >
            Launch Platform
            <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </Link>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative pt-24 pb-20 px-6 max-w-6xl mx-auto text-center">
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full glass-panel border border-accent-cyan/30 text-accent-cyan text-xs font-semibold uppercase tracking-widest mb-8"
        >
          <Sparkles className="w-3.5 h-3.5" /> Next-Generation Enterprise AI OS
        </motion.div>

        <motion.h1 
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.1 }}
          className="text-5xl md:text-7xl font-serif tracking-tight leading-[1.1] mb-8"
        >
          Enterprise Intelligence. <br />
          <span className="italic bg-gradient-to-r from-white via-neutral-200 to-accent-cyan bg-clip-text text-transparent">
            Autonomous Decisions.
          </span>
        </motion.h1>

        <motion.p 
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="text-lg md:text-xl text-neutral-400 max-w-3xl mx-auto font-light leading-relaxed mb-12"
        >
          Nexora AI continuously ingests departmental data, learns your business deeply, coordinates 
          five specialized AI department agents, and proactively flags anomalies through Sentinel AI.
        </motion.p>

        <motion.div 
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.3 }}
          className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16"
        >
          <Link 
            href="/dashboard"
            className="w-full sm:w-auto px-8 py-4 rounded-xl bg-white text-obsidian-950 font-semibold text-base shadow-xl shadow-white/10 hover:bg-neutral-100 transition-all flex items-center justify-center gap-3"
          >
            Enter Executive Dashboard
            <ArrowRight className="w-5 h-5" />
          </Link>
          <a 
            href="#architecture"
            className="w-full sm:w-auto px-8 py-4 rounded-xl glass-panel border border-white/15 text-white font-medium text-base hover:bg-white/5 transition-all flex items-center justify-center gap-3"
          >
            Explore Architecture
          </a>
        </motion.div>
      </section>

      {/* SECTION 1: FEATURES BENTO GRID */}
      <section id="features" className="py-24 px-6 max-w-6xl mx-auto border-t border-white/10">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-5xl font-serif mb-4">Enterprise-Grade AI Capabilities</h2>
          <p className="text-neutral-400 max-w-2xl mx-auto font-light">
            Engineered strictly according to clean architecture, SOLID principles, and local multi-database memory.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Card 1: Enterprise Memory */}
          <div className="md:col-span-2 p-8 rounded-2xl glass-panel border border-white/10 hover:border-accent-cyan/40 transition-all group">
            <div className="w-12 h-12 rounded-xl bg-accent-cyan/10 border border-accent-cyan/30 flex items-center justify-center text-accent-cyan mb-6 group-hover:scale-110 transition-transform">
              <Database className="w-6 h-6" />
            </div>
            <h3 className="text-2xl font-semibold mb-3">Enterprise Memory Engine</h3>
            <p className="text-neutral-400 font-light leading-relaxed mb-6">
              Never feeds raw CSVs to models. Automatically detects column schemas, normalizes nulls, computes KPIs, 
              indexes vector embeddings via SentenceTransformers into ChromaDB, and maintains analytical SQL tables in PostgreSQL.
            </p>
            <div className="flex items-center gap-3 text-xs font-mono text-neutral-400">
              <span className="px-3 py-1 rounded bg-obsidian-850 border border-white/5">PostgreSQL (SQL)</span>
              <span className="px-3 py-1 rounded bg-obsidian-850 border border-white/5">ChromaDB (Vectors)</span>
              <span className="px-3 py-1 rounded bg-obsidian-850 border border-white/5">Redis (Cache)</span>
            </div>
          </div>

          {/* Card 2: 5 Department Agents */}
          <div className="p-8 rounded-2xl glass-panel border border-white/10 hover:border-accent-emerald/40 transition-all group">
            <div className="w-12 h-12 rounded-xl bg-accent-emerald/10 border border-accent-emerald/30 flex items-center justify-center text-accent-emerald mb-6 group-hover:scale-110 transition-transform">
              <BrainCircuit className="w-6 h-6" />
            </div>
            <h3 className="text-2xl font-semibold mb-3">5 Department Agents</h3>
            <p className="text-neutral-400 font-light leading-relaxed mb-6">
              Sales, Finance, HR, Marketing, Operations. Specialized agents returning strict Pydantic JSON contracts. Zero natural language chatter.
            </p>
          </div>

          {/* Card 3: Sentinel AI Monitoring */}
          <div className="p-8 rounded-2xl glass-panel border border-white/10 hover:border-accent-rose/40 transition-all group">
            <div className="w-12 h-12 rounded-xl bg-accent-rose/10 border border-accent-rose/30 flex items-center justify-center text-accent-rose mb-6 group-hover:scale-110 transition-transform">
              <Activity className="w-6 h-6" />
            </div>
            <h3 className="text-2xl font-semibold mb-3">Sentinel AI Monitoring</h3>
            <p className="text-neutral-400 font-light leading-relaxed mb-6">
              Continuous background daemon monitoring metrics for Z-score anomalies, drops, and threshold violations. Dispatches tiered alerts to CEOs and Directors.
            </p>
          </div>

          {/* Card 4: Response Validator */}
          <div className="md:col-span-2 p-8 rounded-2xl glass-panel border border-white/10 hover:border-accent-violet/40 transition-all group">
            <div className="w-12 h-12 rounded-xl bg-accent-violet/10 border border-accent-violet/30 flex items-center justify-center text-accent-violet mb-6 group-hover:scale-110 transition-transform">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <h3 className="text-2xl font-semibold mb-3">Zero-Hallucination Response Validator</h3>
            <p className="text-neutral-400 font-light leading-relaxed mb-6">
              Cross-checks every generated statement and figure against actual database numbers and vector citations. Attaches a verified Confidence Score (0–100%) to every response.
            </p>
          </div>
        </div>
      </section>

      {/* SECTION 2: SYSTEM ARCHITECTURE VISUALIZATION */}
      <section id="architecture" className="py-24 px-6 max-w-6xl mx-auto border-t border-white/10">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-5xl font-serif mb-4">System & Multi-Agent Architecture</h2>
          <p className="text-neutral-400 max-w-2xl mx-auto font-light">
            Decoupled layered architecture ensuring auditability, tenant security, and parallel execution.
          </p>
        </div>

        <div className="p-8 rounded-2xl glass-panel border border-white/10 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4 text-center">
            {/* Step 1 */}
            <div className="p-5 rounded-xl bg-obsidian-850 border border-white/5 space-y-2">
              <div className="w-8 h-8 rounded-lg bg-accent-cyan/10 text-accent-cyan flex items-center justify-center font-bold mx-auto text-xs">1</div>
              <h4 className="font-semibold text-sm">User & Auth</h4>
              <p className="text-[11px] text-neutral-400 font-light">PyJWT & Tenant Context Isolation</p>
            </div>

            {/* Step 2 */}
            <div className="p-5 rounded-xl bg-obsidian-850 border border-accent-cyan/30 space-y-2">
              <div className="w-8 h-8 rounded-lg bg-accent-cyan text-obsidian-950 flex items-center justify-center font-bold mx-auto text-xs">2</div>
              <h4 className="font-semibold text-sm text-accent-cyan">Planner Agent</h4>
              <p className="text-[11px] text-neutral-400 font-light">Intent Understanding & Out-of-Domain Filter</p>
            </div>

            {/* Step 3 */}
            <div className="p-5 rounded-xl bg-obsidian-850 border border-accent-emerald/30 space-y-2">
              <div className="w-8 h-8 rounded-lg bg-accent-emerald text-obsidian-950 flex items-center justify-center font-bold mx-auto text-xs">3</div>
              <h4 className="font-semibold text-sm text-accent-emerald">5 Department Agents</h4>
              <p className="text-[11px] text-neutral-400 font-light">Sales, Finance, HR, Marketing, Operations</p>
            </div>

            {/* Step 4 */}
            <div className="p-5 rounded-xl bg-obsidian-850 border border-white/5 space-y-2">
              <div className="w-8 h-8 rounded-lg bg-accent-violet/10 text-accent-violet flex items-center justify-center font-bold mx-auto text-xs">4</div>
              <h4 className="font-semibold text-sm">Enterprise Memory</h4>
              <p className="text-[11px] text-neutral-400 font-light">PostgreSQL + ChromaDB + Redis</p>
            </div>

            {/* Step 5 */}
            <div className="p-5 rounded-xl bg-obsidian-850 border border-white/5 space-y-2">
              <div className="w-8 h-8 rounded-lg bg-white text-obsidian-950 flex items-center justify-center font-bold mx-auto text-xs">5</div>
              <h4 className="font-semibold text-sm">Response Validator</h4>
              <p className="text-[11px] text-neutral-400 font-light">Confidence Score & Synthesis</p>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-obsidian-850/60 border border-white/5 text-xs text-neutral-400 font-mono text-center">
            🔒 Core Guardrail: Department agents never communicate directly with each other. All routing is strictly managed by the Planner Agent.
          </div>
        </div>
      </section>

      {/* SECTION 3: SENTINEL AI SHOWCASE */}
      <section id="sentinel" className="py-24 px-6 max-w-6xl mx-auto border-t border-white/10">
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-accent-rose/10 text-accent-rose border border-accent-rose/30 text-xs font-bold uppercase tracking-wider mb-4">
            <Activity className="w-3.5 h-3.5" /> USP Feature
          </div>
          <h2 className="text-3xl md:text-5xl font-serif mb-4">Sentinel AI Continuous Monitoring</h2>
          <p className="text-neutral-400 max-w-2xl mx-auto font-light">
            Runs continuously in the background to flag revenue drops, CAC spikes, delay anomalies, and threshold violations.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div className="p-8 rounded-2xl glass-panel border border-white/10 space-y-4">
            <h3 className="text-2xl font-serif font-bold text-accent-rose">Statistical Z-Score Engine</h3>
            <p className="text-neutral-300 font-light text-sm leading-relaxed">
              Sentinel AI continuously reads ingested company metrics and calculates standard deviation bounds ($Z > 2.5\sigma$). 
              When a metric deviates unexpectedly, it automatically conducts a root-cause diagnosis.
            </p>
            <div className="space-y-2 text-xs font-mono text-neutral-400 pt-2">
              <div className="flex items-center justify-between p-2.5 rounded bg-obsidian-850">
                <span>Z-Score &gt; 3.5 (Critical)</span>
                <span className="text-accent-rose font-bold">Alert CEO & Board</span>
              </div>
              <div className="flex items-center justify-between p-2.5 rounded bg-obsidian-850">
                <span>Z-Score &gt; 3.0 (High)</span>
                <span className="text-accent-amber font-bold">Alert Department Director</span>
              </div>
              <div className="flex items-center justify-between p-2.5 rounded bg-obsidian-850">
                <span>Z-Score &gt; 2.5 (Medium)</span>
                <span className="text-accent-cyan font-bold">Alert Manager</span>
              </div>
            </div>
          </div>

          <div className="p-8 rounded-2xl glass-panel border border-accent-rose/30 bg-accent-rose/5 space-y-4">
            <div className="flex items-center justify-between">
              <span className="px-2.5 py-0.5 rounded text-[10px] font-bold bg-accent-rose/20 text-accent-rose border border-accent-rose/30">HIGH SEVERITY</span>
              <span className="text-xs text-neutral-400 font-mono">Target: Director</span>
            </div>
            <h4 className="text-lg font-bold text-white">Marketing CAC Spike Detected (+24.1%)</h4>
            <p className="text-xs text-neutral-300 font-light">
              Customer Acquisition Cost exceeded standard variance thresholds ($42.00 vs baseline $33.80).
            </p>
            <div className="p-3 rounded-lg bg-obsidian-850 text-xs font-mono text-neutral-400">
              <span className="text-accent-cyan font-semibold">Root Cause:</span> Meta Ad Campaign spend increased without proportional conversion lift.
            </div>
          </div>
        </div>
      </section>

      {/* SECTION 4: ENTERPRISE PRICING TIERS */}
      <section id="pricing" className="py-24 px-6 max-w-6xl mx-auto border-t border-white/10">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-5xl font-serif mb-4">Enterprise SaaS Subscription Tiers</h2>
          <p className="text-neutral-400 max-w-2xl mx-auto font-light">
            Deploy local open-source AI operating infrastructure tailored to your enterprise dataset volume.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Tier 1 */}
          <div className="p-8 rounded-2xl glass-panel border border-white/10 space-y-6">
            <div>
              <h3 className="text-xl font-bold mb-2">Growth Tier</h3>
              <p className="text-xs text-neutral-400 font-light">For scaling companies uploading up to 10 department CSVs.</p>
            </div>
            <div className="text-4xl font-serif font-bold">$499 <span className="text-xs text-neutral-400 font-sans font-normal">/ month</span></div>
            <ul className="space-y-3 text-xs text-neutral-300 font-light">
              <li className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-accent-emerald" /> 5 Department Agents</li>
              <li className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-accent-emerald" /> Enterprise Memory (PostgreSQL + ChromaDB)</li>
              <li className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-accent-emerald" /> Response Validator Confidence Scoring</li>
            </ul>
            <Link href="/dashboard" className="block text-center w-full py-3 rounded-xl bg-white/10 hover:bg-white/20 text-white font-medium text-xs transition-all">
              Start Free Trial
            </Link>
          </div>

          {/* Tier 2 */}
          <div className="p-8 rounded-2xl glass-panel border border-accent-cyan/40 bg-accent-cyan/5 space-y-6 relative">
            <div className="absolute -top-3 right-6 px-3 py-0.5 rounded-full bg-accent-cyan text-obsidian-950 font-bold text-[10px] uppercase">
              Most Popular
            </div>
            <div>
              <h3 className="text-xl font-bold mb-2 text-accent-cyan">Enterprise Intelligence</h3>
              <p className="text-xs text-neutral-400 font-light">Full continuous Sentinel AI monitoring and executive recommendations.</p>
            </div>
            <div className="text-4xl font-serif font-bold">$1,499 <span className="text-xs text-neutral-400 font-sans font-normal">/ month</span></div>
            <ul className="space-y-3 text-xs text-neutral-300 font-light">
              <li className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-accent-cyan" /> Unlimited CSV Memory Ingestion</li>
              <li className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-accent-cyan" /> Sentinel AI Anomaly Daemon</li>
              <li className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-accent-cyan" /> Multi-Tier Alerts (Employee to CEO)</li>
              <li className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-accent-cyan" /> Strategic Intelligence Recommendation Engine</li>
            </ul>
            <Link href="/dashboard" className="block text-center w-full py-3 rounded-xl bg-accent-cyan text-obsidian-950 font-semibold text-xs transition-all hover:brightness-110 shadow-lg shadow-accent-cyan/20">
              Launch Enterprise OS
            </Link>
          </div>

          {/* Tier 3 */}
          <div className="p-8 rounded-2xl glass-panel border border-white/10 space-y-6">
            <div>
              <h3 className="text-xl font-bold mb-2">Private Air-Gapped</h3>
              <p className="text-xs text-neutral-400 font-light">For banking, healthcare, and government requiring on-premise hardware.</p>
            </div>
            <div className="text-4xl font-serif font-bold">Custom</div>
            <ul className="space-y-3 text-xs text-neutral-300 font-light">
              <li className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-accent-emerald" /> On-Premise GPU Containerization</li>
              <li className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-accent-emerald" /> Custom Open-Source LLM Fine-Tuning</li>
              <li className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-accent-emerald" /> 24/7 Dedicated Solutions Architect</li>
            </ul>
            <Link href="/dashboard" className="block text-center w-full py-3 rounded-xl bg-white/10 hover:bg-white/20 text-white font-medium text-xs transition-all">
              Contact Architecture Team
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/10 py-12 px-8 text-center text-neutral-500 text-sm">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded bg-accent-cyan/20 text-accent-cyan flex items-center justify-center font-bold text-xs">N</div>
            <span className="text-white font-semibold">Nexora AI</span>
            <span>— Enterprise Intelligence AI Operating System</span>
          </div>
          <p>© 2026 Nexora AI Inc. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
