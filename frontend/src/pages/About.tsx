import React from 'react';
import { useNavigate } from 'react-router-dom';

export const About: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="space-y-8 max-w-5xl mx-auto py-4 animate-in fade-in duration-200 pb-16">
      {/* Hero Banner */}
      <div className="text-center space-y-3">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-surface-container text-primary text-label-sm font-semibold border border-outline-variant/40">
          <span className="material-symbols-outlined text-[16px] text-secondary">verified_user</span>
          <span>CHAINNETRA FORENSIC PLATFORM • LEAF FRAMEWORK</span>
        </div>
        <h1 className="text-3xl md:text-4xl font-bold text-on-surface tracking-tight">
          Real-Time Crypto Fraud Attribution &amp; Freeze Intelligence
        </h1>
        <p className="text-body-md text-on-surface-variant max-w-2xl mx-auto leading-relaxed">
          Turning a days-long manual expert tracing task into a minutes-long automated forensic workflow so proceeds of cybercrime can be frozen before they vanish.
        </p>

        <div className="pt-2 flex justify-center gap-3">
          <button
            onClick={() => navigate('/cases/1')}
            className="px-5 py-2.5 rounded-lg bg-primary text-on-primary font-semibold text-label-md hover:bg-primary-container transition-colors shadow-sm flex items-center gap-2"
          >
            <span>Launch Case Zero Dossier</span>
            <span className="material-symbols-outlined text-sm">arrow_forward</span>
          </button>
          <button
            onClick={() => navigate('/inbox')}
            className="px-4 py-2.5 rounded-lg bg-surface-container hover:bg-surface-container-high text-on-surface text-label-md font-semibold border border-outline-variant/50 transition-colors"
          >
            Explore Complaint Feed
          </button>
        </div>
      </div>

      {/* Problem vs Solution Comparison */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <div className="p-6 rounded-xl bg-surface-container-lowest border border-error/30 shadow-sm space-y-3">
          <h3 className="text-label-md font-bold text-error uppercase tracking-wider flex items-center gap-2">
            <span className="material-symbols-outlined text-lg">warning</span>
            The Law Enforcement Bottleneck
          </h3>
          <ul className="space-y-2 text-body-sm text-on-surface-variant leading-relaxed">
            <li>• Scammers exploit non-custodial burner wallets and rapid layering across Tron, EVM, and bridges.</li>
            <li>• Manual blockchain forensics requires scarce, expensive specialized experts.</li>
            <li>• Investigations take 3 to 7 days, by which time funds have already been off-ramped to fiat.</li>
            <li>• Separate police stations in different states file duplicate FIRs against identical syndicates without knowing.</li>
          </ul>
        </div>

        <div className="p-6 rounded-xl bg-surface-container-lowest border border-secondary/40 shadow-sm space-y-3">
          <h3 className="text-label-md font-bold text-secondary uppercase tracking-wider flex items-center gap-2">
            <span className="material-symbols-outlined text-lg">bolt</span>
            The ChainNetra Breakthrough
          </h3>
          <ul className="space-y-2 text-body-sm text-on-surface-variant leading-relaxed">
            <li>• Automated First-VASP-Hit tracing algorithm explores flows in priority order by tainted value.</li>
            <li>• Reduces attribution response time from ~3 days to under 38 minutes.</li>
            <li>• 1-Click standardized freeze notice generator citing Section 91 CrPC and transaction hashes.</li>
            <li>• Tamper-evident evidence reports with SHA-256 seal and QR verification portal.</li>
          </ul>
        </div>
      </div>

      {/* 4 Pillars of Architecture */}
      <div className="p-7 rounded-xl bg-surface-container-lowest border border-outline-variant/60 shadow-sm space-y-5">
        <h2 className="text-headline-sm font-semibold text-on-surface">Core Architecture Pillars</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-4 rounded-lg bg-surface-container-low border border-outline-variant/30 space-y-2">
            <span className="material-symbols-outlined text-primary text-2xl">account_tree</span>
            <h4 className="text-label-md font-bold text-on-surface">Multi-Chain Telemetry</h4>
            <p className="text-body-sm text-on-surface-variant leading-snug">
              Covers TRON (TRC-20 USDT), Ethereum, BSC, and Polygon PoS with real-time mempool sniffing.
            </p>
          </div>

          <div className="p-4 rounded-lg bg-surface-container-low border border-outline-variant/30 space-y-2">
            <span className="material-symbols-outlined text-secondary text-2xl">hub</span>
            <h4 className="text-label-md font-bold text-on-surface">Cross-Chain Router Tracking</h4>
            <p className="text-body-sm text-on-surface-variant leading-snug">
              Correlates bridge lock-and-mint events across Stargate, Synapse, and Multichain routers.
            </p>
          </div>

          <div className="p-4 rounded-lg bg-surface-container-low border border-outline-variant/30 space-y-2">
            <span className="material-symbols-outlined text-primary text-2xl">policy</span>
            <h4 className="text-label-md font-bold text-on-surface">Statutory Compliance</h4>
            <p className="text-body-sm text-on-surface-variant leading-snug">
              Pre-formats notices under Section 91 CrPC, Section 102 CrPC, and PMLA Section 54 for immediate exchange compliance.
            </p>
          </div>

          <div className="p-4 rounded-lg bg-surface-container-low border border-outline-variant/30 space-y-2">
            <span className="material-symbols-outlined text-secondary text-2xl">verified</span>
            <h4 className="text-label-md font-bold text-on-surface">Section 65B Integrity</h4>
            <p className="text-body-sm text-on-surface-variant leading-snug">
              Tamper-evident SHA-256 hash chains guarantee chain-of-custody admissibility in Hon'ble Special Courts.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
