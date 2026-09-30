import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { 
  Shield, Search, HelpCircle, Bell, User, CheckCircle2, 
  Sparkles, Monitor, Info, ChevronRight, Activity, ToggleLeft, ToggleRight
} from 'lucide-react';
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
  const setUser = useAppStore((s) => s.setUser);

  const switchRole = (role: 'Investigator' | 'Supervisor' | 'Admin') => {
    if (role === 'Investigator') {
      setUser({ id: 1, email: 'investigator@demo', name: 'Vikram Rathore (IO Cyber)', role: 'Investigator' });
    } else if (role === 'Supervisor') {
      setUser({ id: 2, email: 'supervisor@demo', name: 'Meera Sharma (SP Ops)', role: 'Supervisor' });
    } else {
      setUser({ id: 3, email: 'admin@demo', name: 'Admin (Tech Wing)', role: 'Admin' });
    }
    setShowRoleMenu(false);
  };

  return (
    <header className="h-14 border-b border-hairline bg-panel/95 backdrop-blur px-4 flex items-center justify-between z-30 sticky top-0">
      {/* Left: Branding & Connection */}
      <div className="flex items-center gap-3">
        <Link to="/" className="flex items-center gap-2.5 group">
          <img src="/logo.svg" alt="ChainNetra" className="h-7 w-auto transition-transform group-hover:scale-105" />
        </Link>

        {/* Mode Badge (Amber DEMO DATA / Green LIVE) */}
        <div className="flex items-center gap-1.5 ml-2">
          <button
            onClick={() => setMode(mode === 'DEMO' ? 'LIVE' : 'DEMO')}
            className={`px-2 py-0.5 rounded text-[11px] font-mono font-bold tracking-wider transition-colors flex items-center gap-1.5 border ${
              mode === 'DEMO' 
                ? 'bg-amber/10 border-amber/40 text-amber hover:bg-amber/20' 
                : 'bg-mint/10 border-mint/40 text-mint hover:bg-mint/20'
            }`}
            title="Click to toggle Demo and Live Mode"
          >
            <span className={`w-1.5 h-1.5 rounded-full ${mode === 'DEMO' ? 'bg-amber' : 'bg-mint animate-pulse'}`} />
            {mode === 'DEMO' ? 'DEMO DATA' : 'LIVE'}
          </button>

          {/* WS Status */}
          <div className="flex items-center gap-1 px-1.5 py-0.5 text-[10px] font-mono text-text-muted">
            <span className={`w-1.5 h-1.5 rounded-full ${wsConnected ? 'bg-mint' : 'bg-coral'}`} />
            {wsConnected ? 'SYNCED' : 'OFFLINE'}
          </div>
        </div>
      </div>

      {/* Center: Search & Command Palette Trigger */}
      <button
        onClick={onOpenCommand}
        className="hidden md:flex items-center gap-3 px-3 py-1.5 bg-raised/80 hover:bg-raised border border-hairline hover:border-amber/40 rounded-lg text-xs text-text-muted transition-all w-80 justify-between group"
      >
        <span className="flex items-center gap-2">
          <Search className="w-3.5 h-3.5 text-text-muted group-hover:text-amber transition-colors" />
          <span>Search address, tx, complaint, VASP...</span>
        </span>
        <kbd className="px-1.5 py-0.5 rounded bg-panel border border-hairline font-mono text-[10px] text-text-muted">
          Ctrl+K
        </kbd>
      </button>

      {/* Right Controls */}
      <div className="flex items-center gap-2">
        {/* Explain Mode Toggle */}
        <button
          onClick={toggleExplainMode}
          className={`px-2.5 py-1 rounded text-xs flex items-center gap-1.5 border transition-all ${
            explainMode 
              ? 'bg-cyan/15 border-cyan text-cyan' 
              : 'border-hairline text-text-muted hover:text-text-primary'
          }`}
          title="Explain Like I'm New: Shows plain-language guidance on forensic panels"
        >
          <Sparkles className="w-3.5 h-3.5" />
          <span className="hidden lg:inline text-[11px] font-medium">Explain mode</span>
        </button>

        {/* Presentation Mode */}
        <button
          onClick={togglePresentationMode}
          className={`p-1.5 rounded border transition-colors ${
            presentationMode 
              ? 'bg-amber/20 border-amber text-amber' 
              : 'border-hairline text-text-muted hover:text-text-primary'
          }`}
          title="Presentation Mode (Expands view and enlarges graphs for judges)"
        >
          <Monitor className="w-3.5 h-3.5" />
        </button>

        {/* Help & Tour */}
        <button
          onClick={startTour}
          className="p-1.5 rounded border border-hairline text-text-muted hover:text-amber hover:border-amber/40 transition-colors"
          title="Start 17-Step Guided Tour"
        >
          <HelpCircle className="w-3.5 h-3.5" />
        </button>

        {/* Glossary */}
        <button
          onClick={onOpenGlossary}
          className="p-1.5 rounded border border-hairline text-text-muted hover:text-cyan hover:border-cyan/40 transition-colors"
          title="Searchable Crypto-Forensic Glossary"
        >
          <Info className="w-3.5 h-3.5" />
        </button>

        {/* Alerts Bell */}
        <Link
          to="/watchlist"
          className="p-1.5 rounded border border-hairline text-text-muted hover:text-coral hover:border-coral/40 transition-colors relative"
          title="Forensic Alerts"
        >
          <Bell className="w-3.5 h-3.5" />
          {unreadAlertsCount > 0 && (
            <span className="absolute -top-1 -right-1 w-4 h-4 bg-coral text-white font-mono text-[9px] rounded-full flex items-center justify-center font-bold">
              {unreadAlertsCount}
            </span>
          )}
        </Link>

        {/* Role Selector Chip */}
        <div className="relative">
          <button
            onClick={() => setShowRoleMenu(!showRoleMenu)}
            className="flex items-center gap-2 px-2.5 py-1 rounded bg-raised border border-hairline hover:border-amber/40 text-xs transition-colors"
          >
            <Shield className="w-3.5 h-3.5 text-amber" />
            <span className="font-medium text-text-primary text-[11px]">{user?.role}</span>
          </button>

          {showRoleMenu && (
            <div className="absolute right-0 mt-1.5 w-52 bg-panel border border-hairline rounded-lg shadow-xl py-1 z-50 animate-in fade-in zoom-in-95 duration-100">
              <div className="px-3 py-1.5 border-b border-hairline/60 text-[10px] font-mono text-text-muted uppercase">
                Switch Role (Demo Mode)
              </div>
              <button
                onClick={() => switchRole('Investigator')}
                className={`w-full text-left px-3 py-2 text-xs flex items-center justify-between hover:bg-raised ${user?.role === 'Investigator' ? 'text-amber font-semibold' : 'text-text-muted'}`}
              >
                <span>Investigator (IO)</span>
                {user?.role === 'Investigator' && <CheckCircle2 className="w-3 h-3 text-amber" />}
              </button>
              <button
                onClick={() => switchRole('Supervisor')}
                className={`w-full text-left px-3 py-2 text-xs flex items-center justify-between hover:bg-raised ${user?.role === 'Supervisor' ? 'text-amber font-semibold' : 'text-text-muted'}`}
              >
                <span>Supervisor (SP)</span>
                {user?.role === 'Supervisor' && <CheckCircle2 className="w-3 h-3 text-amber" />}
              </button>
              <button
                onClick={() => switchRole('Admin')}
                className={`w-full text-left px-3 py-2 text-xs flex items-center justify-between hover:bg-raised ${user?.role === 'Admin' ? 'text-amber font-semibold' : 'text-text-muted'}`}
              >
                <span>Admin (Tech Wing)</span>
                {user?.role === 'Admin' && <CheckCircle2 className="w-3 h-3 text-amber" />}
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
