import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { api } from '../lib/api';
import { useAppStore } from '../stores/useAppStore';

export const WalletProfile: React.FC = () => {
  const { chain = 'tron', address = 'TJ8wK9vZMb2pQ5aN8cxYz3rP1kLmN7xL9' } = useParams<{ chain: string; address: string }>();
  const navigate = useNavigate();
  const explainMode = useAppStore((s) => s.explainMode);

  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const loadProfile = async () => {
      try {
        setLoading(true);
        const data = await api.getWalletProfile(chain, address);
        setProfile(data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    loadProfile();
  }, [chain, address]);

  const copyAddress = () => {
    navigator.clipboard.writeText(address);
    setCopied(true);
    toast.success('Address copied to clipboard');
    setTimeout(() => setCopied(false), 2000);
  };

  const handleWatchlistAdd = () => {
    toast.success(`Address ${address.slice(0, 10)}... added to live surveillance watchlist`);
  };

  return (
    <div className="flex flex-col w-full gap-6 animate-in fade-in duration-150">
      {/* Case Audit Trail & Evidentiary Banner */}
      <div className="w-full bg-surface-container-lowest shadow-sm rounded-xl px-6 py-3 flex flex-wrap items-center justify-between gap-4 border border-surface-container">
        <div className="flex items-center gap-6 flex-wrap">
          <div className="flex items-center gap-2 text-on-surface">
            <span className="material-symbols-outlined text-[18px] text-primary">verified_user</span>
            <span className="font-label-md text-xs tracking-wider uppercase text-on-surface-variant font-semibold">Evidentiary Record:</span>
            <span className="font-mono text-xs font-bold text-primary">#DOS-TRC-88219</span>
          </div>

          <div className="h-3 w-px bg-surface-container-high hidden sm:block" />

          <div className="flex items-center gap-1.5 text-on-surface-variant text-xs">
            <span className="material-symbols-outlined text-[16px]">badge</span>
            <span>Assigned IO: Insp. R. Sharma (CYB-LE-904)</span>
          </div>

          <div className="h-3 w-px bg-surface-container-high hidden sm:block" />

          <div className="flex items-center gap-1.5 text-on-surface-variant text-xs font-mono">
            <span className="material-symbols-outlined text-[16px] text-secondary">lock</span>
            <span>Block #66,419,021</span>
          </div>
        </div>

        <div className="flex items-center gap-1.5 bg-surface-container-low px-3 py-1 rounded-full text-xs text-on-surface-variant">
          <span className="w-1.5 h-1.5 rounded-full bg-secondary"></span>
          <span>Court-Admissible Snapshot Sync: Active</span>
        </div>
      </div>

      {/* Dossier Header & Action Control Bar */}
      <div className="w-full bg-surface-container-lowest shadow-sm rounded-xl p-6 flex flex-col md:flex-row md:items-center justify-between gap-6 border border-surface-container">
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-[10px] uppercase tracking-wider text-primary font-bold">ChainNetra Forensic Repository</span>
            <span className="text-outline text-xs">•</span>
            <div className="flex items-center gap-1.5 bg-error-container/40 text-on-error-container px-2.5 py-0.5 rounded-full text-[11px] font-semibold">
              <span className="w-1.5 h-1.5 rounded-full bg-error animate-pulse"></span>
              <span>Target Under S.91 CrPC Advisory</span>
            </div>
          </div>

          <h1 className="font-display-lg text-2xl font-bold text-on-surface tracking-tight mt-1">
            Wallet Dossier
          </h1>

          {/* Monospace Address Block */}
          <div className="flex items-center gap-3 flex-wrap mt-2">
            <div className="flex items-center gap-2 bg-surface-container-low px-3 py-1.5 rounded-lg border border-surface-container">
              <span className="material-symbols-outlined text-primary text-[18px]">account_balance_wallet</span>
              <span className="font-mono text-xs font-semibold text-on-surface select-all tracking-wide">
                {address}
              </span>
              <button
                onClick={copyAddress}
                className="text-on-surface-variant hover:text-primary transition-colors p-0.5"
                title="Copy Address"
                type="button"
              >
                <span className="material-symbols-outlined text-[16px]">
                  {copied ? 'check' : 'content_copy'}
                </span>
              </button>
            </div>

            <span className="bg-surface-container-high text-on-surface-variant px-3 py-1 rounded-full text-xs font-medium flex items-center gap-1">
              <span className="material-symbols-outlined text-[14px] text-primary">token</span>
              Tron (TRC-20)
            </span>

            <span className="bg-error-container text-on-error-container px-3 py-1 rounded-full text-xs font-semibold flex items-center gap-1">
              <span className="material-symbols-outlined text-[14px]">warning</span>
              Scammer Primary Collector
            </span>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-3 shrink-0 self-start md:self-center">
          <button
            onClick={handleWatchlistAdd}
            className="flex items-center gap-1.5 bg-surface-container-lowest hover:bg-surface-container text-on-surface text-xs font-semibold px-4 py-2.5 rounded-lg shadow-sm transition-colors border border-surface-container"
            type="button"
          >
            <span className="material-symbols-outlined text-[18px] text-on-surface-variant">playlist_add_check</span>
            <span>Add to Active Watchlist</span>
          </button>

          <button
            onClick={() => navigate('/cases/1')}
            className="flex items-center gap-1.5 bg-primary-container hover:bg-primary text-on-primary text-xs font-semibold px-4 py-2.5 rounded-lg shadow-sm transition-colors"
            type="button"
          >
            <span className="material-symbols-outlined text-[18px]">account_tree</span>
            <span>Trace Full Outflow</span>
          </button>
        </div>
      </div>

      {/* 2-Column Spacious Analytical Canvas */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* LEFT COLUMN: Quantitative Signals (7 cols) */}
        <div className="lg:col-span-7 flex flex-col gap-6">
          {/* Card 1: Risk Assessment & Key Metrics */}
          <div className="bg-surface-container-lowest rounded-xl shadow-sm overflow-hidden border border-surface-container">
            <div className="px-6 py-4 flex items-center justify-between border-b border-surface-container">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-[18px] text-primary">shield_with_heart</span>
                <h2 className="font-headline-sm text-sm font-bold text-on-surface">Risk Assessment &amp; Key Metrics</h2>
              </div>
              <span className="font-mono text-[11px] bg-surface-container-low text-on-surface-variant px-2.5 py-0.5 rounded border border-surface-container">
                Algo Engine: v4.81
              </span>
            </div>

            <div className="p-6 flex flex-col gap-6">
              {/* Semicircle Risk Gauge Visualizer */}
              <div className="flex flex-col sm:flex-row items-center justify-between gap-6 bg-surface-container-low/60 rounded-xl p-6 border border-surface-container">
                <div className="relative w-56 h-28 flex items-end justify-center select-none overflow-hidden shrink-0">
                  <svg className="w-56 h-56 -mb-28 transform -rotate-180" viewBox="0 0 200 200">
                    <circle cx="100" cy="100" fill="none" r="76" stroke="#D2E4FD" strokeDasharray="238.76" strokeDashoffset="0" strokeLinecap="round" strokeWidth="16"></circle>
                    <circle cx="100" cy="100" fill="none" r="76" stroke="#BA1A1A" strokeDasharray="238.76" strokeDashoffset="42.98" strokeLinecap="round" strokeWidth="16"></circle>
                  </svg>
                  <div className="absolute bottom-1 flex flex-col items-center leading-none">
                    <span className="text-[10px] uppercase tracking-widest text-error font-bold">High Risk</span>
                    <div className="flex items-baseline gap-0.5 mt-1">
                      <span className="text-3xl font-bold text-error">82</span>
                      <span className="text-xs text-on-surface-variant">/ 100</span>
                    </div>
                  </div>
                </div>

                <div className="flex flex-col gap-1 text-left">
                  <div className="inline-flex items-center gap-1.5 text-error text-xs font-bold">
                    <span className="material-symbols-outlined text-[16px]">priority_high</span>
                    Critical Laundering Velocity Detected
                  </div>
                  <p className="text-xs text-on-surface-variant leading-relaxed">
                    This entity operates as a rapid funneling node. Incoming victim deposits display a 92% peel dispersal coefficient with negligible holding periods (&lt; 4 minutes), characteristic of organized cyber syndicate collection rails.
                  </p>
                </div>
              </div>

              {/* 3 Key Stats */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="bg-surface-container-low rounded-xl p-4 flex flex-col gap-1 border border-surface-container">
                  <div className="flex items-center gap-1 text-on-surface-variant text-[11px] uppercase font-semibold">
                    <span className="material-symbols-outlined text-[14px]">calendar_today</span>
                    First Seen
                  </div>
                  <span className="text-sm font-bold text-on-surface">12 Oct 2024</span>
                  <span className="font-mono text-[10px] text-outline">12 days ago • Epoch #1728710400</span>
                </div>

                <div className="bg-surface-container-low rounded-xl p-4 flex flex-col gap-1 border border-surface-container">
                  <div className="flex items-center gap-1 text-on-surface-variant text-[11px] uppercase font-semibold">
                    <span className="material-symbols-outlined text-[14px] text-secondary">arrow_downward</span>
                    Total Received
                  </div>
                  <span className="text-sm font-bold text-on-surface">₹84.20 Lakh</span>
                  <span className="font-mono text-[10px] text-secondary font-semibold">98,400 USDT</span>
                </div>

                <div className="bg-surface-container-low rounded-xl p-4 flex flex-col gap-1 border border-surface-container">
                  <div className="flex items-center gap-1 text-on-surface-variant text-[11px] uppercase font-semibold">
                    <span className="material-symbols-outlined text-[14px] text-error">arrow_upward</span>
                    Total Sent
                  </div>
                  <span className="text-sm font-bold text-on-surface">₹82.10 Lakh</span>
                  <span className="font-mono text-[10px] text-error font-semibold">95,950 USDT (Peel)</span>
                </div>
              </div>
            </div>
          </div>

          {/* Card 2: Transaction History Ledger */}
          <div className="bg-surface-container-lowest rounded-xl shadow-sm p-6 border border-surface-container space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-surface-container">
              <h3 className="text-sm font-bold text-on-surface">Confirmed Transaction Ledger</h3>
              <span className="text-[11px] font-mono text-outline">Showing recent 4 transfers</span>
            </div>

            <div className="divide-y divide-surface-container text-xs">
              {[
                { time: '24 Oct, 09:12 AM', counterparty: '0x89c2...41a0 (Victim Complainant)', type: 'INFLOW', amt: '+₹14,50,000 (17,320 USDT)', status: 'Proceeds of Fraud' },
                { time: '24 Oct, 09:15 AM', counterparty: '0x4bE...12D8 (Peel Splitter)', type: 'OUTFLOW', amt: '-₹9,20,000 (11,000 USDT)', status: 'Splitter Hop 1' },
                { time: '24 Oct, 09:16 AM', counterparty: '0x33A...eE21 (Mule B)', type: 'OUTFLOW', amt: '-₹5,30,000 (6,320 USDT)', status: 'Splitter Hop 2' },
                { time: '24 Oct, 11:45 AM', counterparty: 'Binance Global Hot #14', type: 'TERMINUS', amt: '$12,400 USDT', status: 'Sec 91 Lien Target' },
              ].map((tx, idx) => (
                <div key={idx} className="py-3 flex items-center justify-between">
                  <div>
                    <div className="font-semibold text-on-surface">{tx.counterparty}</div>
                    <div className="text-[10px] text-outline font-mono">{tx.time} • {tx.status}</div>
                  </div>
                  <div className="text-right">
                    <span className={`font-mono font-bold ${tx.type === 'INFLOW' ? 'text-secondary' : 'text-error'}`}>
                      {tx.amt}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN: Associated Cases & Entity Profile (5 cols) */}
        <div className="lg:col-span-5 flex flex-col gap-6">
          <div className="bg-surface-container-lowest rounded-xl shadow-sm p-6 border border-surface-container space-y-4">
            <h3 className="text-sm font-bold text-on-surface">Linked Complaints &amp; FIRs</h3>
            <div className="space-y-3">
              <div 
                onClick={() => navigate('/cases/1')}
                className="p-3.5 rounded-lg bg-surface-container-low hover:bg-surface-container transition-colors cursor-pointer border border-surface-container"
              >
                <div className="flex items-center justify-between text-xs font-semibold text-primary">
                  <span>#CN-2024-0944</span>
                  <span className="text-secondary font-mono text-[11px]">VASP Tagged</span>
                </div>
                <p className="text-xs font-medium text-on-surface mt-1">Pune Telegram Task Fraud</p>
                <div className="text-[11px] text-outline mt-0.5">FIR #184/2024 • Loss: ₹42.50 Lakh</div>
              </div>

              <div 
                onClick={() => navigate('/linking')}
                className="p-3.5 rounded-lg bg-surface-container-low hover:bg-surface-container transition-colors cursor-pointer border border-surface-container"
              >
                <div className="flex items-center justify-between text-xs font-semibold text-primary">
                  <span>#CN-2024-0938</span>
                  <span className="text-[#D9901A] font-mono text-[11px]">Cross-Chain Hop</span>
                </div>
                <p className="text-xs font-medium text-on-surface mt-1">Mumbai Stock Investment Scheme</p>
                <div className="text-[11px] text-outline mt-0.5">FIR #201/2024 • Loss: ₹18.00 Lakh</div>
              </div>
            </div>
          </div>

          <div className="bg-surface-container-lowest rounded-xl shadow-sm p-6 border border-surface-container space-y-3 text-xs">
            <h3 className="text-sm font-bold text-on-surface">Behavioral Profile</h3>
            <p className="text-on-surface-variant leading-relaxed">
              Consistently active during IST banking hours (09:00 - 18:00). Utilizes instant TRC-20 energy delegation contracts to minimize on-chain TRX footprint. Direct links to Southeast Asian syndicated mule networks.
            </p>
            <div className="pt-2">
              <button
                onClick={() => navigate('/vasps')}
                className="w-full py-2 bg-primary-container hover:bg-primary text-on-primary font-semibold rounded-lg text-xs transition-colors"
              >
                Generate Sec 91 Freeze Notice
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
