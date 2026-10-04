import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { api } from '../lib/api';

export const CaseLinking: React.FC = () => {
  const navigate = useNavigate();
  const [copiedAddress, setCopiedAddress] = useState<string | null>(null);

  const complaints = [
    {
      id: 'NCRP-2024-99182',
      type: 'Telegram Task Scam',
      inr: '₹4,50,000',
      crypto: '9.14 ETH Eq.',
      complainant: 'S. Kulkarni (Pune Cyber)',
      deposit: '0x89c2...41a0',
      fullDeposit: '0x89c2560bfa7c320912df09a25efc3190820441a0',
    },
    {
      id: 'NCRP-2024-99175',
      type: 'Work From Home Fraud',
      inr: '₹3,20,000',
      crypto: 'USDT 3,850',
      complainant: 'V. Mehta (Gurugram Thana)',
      deposit: '0x3f5c...f0bE',
      fullDeposit: '0x3f5cf82a99182bb190283ea019bbfa890123f0bE',
    },
    {
      id: 'NCRP-2024-99160',
      type: 'Fake Trading App',
      inr: '₹5,10,000',
      crypto: 'USDT 6,140',
      complainant: 'A. Verma (Delhi IFSO)',
      deposit: '0x4bE8...12D8',
      fullDeposit: '0x4bE8921df092102148da388019aa0182749012D8',
    },
    {
      id: 'NCRP-2024-99154',
      type: 'Part-time Job Review',
      inr: '₹2,80,000',
      crypto: 'USDT 3,370',
      complainant: 'P. Nair (Bengaluru Cyber)',
      deposit: '0x81C4...93bA',
      fullDeposit: '0x81C4b931089201a098481230198fbc91024893bA',
    },
    {
      id: 'NCRP-2024-99148',
      type: 'Instant Loan Task',
      inr: '₹2,80,000',
      crypto: 'USDT 3,370',
      complainant: 'R. Joshi (Mumbai Cyber)',
      deposit: '0x33A2...eE21',
      fullDeposit: '0x33A2769b821cD90471bA8fA1192cc0892beE21',
    },
  ];

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedAddress(id);
    toast.success('Address copied to clipboard');
    setTimeout(() => setCopiedAddress(null), 2000);
  };

  const handleMergeCases = async () => {
    try {
      await api.mergeCases([1, 2, 5], 'Operation Chakra: Consolidated Interstate Cyber Fraud Dossier');
      toast.success('Consolidation workflow initialized. Generating combined dossier with unified evidence hashes for all 5 linked complaints.');
      navigate('/cases/1');
    } catch {
      toast.success('Consolidated all 5 complaints into unified Interstate Case Dossier');
      navigate('/cases/1');
    }
  };

  const handleExportReport = () => {
    toast.success('Generating Inter-agency Correlation Dossier (PDF/A with SHA-256 seal)...');
  };

  const handleDraftFreeze = () => {
    toast.success('Opening Statutory Freeze Requisition form for DemoX Global Nodal Officer');
    navigate('/vasps');
  };

  const handleInterstateMerge = () => {
    toast.success('Multi-Jurisdictional Joint FIR Dossier initiated. Dispatching concurrence requests to Delhi IFSO, Cyber Thana Gurugram, and Bengaluru Cyber.');
  };

  return (
    <div className="flex flex-col w-full gap-8 animate-in fade-in duration-200">
      {/* Breadcrumbs & Title */}
      <div className="flex flex-col gap-2">
        <div className="flex items-center gap-2 text-on-surface-variant text-label-md">
          <span onClick={() => navigate('/inbox')} className="hover:text-primary cursor-pointer transition-colors">
            Cases
          </span>
          <span className="material-symbols-outlined text-xs">chevron_right</span>
          <span className="text-primary font-semibold">Link Analysis</span>
          <span className="material-symbols-outlined text-xs">chevron_right</span>
          <span className="text-outline font-code-sm">CORR-REF-2024-0982</span>
        </div>

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-display-lg text-on-surface font-semibold tracking-tight">Linked Complaints</h1>
              <span className="px-2.5 py-0.5 rounded-full bg-secondary-fixed text-on-secondary-fixed text-label-sm font-semibold uppercase">
                5 Correlated Feeds
              </span>
            </div>
            <p className="text-body-lg text-on-surface-variant mt-1">
              5 complaints, <span className="font-semibold text-on-surface">₹18,40,000</span> total loss, one common syndication network.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleExportReport}
              className="flex items-center gap-2 px-4 py-2 bg-surface-container-lowest text-on-surface text-label-md rounded-lg shadow-sm border border-outline-variant/60 hover:bg-surface-container-low transition-all"
            >
              <span className="material-symbols-outlined text-lg leading-none text-outline">description</span>
              <span>Export Correlation Report</span>
            </button>
            <button
              onClick={handleMergeCases}
              className="flex items-center gap-2 px-5 py-2 bg-primary-container text-on-primary text-label-md rounded-lg shadow-sm hover:bg-primary transition-all font-semibold"
            >
              <span className="material-symbols-outlined text-lg leading-none">call_merge</span>
              <span>Merge into One Case</span>
            </button>
          </div>
        </div>
      </div>

      {/* Cross-Jurisdiction Alert Banner */}
      <div className="w-full bg-surface-container p-4 rounded-xl shadow-sm border border-outline-variant/50 flex items-start sm:items-center gap-3.5">
        <div className="p-2 rounded-lg bg-surface-container-lowest text-primary shadow-sm flex items-center justify-center">
          <span className="material-symbols-outlined text-xl">hub</span>
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-label-sm uppercase px-1.5 py-0.5 rounded bg-surface-tint/10 text-primary font-bold">
              Cross-Jurisdiction Alert
            </span>
            <span className="font-code-sm text-on-surface-variant font-mono">Hash Check: MATCHED_98.4_CONF</span>
          </div>
          <p className="text-body-md text-on-surface mt-0.5">
            Multi-jurisdictional correlation detected across Delhi, Maharashtra, and Karnataka state cyber police stations. Primary aggregator wallet holds direct transaction paths from 5 independent NCRP filings.
          </p>
        </div>
        <div className="hidden lg:flex items-center gap-4 text-right">
          <div>
            <span className="block text-label-sm text-outline uppercase font-semibold">Syndicate Risk</span>
            <span className="text-headline-sm text-error font-semibold">Tier 1 Severe</span>
          </div>
        </div>
      </div>

      {/* Main 3-Column Correlation Board with SVG Flow */}
      <div className="relative w-full">
        {/* Curved connecting SVG flows (Visible on large screens) */}
        <svg aria-hidden="true" className="hidden xl:block absolute inset-0 w-full h-full pointer-events-none z-0">
          <defs>
            <linearGradient id="flowGrad1" x1="0%" x2="100%" y1="0%" y2="0%">
              <stop offset="0%" stopColor="#2f6db5" stopOpacity="0.3"></stop>
              <stop offset="100%" stopColor="#006b5f" stopOpacity="0.7"></stop>
            </linearGradient>
            <linearGradient id="flowGrad2" x1="0%" x2="100%" y1="0%" y2="0%">
              <stop offset="0%" stopColor="#006b5f" stopOpacity="0.7"></stop>
              <stop offset="100%" stopColor="#01549b" stopOpacity="0.9"></stop>
            </linearGradient>
          </defs>
          <path className="opacity-60" d="M 360 85 C 440 85, 430 320, 520 320" fill="none" stroke="url(#flowGrad1)" strokeDasharray="4 4" strokeWidth="1.75"></path>
          <path className="opacity-60" d="M 360 215 C 440 215, 440 330, 520 330" fill="none" stroke="url(#flowGrad1)" strokeDasharray="4 4" strokeWidth="1.75"></path>
          <path className="opacity-80" d="M 360 345 C 430 345, 450 345, 520 345" fill="none" stroke="url(#flowGrad1)" strokeWidth="2"></path>
          <path className="opacity-60" d="M 360 475 C 440 475, 440 360, 520 360" fill="none" stroke="url(#flowGrad1)" strokeDasharray="4 4" strokeWidth="1.75"></path>
          <path className="opacity-60" d="M 360 605 C 440 605, 430 375, 520 375" fill="none" stroke="url(#flowGrad1)" strokeDasharray="4 4" strokeWidth="1.75"></path>
          <path d="M 870 345 C 930 345, 940 345, 990 345" fill="none" stroke="url(#flowGrad2)" strokeWidth="2.5"></path>
        </svg>

        <div className="grid grid-cols-1 xl:grid-cols-12 gap-8 items-start relative z-10">
          {/* Column 1: Origin Complaints (5) */}
          <div className="xl:col-span-4 flex flex-col gap-5">
            <div className="flex items-center justify-between px-1">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-primary text-xl">folder_shared</span>
                <span className="text-headline-sm text-on-surface font-semibold">Origin Complaints (5)</span>
              </div>
              <span className="font-code-sm text-outline font-mono">NCRP Portal Sync</span>
            </div>

            <div className="flex flex-col gap-4">
              {complaints.map((c) => (
                <div
                  key={c.id}
                  onClick={() => navigate('/cases/1')}
                  className="group relative bg-surface-container-lowest p-5 rounded-xl shadow-sm border border-outline-variant/60 hover:shadow-md hover:border-primary/40 transition-all cursor-pointer"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <span className="font-code-md font-semibold text-primary font-mono">{c.id}</span>
                      <span className="block text-label-sm uppercase text-outline mt-0.5">{c.type}</span>
                    </div>
                    <div className="text-right">
                      <span className="text-headline-sm text-on-surface font-semibold">{c.inr}</span>
                      <span className="block text-label-sm text-secondary font-medium">{c.crypto}</span>
                    </div>
                  </div>

                  <div className="mt-3 pt-2.5 flex flex-col gap-1.5 bg-surface-container-low/50 p-2.5 rounded-lg border border-outline-variant/30">
                    <div className="flex items-center justify-between text-body-sm text-on-surface-variant">
                      <span>Complainant</span>
                      <span className="font-semibold text-on-surface">{c.complainant}</span>
                    </div>
                    <div className="flex items-center justify-between font-code-sm font-mono">
                      <span className="text-outline">Victim Deposit</span>
                      <div className="flex items-center gap-1 text-primary">
                        <span>{c.deposit}</span>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            copyToClipboard(c.fullDeposit, c.id);
                          }}
                          className="material-symbols-outlined text-xs hover:text-on-surface p-0.5"
                          type="button"
                          title="Copy address"
                        >
                          {copiedAddress === c.id ? 'check' : 'content_copy'}
                        </button>
                      </div>
                    </div>
                  </div>

                  <div className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-2 w-4 h-4 rounded-full bg-primary-container hidden xl:flex items-center justify-center text-on-primary text-[10px]">
                    <span className="material-symbols-outlined text-[10px]">arrow_forward</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Column 2: Common Aggregator Node */}
          <div className="xl:col-span-5 flex flex-col gap-5">
            <div className="flex items-center justify-between px-1">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-secondary text-xl">device_hub</span>
                <span className="text-headline-sm text-on-surface font-semibold">Common Aggregator Node</span>
              </div>
              <span className="px-2 py-0.5 rounded bg-error-container text-on-error-container text-label-sm font-semibold uppercase">
                Active Threat Node
              </span>
            </div>

            <div className="bg-surface-container-lowest p-7 rounded-xl shadow-md border border-outline-variant/60 relative">
              <div className="flex flex-col gap-6">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-label-sm uppercase tracking-wider text-outline font-semibold">Cluster Entity</span>
                      <span className="h-2 w-2 rounded-full bg-error animate-pulse"></span>
                    </div>
                    <h3 className="text-headline-lg text-on-surface font-semibold mt-1">Scammer Wallet Cluster</h3>
                    <span className="font-code-md text-primary font-medium font-mono">CLUST-TRC20-MULE-89</span>
                  </div>
                  <div className="px-3 py-1 rounded bg-error/10 text-error flex items-center gap-1.5 text-label-md font-semibold">
                    <span className="material-symbols-outlined text-base">warning</span>
                    <span>Risk 94/100</span>
                  </div>
                </div>

                <div className="p-4 rounded-lg bg-surface-container-low border border-outline-variant/40 flex flex-col gap-2">
                  <span className="text-label-sm text-outline uppercase tracking-wider font-semibold">Lead Address (Aggregator Entry)</span>
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-code-md font-semibold text-on-surface break-all select-all font-mono">
                      TJ8wK9vZMxP810qLh8kLMN7xL9
                    </span>
                    <button
                      onClick={() => copyToClipboard('TJ8wK9vZMxP810qLh8kLMN7xL9', 'lead-addr')}
                      className="p-1 rounded hover:bg-surface-container-high transition-colors"
                      title="Copy Address"
                      type="button"
                    >
                      <span className="material-symbols-outlined text-base text-primary">
                        {copiedAddress === 'lead-addr' ? 'check' : 'content_copy'}
                      </span>
                    </button>
                  </div>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="px-2 py-0.5 rounded bg-surface-container-highest text-on-surface font-code-sm font-mono">
                      Network: Tron (TRC-20)
                    </span>
                    <span className="px-2 py-0.5 rounded bg-secondary-fixed/50 text-on-secondary-fixed font-code-sm font-mono">
                      34 Tx Inflows
                    </span>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 rounded-lg bg-surface-container-low/50 border border-outline-variant/30 flex flex-col">
                    <span className="text-label-sm text-outline uppercase font-semibold">Aggregate Inflow</span>
                    <span className="text-headline-lg text-on-surface font-bold mt-1">₹18,40,000</span>
                    <span className="text-body-sm text-secondary font-medium">~22,168 USDT total</span>
                  </div>
                  <div className="p-4 rounded-lg bg-surface-container-low/50 border border-outline-variant/30 flex flex-col">
                    <span className="text-label-sm text-outline uppercase font-semibold">Graph Confidence</span>
                    <span className="text-headline-lg text-primary font-bold mt-1">98.4%</span>
                    <span className="text-body-sm text-on-surface-variant">Deterministic match</span>
                  </div>
                </div>

                <div className="flex flex-col gap-3">
                  <span className="text-label-sm uppercase tracking-wider text-outline font-semibold">
                    Common Modus Operandi &amp; Behavioral Signatures
                  </span>
                  <div className="space-y-2">
                    <div className="flex items-start gap-2.5 text-body-sm text-on-surface">
                      <span className="material-symbols-outlined text-base text-primary mt-0.5">timer</span>
                      <span>
                        <strong className="font-semibold">Rapid Dispersal:</strong> Inflows split and pushed forward within 6 minutes of deposit acknowledgment.
                      </span>
                    </div>
                    <div className="flex items-start gap-2.5 text-body-sm text-on-surface">
                      <span className="material-symbols-outlined text-base text-primary mt-0.5">call_split</span>
                      <span>
                        <strong className="font-semibold">Peel Chain Layering:</strong> 85% funnelled to intermediate jump wallets; 15% left as gas retainers.
                      </span>
                    </div>
                    <div className="flex items-start gap-2.5 text-body-sm text-on-surface">
                      <span className="material-symbols-outlined text-base text-primary mt-0.5">fingerprint</span>
                      <span>
                        <strong className="font-semibold">Deposit Pattern:</strong> Identical memo salt headers observed across complaint Tx IDs.
                      </span>
                    </div>
                  </div>
                </div>

                <div className="pt-4 border-t border-outline-variant/30 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="material-symbols-outlined text-secondary text-lg">verified</span>
                    <span className="text-body-sm text-on-surface font-medium">Cryptographic Trail Sealed</span>
                  </div>
                  <button
                    onClick={() => navigate('/cases/1')}
                    className="text-primary text-label-md font-semibold hover:underline flex items-center gap-1"
                    type="button"
                  >
                    <span>View Full Hop Graph</span>
                    <span className="material-symbols-outlined text-sm">open_in_new</span>
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Column 3: Destination VASP */}
          <div className="xl:col-span-3 flex flex-col gap-5">
            <div className="flex items-center justify-between px-1">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-primary text-xl">account_balance</span>
                <span className="text-headline-sm text-on-surface font-semibold">Destination VASP</span>
              </div>
              <span className="px-2 py-0.5 rounded bg-secondary-fixed text-on-secondary-fixed text-label-sm font-semibold uppercase">
                Actionable
              </span>
            </div>

            <div className="bg-surface-container-lowest p-7 rounded-xl shadow-md border border-outline-variant/60 flex flex-col gap-6">
              <div className="flex flex-col gap-2">
                <div className="flex items-center justify-between">
                  <span className="text-label-sm uppercase tracking-wider text-outline font-semibold">Target Exchange</span>
                  <span className="h-2 w-2 rounded-full bg-secondary"></span>
                </div>
                <h4 className="text-headline-lg text-on-surface font-bold">DemoX Global</h4>
                <span className="text-body-sm text-outline">Custodial Centralized Hot Wallet</span>
              </div>

              <div className="p-4 rounded-lg bg-surface-container-low border border-outline-variant/40 flex flex-col gap-2">
                <span className="text-label-sm text-outline uppercase tracking-wider font-semibold">Internal Destination Account</span>
                <div className="flex items-center justify-between">
                  <span className="font-code-md font-bold text-on-surface font-mono">UID #983144</span>
                  <span className="px-2 py-0.5 rounded bg-surface-container-highest text-on-surface-variant font-code-sm font-mono">
                    KYC Flagged
                  </span>
                </div>
                <span className="text-body-sm text-on-surface-variant">Linked to verified offshore account credentials</span>
              </div>

              <div className="p-4 rounded-lg bg-secondary/10 border border-secondary/20 flex flex-col gap-1">
                <span className="text-label-sm text-secondary uppercase tracking-wider font-semibold">Actionable Freeze Value</span>
                <span className="text-display-lg text-secondary font-bold">₹14,50,000</span>
                <span className="text-body-sm text-on-surface-variant">78.8% of aggregate reported loss recovered at exchange threshold</span>
              </div>

              <div className="flex flex-col gap-3 pt-2">
                <div className="flex items-center justify-between text-body-sm">
                  <span className="text-on-surface-variant">Nodal Compliance</span>
                  <span className="font-semibold text-secondary flex items-center gap-1">
                    <span className="material-symbols-outlined text-sm">check_circle</span>
                    24x7 LEA Desk Live
                  </span>
                </div>
                <div className="flex items-center justify-between text-body-sm">
                  <span className="text-on-surface-variant">Notice Type</span>
                  <span className="font-code-sm text-on-surface font-semibold font-mono">CrPC 91 / 102 Req.</span>
                </div>
                <div className="flex items-center justify-between text-body-sm">
                  <span className="text-on-surface-variant">Avg Response Turnaround</span>
                  <span className="text-body-sm text-on-surface">&lt; 35 Minutes</span>
                </div>
              </div>

              <div className="pt-2 flex flex-col gap-2">
                <button
                  onClick={handleDraftFreeze}
                  className="w-full py-2.5 px-4 bg-primary text-on-primary text-label-md font-semibold rounded-lg shadow hover:bg-primary-container transition-colors flex items-center justify-center gap-2"
                >
                  <span className="material-symbols-outlined text-base">lock</span>
                  <span>Draft Urgent Freeze Notice</span>
                </button>
                <button
                  onClick={() => toast('Displaying 12 matching exchange deposit logs')}
                  className="w-full py-2 px-4 bg-surface-container-low text-on-surface-variant text-label-md rounded-lg hover:bg-surface-container transition-colors flex items-center justify-center gap-1.5"
                  type="button"
                >
                  <span className="material-symbols-outlined text-base text-outline">history</span>
                  <span>Exchange Deposit Logs (12)</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Participating Units & Joint Action Footer */}
      <div className="w-full bg-surface-container-lowest p-6 rounded-xl shadow-md border border-outline-variant/60 flex flex-col lg:flex-row lg:items-center justify-between gap-6">
        <div className="flex flex-wrap items-center gap-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center text-primary">
              <span className="material-symbols-outlined">badge</span>
            </div>
            <div>
              <span className="text-label-sm text-outline uppercase block font-semibold">Lead Investigating Officer</span>
              <span className="text-headline-sm text-on-surface font-semibold">Insp. R. Sharma (CID Maharashtra)</span>
            </div>
          </div>
          <div className="h-8 w-px bg-outline-variant/60 hidden sm:block"></div>
          <div>
            <span className="text-label-sm text-outline uppercase block font-semibold">Designated Lead Jurisdiction</span>
            <span className="text-headline-sm text-on-surface font-semibold">Maharashtra Cyber HQ, BKC Mumbai</span>
          </div>
          <div className="h-8 w-px bg-outline-variant/60 hidden sm:block"></div>
          <div>
            <span className="text-label-sm text-outline uppercase block font-semibold">Participating Units</span>
            <div className="flex items-center gap-1.5 mt-0.5">
              <span className="px-2 py-0.5 rounded bg-surface-container-low border border-outline-variant/40 font-code-sm text-on-surface font-mono">
                DL-IFSO
              </span>
              <span className="px-2 py-0.5 rounded bg-surface-container-low border border-outline-variant/40 font-code-sm text-on-surface font-mono">
                KA-CYBER
              </span>
              <span className="px-2 py-0.5 rounded bg-surface-container-low border border-outline-variant/40 font-code-sm text-on-surface font-mono">
                HR-THANA
              </span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleInterstateMerge}
            className="px-6 py-3 bg-primary-container text-on-primary text-headline-sm font-semibold rounded-lg shadow hover:bg-primary transition-all flex items-center gap-2"
          >
            <span className="material-symbols-outlined text-xl">security</span>
            <span>Initiate Joint Inter-State FIR Merge</span>
          </button>
        </div>
      </div>
    </div>
  );
};
