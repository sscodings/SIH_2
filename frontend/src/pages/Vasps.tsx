import React, { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import { api } from '../lib/api';
import { useAppStore } from '../stores/useAppStore';

export const Vasps: React.FC = () => {
  const explainMode = useAppStore((s) => s.explainMode);
  const user = useAppStore((s) => s.user);

  const [vasps, setVasps] = useState<any[]>([]);
  const [freezeRequests, setFreezeRequests] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFilter, setSelectedFilter] = useState<'All' | 'Domestic' | 'Global'>('All');

  // Freeze Modal State
  const [showFreezeModal, setShowFreezeModal] = useState(false);
  const [currentStep, setCurrentStep] = useState(1);
  const [freezeTargetVasp, setFreezeTargetVasp] = useState('DemoX Global India Pvt Ltd (FIU-9021)');
  const [freezeFirRef, setFreezeFirRef] = useState('FIR No. 184/2024, Pune South Cyber PS, u/s 66D IT Act 2000 & 420 IPC');
  const [freezeUid, setFreezeUid] = useState('983144');
  const [freezeWallet, setFreezeWallet] = useState('0x3f5CE5FBFe3E9af3971dD833D26bA9b5C936f0bE');
  const [freezeAmount, setFreezeAmount] = useState('17,200 USDT (~₹14,50,000)');

  const mockVasps = [
    {
      id: 1,
      name: 'Binance Global',
      country: 'Seychelles / International',
      fiu_reg: 'FIU-IND-9021',
      nodal_officer: 'Mr. Kenneth Brown (LERS Desk)',
      email: 'legal-compliance@binance.com',
      phone: '+1-800-LERS-INTL',
      avg_resp: '4.2 hrs',
      supported_chains: 'Tron, Ethereum, BSC, Bitcoin, Polygon',
      type: 'Global'
    },
    {
      id: 2,
      name: 'WazirX (Zanmai Labs Pvt Ltd)',
      country: 'Mumbai, India',
      fiu_reg: 'FIU-IND-4091',
      nodal_officer: 'Adv. Priya Deshpande',
      email: 'nodal-officer@wazirx.com',
      phone: '+91-22-6891-4400',
      avg_resp: '1.5 hrs',
      supported_chains: 'Ethereum, Tron, Polygon, Bitcoin',
      type: 'Domestic'
    },
    {
      id: 3,
      name: 'CoinDCX (Neblio Technologies)',
      country: 'Bengaluru, India',
      fiu_reg: 'FIU-IND-1044',
      nodal_officer: 'Mr. Rajesh Menon (Legal Head)',
      email: 'legal@coindcx.com',
      phone: '+91-80-4921-8800',
      avg_resp: '1.2 hrs',
      supported_chains: 'Ethereum, Tron, BSC, Polygon',
      type: 'Domestic'
    },
    {
      id: 4,
      name: 'Bybit Fintech Limited',
      country: 'Dubai, UAE',
      fiu_reg: 'VASP-BYB-INTL',
      nodal_officer: 'Elena Rostova (Compliance)',
      email: 'lawenforcement@bybit.com',
      phone: '+971-4-892-1000',
      avg_resp: '12.0 hrs',
      supported_chains: 'Tron, Ethereum, BSC, Solana',
      type: 'Global'
    },
    {
      id: 5,
      name: 'ZebPay (Awlencan Innovations)',
      country: 'Ahmedabad, India',
      fiu_reg: 'FIU-IND-2088',
      nodal_officer: 'Adv. S. K. Nair',
      email: 'compliance@zebpay.com',
      phone: '+91-79-4001-9922',
      avg_resp: '1.8 hrs',
      supported_chains: 'Ethereum, Tron, Bitcoin',
      type: 'Domestic'
    },
    {
      id: 6,
      name: 'Bitget Limited',
      country: 'Seychelles',
      fiu_reg: 'BG-LERS-7712',
      nodal_officer: 'Marcus Wong (Regulatory Desk)',
      email: 'le-inquiry@bitget.com',
      phone: '+248-422-9100',
      avg_resp: '18.5 hrs',
      supported_chains: 'Tron, Ethereum, BSC, Arbitrum',
      type: 'Global'
    }
  ];

  const loadData = async () => {
    try {
      setLoading(true);
      const [vRes, fRes] = await Promise.all([
        api.getVasps(),
        api.getFreezeRequests()
      ]);
      setVasps(vRes.vasps?.length ? vRes.vasps : mockVasps);
      setFreezeRequests(fRes.freeze_requests || []);
    } catch {
      setVasps(mockVasps);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleOpenFreeze = (vasp: any) => {
    setFreezeTargetVasp(`${vasp.name} (${vasp.fiu_reg})`);
    setShowFreezeModal(true);
    setCurrentStep(1);
  };

  const filteredVasps = vasps.filter((v) => {
    const q = searchQuery.toLowerCase();
    const matchSearch = 
      !q || 
      v.name?.toLowerCase().includes(q) || 
      v.fiu_reg?.toLowerCase().includes(q) ||
      v.country?.toLowerCase().includes(q) ||
      v.nodal_officer?.toLowerCase().includes(q);

    const matchType = 
      selectedFilter === 'All' || 
      v.type === selectedFilter;

    return matchSearch && matchType;
  });

  return (
    <div className="flex flex-col w-full gap-8 animate-in fade-in duration-150">
      {/* Top Identity & Action Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 pb-2">
        <div className="space-y-2 max-w-3xl">
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center px-2 py-0.5 rounded bg-surface-container-high text-primary font-label-sm text-[10px] uppercase tracking-wider font-semibold">
              LEAF Legal Coordination
            </span>
            <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded bg-surface-container-low text-secondary font-label-sm text-[10px] font-semibold">
              <span className="w-1.5 h-1.5 rounded-full bg-secondary"></span>
              FIU-IND Verified Registry
            </span>
          </div>
          <h1 className="font-display-lg text-[28px] font-bold text-on-surface tracking-tight">
            VASP &amp; Exchange Directory
          </h1>
          <p className="font-body-lg text-xs text-on-surface-variant leading-relaxed">
            Registered Virtual Asset Service Providers under FIU-IND and international law enforcement cooperation channels. Facilitates evidentiary requisition under Section 91 CrPC and PMLA disclosures.
          </p>
        </div>

        <div className="flex items-center gap-3 shrink-0 flex-wrap">
          <button
            onClick={() => {
              toast.success('Viewing 19 active statutory requisitions audit trail');
            }}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-surface-container-lowest text-on-surface hover:bg-surface-container text-xs font-semibold transition-colors shadow-sm border border-surface-container"
            type="button"
          >
            <span className="material-symbols-outlined text-[18px] text-tertiary">history_edu</span>
            <span>Requisition Audit Log</span>
          </button>

          <button
            onClick={() => {
              setFreezeTargetVasp('DemoX Global India Pvt Ltd (FIU-9021)');
              setShowFreezeModal(true);
              setCurrentStep(1);
            }}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-primary-container hover:bg-primary text-on-primary text-xs font-semibold transition-all shadow-sm active:scale-[0.99]"
            type="button"
          >
            <span className="material-symbols-outlined text-[18px]">add_circle</span>
            <span>Draft Section 91 CrPC</span>
          </button>
        </div>
      </div>

      {/* Live Counter Banner (4 Cards) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 p-5 rounded-xl bg-surface-container-lowest border border-surface-container shadow-sm">
        <div className="flex items-center gap-4 px-2">
          <div className="w-10 h-10 rounded-lg bg-surface-container flex items-center justify-center text-primary">
            <span className="material-symbols-outlined text-xl">account_balance</span>
          </div>
          <div>
            <div className="text-xl font-bold text-on-surface">{vasps.length || 28}</div>
            <div className="text-[11px] text-outline">Registered VASPs</div>
          </div>
        </div>

        <div className="flex items-center gap-4 px-2">
          <div className="w-10 h-10 rounded-lg bg-surface-container flex items-center justify-center text-secondary">
            <span className="material-symbols-outlined text-xl">gavel</span>
          </div>
          <div>
            <div className="text-xl font-bold text-on-surface">19</div>
            <div className="text-[11px] text-secondary font-semibold">Active Sec 91 Orders</div>
          </div>
        </div>

        <div className="flex items-center gap-4 px-2">
          <div className="w-10 h-10 rounded-lg bg-surface-container flex items-center justify-center text-tertiary">
            <span className="material-symbols-outlined text-xl">speed</span>
          </div>
          <div>
            <div className="text-xl font-bold text-on-surface">3.8 hrs</div>
            <div className="text-[11px] text-outline">Avg Turnaround SLA</div>
          </div>
        </div>

        <div className="flex items-center gap-4 px-2">
          <div className="w-10 h-10 rounded-lg bg-secondary-container/40 flex items-center justify-center text-secondary">
            <span className="material-symbols-outlined text-xl">verified_user</span>
          </div>
          <div>
            <div className="text-xl font-bold text-secondary">100%</div>
            <div className="text-[11px] text-secondary font-semibold">Nodal Channels Verified</div>
          </div>
        </div>
      </div>

      {/* Search & Filter Toolbar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="relative w-full sm:w-96">
          <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline text-[18px]">
            search
          </span>
          <input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full h-11 pl-9 pr-4 bg-surface-container-lowest text-xs text-on-surface rounded-xl border border-surface-container focus:outline-none focus:ring-1 focus:ring-primary shadow-xs"
            placeholder="Search VASP name, FIU registration, or Nodal Officer..."
            type="text"
          />
        </div>

        <div className="inline-flex p-1 bg-surface-container rounded-xl shadow-xs self-start sm:self-auto">
          {(['All', 'Domestic', 'Global'] as const).map((filter) => (
            <button
              key={filter}
              onClick={() => setSelectedFilter(filter)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                selectedFilter === filter
                  ? 'bg-surface-container-lowest text-primary shadow-xs'
                  : 'text-on-surface-variant hover:text-on-surface'
              }`}
            >
              {filter === 'All' ? 'All Providers' : filter === 'Domestic' ? 'FIU-IND Domestic' : 'Global Exchanges'}
            </button>
          ))}
        </div>
      </div>

      {/* VASP Grid Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredVasps.map((v) => (
          <div 
            key={v.id} 
            className="p-6 rounded-xl bg-surface-container-lowest border border-surface-container shadow-sm flex flex-col justify-between hover:shadow-md transition-shadow space-y-4"
          >
            <div>
              <div className="flex items-start justify-between gap-2 mb-2">
                <div>
                  <h3 className="text-base font-bold text-on-surface">{v.name}</h3>
                  <span className="text-[11px] text-outline font-medium">{v.country}</span>
                </div>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold bg-secondary-container/40 text-secondary border border-secondary-container">
                  {v.fiu_reg}
                </span>
              </div>

              <div className="mt-4 pt-3 border-t border-surface-container space-y-2 text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-outline">Nodal Officer:</span>
                  <span className="font-semibold text-on-surface">{v.nodal_officer}</span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-outline">Direct Contact:</span>
                  <a href={`mailto:${v.email}`} className="font-mono text-primary hover:underline text-[11px]">
                    {v.email}
                  </a>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-outline">Avg Turnaround:</span>
                  <span className="font-semibold text-secondary">{v.avg_resp}</span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-outline">Chains:</span>
                  <span className="font-mono text-[11px] text-on-surface-variant truncate max-w-[150px]">{v.supported_chains}</span>
                </div>
              </div>
            </div>

            <div className="pt-3 border-t border-surface-container flex items-center justify-between gap-2">
              <button
                onClick={() => {
                  navigator.clipboard.writeText(v.email);
                  toast.success(`Copied Nodal Email: ${v.email}`);
                }}
                className="text-xs text-on-surface-variant hover:text-on-surface p-1.5 rounded hover:bg-surface-container-low transition-colors"
                title="Copy Contact"
              >
                <span className="material-symbols-outlined text-[16px]">content_copy</span>
              </button>

              <button
                onClick={() => handleOpenFreeze(v)}
                className="flex-1 px-3 py-2 bg-primary-container hover:bg-primary text-on-primary text-xs font-semibold rounded-lg transition-colors flex items-center justify-center gap-1.5 shadow-xs"
              >
                <span className="material-symbols-outlined text-[15px]">gavel</span>
                <span>Draft Sec 91 CrPC</span>
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* SECTION 91 CRPC STATUTORY FREEZE MODAL (Matches chainnetra_freeze_request) */}
      {showFreezeModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-inverse-surface/50 backdrop-blur-xs overflow-y-auto">
          <div className="bg-surface-container-lowest rounded-2xl max-w-5xl w-full p-8 shadow-2xl border border-surface-container space-y-6 my-8 animate-in fade-in zoom-in-95">
            {/* Modal Header */}
            <div className="flex items-center justify-between pb-4 border-b border-surface-container">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-[10px] font-bold text-error uppercase tracking-wider bg-error-container/40 px-2 py-0.5 rounded">
                    URGENT STATUTORY REQUISITION
                  </span>
                  <span className="text-xs text-outline">•</span>
                  <span className="font-mono text-xs text-outline">SEC. 91 &amp; 102 CR.P.C.</span>
                </div>
                <h2 className="text-xl font-bold text-on-surface">
                  Draft Statutory Freeze Notice
                </h2>
              </div>
              <button
                onClick={() => setShowFreezeModal(false)}
                className="text-on-surface-variant hover:text-on-surface p-1.5 rounded-lg"
              >
                <span className="material-symbols-outlined text-[22px]">close</span>
              </button>
            </div>

            {/* 4-Step Tracker */}
            <div className="grid grid-cols-4 gap-2 p-3 bg-surface-container-low rounded-xl">
              {[
                { step: 1, title: 'Draft Notice', desc: 'Investigating Officer' },
                { step: 2, title: 'Supervisor Review', desc: 'ACP / DySP Cyber' },
                { step: 3, title: 'Dispatched to VASP', desc: 'API / Encrypted Nodal' },
                { step: 4, title: 'Frozen & Confirmed', desc: 'Lien Receipt Seal' },
              ].map((s) => (
                <div 
                  key={s.step} 
                  onClick={() => setCurrentStep(s.step)}
                  className={`flex items-center gap-3 p-2 rounded-lg cursor-pointer transition-colors ${
                    currentStep === s.step 
                      ? 'bg-surface-container-lowest shadow-xs text-primary' 
                      : currentStep > s.step
                      ? 'text-secondary'
                      : 'text-outline opacity-60'
                  }`}
                >
                  <div className={`w-7 h-7 rounded-full flex items-center justify-center font-bold text-xs ${
                    currentStep === s.step 
                      ? 'bg-primary text-on-primary' 
                      : currentStep > s.step
                      ? 'bg-secondary text-on-secondary'
                      : 'bg-surface-container text-outline'
                  }`}>
                    {s.step}
                  </div>
                  <div className="hidden sm:flex flex-col min-w-0">
                    <span className="font-bold text-xs truncate">{s.title}</span>
                    <span className="text-[10px] text-outline truncate">{s.desc}</span>
                  </div>
                </div>
              ))}
            </div>

            {/* Split Form & Letter Preview Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
              {/* Left Column: Form Parameters (5 cols) */}
              <div className="lg:col-span-5 space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-on-surface mb-1">Target Registered VASP</label>
                  <input
                    value={freezeTargetVasp}
                    onChange={(e) => setFreezeTargetVasp(e.target.value)}
                    className="w-full h-10 px-3 bg-surface-container-low rounded-lg text-xs font-semibold text-on-surface border border-surface-container"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-on-surface mb-1">FIR / Incident Attribution</label>
                  <input
                    value={freezeFirRef}
                    onChange={(e) => setFreezeFirRef(e.target.value)}
                    className="w-full h-10 px-3 bg-surface-container-low rounded-lg text-xs text-on-surface border border-surface-container font-mono"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-semibold text-on-surface mb-1">Suspect VASP UID</label>
                    <input
                      value={freezeUid}
                      onChange={(e) => setFreezeUid(e.target.value)}
                      className="w-full h-10 px-3 bg-surface-container-low rounded-lg text-xs text-on-surface border border-surface-container font-mono"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-on-surface mb-1">Restraint Amount</label>
                    <input
                      value={freezeAmount}
                      onChange={(e) => setFreezeAmount(e.target.value)}
                      className="w-full h-10 px-3 bg-surface-container-low rounded-lg text-xs text-on-surface border border-surface-container font-mono"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-on-surface mb-1">Deposit Hot Wallet Address</label>
                  <input
                    value={freezeWallet}
                    onChange={(e) => setFreezeWallet(e.target.value)}
                    className="w-full h-10 px-3 bg-surface-container-low rounded-lg text-xs font-mono text-on-surface border border-surface-container"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-on-surface mb-1">Statutory Grounds</label>
                  <div className="p-3 bg-surface-container-low rounded-lg text-[11px] text-on-surface-variant space-y-1">
                    <p>&bull; Criminal breach of trust &amp; cheating (Sec 420 IPC / BNS 318)</p>
                    <p>&bull; Identity fraud &amp; impersonation (Sec 66D IT Act, 2000)</p>
                    <p>&bull; Emergency asset preservation pursuant to Sec 91 &amp; 102 Cr.P.C.</p>
                  </div>
                </div>
              </div>

              {/* Right Column: Live Letter Preview (7 cols) */}
              <div className="lg:col-span-7 bg-surface-bright border border-surface-container-high rounded-xl p-6 shadow-inner space-y-4 font-serif text-xs text-on-surface">
                <div className="text-center pb-3 border-b border-surface-container">
                  <div className="font-bold uppercase tracking-wider text-xs font-sans text-primary">Office of the Investigating Officer</div>
                  <div className="text-[11px] font-sans font-semibold">CYBER CRIME POLICE STATION, SPECIAL CELL</div>
                  <div className="text-[10px] text-outline font-sans">STATE POLICE COMMAND • CRIME INVESTIGATION DEPARTMENT</div>
                </div>

                <div className="space-y-3 font-sans leading-relaxed text-xs">
                  <div className="flex justify-between text-[11px]">
                    <span>Dispatch No: <strong>CYB/LE-91/2024/0944</strong></span>
                    <span>Date: <strong>24 Oct 2024</strong></span>
                  </div>

                  <div>
                    <strong>To,</strong><br />
                    The Nodal Legal Compliance Officer,<br />
                    {freezeTargetVasp}
                  </div>

                  <div className="font-bold underline text-center py-1">
                    SUBJECT: FORMAL REQUISITION UNDER SECTION 91 &amp; 102 OF CODE OF CRIMINAL PROCEDURE (Cr.P.C.) TO RESTRAIN ASSETS AND PRESERVE KYC DATA
                  </div>

                  <p>
                    Whereas investigation into <strong>{freezeFirRef}</strong> reveals that stolen proceeds of cyber fraud totaling <strong>{freezeAmount}</strong> have been traced and deposited into your exchange custody at deposit account <strong>UID: {freezeUid}</strong> / deposit address <strong>{freezeWallet}</strong>.
                  </p>

                  <p>
                    You are hereby commanded to immediately place an administrative lien and debit freeze on all accounts associated with UID #{freezeUid}, suspend outbound withdrawals, and furnish complete KYC, IP logs, and withdrawal transaction hashes within 24 hours.
                  </p>

                  <div className="pt-4 flex justify-between items-end font-sans">
                    <div className="border border-outline/30 px-3 py-1.5 rounded text-[10px] text-outline font-mono">
                      [SEAL OF CYBER POLICE STATION]<br />
                      TAMPER HASH: 0x89e2...c419
                    </div>
                    <div className="text-right">
                      <strong>(Insp. R. Sharma)</strong><br />
                      <span className="text-[10px] text-outline">Investigating Officer<br />Cyber Crime Unit</span>
                    </div>
                  </div>
                </div>

                <div className="pt-3 border-t border-surface-container flex items-center justify-between gap-3 font-sans">
                  <button
                    type="button"
                    onClick={() => {
                      navigator.clipboard.writeText(
                        `FORMAL NOTICE UNDER SECTION 91 Cr.P.C.\nCase: ${freezeFirRef}\nTarget VASP: ${freezeTargetVasp}\nUID: ${freezeUid}\nWallet: ${freezeWallet}\nAmount: ${freezeAmount}`
                      );
                      toast.success('Notice copied to clipboard');
                    }}
                    className="px-3 py-1.5 rounded bg-surface-container text-xs font-semibold text-on-surface hover:bg-surface-container-high transition-colors"
                  >
                    Copy Text
                  </button>

                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => window.print()}
                      className="px-3 py-1.5 rounded bg-surface-container-low text-xs font-semibold text-on-surface hover:bg-surface-container transition-colors border border-surface-container"
                    >
                      Print PDF
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        toast.success('Transmitted to VASP Legal API Gateway. Lien Ref #LN-8831 issued.');
                        setCurrentStep(4);
                        setTimeout(() => setShowFreezeModal(false), 1200);
                      }}
                      className="px-4 py-1.5 rounded bg-primary text-xs font-semibold text-on-primary hover:bg-primary-container transition-all shadow-xs"
                    >
                      Transmit via Encrypted API
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
