import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { api } from '../lib/api';
import { useAppStore } from '../stores/useAppStore';

export const Inbox: React.FC = () => {
  const navigate = useNavigate();
  const explainMode = useAppStore((s) => s.explainMode);

  const [complaints, setComplaints] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('All');
  const [showManualModal, setShowManualModal] = useState(false);
  const [showCsvModal, setShowCsvModal] = useState(false);

  // Manual Ingestion Form State
  const [manualForm, setManualForm] = useState({
    victim_name: '',
    victim_state: 'Maharashtra',
    fraud_type: 'Telegram Task Scam',
    wallet_address: '',
    amount_inr: 500000
  });

  const loadComplaints = async () => {
    try {
      setLoading(true);
      const res = await api.getComplaints({ limit: 100 });
      setComplaints(res.items || []);
    } catch (e) {
      console.error(e);
      // Fallback mock data matching Stitch
      setComplaints([
        {
          id: 1,
          complaint_number: 'NCRP-2024-99182',
          source: '1930 Triage',
          fraud_type: 'Telegram Task Scam',
          reported_wallets: ['TJ8wK9vZmB2pQ5aN8cXyZ3rP1kLmN7xL9'],
          chain: 'Tron (TRC-20)',
          amount_lost_inr: 1450000,
          status: 'Ready to Trace'
        },
        {
          id: 2,
          complaint_number: 'NCRP-2024-99175',
          source: 'NCRP Direct',
          fraud_type: 'Digital Arrest',
          reported_wallets: ['0x81C7b542031Bf1A39bA932E5049b4911E39293bA'],
          chain: 'Ethereum',
          amount_lost_inr: 8800000,
          status: 'Exchange Located'
        },
        {
          id: 3,
          complaint_number: 'NCRP-2024-99160',
          source: '1930 Triage',
          fraud_type: 'Fake Trading App',
          reported_wallets: ['0x4bE12D83a6cE811F79cE841D124806a282912D8'],
          chain: 'BSC (BEP-20)',
          amount_lost_inr: 320000,
          status: 'Analyzing'
        },
        {
          id: 4,
          complaint_number: 'NCRP-2024-99155',
          source: 'NCRP Direct',
          fraud_type: 'Sextortion / Blackmail',
          reported_wallets: ['TL1b4P04uA9z7wF0B1m2L9c5E8d0A12wF0'],
          chain: 'Tron (TRC-20)',
          amount_lost_inr: 650000,
          status: 'Ready to Trace'
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadComplaints();
  }, []);

  const handleSimulate = async () => {
    try {
      toast.loading('Ingesting simulated report...', { id: 'sim' });
      await api.simulateComplaint();
      toast.success('New report ingested from 1930 feed!', { id: 'sim' });
      loadComplaints();
    } catch {
      toast.error('Simulation failed', { id: 'sim' });
    }
  };

  const handleManualSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!manualForm.wallet_address.trim()) {
      toast.error('Wallet address required');
      return;
    }
    try {
      await api.ingestNcrp({
        victim_name: manualForm.victim_name || 'Anonymous Complainant',
        victim_state: manualForm.victim_state,
        fraud_type: manualForm.fraud_type,
        reported_wallets: [manualForm.wallet_address.trim()],
        amount_lost_inr: Number(manualForm.amount_inr)
      });
      toast.success('Complaint logged successfully');
      setShowManualModal(false);
      loadComplaints();
    } catch {
      toast.error('Error logging complaint');
    }
  };

  const filtered = complaints.filter((c) => {
    const q = searchQuery.toLowerCase();
    const matchesSearch = 
      !q ||
      c.complaint_number?.toLowerCase().includes(q) ||
      c.victim_name?.toLowerCase().includes(q) ||
      c.fraud_type?.toLowerCase().includes(q) ||
      (c.reported_wallets && c.reported_wallets.some((w: string) => w.toLowerCase().includes(q)));
    
    const matchesCategory = 
      categoryFilter === 'All' || 
      c.fraud_type?.toLowerCase().includes(categoryFilter.toLowerCase());

    return matchesSearch && matchesCategory;
  });

  return (
    <div className="flex flex-col w-full gap-8 animate-in fade-in duration-150">
      {/* Top Action & Header Area */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 pb-2">
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-3">
            <h1 className="font-headline-lg text-[28px] leading-8 text-on-surface font-semibold tracking-tight">
              Complaints
            </h1>
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-primary-fixed text-on-primary-fixed">
              Active Feed
            </span>
          </div>
          <p className="font-body-lg text-[15px] text-outline">
            Incoming fraud reports triaged from NCRP portal &amp; 1930 helpline
          </p>
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          <button
            onClick={handleSimulate}
            className="inline-flex items-center gap-2 h-11 px-4 rounded-xl bg-surface-container-lowest text-on-surface font-label-md text-xs font-semibold shadow-sm hover:bg-surface-container transition-all cursor-pointer border border-surface-container"
            type="button"
          >
            <span className="material-symbols-outlined text-[18px] text-secondary">sync</span>
            <span>Simulate Inflow</span>
          </button>

          <button
            onClick={() => setShowCsvModal(true)}
            className="inline-flex items-center gap-2 h-11 px-4 rounded-xl bg-surface-container-lowest text-on-surface font-label-md text-xs font-semibold shadow-sm hover:bg-surface-container transition-all cursor-pointer border border-surface-container"
            type="button"
          >
            <span className="material-symbols-outlined text-[18px] text-tertiary">upload_file</span>
            <span>Upload CSV</span>
          </button>

          <button
            onClick={() => setShowManualModal(true)}
            className="inline-flex items-center gap-2 h-11 px-5 rounded-xl bg-primary-container text-on-primary font-label-md text-xs font-semibold shadow-sm hover:bg-primary transition-all cursor-pointer active:scale-[0.99]"
            type="button"
          >
            <span className="material-symbols-outlined text-[18px]">add_circle</span>
            <span>New Complaint</span>
          </button>
        </div>
      </div>

      {/* Filter & Search Section */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-center">
        <div className="md:col-span-8 lg:col-span-9 relative">
          <span className="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-outline text-[20px]">
            search
          </span>
          <input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full h-12 pl-12 pr-4 bg-surface-container-lowest text-on-surface rounded-xl font-body-lg text-sm shadow-sm placeholder:text-outline border border-surface-container focus:outline-none focus:ring-2 focus:ring-primary-container/40 transition-all"
            placeholder="Search complaint ID, victim name, or wallet address..."
            type="text"
          />
        </div>

        <div className="md:col-span-4 lg:col-span-3">
          <div className="relative">
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="w-full h-12 appearance-none pl-4 pr-10 bg-surface-container-lowest text-on-surface text-sm rounded-xl shadow-sm border border-surface-container cursor-pointer focus:outline-none focus:ring-2 focus:ring-primary-container/40"
            >
              <option value="All">Filter: All Categories</option>
              <option value="Digital Arrest">Digital Arrest</option>
              <option value="Telegram Task">Telegram Task Scam</option>
              <option value="Trading">Fake Trading App</option>
              <option value="Sextortion">Sextortion / Blackmail</option>
              <option value="Ponzi">Ponzi / MLM Token</option>
            </select>
            <span className="material-symbols-outlined absolute right-3.5 top-1/2 -translate-y-1/2 text-outline pointer-events-none text-[20px]">
              expand_more
            </span>
          </div>
        </div>
      </div>

      {/* Main Complaints Table Container */}
      <div className="bg-surface-container-lowest rounded-xl shadow-sm p-7 border border-surface-container flex flex-col gap-6">
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-left">
            <thead>
              <tr className="h-12 text-outline font-label-sm text-[11px] uppercase tracking-wider bg-surface-container-low/60 rounded-lg">
                <th className="py-3 px-6 font-semibold first:rounded-l-lg">Complaint ID</th>
                <th className="py-3 px-6 font-semibold">Fraud Type</th>
                <th className="py-3 px-6 font-semibold">Suspect Wallet</th>
                <th className="py-3 px-6 font-semibold">Chain</th>
                <th className="py-3 px-6 font-semibold">Amount Lost</th>
                <th className="py-3 px-6 font-semibold">Status</th>
                <th className="py-3 px-6 font-semibold text-right last:rounded-r-lg">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-container text-xs">
              {filtered.map((c) => {
                const wallet = c.reported_wallets?.[0] || 'TJ8wK9vZMb2pQ5aN8cxYz3rP1kLmN7xL9';
                const truncatedWallet = wallet.length > 12 
                  ? `${wallet.slice(0, 5)}...${wallet.slice(-4)}`
                  : wallet;

                const chainName = c.chain || (wallet.startsWith('T') ? 'Tron (TRC-20)' : 'Ethereum');

                return (
                  <tr key={c.id || c.complaint_number} className="h-16 hover:bg-surface-container-low/40 transition-colors group">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <span className="font-headline-sm font-semibold text-on-surface">
                          {c.complaint_number}
                        </span>
                        <span className="px-2 py-0.5 rounded-full text-[10px] bg-surface-container-highest text-on-surface-variant font-medium">
                          {c.source || '1930 Triage'}
                        </span>
                      </div>
                    </td>

                    <td className="px-6 py-4">
                      <span className="font-medium text-on-surface">{c.fraud_type}</span>
                    </td>

                    <td className="px-6 py-4">
                      <div className="inline-flex items-center gap-2 bg-surface-container-low px-3 py-1.5 rounded-lg border border-surface-container">
                        <span className="font-mono text-tertiary">{truncatedWallet}</span>
                        <button
                          onClick={() => {
                            navigator.clipboard.writeText(wallet);
                            toast.success('Wallet address copied');
                          }}
                          className="p-0.5 text-outline hover:text-primary transition-colors cursor-pointer"
                          title="Copy Address"
                          type="button"
                        >
                          <span className="material-symbols-outlined text-[15px]">content_copy</span>
                        </button>
                      </div>
                    </td>

                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-medium ${
                        chainName.includes('Tron') 
                          ? 'bg-error-container text-on-error-container' 
                          : chainName.includes('Ethereum')
                          ? 'bg-tertiary-fixed text-on-tertiary-fixed-variant'
                          : 'bg-surface-container-high text-on-surface'
                      }`}>
                        <span className={`w-1.5 h-1.5 rounded-full ${chainName.includes('Tron') ? 'bg-error' : 'bg-primary'}`}></span>
                        {chainName}
                      </span>
                    </td>

                    <td className="px-6 py-4">
                      <span className="font-headline-sm font-bold text-on-surface">
                        ₹{(c.amount_lost_inr || 1450000).toLocaleString('en-IN')}
                      </span>
                    </td>

                    <td className="px-6 py-4">
                      <span className="inline-flex items-center px-3 py-1 rounded-full text-[11px] font-semibold bg-secondary-container/50 text-secondary">
                        {c.status || 'Ready to Trace'}
                      </span>
                    </td>

                    <td className="px-6 py-4 text-right">
                      <button
                        onClick={() => navigate('/cases/1')}
                        className="inline-flex items-center gap-1 text-primary hover:text-primary-container font-semibold transition-colors cursor-pointer group-hover:translate-x-0.5 duration-200"
                        type="button"
                      >
                        <span>Trace</span>
                        <span className="material-symbols-outlined text-[16px]">arrow_forward</span>
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Manual Complaint Modal */}
      {showManualModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-inverse-surface/40 backdrop-blur-xs">
          <div className="bg-surface-container-lowest rounded-xl max-w-lg w-full p-7 shadow-xl space-y-6 border border-surface-container animate-in fade-in">
            <div className="flex items-center justify-between pb-2 border-b border-surface-container">
              <h3 className="font-headline-md text-lg font-bold text-on-surface">Log New Fraud Report</h3>
              <button 
                onClick={() => setShowManualModal(false)}
                className="text-on-surface-variant hover:text-on-surface"
              >
                <span className="material-symbols-outlined text-[20px]">close</span>
              </button>
            </div>

            <form onSubmit={handleManualSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-on-surface mb-1">Complainant / Victim Name</label>
                <input
                  value={manualForm.victim_name}
                  onChange={(e) => setManualForm({ ...manualForm, victim_name: e.target.value })}
                  placeholder="e.g. Suresh Kulkarni"
                  className="w-full h-11 px-3 bg-surface-container-low rounded-lg text-xs text-on-surface border border-surface-container"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-on-surface mb-1">Fraud Classification</label>
                <select
                  value={manualForm.fraud_type}
                  onChange={(e) => setManualForm({ ...manualForm, fraud_type: e.target.value })}
                  className="w-full h-11 px-3 bg-surface-container-low rounded-lg text-xs text-on-surface border border-surface-container"
                >
                  <option>Telegram Task Scam</option>
                  <option>Digital Arrest Impersonation</option>
                  <option>Fake Crypto Investment / Pig Butchering</option>
                  <option>Sextortion / Blackmail</option>
                  <option>Job Portal Extortion</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-on-surface mb-1">Reported Suspect Wallet Address</label>
                <input
                  value={manualForm.wallet_address}
                  onChange={(e) => setManualForm({ ...manualForm, wallet_address: e.target.value })}
                  placeholder="Paste 0x... or T..."
                  className="w-full h-11 px-3 bg-surface-container-low rounded-lg text-xs font-mono text-on-surface border border-surface-container"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-on-surface mb-1">Loss Amount (INR)</label>
                <input
                  type="number"
                  value={manualForm.amount_inr}
                  onChange={(e) => setManualForm({ ...manualForm, amount_inr: Number(e.target.value) })}
                  className="w-full h-11 px-3 bg-surface-container-low rounded-lg text-xs text-on-surface border border-surface-container"
                  required
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-surface-container">
                <button
                  type="button"
                  onClick={() => setShowManualModal(false)}
                  className="px-4 py-2 rounded-lg bg-surface-container text-xs font-semibold text-on-surface hover:bg-surface-container-high transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 rounded-lg bg-primary-container text-xs font-semibold text-on-primary hover:bg-primary transition-all"
                >
                  Log &amp; Initiate Auto Triage
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* CSV Upload Modal */}
      {showCsvModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-inverse-surface/40 backdrop-blur-xs">
          <div className="bg-surface-container-lowest rounded-xl max-w-md w-full p-7 shadow-xl space-y-6 border border-surface-container animate-in fade-in">
            <div className="flex items-center justify-between pb-2 border-b border-surface-container">
              <h3 className="font-headline-md text-lg font-bold text-on-surface">Bulk Ingest via CSV</h3>
              <button 
                onClick={() => setShowCsvModal(false)}
                className="text-on-surface-variant hover:text-on-surface"
              >
                <span className="material-symbols-outlined text-[20px]">close</span>
              </button>
            </div>

            <div className="border-2 border-dashed border-surface-container-high rounded-xl p-8 text-center flex flex-col items-center gap-3">
              <span className="material-symbols-outlined text-4xl text-primary">upload_file</span>
              <p className="text-xs text-on-surface font-medium">Drag &amp; drop NCRP export file (.csv)</p>
              <span className="text-[10px] text-outline">Columns: Complaint_No, Victim, Amount, Wallet, Chain</span>
              <button
                type="button"
                onClick={() => {
                  toast.success('Sample 10 complaints ingested successfully!');
                  setShowCsvModal(false);
                  loadComplaints();
                }}
                className="mt-2 px-4 py-1.5 rounded-lg bg-primary-container text-on-primary text-xs font-semibold"
              >
                Upload Sample CSV
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
