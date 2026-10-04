import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Search, Bell, User, CheckCircle2, 
  HelpCircle, Monitor, Sparkles, ChevronDown, ShieldAlert
} from 'lucide-react';
import toast from 'react-hot-toast';
import { api } from '../lib/api';
import { useAppStore } from '../stores/useAppStore';

interface NavbarProps {
  onOpenCommand: () => void;
  onOpenGlossary: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ onOpenCommand, onOpenGlossary }) => {
  const navigate = useNavigate();
  const { 
    user, mode, setMode, wsConnected, unreadAlertsCount,
    explainMode, toggleExplainMode, presentationMode, togglePresentationMode,
    startTour 
  } = useAppStore();

  const [showRoleMenu, setShowRoleMenu] = useState(false);
  const [searchInput, setSearchInput] = useState('');
  const setUser = useAppStore((s) => s.setUser);

  const switchRole = async (role: 'Investigator' | 'Supervisor' | 'Admin') => {
    const roleEmail = role === 'Investigator' 
      ? 'investigator@demo' 
      : role === 'Supervisor' 
      ? 'supervisor@demo' 
      : 'admin@demo';

    try {
      const res = await api.login(roleEmail, 'demo123');
      setUser(res.user);
      toast.success(`Switched active session to ${role}`);
    } catch {
      if (role === 'Investigator') {
        setUser({ id: 1, email: 'investigator@demo', name: 'Insp. R. Sharma', role: 'Investigator' });
      } else if (role === 'Supervisor') {
        setUser({ id: 2, email: 'supervisor@demo', name: 'Meera Sharma (SP Ops)', role: 'Supervisor' });
      } else {
        setUser({ id: 3, email: 'admin@demo', name: 'Admin (Tech Wing)', role: 'Admin' });
      }
    }
    setShowRoleMenu(false);
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchInput.trim()) return;
    const q = searchInput.trim();
    if (q.startsWith('0x') || q.startsWith('T') || q.startsWith('bc1')) {
      navigate(`/wallet/tron/${q}`);
    } else if (q.toLowerCase().startsWith('ncrp') || q.toLowerCase().startsWith('fir')) {
      navigate('/inbox');
    } else {
      navigate(`/cases/1`);
    }
  };

  return (
    <header className="fixed top-0 left-64 right-0 h-14 bg-surface-container-lowest z-40 flex items-center justify-between px-6 shadow-[0_1px_8px_rgba(0,0,0,0.04)] border-b border-surface-container">
      {/* Search Input & Demo Indicator */}
      <div className="flex items-center gap-4 flex-1 max-w-2xl">
        <form onSubmit={handleSearchSubmit} className="relative w-full">
          <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-[18px]">
            search
          </span>
          <input 
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="w-full h-9 pl-9 pr-12 bg-surface-container-low rounded-lg font-code-md text-[13px] text-on-surface placeholder:text-outline placeholder:font-sans focus:outline-none focus:bg-surface-container-lowest focus:ring-1 focus:ring-primary transition-all"
            placeholder="Search wallet address (0x..., T...), tx hash, complaint ID..." 
            type="text"
          />
          <button 
            type="button"
            onClick={onOpenCommand}
            className="absolute right-2.5 top-1/2 -translate-y-1/2 px-1.5 py-0.5 rounded bg-surface-container text-outline text-[10px] font-mono hover:text-on-surface"
            title="Open Command Palette (Ctrl+K)"
          >
            ⌘K
          </button>
        </form>

        {/* Demo Mode Badge */}
        <div className="shrink-0 hidden lg:flex items-center gap-2 bg-secondary-container/30 px-3 py-1 rounded-full text-on-secondary-fixed border border-secondary-container">
          <span className="w-2 h-2 rounded-full bg-secondary animate-pulse" />
          <span className="font-label-sm text-[11px] font-semibold tracking-wide">Demo Mode: Sample Ledger</span>
        </div>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-3">
        {/* Explain Mode Toggle */}
        <button
          onClick={toggleExplainMode}
          className={`hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium transition-all ${
            explainMode 
              ? 'bg-primary-container text-on-primary shadow-xs' 
              : 'text-on-surface-variant hover:text-on-surface hover:bg-surface-container-low'
          }`}
          title="Toggle Plain-Language Explanations"
          type="button"
        >
          <Sparkles className="w-3.5 h-3.5" />
          <span>Explain Mode</span>
        </button>

        {/* Guided Tour Trigger */}
        <button
          onClick={startTour}
          className="hidden md:flex items-center gap-1.5 px-2.5 py-1 text-xs text-on-surface-variant hover:text-on-surface hover:bg-surface-container-low rounded-lg transition-colors"
          title="Start Guided System Tour"
          type="button"
        >
          <HelpCircle className="w-3.5 h-3.5" />
          <span>Tour</span>
        </button>

        {/* Notifications Button */}
        <button 
          onClick={() => navigate('/watchlist')}
          className="relative p-2 text-on-surface-variant hover:text-on-surface hover:bg-surface-container-low rounded-lg transition-colors" 
          type="button"
          title="Surveillance Alerts"
        >
          <span className="material-symbols-outlined text-[20px]">notifications</span>
          {unreadAlertsCount > 0 && (
            <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-error rounded-full ring-2 ring-surface-container-lowest" />
          )}
        </button>

        {/* Official LE Profile Box */}
        <div className="relative">
          <button
            onClick={() => setShowRoleMenu(!showRoleMenu)}
            className="flex items-center gap-2 pl-2 bg-surface-container-low hover:bg-surface-container py-1 pr-3 rounded-full transition-all"
            type="button"
          >
            <img 
              alt="Inspector R. Sharma" 
              className="w-8 h-8 rounded-full object-cover ring-1 ring-surface-container-high" 
              src="/inspector.png"
              onError={(e) => {
                (e.currentTarget as HTMLImageElement).src = 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100&h=100&fit=crop&crop=faces';
              }}
            />
            <div className="flex flex-col text-left">
              <span className="font-label-md text-[12px] font-semibold text-on-surface leading-tight">
                {user?.name || 'Insp. R. Sharma'}
              </span>
              <span className="font-label-sm text-[10px] text-on-surface-variant leading-tight">
                {user?.role || 'Cyber Crime Unit'}
              </span>
            </div>
            <ChevronDown className="w-3.5 h-3.5 text-on-surface-variant" />
          </button>

          {/* Role Dropdown */}
          {showRoleMenu && (
            <div className="absolute right-0 mt-2 w-56 bg-surface-container-lowest border border-surface-container rounded-xl shadow-lg p-2 z-50 animate-in fade-in slide-in-from-top-2">
              <div className="px-3 py-2 border-b border-surface-container mb-1">
                <span className="text-[10px] uppercase font-bold text-outline tracking-wider">Operational Clearance</span>
                <p className="text-xs font-semibold text-on-surface">{user?.email || 'sharma.cyber@gov.in'}</p>
              </div>

              {(['Investigator', 'Supervisor', 'Admin'] as const).map((r) => (
                <button
                  key={r}
                  onClick={() => switchRole(r)}
                  className={`w-full text-left px-3 py-1.5 rounded-lg text-xs flex items-center justify-between transition-colors ${
                    user?.role === r 
                      ? 'bg-primary-container text-on-primary font-semibold' 
                      : 'text-on-surface hover:bg-surface-container-low'
                  }`}
                  type="button"
                >
                  <span>{r} View</span>
                  {user?.role === r && <CheckCircle2 className="w-3.5 h-3.5 text-on-primary" />}
                </button>
              ))}

              <div className="border-t border-surface-container mt-1 pt-1">
                <button
                  onClick={() => {
                    navigate('/login');
                    setShowRoleMenu(false);
                  }}
                  className="w-full text-left px-3 py-1.5 rounded-lg text-xs text-error hover:bg-error-container/40 transition-colors"
                  type="button"
                >
                  Sign Out / Switch Station
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
