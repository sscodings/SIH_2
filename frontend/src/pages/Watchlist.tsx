import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { api } from '../lib/api';
import { useAppStore } from '../stores/useAppStore';

export const Watchlist: React.FC = () => {
  const navigate = useNavigate();
  const clearUnreadAlerts = useAppStore((s) => s.clearUnreadAlerts);

  const [activeTab, setActiveTab] = useState<'all' | 'active' | 'frozen'>('all');
  const [filterText, setFilterText] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [selectedChain, setSelectedChain] = useState<'tron' | 'ethereum' | 'bsc'>('tron');
  const [targetAddress, setTargetAddress] = useState('');
  const [firNumber, setFirNumber] = useState('');
  const [classification, setClassification] = useState('Primary Scammer Collector');
  const [fiuPrompt, setFiuPrompt] = useState(true);
  const [simulating, setSimulating] = useState(false);

  // Initial monitored wallets
  const initialWallets = [
    {
      id: 1,
      address: 'TJ8wK9vZM2yKk7W8dE99aXMN7xL9',
      displayAddress: 'TJ8wK9vZM...N7xL9',
      chain: 'Tron (TRC-20)',
      chainColor: 'bg-error',
      role: 'Primary Scammer Collector',
      fir: 'Telegram Task Scam #CN-0944',
      lastActivity: 'Outflow $17,320',
      lastTime: '12 min ago',
      activityType: 'error',
      risk: 'High Risk',
      riskType: 'error',
      status: 'active',
    },
    {
      id: 2,
      address: '0x3f5cf82a99182bb190283ea019bbfa890123f0bE',
      displayAddress: '0x3f5c...f0bE',
      chain: 'Ethereum',
      chainColor: 'bg-primary',
      role: 'Deposit Aggregator Node',
      fir: 'Work From Home #CN-0918',
      lastActivity: 'Inflow $45,000 USDT',
      lastTime: '34 min ago',
      activityType: 'success',
      risk: 'High Risk',
      riskType: 'error',
      status: 'active',
    },
    {
      id: 3,
      address: '0x4bE8921df092102148da388019aa0182749012D8',
      displayAddress: '0x4bE8...12D8',
      chain: 'BNB Smart Chain',
      chainColor: 'bg-secondary',
      role: 'Peel Chain Splitter',
      fir: 'Fake Trading App #CN-0960',
      lastActivity: 'Split $8,400 BSC-USD',
      lastTime: '2 hours ago',
      activityType: 'neutral',
      risk: 'Under Surveillance',
      riskType: 'tertiary',
      status: 'active',
    },
    {
      id: 4,
      address: 'TMvKq11039daLL9128aaQpZmB9311244p0X',
      displayAddress: 'TMvKq...4p0X',
      chain: 'Tron (TRC-20)',
      chainColor: 'bg-error',
      role: 'Extortion Collector',
      fir: 'Sextortion FIR #112',
      lastActivity: 'Inactive',
      lastTime: '5 hours ago',
      activityType: 'dormant',
      risk: 'Dormant',
      riskType: 'dormant',
      status: 'frozen',
    },
    {
      id: 5,
      address: '0x33A769b821cD90471bA8fA1192cc0892beE21',
      displayAddress: '0x33A...eE21',
      chain: 'Ethereum',
      chainColor: 'bg-primary',
      role: 'Cross-chain Bridge Receiver',
      fir: 'Stargate Hop #CN-0935',
      lastActivity: 'Bridge Hop (Arbitrum)',
      lastTime: '1 day ago',
      activityType: 'neutral',
      risk: 'Exchange Identified',
      riskType: 'identified',
      status: 'frozen',
    },
  ];

  const [wallets, setWallets] = useState(initialWallets);

  useEffect(() => {
    clearUnreadAlerts();
    api.getWatchlist().then((res) => {
      if (res && res.items && res.items.length > 0) {
        // Merge with initial wallets
        const mapped = res.items.map((it: any) => ({
          id: it.id,
          address: it.address,
          displayAddress: `${it.address.slice(0, 8)}...${it.address.slice(-5)}`,
          chain: it.chain === 'tron' ? 'Tron (TRC-20)' : it.chain === 'ethereum' ? 'Ethereum' : 'BNB Smart Chain',
          chainColor: it.chain === 'tron' ? 'bg-error' : it.chain === 'ethereum' ? 'bg-primary' : 'bg-secondary',
          role: it.label || 'Monitored Target',
          fir: it.reason || 'Surveillance Target',
          lastActivity: 'Live Monitoring',
          lastTime: 'Just now',
          activityType: 'neutral',
          risk: 'High Risk',
          riskType: 'error',
          status: 'active',
        }));
        setWallets((prev) => {
          const ids = new Set(mapped.map((m: any) => m.address));
          return [...mapped, ...prev.filter((p) => !ids.has(p.address))];
        });
      }
    }).catch(() => {});
  }, []);

  const filteredWallets = wallets.filter((w) => {
    if (activeTab === 'active' && w.status !== 'active') return false;
    if (activeTab === 'frozen' && w.status !== 'frozen') return false;
    if (filterText) {
      const q = filterText.toLowerCase();
      return (
        w.address.toLowerCase().includes(q) ||
        w.role.toLowerCase().includes(q) ||
        w.fir.toLowerCase().includes(q) ||
        w.chain.toLowerCase().includes(q)
      );
    }
    return true;
  });

  const handleSimulateMovement = async () => {
    setSimulating(true);
    try {
      const res = await api.simulateMovement();
      toast.error(
        `CRITICAL ALERT: Target moved $${res.alert?.amount_usd?.toLocaleString() || '17,320'} to new exchange deposit!`,
        { duration: 5000 }
      );
    } catch {
      toast.error('SURVEILLANCE HIT: Target TJ8wK9vZM... moved $17,320 USDT towards DemoX Global hot wallet.');
    } finally {
      setSimulating(false);
    }
  };

  const handleAddSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!targetAddress) {
      toast.error('Please enter a target address');
      return;
    }

    try {
      await api.addToWatchlist({
        address: targetAddress.trim(),
        chain: selectedChain,
        label: classification,
        reason: firNumber || 'Surveillance Target',
      });
    } catch {}

    const newEntry = {
      id: Date.now(),
      address: targetAddress,
      displayAddress: `${targetAddress.slice(0, 8)}...${targetAddress.slice(-5)}`,
      chain: selectedChain === 'tron' ? 'Tron (TRC-20)' : selectedChain === 'ethereum' ? 'Ethereum' : 'BNB Smart Chain',
      chainColor: selectedChain === 'tron' ? 'bg-error' : selectedChain === 'ethereum' ? 'bg-primary' : 'bg-secondary',
      role: classification,
      fir: firNumber || 'FIR Not Specified',
      lastActivity: 'Monitoring Initialized',
      lastTime: 'Just now',
      activityType: 'neutral',
      risk: 'Under Surveillance',
      riskType: 'tertiary',
      status: 'active',
    };

    setWallets([newEntry, ...wallets]);
    setShowAddModal(false);
    setTargetAddress('');
    setFirNumber('');
    toast.success('Address placed on 24/7 mempool & block surveillance!');
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success('Address copied to clipboard');
  };

  return (
    <div className="flex flex-col w-full pb-16 animate-in fade-in duration-200">
      {/* Case Audit Header & Global Breadcrumbs */}
      <div className="flex items-center justify-between mb-8 bg-surface-container-lowest px-6 py-3.5 rounded-xl shadow-sm border border-outline-variant/60">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-primary text-xl">security</span>
            <span className="text-headline-sm text-on-surface font-semibold tracking-tight">LEA Surveillance Stream</span>
          </div>
          <div className="h-4 w-px bg-outline-variant/60"></div>
          <span className="font-code-sm text-on-surface-variant flex items-center gap-1.5 font-mono">
            <span className="inline-block w-2 h-2 rounded-full bg-secondary"></span>
            NODE: DL-POLICE-FORENSIC-04
          </span>
          <span className="font-code-sm text-outline font-mono hidden sm:inline">ENC: AES-256 GCM</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-label-sm text-on-surface-variant uppercase tracking-wider bg-surface-container px-2.5 py-1 rounded font-semibold hidden md:inline">
            EVIDENTIARY AUDIT LOG #EV-2024-8891
          </span>
          <button
            onClick={() => toast.success('Exporting full cryptographically sealed surveillance audit log')}
            className="flex items-center gap-1.5 px-3 py-1 text-label-md text-primary hover:bg-surface-container-low rounded transition-colors font-semibold"
          >
            <span className="material-symbols-outlined text-sm">print</span> Export Trail
          </button>
        </div>
      </div>

      {/* Page Header Area */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-8">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-label-sm text-primary tracking-widest uppercase font-semibold">Target Surveillance Hub</span>
            <span className="text-outline text-xs">•</span>
            <span className="font-code-sm text-outline font-mono">Updated real-time via RPC Webhooks</span>
          </div>
          <h1 className="text-headline-lg text-on-surface font-bold tracking-tight">Watchlist &amp; Real-Time Alerts</h1>
          <p className="text-body-md text-on-surface-variant mt-1 max-w-2xl">
            Monitored scammer hot wallets and automated movement triggers across Ethereum, Tron, and BNB Smart Chain networks.
          </p>
        </div>

        {/* Actions & Filter Segment */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Status Segmented Filter */}
          <div className="inline-flex p-1 bg-surface-container rounded-lg border border-outline-variant/50">
            <button
              onClick={() => setActiveTab('all')}
              className={`px-3.5 py-1.5 text-label-md rounded transition-all font-semibold ${
                activeTab === 'all'
                  ? 'bg-surface-container-lowest text-primary shadow-sm'
                  : 'text-on-surface-variant hover:text-on-surface'
              }`}
            >
              All Watched ({wallets.length})
            </button>
            <button
              onClick={() => setActiveTab('active')}
              className={`px-3.5 py-1.5 text-label-md rounded transition-all font-semibold ${
                activeTab === 'active'
                  ? 'bg-surface-container-lowest text-primary shadow-sm'
                  : 'text-on-surface-variant hover:text-on-surface'
              }`}
            >
              Active ({wallets.filter((w) => w.status === 'active').length})
            </button>
            <button
              onClick={() => setActiveTab('frozen')}
              className={`px-3.5 py-1.5 text-label-md rounded transition-all font-semibold ${
                activeTab === 'frozen'
                  ? 'bg-surface-container-lowest text-primary shadow-sm'
                  : 'text-on-surface-variant hover:text-on-surface'
              }`}
            >
              Frozen ({wallets.filter((w) => w.status === 'frozen').length})
            </button>
          </div>

          {/* Simulate Action */}
          <button
            onClick={handleSimulateMovement}
            disabled={simulating}
            className="inline-flex items-center gap-1.5 px-3 py-2 bg-surface-container text-on-surface text-label-md font-semibold rounded-lg border border-outline-variant/60 hover:bg-surface-container-high transition-colors"
            title="Simulate live transaction hit"
          >
            <span className="material-symbols-outlined text-base text-error">sensors</span>
            <span>{simulating ? 'Simulating...' : 'Simulate Outflow'}</span>
          </button>

          {/* Add Wallet Primary Action */}
          <button
            onClick={() => setShowAddModal(true)}
            className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-on-primary text-label-md font-semibold rounded-lg shadow-sm hover:bg-primary-container active:scale-[0.99] transition-all"
          >
            <span className="material-symbols-outlined text-lg leading-none">add</span>
            <span>Add Wallet to Watchlist</span>
          </button>
        </div>
      </div>

      {/* Key Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-surface-container-lowest p-5 rounded-xl shadow-sm border border-outline-variant/60 flex items-center justify-between">
          <div>
            <p className="text-label-sm text-outline uppercase tracking-wider font-semibold">Total Capital Monitored</p>
            <p className="text-headline-lg text-on-surface font-semibold mt-1">$2,419,850</p>
            <div className="flex items-center gap-1.5 mt-2">
              <span className="text-secondary text-xs font-semibold flex items-center">
                <span className="material-symbols-outlined text-xs">arrow_upward</span> +$17.3k
              </span>
              <span className="text-body-sm text-outline">last 1 hr</span>
            </div>
          </div>
          <div className="w-10 h-10 rounded-lg bg-surface-container-low flex items-center justify-center text-primary">
            <span className="material-symbols-outlined text-xl">account_balance_wallet</span>
          </div>
        </div>

        <div className="bg-surface-container-lowest p-5 rounded-xl shadow-sm border border-outline-variant/60 flex items-center justify-between">
          <div>
            <p className="text-label-sm text-outline uppercase tracking-wider font-semibold">Active Critical Triggers</p>
            <p className="text-headline-lg text-error font-semibold mt-1">4 Unread</p>
            <div className="flex items-center gap-1.5 mt-2">
              <span className="inline-block w-2 h-2 rounded-full bg-error animate-pulse"></span>
              <span className="text-body-sm text-on-surface-variant font-medium">Immediate action req.</span>
            </div>
          </div>
          <div className="w-10 h-10 rounded-lg bg-error-container/40 flex items-center justify-center text-error">
            <span className="material-symbols-outlined text-xl">crisis_alert</span>
          </div>
        </div>

        <div className="bg-surface-container-lowest p-5 rounded-xl shadow-sm border border-outline-variant/60 flex items-center justify-between">
          <div>
            <p className="text-label-sm text-outline uppercase tracking-wider font-semibold">Exchange Interceptions</p>
            <p className="text-headline-lg text-on-surface font-semibold mt-1">3 VASPs</p>
            <div className="flex items-center gap-1.5 mt-2">
              <span className="text-label-sm text-secondary bg-secondary-container/40 px-2 py-0.5 rounded font-semibold">
                DemoX, Bybit, Binance
              </span>
            </div>
          </div>
          <div className="w-10 h-10 rounded-lg bg-secondary-container/30 flex items-center justify-center text-secondary">
            <span className="material-symbols-outlined text-xl">hub</span>
          </div>
        </div>

        <div className="bg-surface-container-lowest p-5 rounded-xl shadow-sm border border-outline-variant/60 flex items-center justify-between">
          <div>
            <p className="text-label-sm text-outline uppercase tracking-wider font-semibold">Sec 91 Freeze Requests</p>
            <p className="text-headline-lg text-on-surface font-semibold mt-1">8 Dispatched</p>
            <div className="flex items-center gap-1.5 mt-2">
              <span className="text-body-sm text-outline">6 Ack • 2 Pending</span>
            </div>
          </div>
          <div className="w-10 h-10 rounded-lg bg-surface-container-low flex items-center justify-center text-tertiary">
            <span className="material-symbols-outlined text-xl">gavel</span>
          </div>
        </div>
      </div>

      {/* Main Content Layout (65% Left, 35% Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* LEFT SECTION (Table/Cards) */}
        <div className="lg:col-span-8 flex flex-col gap-4">
          <div className="bg-surface-container-lowest rounded-xl shadow-sm border border-outline-variant/60 overflow-hidden">
            {/* Table Control Toolbar */}
            <div className="p-6 pb-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-surface-container-lowest border-b border-outline-variant/30">
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-headline-md text-on-surface font-semibold">Monitored Wallets</h2>
                  <span className="text-label-sm px-2.5 py-0.5 rounded-full bg-primary-fixed text-on-primary-fixed font-bold">
                    {filteredWallets.length} Targets
                  </span>
                </div>
                <p className="text-body-sm text-outline mt-0.5">High-frequency surveillance synced with node clusters</p>
              </div>
              <div className="flex items-center gap-2.5">
                <div className="relative">
                  <span className="material-symbols-outlined absolute left-2.5 top-1/2 -translate-y-1/2 text-outline text-base pointer-events-none">
                    filter_list
                  </span>
                  <input
                    value={filterText}
                    onChange={(e) => setFilterText(e.target.value)}
                    className="pl-8 pr-3 py-1.5 text-body-sm bg-surface-container-low text-on-surface placeholder:text-outline rounded-lg focus:outline-none focus:bg-surface-container w-52 transition-colors border border-outline-variant/40"
                    placeholder="Filter reason, tag or hash..."
                    type="text"
                  />
                </div>
                <button
                  onClick={() => toast.success('Surveillance ledger reloaded')}
                  className="p-2 text-on-surface-variant hover:text-on-surface hover:bg-surface-container-low rounded-lg transition-colors border border-outline-variant/40"
                  title="Reload Ledger"
                >
                  <span className="material-symbols-outlined text-lg leading-none">refresh</span>
                </button>
              </div>
            </div>

            {/* Ledger Table */}
            <div className="w-full overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-surface-container-low/60 text-outline text-label-sm tracking-wider uppercase">
                    <th className="py-3.5 pl-6 pr-3">Target Address &amp; Chain</th>
                    <th className="py-3.5 px-3">Classification &amp; FIR Case</th>
                    <th className="py-3.5 px-3">Last On-Chain Activity</th>
                    <th className="py-3.5 px-3">Surveillance Risk</th>
                    <th className="py-3.5 pr-6 pl-3 text-right">Forensic Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-outline-variant/20 text-on-surface">
                  {filteredWallets.map((w) => (
                    <tr key={w.id} className="h-16 hover:bg-surface-container-low/40 transition-colors group">
                      <td className="py-3 pl-6 pr-3 align-middle">
                        <div className="flex flex-col">
                          <div className="flex items-center gap-1.5">
                            <span className="font-code-md font-semibold text-on-surface font-mono">{w.displayAddress}</span>
                            <button
                              onClick={() => copyToClipboard(w.address)}
                              className="text-outline hover:text-primary transition-colors"
                              title="Copy Address"
                            >
                              <span className="material-symbols-outlined text-sm leading-none">content_copy</span>
                            </button>
                          </div>
                          <div className="flex items-center gap-1 mt-0.5">
                            <span className={`inline-block w-1.5 h-1.5 rounded-full ${w.chainColor}`}></span>
                            <span className="text-label-sm text-outline">{w.chain}</span>
                          </div>
                        </div>
                      </td>

                      <td className="py-3 px-3 align-middle">
                        <div className="flex flex-col max-w-xs">
                          <span className="text-body-md font-medium text-on-surface line-clamp-1">{w.role}</span>
                          <span
                            onClick={() => navigate('/cases/1')}
                            className="font-code-sm text-primary hover:underline cursor-pointer font-mono"
                          >
                            {w.fir}
                          </span>
                        </div>
                      </td>

                      <td className="py-3 px-3 align-middle">
                        <div className="flex flex-col">
                          <span
                            className={`text-body-md font-medium ${
                              w.activityType === 'error'
                                ? 'text-error'
                                : w.activityType === 'success'
                                ? 'text-secondary font-semibold'
                                : w.activityType === 'dormant'
                                ? 'text-outline'
                                : 'text-on-surface'
                            }`}
                          >
                            {w.lastActivity}
                          </span>
                          <span className="text-body-sm text-outline">{w.lastTime}</span>
                        </div>
                      </td>

                      <td className="py-3 px-3 align-middle">
                        {w.riskType === 'error' && (
                          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-label-sm bg-error-container text-on-error-container font-semibold">
                            <span className="material-symbols-outlined text-xs leading-none">warning</span>
                            High Risk
                          </span>
                        )}
                        {w.riskType === 'tertiary' && (
                          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-label-sm bg-tertiary-fixed text-on-tertiary-fixed-variant font-semibold">
                            <span className="material-symbols-outlined text-xs leading-none">visibility</span>
                            Under Surveillance
                          </span>
                        )}
                        {w.riskType === 'dormant' && (
                          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-label-sm bg-surface-container-high text-on-surface-variant font-medium">
                            <span className="material-symbols-outlined text-xs leading-none">bedtime</span>
                            Dormant
                          </span>
                        )}
                        {w.riskType === 'identified' && (
                          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-label-sm bg-secondary-container/40 text-on-secondary-container font-semibold">
                            <span className="material-symbols-outlined text-xs leading-none">check_circle</span>
                            Exchange Identified
                          </span>
                        )}
                      </td>

                      <td className="py-3 pr-6 pl-3 align-middle text-right">
                        <button
                          onClick={() => navigate('/cases/1')}
                          className="inline-flex items-center gap-1 px-3 py-1 bg-surface-container hover:bg-primary hover:text-on-primary text-primary text-label-md font-semibold rounded-md transition-all shadow-sm"
                        >
                          <span>Trace</span>
                          <span className="material-symbols-outlined text-sm leading-none">arrow_forward</span>
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Ledger Footer */}
            <div className="px-6 py-4 bg-surface-container-lowest border-t border-outline-variant/30 flex items-center justify-between">
              <span className="text-body-sm text-outline">
                Showing {filteredWallets.length} of {wallets.length} tracked wallets
              </span>
              <div className="flex items-center gap-2">
                <button
                  disabled
                  className="px-3 py-1 text-label-sm bg-surface-container text-on-surface-variant rounded opacity-50 cursor-not-allowed"
                >
                  Previous
                </button>
                <button
                  disabled
                  className="px-3 py-1 text-label-sm bg-surface-container text-on-surface-variant rounded opacity-50 cursor-not-allowed"
                >
                  Next
                </button>
              </div>
            </div>
          </div>

          {/* Peel Chain Visualization Preview Banner */}
          <div className="bg-surface-container-lowest p-6 rounded-xl shadow-sm border border-outline-variant/60 flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-start gap-4">
              <div className="p-3 bg-primary-fixed/40 text-primary rounded-xl">
                <span className="material-symbols-outlined text-2xl">account_tree</span>
              </div>
              <div>
                <h3 className="text-headline-sm text-on-surface font-semibold">Automated Peel Chain Sniffer</h3>
                <p className="text-body-sm text-on-surface-variant mt-0.5 max-w-lg">
                  ChainNetra tracks downstream change outputs automatically up to 8 hops. Immediate alerts trigger whenever funds hit regulated FIU-registered Indian VASPs.
                </p>
              </div>
            </div>
            <button
              onClick={() => toast.success('Peel chain heuristic threshold set to: 8 hops, >$1,000 threshold')}
              className="whitespace-nowrap px-4 py-2 bg-surface-container text-on-surface text-label-md font-semibold rounded-lg hover:bg-surface-container-high transition-colors"
            >
              Configure Heuristics
            </button>
          </div>
        </div>

        {/* RIGHT SECTION (Live Movement Alerts Feed - 35%) */}
        <div className="lg:col-span-4 flex flex-col gap-6">
          <div className="bg-surface-container-lowest rounded-xl shadow-sm border border-outline-variant/60 p-6">
            {/* Live Alerts Header */}
            <div className="flex items-center justify-between pb-4 mb-5 border-b border-outline-variant/30">
              <div>
                <h2 className="text-headline-sm text-on-surface font-semibold">Live Movement Alerts</h2>
                <p className="text-body-sm text-outline">Real-time memory pool &amp; block logs</p>
              </div>
              <div className="flex items-center gap-2 px-2.5 py-1 rounded-full bg-secondary-fixed/30 text-on-secondary-fixed">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-secondary opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-secondary"></span>
                </span>
                <span className="text-label-sm font-semibold uppercase tracking-wider">Monitoring Active</span>
              </div>
            </div>

            {/* Alert Cards Feed Stack */}
            <div className="flex flex-col gap-4">
              {/* Alert Card 1 (Red High Risk) */}
              <div className="p-4 rounded-xl bg-surface-container-low border border-outline-variant/30 transition-all hover:shadow-md flex flex-col gap-3">
                <div className="flex items-center justify-between">
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-label-sm bg-error-container text-on-error-container font-semibold">
                    <span className="material-symbols-outlined text-xs">priority_high</span>
                    Large Outflow Detected
                  </span>
                  <span className="font-code-sm text-outline font-mono">12m ago</span>
                </div>
                <div>
                  <p className="text-body-md text-on-surface font-medium leading-snug">
                    <span className="font-code-md text-primary font-semibold font-mono">TJ8wK9vZM...N7xL9</span> moved{' '}
                    <span className="text-error font-semibold">$17,320 USDT</span> to intermediary splitter wallet.
                  </p>
                  <div className="mt-2 flex items-center gap-2 text-outline font-code-sm font-mono">
                    <span>TX: 0x8a92...bf01</span>
                    <span>•</span>
                    <span>Tron Network</span>
                  </div>
                </div>
                <div className="pt-2 flex items-center justify-between border-t border-outline-variant/20">
                  <span className="text-label-sm text-outline">Task Scam #CN-0944</span>
                  <button
                    onClick={() => navigate('/cases/1')}
                    className="px-3 py-1.5 bg-primary text-on-primary text-label-md font-semibold rounded shadow-sm hover:bg-primary-container transition-all flex items-center gap-1"
                  >
                    <span className="material-symbols-outlined text-sm leading-none">timeline</span>
                    Run Trace
                  </button>
                </div>
              </div>

              {/* Alert Card 2 (Teal Success / VASP Deposit) */}
              <div className="p-4 rounded-xl bg-surface-container-low border border-outline-variant/30 transition-all hover:shadow-md flex flex-col gap-3">
                <div className="flex items-center justify-between">
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-label-sm bg-secondary-container/60 text-on-secondary-container font-semibold">
                    <span className="material-symbols-outlined text-xs">account_balance</span>
                    Deposit Reached VASP
                  </span>
                  <span className="font-code-sm text-outline font-mono">34m ago</span>
                </div>
                <div>
                  <p className="text-body-md text-on-surface font-medium leading-snug">
                    <span className="font-code-md text-primary font-semibold font-mono">0x3f5c...f0bE</span> deposited funds into{' '}
                    <span className="font-semibold text-secondary">DemoX Global</span> hot wallet.
                  </p>
                  <div className="mt-2 inline-flex items-center gap-1.5 px-2 py-1 bg-surface-container rounded font-code-sm text-on-surface-variant font-mono">
                    <span>User Internal Tag:</span>
                    <span className="font-semibold text-primary">#983144</span>
                  </div>
                </div>
                <div className="pt-2 flex items-center justify-between border-t border-outline-variant/20">
                  <span className="text-label-sm text-outline">Surveillance Hit</span>
                  <button
                    onClick={() => navigate('/vasps')}
                    className="px-3 py-1.5 bg-secondary text-on-secondary text-label-md font-semibold rounded shadow-sm hover:opacity-95 transition-all flex items-center gap-1"
                  >
                    <span className="material-symbols-outlined text-sm leading-none">policy</span>
                    Send Sec 91
                  </button>
                </div>
              </div>

              {/* Alert Card 3 (Amber Warning / Bridge) */}
              <div className="p-4 rounded-xl bg-surface-container-low border border-outline-variant/30 transition-all hover:shadow-md flex flex-col gap-3">
                <div className="flex items-center justify-between">
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-label-sm bg-tertiary-fixed text-on-tertiary-fixed-variant font-semibold">
                    <span className="material-symbols-outlined text-xs">swap_calls</span>
                    Cross-Chain Bridge Activated
                  </span>
                  <span className="font-code-sm text-outline font-mono">1h ago</span>
                </div>
                <div>
                  <p className="text-body-md text-on-surface font-medium leading-snug">
                    <span className="font-code-md text-primary font-semibold font-mono">0x81C...93bA</span> initiated Stargate bridge protocol from Tron to Ethereum network.
                  </p>
                  <div className="mt-2 flex items-center gap-2 text-outline font-code-sm font-mono">
                    <span>Bridge: Stargate Router V2</span>
                    <span>•</span>
                    <span>4.2 ETH Eqv</span>
                  </div>
                </div>
                <div className="pt-2 flex items-center justify-between border-t border-outline-variant/20">
                  <span className="text-label-sm text-outline">Digital Arrest #CN-0941</span>
                  <button
                    onClick={() => navigate('/cross-chain')}
                    className="px-3 py-1.5 bg-surface-container hover:bg-surface-container-high text-on-surface text-label-md font-semibold rounded transition-all flex items-center gap-1"
                  >
                    <span className="material-symbols-outlined text-sm leading-none">hub</span>
                    Inspect Bridge
                  </button>
                </div>
              </div>

              {/* Alert Card 4 (Teal Acknowledgment) */}
              <div className="p-4 rounded-xl bg-surface-container-low border border-outline-variant/30 transition-all hover:shadow-md flex flex-col gap-3">
                <div className="flex items-center justify-between">
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-label-sm bg-secondary-container/40 text-on-secondary-container font-semibold">
                    <span className="material-symbols-outlined text-xs">verified</span>
                    VASP Acknowledgment Received
                  </span>
                  <span className="font-code-sm text-outline font-mono">3h ago</span>
                </div>
                <div>
                  <p className="text-body-md text-on-surface font-medium leading-snug">
                    Bybit Legal Compliance acknowledged freeze order under Sec 91 CrPC for case{' '}
                    <span className="font-semibold text-primary">#CN-0929</span>.
                  </p>
                  <p className="text-body-sm text-outline mt-1">Holding $34,890 pending magistrate warrant.</p>
                </div>
                <div className="pt-2 flex items-center justify-between border-t border-outline-variant/20">
                  <span className="text-label-sm text-outline">Legal Ticket #BY-88319</span>
                  <button
                    onClick={() => toast.success('Legal Ticket #BY-88319: Funds frozen for 72 hours per CrPC Section 102')}
                    className="px-3 py-1.5 bg-surface-container hover:bg-surface-container-high text-on-surface text-label-md font-semibold rounded transition-all flex items-center gap-1"
                  >
                    <span className="material-symbols-outlined text-sm leading-none">drafts</span>
                    View Acknowledgment
                  </button>
                </div>
              </div>
            </div>

            {/* Alerts Action Link */}
            <button
              onClick={() => toast.success('Displaying complete log of 142 historical surveillance hits')}
              className="w-full mt-4 py-2.5 text-center text-label-md font-semibold text-primary hover:bg-surface-container-low rounded-lg transition-colors flex items-center justify-center gap-1"
            >
              <span>View All Alert Logs (142 historical)</span>
              <span className="material-symbols-outlined text-sm">arrow_forward</span>
            </button>
          </div>

          {/* Quick Regulatory Notice */}
          <div className="p-5 rounded-xl bg-surface-container-high/40 border border-outline-variant/40 flex items-start gap-3">
            <span className="material-symbols-outlined text-primary text-xl mt-0.5">policy</span>
            <div>
              <h4 className="text-headline-sm text-on-surface font-semibold">Statutory Freeze Protocol</h4>
              <p className="text-body-sm text-on-surface-variant mt-1">
                Notices issued under Section 91 CrPC/102 CrPC via ChainNetra are digitally hash-stamped and forwarded directly to designated compliance officers.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Add Wallet to Watchlist Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-inverse-surface/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-surface-container-lowest w-full max-w-lg rounded-xl shadow-2xl border border-outline-variant/60 overflow-hidden animate-in fade-in zoom-in duration-150">
            <div className="px-6 py-4 bg-surface-container-lowest border-b border-outline-variant/30 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-primary">add_moderator</span>
                <h3 className="text-headline-sm text-on-surface font-semibold">Add Target to Watchlist</h3>
              </div>
              <button
                className="p-1 text-outline hover:text-on-surface rounded transition-colors"
                onClick={() => setShowAddModal(false)}
              >
                <span className="material-symbols-outlined text-xl">close</span>
              </button>
            </div>

            <form onSubmit={handleAddSubmit}>
              <div className="p-6 space-y-4">
                <div>
                  <label className="block text-label-sm text-on-surface uppercase mb-1.5 font-semibold">
                    Blockchain Network
                  </label>
                  <div className="grid grid-cols-3 gap-2">
                    <button
                      type="button"
                      onClick={() => setSelectedChain('tron')}
                      className={`px-3 py-2 rounded-lg text-label-md text-center font-semibold transition-all ${
                        selectedChain === 'tron'
                          ? 'bg-primary-fixed text-on-primary-fixed shadow-sm'
                          : 'bg-surface-container text-on-surface hover:bg-surface-container-high'
                      }`}
                    >
                      Tron (TRC20)
                    </button>
                    <button
                      type="button"
                      onClick={() => setSelectedChain('ethereum')}
                      className={`px-3 py-2 rounded-lg text-label-md text-center font-semibold transition-all ${
                        selectedChain === 'ethereum'
                          ? 'bg-primary-fixed text-on-primary-fixed shadow-sm'
                          : 'bg-surface-container text-on-surface hover:bg-surface-container-high'
                      }`}
                    >
                      Ethereum
                    </button>
                    <button
                      type="button"
                      onClick={() => setSelectedChain('bsc')}
                      className={`px-3 py-2 rounded-lg text-label-md text-center font-semibold transition-all ${
                        selectedChain === 'bsc'
                          ? 'bg-primary-fixed text-on-primary-fixed shadow-sm'
                          : 'bg-surface-container text-on-surface hover:bg-surface-container-high'
                      }`}
                    >
                      BNB Chain
                    </button>
                  </div>
                </div>

                <div>
                  <label className="block text-label-sm text-on-surface uppercase mb-1.5 font-semibold">
                    Wallet Public Address
                  </label>
                  <input
                    value={targetAddress}
                    onChange={(e) => setTargetAddress(e.target.value)}
                    className="w-full h-10 px-3 bg-surface-container-low font-code-md text-on-surface placeholder:text-outline rounded-lg focus:outline-none focus:bg-surface-container border border-outline-variant/40 font-mono"
                    placeholder="e.g. 0x... or T..."
                    type="text"
                    required
                  />
                </div>

                <div>
                  <label className="block text-label-sm text-on-surface uppercase mb-1.5 font-semibold">
                    Associated Case / FIR Number
                  </label>
                  <input
                    value={firNumber}
                    onChange={(e) => setFirNumber(e.target.value)}
                    className="w-full h-10 px-3 bg-surface-container-low text-body-md text-on-surface placeholder:text-outline rounded-lg focus:outline-none focus:bg-surface-container border border-outline-variant/40"
                    placeholder="e.g. Cyber Crime PS FIR #944/2024"
                    type="text"
                  />
                </div>

                <div>
                  <label className="block text-label-sm text-on-surface uppercase mb-1.5 font-semibold">
                    Classification &amp; Notes
                  </label>
                  <select
                    value={classification}
                    onChange={(e) => setClassification(e.target.value)}
                    className="w-full h-10 px-3 bg-surface-container-low text-body-md text-on-surface rounded-lg focus:outline-none border border-outline-variant/40"
                  >
                    <option>Primary Scammer Collector</option>
                    <option>Mule Intermediary</option>
                    <option>Layering Peel Chain</option>
                    <option>Mixer / Tumbler Ingress</option>
                    <option>Crypto POS Cashout Outlet</option>
                  </select>
                </div>

                <div className="p-3 bg-surface-container-low rounded-lg flex items-center gap-3 border border-outline-variant/30">
                  <input
                    checked={fiuPrompt}
                    onChange={(e) => setFiuPrompt(e.target.checked)}
                    className="w-4 h-4 rounded text-primary"
                    id="fiu-alert"
                    type="checkbox"
                  />
                  <label className="text-body-sm text-on-surface cursor-pointer select-none" htmlFor="fiu-alert">
                    Auto-generate FIU-IND suspicious transaction prompt if funds exceed $10,000 threshold.
                  </label>
                </div>
              </div>

              <div className="px-6 py-4 bg-surface-container-low/50 border-t border-outline-variant/30 flex items-center justify-end gap-3">
                <button
                  type="button"
                  className="px-4 py-2 text-label-md text-on-surface-variant hover:text-on-surface transition-colors"
                  onClick={() => setShowAddModal(false)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 text-label-md font-semibold bg-primary text-on-primary rounded-lg shadow-sm hover:bg-primary-container transition-all"
                >
                  Deploy Surveillance
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
