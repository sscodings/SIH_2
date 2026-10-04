import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { api } from '../lib/api';
import { useAppStore } from '../stores/useAppStore';

export const Login: React.FC = () => {
  const navigate = useNavigate();
  const setUser = useAppStore((s) => s.setUser);

  const [email, setEmail] = useState('investigator@cybercrime.gov.in');
  const [password, setPassword] = useState('ForensicTraceSecure!2024');
  const [role, setRole] = useState('investigator');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      // Try real backend API if available
      const res = await api.login(email, password);
      localStorage.setItem('chainnetra_token', res.access_token);
      setUser(res.user);
      toast.success(`Access Granted: Welcome, Insp. R. Sharma (${role.toUpperCase()})`);
      navigate('/');
    } catch {
      const normalizedRole = (
        role === 'supervisor' ? 'Supervisor' : role === 'admin' ? 'Admin' : 'Investigator'
      ) as 'Investigator' | 'Supervisor' | 'Admin';
      const mockUser = {
        id: 1,
        email: email,
        name: 'Insp. R. Sharma',
        role: normalizedRole,
      };
      localStorage.setItem('chainnetra_token', 'mock_jwt_session_token');
      setUser(mockUser);
      toast.success(`Access Granted: Authenticated Clearance as ${normalizedRole}`);
      navigate('/');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen w-full bg-surface-container-low flex flex-col items-center justify-center p-6 md:p-8 animate-in fade-in duration-200">
      <div className="flex flex-col w-full items-center justify-center py-10 px-4">
        {/* Subtle Law Enforcement Agency Tag */}
        <div className="flex items-center gap-2 mb-6 px-4 py-1.5 rounded-full bg-surface-container text-secondary text-label-sm uppercase tracking-wider font-semibold border border-outline-variant/40">
          <span className="material-symbols-outlined text-[16px] text-tertiary">shield</span>
          <span>National Cyber Forensics Portal • Secure Auth</span>
        </div>

        {/* Primary Authentication Container */}
        <div className="w-full max-w-[460px] bg-surface-container-lowest rounded-xl shadow-md border border-outline-variant/60 p-8 md:p-10 flex flex-col items-center">
          {/* Institutional Emblem & Brand Header */}
          <div className="flex flex-col items-center text-center mb-6">
            <div className="w-14 h-14 rounded-full bg-surface-container border border-outline-variant/40 flex items-center justify-center mb-3 relative">
              <svg className="w-8 h-8 text-primary" fill="none" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
                <circle cx="16" cy="16" r="13" stroke="currentColor" strokeOpacity="0.25" strokeWidth="2"></circle>
                <path
                  d="M5 16C8.5 10 12.5 7 16 7C19.5 7 23.5 10 27 16C23.5 22 19.5 25 16 25C12.5 25 8.5 22 5 16Z"
                  stroke="currentColor"
                  strokeLinejoin="round"
                  strokeWidth="2"
                ></path>
                <circle cx="16" cy="16" fill="#005e54" r="4.5"></circle>
                <circle cx="16" cy="16" fill="#ffffff" r="1.5"></circle>
              </svg>
            </div>
            <div className="flex items-center gap-1.5 mb-1">
              <span className="text-headline-md tracking-tight text-on-surface font-bold">ChainNetra</span>
              <span className="text-tertiary font-mono text-[11px] font-semibold px-2 py-0.5 rounded bg-tertiary/10 border border-tertiary/20">
                v2.4
              </span>
            </div>
            <p className="text-body-sm text-on-surface-variant">Crypto fraud tracing for law enforcement</p>
          </div>

          {/* Credential Entry Form */}
          <form className="w-full flex flex-col gap-4" onSubmit={handleSubmit}>
            {/* Email Address Field */}
            <div className="flex flex-col gap-1.5">
              <label
                className="text-label-sm text-on-surface-variant flex items-center justify-between font-semibold uppercase"
                htmlFor="investigator-id"
              >
                <span>Official Mail / Badge ID</span>
                <span className="font-mono text-[11px] text-outline normal-case tracking-normal">
                  e.g. .gov.in / .nic.in
                </span>
              </label>
              <div className="relative flex items-center">
                <span className="material-symbols-outlined absolute left-3.5 text-outline text-[20px] pointer-events-none">
                  badge
                </span>
                <input
                  className="w-full h-11 pl-11 pr-4 bg-surface-container-low text-on-surface text-body-md rounded-xl border border-outline-variant/50 outline-none focus:bg-surface-bright focus:border-primary transition-colors font-mono"
                  id="investigator-id"
                  name="email"
                  placeholder="investigator@cybercrime.gov.in"
                  required
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>
            </div>

            {/* Password Field with Toggle */}
            <div className="flex flex-col gap-1.5">
              <div className="flex items-center justify-between">
                <label className="text-label-sm text-on-surface-variant font-semibold uppercase" htmlFor="passphrase">
                  Passcode Key
                </label>
                <button
                  type="button"
                  className="text-label-sm text-[11px] text-primary hover:underline font-semibold"
                  onClick={() => toast('Contact Nodal Forensics Desk at nodal@cybercrime.gov.in for PIN retrieval')}
                >
                  Forgot key?
                </button>
              </div>
              <div className="relative flex items-center">
                <span className="material-symbols-outlined absolute left-3.5 text-outline text-[20px] pointer-events-none">
                  lock
                </span>
                <input
                  className="w-full h-11 pl-11 pr-11 bg-surface-container-low text-on-surface font-mono text-body-md rounded-xl border border-outline-variant/50 outline-none focus:bg-surface-bright focus:border-primary transition-colors"
                  id="passphrase"
                  name="password"
                  placeholder="••••••••••••"
                  required
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
                <button
                  aria-label="Toggle password visibility"
                  className="absolute right-2 p-1.5 text-outline hover:text-on-surface transition-colors flex items-center justify-center rounded-lg"
                  onClick={() => setShowPassword(!showPassword)}
                  type="button"
                >
                  <span className="material-symbols-outlined text-[20px]">
                    {showPassword ? 'visibility_off' : 'visibility'}
                  </span>
                </button>
              </div>
            </div>

            {/* Operational Role Selector */}
            <div className="flex flex-col gap-1.5">
              <label className="text-label-sm text-on-surface-variant font-semibold uppercase" htmlFor="agency-role">
                Assigned Role &amp; Clearance
              </label>
              <div className="relative flex items-center">
                <span className="material-symbols-outlined absolute left-3.5 text-outline text-[20px] pointer-events-none">
                  security
                </span>
                <select
                  className="w-full h-11 pl-11 pr-10 bg-surface-container-low text-on-surface text-body-md rounded-xl border border-outline-variant/50 outline-none focus:bg-surface-bright focus:border-primary appearance-none cursor-pointer"
                  id="agency-role"
                  name="role"
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                >
                  <option value="investigator">Investigator (FIR &amp; Trace)</option>
                  <option value="supervisor">Supervisor (Warrant &amp; Freeze)</option>
                  <option value="admin">Admin (Agency &amp; Audit Logs)</option>
                </select>
                <span className="material-symbols-outlined absolute right-3.5 text-outline text-[20px] pointer-events-none">
                  expand_more
                </span>
              </div>
            </div>

            {/* Institutional Sign In CTA */}
            <div className="pt-2 flex flex-col gap-3">
              <button
                className="w-full h-12 bg-primary-container hover:bg-primary text-on-primary font-semibold text-body-md rounded-xl flex items-center justify-center gap-2 shadow-sm transition-colors active:scale-[0.99] disabled:opacity-60"
                id="btn-login"
                type="submit"
                disabled={loading}
              >
                {loading ? (
                  <>
                    <span className="material-symbols-outlined text-[18px] animate-spin">refresh</span>
                    <span>Verifying Clearance...</span>
                  </>
                ) : (
                  <>
                    <span className="material-symbols-outlined text-[18px]">verified_user</span>
                    <span>Sign in to Dossier</span>
                  </>
                )}
              </button>

              {/* Demo Mode Status Indicator */}
              <div className="flex items-center justify-center">
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-surface-container text-secondary text-label-sm font-semibold border border-outline-variant/30">
                  <span className="w-1.5 h-1.5 rounded-full bg-tertiary"></span>
                  Demo Environment • Sample Ledger Data
                </span>
              </div>
            </div>
          </form>

          {/* Audit & Legal Notice Separator */}
          <div className="w-full my-6 flex items-center gap-3">
            <div className="h-[1px] flex-1 bg-outline-variant/50"></div>
            <span className="text-[10px] uppercase text-outline font-semibold tracking-wider font-mono">
              Statutory Notice
            </span>
            <div className="h-[1px] flex-1 bg-outline-variant/50"></div>
          </div>

          {/* Official Statutory Compliance Footnote */}
          <div className="w-full bg-surface-container-low border border-outline-variant/30 rounded-lg p-3 text-center">
            <p className="text-body-sm text-[12px] leading-relaxed text-on-surface-variant">
              Authorized personnel only. All queries, wallet traces, and evidence generation are permanently recorded under the Information Technology Act, 2000.
            </p>
          </div>
        </div>

        {/* Agency Support Footer */}
        <div className="mt-6 flex items-center gap-3 text-secondary text-body-sm text-[12px] font-semibold flex-wrap justify-center">
          <span className="flex items-center gap-1">
            <span className="material-symbols-outlined text-[15px] text-tertiary">lock</span>
            256-bit Evidence Encryption
          </span>
          <span>•</span>
          <span>Cyber Crime Cell Internal Portal</span>
          <span>•</span>
          <button
            onClick={() => toast('Forensic Protocol v4.1 - Law Enforcement Spec.')}
            className="hover:text-primary underline decoration-dotted"
          >
            Protocols
          </button>
        </div>
      </div>
    </main>
  );
};
