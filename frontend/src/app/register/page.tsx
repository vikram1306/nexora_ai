'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import {
  BrainCircuit,
  Lock,
  Mail,
  User,
  Building,
  ArrowRight,
  ShieldCheck,
  AlertCircle,
  Eye,
  EyeOff,
  CheckCircle2,
  Sparkles,
  LogOut
} from 'lucide-react';
import { useAuth } from '@/context/AuthContext';

export default function RegisterPage() {
  const router = useRouter();
  const { user, register, logout, isAuthenticated } = useAuth();

  const [companyName, setCompanyName] = useState('');
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('CEO');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!companyName.trim() || !fullName.trim() || !email.trim() || !password) {
      setErrorMessage('Please fill in all required organization fields.');
      return;
    }

    if (password.length < 8) {
      setErrorMessage('Password must be at least 8 characters long.');
      return;
    }

    setIsLoading(true);
    setErrorMessage('');

    try {
      await register({
        company_name: companyName,
        full_name: fullName,
        email,
        password,
        role,
      });
      router.push('/dashboard');
    } catch (err: any) {
      setErrorMessage(err.message || 'Tenant registration failed. Please check your inputs.');
    } finally {
      setIsLoading(false);
    }
  };

  const roles = [
    { id: 'CEO', label: 'CEO / Executive', desc: 'Full tenant authority, all Sentinel alerts & strategic actions' },
    { id: 'Director', label: 'Director', desc: 'Department oversight, high/medium anomaly alerts' },
    { id: 'Manager', label: 'Manager', desc: 'Operational reviews, medium anomaly alerts' },
    { id: 'Employee', label: 'Analyst', desc: 'Standard data querying and basic alerts' },
  ];

  return (
    <div className="relative min-h-screen bg-obsidian-950 text-white flex flex-col justify-center items-center px-4 py-12 overflow-hidden selection:bg-accent-cyan/30 selection:text-accent-cyan font-sans">
      {/* Background Lighting Accents */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[850px] h-[450px] bg-glow-radial pointer-events-none opacity-80 blur-3xl" />
      <div className="absolute bottom-10 left-10 w-[350px] h-[350px] bg-accent-cyan/10 rounded-full blur-3xl pointer-events-none" />

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
          Provision Organization Tenant & Enterprise Memory
        </p>
      </motion.div>

      {/* Main Registration Card */}
      <motion.div
        initial={{ opacity: 0, scale: 0.98, y: 10 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.1 }}
        className="w-full max-w-lg glass-panel rounded-2xl p-8 border border-white/10 shadow-2xl relative z-10"
      >
        <div className="mb-6">
          <h1 className="text-2xl font-serif font-bold text-white tracking-tight">
            Register Enterprise Workspace
          </h1>
          <p className="text-xs text-neutral-400 mt-1">
            Creates an isolated database schema, vector memory partition, and role-governed executive portal.
          </p>
        </div>

        {/* If currently logged in, show info badge */}
        {isAuthenticated && user && (
          <div className="mb-5 p-3 rounded-xl bg-obsidian-850 border border-white/10 flex items-center justify-between text-xs">
            <span className="text-neutral-300">
              Currently signed in as <strong>{user.full_name}</strong>
            </span>
            <button
              onClick={logout}
              className="text-accent-rose hover:underline flex items-center gap-1 font-mono text-[11px]"
            >
              <LogOut className="w-3 h-3" /> Sign Out
            </button>
          </div>
        )}

        {errorMessage && (
          <div className="mb-5 p-3.5 rounded-xl bg-accent-rose/10 border border-accent-rose/30 text-accent-rose text-xs flex items-center gap-2.5">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-mono uppercase text-neutral-400 mb-1.5 font-semibold">
              Company / Organization Name
            </label>
            <div className="relative">
              <Building className="w-4 h-4 text-neutral-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                placeholder="My Organization"
                required
                className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-obsidian-850 border border-white/10 text-white placeholder-neutral-500 text-sm focus:outline-none focus:border-accent-cyan/60 transition-all font-sans"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-mono uppercase text-neutral-400 mb-1.5 font-semibold">
                Your Full Name
              </label>
              <div className="relative">
                <User className="w-4 h-4 text-neutral-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Your Name"
                  required
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-obsidian-850 border border-white/10 text-white placeholder-neutral-500 text-sm focus:outline-none focus:border-accent-cyan/60 transition-all font-sans"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-mono uppercase text-neutral-400 mb-1.5 font-semibold">
                Work Email
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
          </div>

          <div>
            <label className="block text-xs font-mono uppercase text-neutral-400 mb-1.5 font-semibold">
              Master Password
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-neutral-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                required
                minLength={8}
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

          <div>
            <label className="block text-xs font-mono uppercase text-neutral-400 mb-2 font-semibold">
              Primary Executive Role (RBAC)
            </label>
            <div className="grid grid-cols-2 gap-2">
              {roles.map((r) => (
                <button
                  key={r.id}
                  type="button"
                  onClick={() => setRole(r.id)}
                  className={`p-2.5 rounded-xl border text-left transition-all ${
                    role === r.id
                      ? 'bg-accent-cyan/10 border-accent-cyan/60 text-white shadow-sm'
                      : 'bg-obsidian-850 border-white/5 text-neutral-400 hover:border-white/15 hover:text-neutral-200'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold">{r.label}</span>
                    {role === r.id && <CheckCircle2 className="w-3.5 h-3.5 text-accent-cyan" />}
                  </div>
                  <span className="text-[10px] text-neutral-400 block mt-0.5 line-clamp-1">{r.desc}</span>
                </button>
              ))}
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-3 rounded-xl bg-accent-cyan text-obsidian-950 font-bold text-sm hover:brightness-110 transition-all shadow-lg shadow-accent-cyan/20 flex items-center justify-center gap-2 group disabled:opacity-50 mt-4"
          >
            {isLoading ? (
              <span className="inline-flex items-center gap-2">
                <span className="w-4 h-4 border-2 border-obsidian-950 border-t-transparent rounded-full animate-spin" />
                Provisioning Tenant...
              </span>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                Complete Workspace Provisioning
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </>
            )}
          </button>
        </form>

        <div className="mt-6 pt-5 border-t border-white/5 text-center text-xs text-neutral-400">
          Already registered?{' '}
          <Link href="/login" className="text-accent-cyan hover:underline font-medium">
            Sign in to existing workspace
          </Link>
        </div>
      </motion.div>
    </div>
  );
}
