import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, Eye, Lock, ArrowRight, UserCheck } from 'lucide-react';
import toast from 'react-hot-toast';
import { api } from '../lib/api';
import { useAppStore } from '../stores/useAppStore';

export const Login: React.FC = () => {
  const navigate = useNavigate();
  const setUser = useAppStore((s) => s.setUser);

  const [email, setEmail] = useState('investigator@demo');
  const [password, setPassword] = useState('demo123');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      const res = await api.login(email, password);
      setUser(res.user);
      toast.success(`Authenticated as ${res.user.role}!`);
      navigate('/');
    } catch (e: any) {
      toast.error(e.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const fillCredentials = (roleEmail: string) => {
    setEmail(roleEmail);
    setPassword('demo123');
  };

  return (
    <div className="min-h-screen bg-ink flex items-center justify-center p-4 forensic-grid">
      <div className="w-full max-w-md bg-panel border border-hairline rounded-2xl shadow-2xl p-7 space-y-6">
        {/* Branding */}
        <div className="text-center space-y-2">
          <div className="inline-flex p-3 rounded-2xl bg-raised border border-hairline shadow-inner">
            <img src="/logo.svg" alt="ChainNetra" className="h-8 w-auto" />
          </div>
          <h1 className="text-xl font-bold text-text-primary tracking-tight">
            Law Enforcement Portal Access
          </h1>
          <p className="text-xs text-text-muted">
            Authenticated multi-chain forensic attribution & evidence environment.
          </p>
        </div>

        {/* Demo Fast Fill Credentials */}
        <div className="p-3 bg-raised/70 rounded-xl border border-hairline space-y-2">
          <div className="text-[10px] font-mono text-amber font-bold uppercase tracking-wider">
            Demo Mode Credentials (Click to pre-fill)
          </div>
          <div className="grid grid-cols-3 gap-1.5 text-xs font-mono">
            <button
              type="button"
              onClick={() => fillCredentials('investigator@demo')}
              className="p-1.5 rounded bg-ink border border-hairline hover:border-amber text-text-primary text-center"
            >
              <span className="block font-bold text-amber">Investigator</span>
              <span className="text-[9px] text-text-muted">IO Case Officer</span>
            </button>

            <button
              type="button"
              onClick={() => fillCredentials('supervisor@demo')}
              className="p-1.5 rounded bg-ink border border-hairline hover:border-cyan text-text-primary text-center"
            >
              <span className="block font-bold text-cyan">Supervisor</span>
              <span className="text-[9px] text-text-muted">SP Operations</span>
            </button>

            <button
              type="button"
              onClick={() => fillCredentials('admin@demo')}
              className="p-1.5 rounded bg-ink border border-hairline hover:border-mint text-text-primary text-center"
            >
              <span className="block font-bold text-mint">Admin</span>
              <span className="text-[9px] text-text-muted">Tech Wing</span>
            </button>
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4 text-xs">
          <div>
            <label className="block text-text-muted mb-1 font-mono uppercase text-[10px]">Official Email ID</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-ink border border-hairline rounded-lg px-3 py-2 text-text-primary font-mono focus:border-amber focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-text-muted mb-1 font-mono uppercase text-[10px]">Access Password</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-ink border border-hairline rounded-lg px-3 py-2 text-text-primary font-mono focus:border-amber focus:outline-none"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 rounded-lg bg-amber text-ink font-bold hover:bg-amber-400 transition-colors shadow flex items-center justify-center gap-2"
          >
            Authenticate Session <ArrowRight className="w-4 h-4" />
          </button>
        </form>

        <div className="text-[10px] text-center text-text-muted font-mono pt-2 border-t border-hairline">
          Protected by SHA-256 Hash-Chained Audit Ledger
        </div>
      </div>
    </div>
  );
};
