import React from 'react';
import { Volume2, Sparkles, X } from 'lucide-react';
import { useAppStore } from '../stores/useAppStore';

export const NarrationBar: React.FC = () => {
  const activeNarration = useAppStore((s) => s.activeNarration);
  const setNarration = useAppStore((s) => s.setNarration);

  if (!activeNarration) return null;

  return (
    <div className="bg-raised border border-amber/40 px-4 py-2 flex items-center justify-between gap-3 text-xs text-text-primary rounded-lg shadow-lg animate-in slide-in-from-top duration-150">
      <div className="flex items-center gap-2.5 overflow-hidden">
        <span className="w-2 h-2 rounded-full bg-amber animate-ping shrink-0" />
        <Volume2 className="w-4 h-4 text-amber shrink-0" />
        <span className="font-mono text-amber text-[11px] font-bold uppercase tracking-wider shrink-0">Live Narration:</span>
        <span className="truncate text-text-primary font-medium tracking-wide">{activeNarration}</span>
      </div>
      <button 
        onClick={() => setNarration(null)}
        className="text-text-muted hover:text-text-primary p-0.5 rounded shrink-0"
      >
        <X className="w-3.5 h-3.5" />
      </button>
    </div>
  );
};
