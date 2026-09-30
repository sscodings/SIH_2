import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Search, Eye, Inbox, FileText, Building2, 
  GitBranch, PlayCircle, Shield, CheckCircle, Network, ArrowRight 
} from 'lucide-react';
import { api } from '../lib/api';

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
}

export const CommandPalette: React.FC<CommandPaletteProps> = ({ isOpen, onClose }) => {
  const [query, setQuery] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        if (isOpen) onClose();
        else setQuery('');
      }
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const actions = [
    { label: 'Go to Command Center', icon: Eye, action: () => navigate('/') },
    { label: 'Go to Case Zero (Guided Demo)', icon: PlayCircle, action: () => navigate('/cases/1') },
    { label: 'Go to Complaint Inbox (NCRP / SAHYOG)', icon: Inbox, action: () => navigate('/inbox') },
    { label: 'Go to Case Linking / Syndicate Board', icon: Network, action: () => navigate('/linking') },
    { label: 'Go to Cross-Chain Analytics', icon: GitBranch, action: () => navigate('/cross-chain') },
    { label: 'Go to VASP Directory & Freeze Requests', icon: Building2, action: () => navigate('/vasps') },
    { label: 'Go to Cryptographic Evidence Verification', icon: CheckCircle, action: () => navigate('/verify') },
    { label: 'Inspect Wallet Profile (DemoX Hot Wallet)', icon: Shield, action: () => navigate('/wallet/tron/TXDemoxHotWalletPrimary88888888888') },
  ];

  const filtered = actions.filter((a) => a.label.toLowerCase().includes(query.toLowerCase()));

  const handleSelect = (actionFn: () => void) => {
    actionFn();
    onClose();
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const q = query.trim();
    if (!q) return;

    if (q.startsWith('0x') || q.startsWith('T') || q.startsWith('1') || q.startsWith('bc1')) {
      const chain = q.startsWith('T') ? 'tron' : (q.startsWith('0x') ? 'ethereum' : 'bitcoin');
      navigate(`/wallet/${chain}/${q}`);
      onClose();
    } else if (q.toUpperCase().startsWith('NCRP-')) {
      navigate('/inbox');
      onClose();
    } else if (q.toUpperCase().startsWith('CASE-')) {
      navigate('/cases/1');
      onClose();
    } else {
      if (filtered.length > 0) {
        handleSelect(filtered[0].action);
      }
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-24 bg-black/70 backdrop-blur-sm animate-in fade-in">
      <div 
        className="w-full max-w-xl bg-panel border border-hairline rounded-xl shadow-2xl overflow-hidden animate-in zoom-in-95 duration-150"
        onClick={(e) => e.stopPropagation()}
      >
        <form onSubmit={handleSearchSubmit} className="p-3 border-b border-hairline flex items-center gap-3">
          <Search className="w-5 h-5 text-amber shrink-0 ml-1" />
          <input
            type="text"
            placeholder="Type a command, address, hash, complaint ID, or case number..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full bg-transparent text-sm text-text-primary placeholder:text-text-muted focus:outline-none"
            autoFocus
          />
          <kbd className="px-2 py-0.5 rounded bg-raised border border-hairline text-[10px] font-mono text-text-muted">ESC</kbd>
        </form>

        <div className="max-h-80 overflow-y-auto p-2 space-y-1">
          <div className="px-2 py-1 text-[10px] font-mono text-text-muted uppercase">Quick Navigation & Actions</div>
          {filtered.map((item, idx) => {
            const Icon = item.icon;
            return (
              <button
                key={idx}
                onClick={() => handleSelect(item.action)}
                className="w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs text-text-primary hover:bg-raised transition-colors group"
              >
                <div className="flex items-center gap-2.5">
                  <Icon className="w-4 h-4 text-text-muted group-hover:text-amber transition-colors" />
                  <span>{item.label}</span>
                </div>
                <ArrowRight className="w-3.5 h-3.5 text-text-muted opacity-0 group-hover:opacity-100 transition-opacity" />
              </button>
            );
          })}
        </div>

        <div className="p-2 border-t border-hairline bg-ink text-[11px] text-text-muted flex justify-between px-3 font-mono">
          <span>Search hints: paste 0x/T/bc1 address to inspect wallet</span>
          <span>↵ Enter to select</span>
        </div>
      </div>
    </div>
  );
};
