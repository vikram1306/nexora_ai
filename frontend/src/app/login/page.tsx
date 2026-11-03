'use client';

import React, { useState, useEffect, Suspense } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { motion } from 'framer-motion';
import {
  BrainCircuit,
  Lock,
  Mail,
  ArrowRight,
  Sparkles,
  ShieldCheck,
  AlertCircle,
  Eye,
  EyeOff,
  Building,
  Zap,
  CheckCircle2,
  User,
  LogOut
} from 'lucide-react';
import { useAuth } from '@/context/AuthContext';

function LoginFormContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, login, demoLogin, logout, isAuthenticated } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [demoLoading, setDemoLoading] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState('');
  const [sessionExpiredNotice, setSessionExpiredNotice] = useState(false);

  useEffect(() => {
    if (searchParams && searchParams.get('expired') === 'true') {
      setSessionExpiredNotice(true);
    }
  }, [searchParams]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setErrorMessage('Please provide both work email and password.');
      return;
    }

    setIsLoading(true);
    setErrorMessage('');
    setSessionExpiredNotice(false);

    try {
      await login(email, password);
      router.push('/dashboard');
    } catch (err: any) {
      setErrorMessage(err.message || 'Authentication failed. Please verify your credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDemoAccess = async (role: 'CEO' | 'Director') => {
    setDemoLoading(role);
    setErrorMessage('');
    setSessionExpiredNotice(false);

    try {
      await demoLogin(role);
      router.push('/dashboard');
    } catch (err: any) {
      setErrorMessage(err.message || 'Unable to establish demo executive session.');
    } finally {
      setDemoLoading(null);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.98, y: 10 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.1 }}
      className="w-full max-w-md glass-panel rounded-2xl p-8 border border-white/10 shadow-2xl relative z-10"
    >
      <div className="mb-6">
        <h1 className="text-2xl font-serif font-bold text-white tracking-tight">
          Sign In to Executive Portal
        </h1>
        <p className="text-xs text-neutral-400 mt-1">
          Access multi-tenant memory, continuous Sentinel telemetry, and AI governance.
        </p>
      </div>

      {/* If currently signed in, show status banner */}
      {isAuthenticated && user && (
        <div className="mb-6 p-4 rounded-xl bg-accent-cyan/10 border border-accent-cyan/30 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono uppercase text-accent-cyan font-bold tracking-wider">
              Active Session
            </span>
            <button
              onClick={logout}
              className="text-[11px] font-mono text-neutral-400 hover:text-accent-rose flex items-center gap-1 transition-colors"
            >
              <LogOut className="w-3 h-3" /> Log Out
            </button>
          </div>
          <div className="text-xs text-white">
            Signed in as <strong>{user.full_name}</strong> ({user.role})
            <div className="text-[11px] text-neutral-400 font-mono mt-0.5">
              Tenant: {user.tenant?.name || 'Acme Global'}
            </div>
          </div>
          <button
            onClick={() => router.push('/dashboard')}
            className="w-full py-2 rounded-lg bg-accent-cyan text-obsidian-950 font-bold text-xs hover:brightness-110 transition-all flex items-center justify-center gap-2 shadow-sm"
          >
            Continue to Dashboard <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {sessionExpiredNotice && (
        <div className="mb-5 p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs flex items-center gap-2.5">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>Your session has expired. Please sign in again.</span>
        </div>
      )}

      {errorMessage && (
        <div className="mb-5 p-3.5 rounded-xl bg-accent-rose/10 border border-accent-rose/30 text-accent-rose text-xs flex items-center gap-2.5">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Credentials Form */}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs font-mono uppercase text-neutral-400 mb-1.5 font-semibold">
            Corporate Email
          </label>
          <div className="relative">
            <Mail className="w-4 h-4 text-neutral-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@company.com"
              required
              className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-obsidian-850 border border-white/10 text-white placeholder-neutral-500 text-sm focus:outline-none focus:border-accent-cyan/60 transition-all font-sans"
            />
          </div>
        </div>

        <div>
          <div className="flex items-center justify-between mb-1.5">
            <label className="block text-xs font-mono uppercase text-neutral-400 font-semibold">
              Password
            </label>
          </div>
          <div className="relative">
            <Lock className="w-4 h-4 text-neutral-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type={showPassword ? 'text' : 'password'}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••••••"
              required
              className="w-full pl-10 pr-10 py-2.5 rounded-xl bg-obsidian-850 border border-white/10 text-white placeholder-neutral-500 text-sm focus:outline-none focus:border-accent-cyan/60 transition-all font-sans"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3.5 top-1/2 -translate-y-1/2 text-neutral-400 hover:text-white"
            >
              {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>
        </div>

        <button
          type="submit"
          disabled={isLoading || !!demoLoading}
          className="w-full py-3 rounded-xl bg-white text-obsidian-950 font-semibold text-sm hover:bg-neutral-200 transition-all shadow-lg hover:shadow-white/10 flex items-center justify-center gap-2 group disabled:opacity-50 mt-2"
        >
          {isLoading ? (
            <span className="inline-flex items-center gap-2">
              <span className="w-4 h-4 border-2 border-obsidian-950 border-t-transparent rounded-full animate-spin" />
              Authenticating...
            </span>
          ) : (
            <>
              Sign In to Workspace
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </>
          )}
        </button>
      </form>

      {/* Divider */}
      <div className="relative my-6">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-white/10" />
        </div>
        <div className="relative flex justify-center text-[10px] uppercase font-mono tracking-wider">
          <span className="bg-obsidian-900 px-3 text-neutral-500">Or Launch Instant Demo</span>
        </div>
      </div>

      {/* Quick Demo Access Shortcuts */}
      <div className="grid grid-cols-2 gap-3">
        <button
          type="button"
          onClick={() => handleDemoAccess('CEO')}
          disabled={isLoading || !!demoLoading}
          className="p-3 rounded-xl bg-obsidian-850 hover:bg-accent-cyan/10 border border-white/10 hover:border-accent-cyan/40 text-left transition-all group disabled:opacity-50"
        >
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-accent-cyan/10 text-accent-cyan border border-accent-cyan/30 font-semibold">
              CEO Demo
            </span>
            <Sparkles className="w-3.5 h-3.5 text-accent-cyan group-hover:rotate-12 transition-transform" />
          </div>
          <div className="text-xs font-semibold text-white">Jane Doe</div>
          <div className="text-[10px] text-neutral-400 font-mono">Acme Global</div>
        </button>

        <button
          type="button"
          onClick={() => handleDemoAccess('Director')}
          disabled={isLoading || !!demoLoading}
          className="p-3 rounded-xl bg-obsidian-850 hover:bg-accent-emerald/10 border border-white/10 hover:border-accent-emerald/40 text-left transition-all group disabled:opacity-50"
        >
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-accent-emerald/10 text-accent-emerald border border-accent-emerald/30 font-semibold">
              Director Demo
            </span>
            <ShieldCheck className="w-3.5 h-3.5 text-accent-emerald group-hover:scale-110 transition-transform" />
          </div>
          <div className="text-xs font-semibold text-white">Alex Vance</div>
          <div className="text-[10px] text-neutral-400 font-mono">Operations Dept</div>
        </button>
      </div>

      {/* Footer Link */}
      <div className="mt-6 pt-5 border-t border-white/5 text-center text-xs text-neutral-400">
        Need an organization tenant?{' '}
        <Link href="/register" className="text-accent-cyan hover:underline font-medium">
          Register new enterprise
        </Link>
      </div>
    </motion.div>
  );
}

export default function LoginPage() {
  return (
    <div className="relative min-h-screen bg-obsidian-950 text-white flex flex-col justify-center items-center px-4 py-12 overflow-hidden selection:bg-accent-cyan/30 selection:text-accent-cyan font-sans">
      {/* Background Lighting Accents */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-glow-radial pointer-events-none opacity-80 blur-3xl" />
      <div className="absolute bottom-10 right-10 w-[350px] h-[350px] bg-accent-violet/10 rounded-full blur-3xl pointer-events-none" />

      {/* Top Header Logo */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="mb-8 text-center"
      >
        <Link href="/" className="inline-flex items-center gap-3 group">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-accent-cyan to-accent-emerald flex items-center justify-center font-bold text-obsidian-950 text-xl shadow-lg shadow-accent-cyan/20 group-hover:scale-105 transition-transform">
            N
          </div>
          <span className="font-bold tracking-tight text-2xl font-sans text-white">
            NEXORA <span className="text-accent-cyan text-xs font-mono font-semibold uppercase px-2 py-0.5 rounded bg-accent-cyan/10 border border-accent-cyan/30">AI OS</span>
          </span>
        </Link>
        <p className="text-xs font-mono uppercase tracking-widest text-neutral-400 mt-2">
          Enterprise Multi-Agent Intelligence Platform
        </p>
      </motion.div>

      <Suspense
        fallback={
          <div className="w-full max-w-md glass-panel rounded-2xl p-8 border border-white/10 text-center text-xs text-neutral-400">
            <span className="w-6 h-6 border-2 border-accent-cyan border-t-transparent rounded-full animate-spin inline-block mb-3" />
            <p>Loading Executive Authentication...</p>
          </div>
        }
      >
        <LoginFormContent />
      </Suspense>

      {/* Security & RBAC Guardrail Badge */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5, delay: 0.2 }}
        className="mt-8 flex items-center gap-2 text-[11px] font-mono text-neutral-500"
      >
        <ShieldCheck className="w-3.5 h-3.5 text-accent-emerald" />
        <span>Enterprise JWT Token • Rate-Limited • RBAC Scoped Memory</span>
      </motion.div>
    </div>
  );
}
