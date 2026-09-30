import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Network, Pin, Merge, ArrowRight, Shield, AlertTriangle, Sparkles } from 'lucide-react';
import toast from 'react-hot-toast';
import { api } from '../lib/api';
import { useAppStore } from '../stores/useAppStore';

export const CaseLinking: React.FC = () => {
  const navigate = useNavigate();
  const explainMode = useAppStore((s) => s.explainMode);

  const [syndicateData] = useState({
    title: 'Operation Chakra: Eurasian Cyber-Financial Syndicate',
    complaintCount: 5,
    totalLossInr: 13650000,
    totalLossUsd: 163470,
    sharedWalletsCount: 4,
    convergentCollector: 'TSyndicateCoreCollectorNexus77777',
    targetVasp: 'DemoX Exchange',
    complaints: [
      { id: 'NCRP-2026-000301', victim: 'Vikram Singhania (Gujarat)', loss: '₹32.0 Lakh', fraud: 'Stock Market Investment' },
      { id: 'NCRP-2026-000302', victim: 'Divya Menon (Kerala)', loss: '₹18.5 Lakh', fraud: 'Work-from-Home Commission' },
      { id: 'NCRP-2026-000303', victim: 'Manish Tiwari (MP)', loss: '₹27.0 Lakh', fraud: 'Fake Crypto Staking Protocol' },
      { id: 'NCRP-2026-000304', victim: 'Sunita Sen (Assam)', loss: '₹14.0 Lakh', fraud: 'Telegram Signal Scam' },
      { id: 'NCRP-2026-000305', victim: 'Rakesh Bansal (Rajasthan)', loss: '₹45.0 Lakh', fraud: 'Pre-IPO Digital Share Fraud' }
    ]
  });

  const handleMergeSyndicate = async () => {
    try {
      await api.mergeCases([1, 2, 5], 'Operation Chakra: Unified Interstate Syndicate Dossier');
      toast.success('Successfully consolidated 5 complaints into unified Syndicate Case!');
      navigate('/cases/5');
    } catch (e) {
      toast.error('Merge failed');
    }
  };

  return (
    <div className="space-y-4 animate-in fade-in duration-200">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-2 border-b border-hairline">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-text-primary flex items-center gap-2">
            Interstate Syndicate Evidence Board
            <span className="text-xs px-2 py-0.5 rounded font-mono font-bold bg-coral/20 border border-coral/40 text-coral">
              5 CONVERGING COMPLAINTS
            </span>
          </h1>
          <p className="text-xs text-text-muted mt-0.5">
            Cross-jurisdictional intelligence showing separate victim complaints that funnel into common collector infrastructure.
          </p>
        </div>

        <button
          onClick={handleMergeSyndicate}
          className="px-4 py-2 rounded-lg bg-coral text-white font-bold text-xs hover:bg-coral-600 transition-colors flex items-center gap-2 shadow"
        >
          <Merge className="w-4 h-4" />
          Merge into Syndicate Dossier
        </button>
      </div>

      {explainMode && (
        <div className="p-3 bg-cyan/10 border border-cyan/30 rounded-lg text-xs text-cyan flex items-start gap-2.5">
          <Sparkles className="w-4 h-4 shrink-0 mt-0.5" />
          <div>
            <span className="font-bold">Investigator Insight:</span> Often multiple police stations in different states file separate FIRs for what is actually the exact same cyber syndicate.
            ChainNetra's clustering engine spots that funds from Gujarat, Kerala, MP, Assam, and Rajasthan all converge on wallet <code className="font-mono text-text-primary">TSyndicateCore...</code> within 48 hours.
          </div>
        </div>
      )}

      {/* Syndicate Banner Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="p-3 rounded-xl bg-panel border border-hairline">
          <span className="text-[10px] font-mono text-text-muted uppercase">Convergent Complaints</span>
          <div className="text-xl font-bold font-mono text-text-primary mt-1">{syndicateData.complaintCount} Interstate FIRs</div>
          <span className="text-[10px] text-coral font-mono">Gujarat, Kerala, MP, Assam, Raj</span>
        </div>

        <div className="p-3 rounded-xl bg-panel border border-hairline">
          <span className="text-[10px] font-mono text-text-muted uppercase">Cumulative Financial Loss</span>
          <div className="text-xl font-bold font-mono text-amber mt-1">₹{(syndicateData.totalLossInr / 10000000).toFixed(2)} Crore</div>
          <span className="text-[10px] text-text-muted font-mono">${(syndicateData.totalLossUsd / 1000).toFixed(0)}k USD</span>
        </div>

        <div className="p-3 rounded-xl bg-panel border border-hairline">
          <span className="text-[10px] font-mono text-text-muted uppercase">Common Collector Hub</span>
          <div className="text-sm font-mono font-bold text-cyan mt-1 truncate">{syndicateData.convergentCollector.slice(0, 14)}...</div>
          <span className="text-[10px] text-text-muted">Tron TRC-20 Hub</span>
        </div>

        <div className="p-3 rounded-xl bg-panel border border-hairline">
          <span className="text-[10px] font-mono text-text-muted uppercase">Target Cash-out VASP</span>
          <div className="text-lg font-bold text-mint mt-1">{syndicateData.targetVasp}</div>
          <span className="text-[10px] text-mint font-mono">Attributed (&lt; 2h SLA)</span>
        </div>
      </div>

      {/* Evidence Board Canvas (Index Cards with Red Thread Connectors) */}
      <div className="p-6 rounded-2xl bg-ink border-2 border-hairline relative min-h-[500px] overflow-hidden shadow-2xl forensic-grid">
        {/* Red Thread SVG Connectors */}
        <svg className="absolute inset-0 w-full h-full pointer-events-none z-10">
          {/* Connector lines from pinned complaint cards to central collector hub */}
          <line x1="220" y1="90" x2="520" y2="240" className="red-thread" />
          <line x1="220" y1="180" x2="520" y2="240" className="red-thread" />
          <line x1="220" y1="270" x2="520" y2="240" className="red-thread" />
          <line x1="220" y1="360" x2="520" y2="240" className="red-thread" />
          <line x1="220" y1="450" x2="520" y2="240" className="red-thread" />

          {/* Line from central collector hub to VASP */}
          <line x1="680" y1="240" x2="880" y2="240" stroke="#3DDC97" strokeWidth="2.5" strokeDasharray="3 3" />
        </svg>

        <div className="relative z-20 flex justify-between items-center h-full">
          {/* Left Column: Pinned Victim Complaint Cards */}
          <div className="space-y-3 w-80">
            {syndicateData.complaints.map((c, idx) => (
              <div 
                key={idx} 
                className="evidence-card p-3 rounded-lg border border-hairline/80 relative shadow-lg hover:scale-102 transition-transform"
              >
                {/* Visual Pin */}
                <div className="absolute -top-1.5 left-4 w-3 h-3 rounded-full bg-coral border border-white shadow" />
                
                <div className="flex justify-between items-start pt-1 font-mono">
                  <span className="text-xs font-bold text-cyan">{c.id}</span>
                  <span className="text-xs font-bold text-amber">{c.loss}</span>
                </div>
                <div className="text-xs font-semibold text-text-primary mt-1">{c.victim}</div>
                <div className="text-[10px] text-text-muted">{c.fraud}</div>
              </div>
            ))}
          </div>

          {/* Center: Central Collector Hub Card */}
          <div className="w-72 evidence-card p-5 rounded-xl border-2 border-amber/70 shadow-2xl text-center relative animate-pulse-subtle">
            <div className="absolute -top-2.5 left-1/2 -translate-x-1/2 w-4 h-4 rounded-full bg-amber border-2 border-white shadow" />
            <span className="px-2 py-0.5 rounded bg-amber/20 text-amber font-mono text-[10px] font-bold uppercase">
              COMMON NEXUS COLLECTOR
            </span>
            <h3 className="text-xs font-mono font-bold text-cyan mt-2 break-all">
              {syndicateData.convergentCollector}
            </h3>
            <p className="text-xs text-text-muted mt-2">
              All 5 complaints deposited into this wallet within 48h. Co-spending and same-sweep heuristic confirms common ownership.
            </p>
            <div className="mt-3 p-2 bg-ink rounded font-mono text-xs text-amber font-bold">
              Total Swept: ₹1.36 Crore
            </div>
          </div>

          {/* Right: Cash-out VASP Card */}
          <div className="w-64 evidence-card p-5 rounded-xl border-2 border-mint/70 shadow-2xl text-center relative">
            <div className="absolute -top-2.5 left-1/2 -translate-x-1/2 w-4 h-4 rounded-full bg-mint border-2 border-white shadow" />
            <span className="px-2 py-0.5 rounded bg-mint/20 text-mint font-mono text-[10px] font-bold uppercase">
              CASH-OUT DESTINATION
            </span>
            <h3 className="text-sm font-bold text-text-primary mt-2">
              {syndicateData.targetVasp}
            </h3>
            <p className="text-xs text-text-muted mt-1">
              Deposit Vault: <code className="text-cyan font-mono text-[11px]">TXDemoxDeposit...</code>
            </p>
            <div className="mt-3">
              <button
                onClick={() => navigate('/vasps')}
                className="w-full py-1.5 rounded-lg bg-mint text-ink font-bold text-xs hover:bg-mint-400 transition-colors shadow"
              >
                Send Joint Freeze Order
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
