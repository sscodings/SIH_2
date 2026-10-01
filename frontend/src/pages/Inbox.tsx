import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Inbox as InboxIcon, PlusCircle, UploadCloud, RefreshCw, 
  Search, Shield, CheckCircle2, AlertTriangle, ArrowRight, Eye, Play, Sparkles, Filter
} from 'lucide-react';
import toast from 'react-hot-toast';
import { api } from '../lib/api';
import { getApiBaseUrl } from '../lib/config';
import { useAppStore } from '../stores/useAppStore';

export const Inbox: React.FC = () => {
  const navigate = useNavigate();
  const explainMode = useAppStore((s) => s.explainMode);
  const [complaints, setComplaints] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [chainFilter, setChainFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [showManualModal, setShowManualModal] = useState(false);
  const [showCsvModal, setShowCsvModal] = useState(false);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [autoStreamActive, setAutoStreamActive] = useState(false);

  // Address validation quick tester state
  const [testAddress, setTestAddress] = useState('');
  const [validationResult, setValidationResult] = useState<any>(null);

  // Manual Ingestion Form State
  const [manualForm, setManualForm] = useState({
    victim_name: '',
    victim_state: 'Maharashtra',
    fraud_type: 'Investment Scam',
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
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadComplaints();
  }, []);

  // Auto stream simulation timer
  useEffect(() => {
    let interval: any;
    if (autoStreamActive) {
      interval = setInterval(async () => {
        try {
          await api.simulateComplaint();
          loadComplaints();
        } catch (e) {
          console.error(e);
        }
      }, 5000);
    }
    return () => clearInterval(interval);
  }, [autoStreamActive]);

  const handleSimulate = async () => {
    try {
      const res = await api.simulateComplaint();
      toast.success(`Simulated complaint ${res.complaint.complaint_number} received!`);
      loadComplaints();
    } catch (e) {
      toast.error('Simulation failed');
    }
  };

  const handleTestAddress = async () => {
    if (!testAddress.trim()) return;
    try {
      const res = await api.validateAddress(testAddress.trim());
      setValidationResult(res);
    } catch (e) {
      setValidationResult({ valid: false, error: 'Validation failed' });
    }
  };

  const handleManualSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.ingestNcrp({
        victim_name: manualForm.victim_name,
        victim_state: manualForm.victim_state,
        fraud_type: manualForm.fraud_type,
        reported_wallets: [manualForm.wallet_address.trim()],
        amount_lost_inr: Number(manualForm.amount_inr)
      });
      toast.success('Complaint successfully logged and validated!');
      setShowManualModal(false);
      loadComplaints();
    } catch (err: any) {
      toast.error(err.message || 'Submission error');
    }
  };

  const handleCsvUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      const token = localStorage.getItem('chainnetra_token');
      const res = await fetch(`${getApiBaseUrl()}/ingest/csv`, {
        method: 'POST',
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: formData
      });
      const data = await res.json();
      toast.success(`Bulk upload complete: ${data.valid_rows} complaints ingested!`);
      setShowCsvModal(false);
      loadComplaints();
    } catch (e) {
      toast.error('CSV upload failed');
    }
  };

  const filtered = complaints.filter((c) => {
    const matchQ = 
      c.complaint_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.victim_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.reported_wallets.some((w: string) => w.toLowerCase().includes(searchQuery.toLowerCase()));
    const matchChain = chainFilter ? c.chain === chainFilter : true;
    const matchStatus = statusFilter ? c.status === statusFilter : true;
    return matchQ && matchChain && matchStatus;
  });

  const toggleSelect = (id: number) => {
    setSelectedIds((prev) => prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]);
  };

  const handleTraceSelected = async () => {
    if (selectedIds.length === 0) return;
    const target = complaints.find((c) => c.id === selectedIds[0]);
    if (target) {
      navigate('/cases/1');
    }
  };

  return (
    <div className="space-y-4 animate-in fade-in duration-200">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-2 border-b border-hairline">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-text-primary flex items-center gap-2">
            Complaint Ingestion Inbox
            <span className="text-xs px-2 py-0.5 rounded font-mono font-bold bg-cyan/15 border border-cyan/30 text-cyan">
              NCRP / SAHYOG CONNECTORS
            </span>
          </h1>
          <p className="text-xs text-text-muted mt-0.5">
            Automated cybercrime portal feeds with address validation, chain auto-detection, and duplicate linking.
          </p>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={() => setAutoStreamActive(!autoStreamActive)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-colors flex items-center gap-1.5 ${
              autoStreamActive 
                ? 'bg-coral/20 border-coral text-coral animate-pulse' 
                : 'bg-raised hover:bg-hairline text-text-muted border-hairline'
            }`}
          >
            <span className={`w-2 h-2 rounded-full ${autoStreamActive ? 'bg-coral' : 'bg-text-muted'}`} />
            {autoStreamActive ? 'Streaming Live Feed' : 'Auto-Stream Inflow'}
          </button>

          <button
            onClick={handleSimulate}
            className="px-3.5 py-1.5 rounded-lg bg-raised hover:bg-hairline text-text-primary text-xs font-semibold border border-hairline transition-colors flex items-center gap-1.5"
          >
            <PlusCircle className="w-3.5 h-3.5 text-amber" />
            Simulate 1 Complaint
          </button>

          <button
            onClick={() => setShowManualModal(true)}
            className="px-3.5 py-1.5 rounded-lg bg-amber text-ink font-bold text-xs hover:bg-amber-400 transition-colors flex items-center gap-1.5 shadow"
          >
            Log Complaint Form
          </button>

          <button
            onClick={() => setShowCsvModal(true)}
            className="px-3.5 py-1.5 rounded-lg bg-raised hover:bg-hairline text-text-primary text-xs font-semibold border border-hairline transition-colors flex items-center gap-1.5"
          >
            <UploadCloud className="w-3.5 h-3.5 text-cyan" />
            CSV Bulk Import
          </button>
        </div>
      </div>

      {explainMode && (
        <div className="p-3 bg-cyan/10 border border-cyan/30 rounded-lg text-xs text-cyan flex items-start gap-2.5">
          <Sparkles className="w-4 h-4 shrink-0 mt-0.5" />
          <div>
            <span className="font-bold">Investigator Tip:</span> ChainNetra automatically parses incoming complainant statements from NCRP / SAHYOG APIs.
            The engine automatically determines the underlying blockchain (Tron Base58, Bitcoin Bech32/Legacy, or EVM) and alerts if the scammer wallet was previously reported in another police jurisdiction.
          </div>
        </div>
      )}

      {/* Address Chain Auto-Detection Quick Inspector Banner */}
      <div className="bg-panel border border-hairline rounded-xl p-3 flex flex-col md:flex-row items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-xs font-mono text-text-muted shrink-0">
          <Shield className="w-4 h-4 text-amber" />
          <span>Address Chain Auto-Detector:</span>
        </div>
        <div className="flex items-center gap-2 flex-1 w-full max-w-2xl">
          <input
            type="text"
            placeholder="Paste Tron (T...), Bitcoin (1/3/bc1...), or EVM (0x...) address to test auto-detection..."
            value={testAddress}
            onChange={(e) => setTestAddress(e.target.value)}
            className="flex-1 bg-ink border border-hairline rounded-lg px-3 py-1.5 text-xs text-text-primary placeholder:text-text-muted focus:outline-none focus:border-amber font-mono"
          />
          <button
            onClick={handleTestAddress}
            className="px-3 py-1.5 rounded-lg bg-raised hover:bg-hairline border border-hairline text-xs font-semibold text-text-primary shrink-0"
          >
            Probe Chain
          </button>
        </div>

        {validationResult && (
          <div className="flex items-center gap-2 font-mono text-xs shrink-0">
            {validationResult.valid ? (
              <span className="px-2 py-0.5 rounded bg-mint/15 text-mint border border-mint/30 font-bold uppercase flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" /> {validationResult.chain} ({validationResult.standard})
              </span>
            ) : (
              <span className="px-2 py-0.5 rounded bg-coral/15 text-coral border border-coral/30 font-bold flex items-center gap-1">
                <AlertTriangle className="w-3 h-3" /> Invalid Address Format
              </span>
            )}
          </div>
        )}
      </div>

      {/* Filters & Bulk Bar */}
      <div className="flex flex-col md:flex-row items-center justify-between gap-3 bg-panel p-2.5 rounded-xl border border-hairline">
        <div className="flex items-center gap-2 flex-1 w-full">
          <div className="relative flex-1 max-w-sm">
            <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-text-muted" />
            <input
              type="text"
              placeholder="Search by complaint number, victim name, wallet..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-ink border border-hairline rounded-lg pl-8 pr-3 py-1.5 text-xs text-text-primary placeholder:text-text-muted focus:outline-none focus:border-amber font-mono"
            />
          </div>

          <select
            value={chainFilter}
            onChange={(e) => setChainFilter(e.target.value)}
            className="bg-ink border border-hairline rounded-lg px-2.5 py-1.5 text-xs text-text-muted focus:outline-none focus:border-amber"
          >
            <option value="">All Chains</option>
            <option value="tron">Tron (TRC-20)</option>
            <option value="ethereum">Ethereum</option>
            <option value="bsc">BSC (BEP-20)</option>
            <option value="bitcoin">Bitcoin</option>
          </select>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-ink border border-hairline rounded-lg px-2.5 py-1.5 text-xs text-text-muted focus:outline-none focus:border-amber"
          >
            <option value="">All Statuses</option>
            <option value="New">New</option>
            <option value="Assigned">Assigned</option>
            <option value="Tracing">Tracing</option>
          </select>
        </div>

        {selectedIds.length > 0 && (
          <div className="flex items-center gap-2 text-xs font-mono text-amber">
            <span>{selectedIds.length} selected</span>
            <button
              onClick={handleTraceSelected}
              className="px-2.5 py-1 rounded bg-amber text-ink font-bold text-xs hover:bg-amber-400 transition-colors flex items-center gap-1"
            >
              Trace in Workspace <ArrowRight className="w-3 h-3" />
            </button>
          </div>
        )}
      </div>

      {/* Complaints Table */}
      <div className="bg-panel border border-hairline rounded-xl overflow-hidden shadow">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-raised/70 border-b border-hairline font-mono text-[11px] text-text-muted uppercase">
              <tr>
                <th className="p-3 w-10 text-center">
                  <input
                    type="checkbox"
                    checked={selectedIds.length === filtered.length && filtered.length > 0}
                    onChange={(e) => setSelectedIds(e.target.checked ? filtered.map((c) => c.id) : [])}
                    className="rounded bg-ink border-hairline text-amber focus:ring-0"
                  />
                </th>
                <th className="p-3">Complaint ID</th>
                <th className="p-3">Source</th>
                <th className="p-3">Victim & State</th>
                <th className="p-3">Fraud Typology</th>
                <th className="p-3">Reported Wallet</th>
                <th className="p-3">Chain</th>
                <th className="p-3 text-right">Loss Amount (₹)</th>
                <th className="p-3">Priority</th>
                <th className="p-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-hairline">
              {loading ? (
                <tr>
                  <td colSpan={10} className="p-8 text-center text-text-muted font-mono">
                    Loading incoming complaints...
                  </td>
                </tr>
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={10} className="p-8 text-center text-text-muted">
                    No complaints match the filter criteria.
                  </td>
                </tr>
              ) : (
                filtered.map((c) => {
                  const isSelected = selectedIds.includes(c.id);
                  const isCaseZeroComplaint = c.id >= 101 && c.id <= 109;
                  const walletStr = c.reported_wallets[0] || 'Unknown';
                  return (
                    <tr
                      key={c.id}
                      className={`hover:bg-raised/50 transition-colors ${
                        isSelected ? 'bg-amber/5' : ''
                      }`}
                    >
                      <td className="p-3 text-center">
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => toggleSelect(c.id)}
                          className="rounded bg-ink border-hairline text-amber focus:ring-0"
                        />
                      </td>

                      <td className="p-3 font-mono font-bold text-text-primary">
                        <span className="flex items-center gap-1.5">
                          {c.complaint_number}
                          {isCaseZeroComplaint && (
                            <span className="px-1.5 py-0.2 rounded bg-amber/20 text-amber text-[9px] font-bold">
                              CASE ZERO
                            </span>
                          )}
                        </span>
                      </td>

                      <td className="p-3">
                        <span className="px-2 py-0.5 rounded font-mono text-[10px] font-semibold bg-raised border border-hairline text-text-muted">
                          {c.source}
                        </span>
                      </td>

                      <td className="p-3">
                        <div className="font-medium text-text-primary">{c.victim_name}</div>
                        <div className="text-[10px] text-text-muted font-mono">{c.victim_state}</div>
                      </td>

                      <td className="p-3">
                        <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-raised border border-hairline text-text-primary">
                          {c.fraud_type}
                        </span>
                      </td>

                      <td className="p-3 font-mono text-[11px] text-cyan">
                        <div className="flex items-center gap-1.5">
                          <span className="truncate max-w-[130px]">{walletStr}</span>
                          {/* Duplicate Detection Badge */}
                          {c.reported_wallets.length > 0 && (
                            <span className="px-1.5 py-0.2 rounded bg-coral/20 text-coral text-[9px] font-bold shrink-0">
                              Linked
                            </span>
                          )}
                        </div>
                      </td>

                      <td className="p-3">
                        <span className={`px-2 py-0.5 rounded font-mono text-[10px] font-bold uppercase ${
                          c.chain === 'tron' ? 'bg-red-500/15 text-red-400 border border-red-500/30' :
                          c.chain === 'ethereum' ? 'bg-indigo-500/15 text-indigo-400 border border-indigo-500/30' :
                          c.chain === 'bsc' ? 'bg-yellow-500/15 text-yellow-400 border border-yellow-500/30' :
                          'bg-orange-500/15 text-orange-400 border border-orange-500/30'
                        }`}>
                          {c.chain}
                        </span>
                      </td>

                      <td className="p-3 text-right font-mono font-bold text-text-primary">
                        ₹{Number(c.amount_lost_inr).toLocaleString('en-IN')}
                        <div className="text-[10px] text-text-muted font-normal">
                          ${Number(c.amount_lost_usd).toLocaleString()} USD
                        </div>
                      </td>

                      <td className="p-3">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase ${
                          c.priority === 'Critical' ? 'bg-coral/20 text-coral border border-coral/40' :
                          c.priority === 'High' ? 'bg-amber/20 text-amber border border-amber/40' :
                          'bg-raised text-text-muted border border-hairline'
                        }`}>
                          {c.priority}
                        </span>
                      </td>

                      <td className="p-3 text-right">
                        <button
                          onClick={() => navigate('/cases/1')}
                          className="px-2.5 py-1 rounded bg-raised hover:bg-hairline text-text-primary hover:text-amber text-xs font-medium border border-hairline transition-colors inline-flex items-center gap-1"
                        >
                          <Play className="w-3 h-3 text-amber" /> Trace
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Manual Ingestion Modal */}
      {showManualModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in">
          <div className="w-full max-w-md bg-panel border border-hairline rounded-xl shadow-2xl p-5 space-y-4">
            <h2 className="text-base font-bold text-text-primary">Manual NCRP Citizen Complaint Entry</h2>
            <form onSubmit={handleManualSubmit} className="space-y-3 text-xs">
              <div>
                <label className="block text-text-muted mb-1">Complainant / Victim Full Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Ramesh Kumar"
                  value={manualForm.victim_name}
                  onChange={(e) => setManualForm({ ...manualForm, victim_name: e.target.value })}
                  className="w-full bg-ink border border-hairline rounded-lg px-3 py-2 text-text-primary focus:border-amber focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-text-muted mb-1">State / Jurisdiction</label>
                  <select
                    value={manualForm.victim_state}
                    onChange={(e) => setManualForm({ ...manualForm, victim_state: e.target.value })}
                    className="w-full bg-ink border border-hairline rounded-lg px-3 py-2 text-text-primary focus:border-amber focus:outline-none"
                  >
                    <option value="Maharashtra">Maharashtra</option>
                    <option value="Karnataka">Karnataka</option>
                    <option value="Delhi">Delhi</option>
                    <option value="Gujarat">Gujarat</option>
                    <option value="Telangana">Telangana</option>
                  </select>
                </div>

                <div>
                  <label className="block text-text-muted mb-1">Fraud Typology</label>
                  <select
                    value={manualForm.fraud_type}
                    onChange={(e) => setManualForm({ ...manualForm, fraud_type: e.target.value })}
                    className="w-full bg-ink border border-hairline rounded-lg px-3 py-2 text-text-primary focus:border-amber focus:outline-none"
                  >
                    <option value="Investment Scam">Investment Scam</option>
                    <option value="Task-Based Fraud">Task-Based Fraud</option>
                    <option value="Sextortion">Sextortion</option>
                    <option value="Ransomware">Ransomware</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-text-muted mb-1">Reported Scammer Crypto Wallet Address</label>
                <input
                  type="text"
                  required
                  placeholder="Paste T..., 0x..., or bc1... wallet address"
                  value={manualForm.wallet_address}
                  onChange={(e) => setManualForm({ ...manualForm, wallet_address: e.target.value })}
                  className="w-full bg-ink border border-hairline rounded-lg px-3 py-2 font-mono text-text-primary focus:border-amber focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-text-muted mb-1">Amount Lost in INR (₹)</label>
                <input
                  type="number"
                  required
                  value={manualForm.amount_inr}
                  onChange={(e) => setManualForm({ ...manualForm, amount_inr: Number(e.target.value) })}
                  className="w-full bg-ink border border-hairline rounded-lg px-3 py-2 font-mono text-text-primary focus:border-amber focus:outline-none"
                />
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-hairline">
                <button
                  type="button"
                  onClick={() => setShowManualModal(false)}
                  className="px-3 py-1.5 rounded-lg text-text-muted hover:text-text-primary"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded-lg bg-amber text-ink font-bold hover:bg-amber-400"
                >
                  Log Complaint
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* CSV Upload Modal */}
      {showCsvModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in">
          <div className="w-full max-w-md bg-panel border border-hairline rounded-xl shadow-2xl p-5 space-y-4">
            <h2 className="text-base font-bold text-text-primary">Bulk Ingestion from CSV</h2>
            <p className="text-xs text-text-muted">
              Upload standardized NCRP / SAHYOG CSV export with columns: <code>victim_name, victim_state, fraud_type, wallet, amount_inr</code>.
            </p>
            <div className="border-2 border-dashed border-hairline hover:border-amber/40 rounded-xl p-8 text-center cursor-pointer relative bg-ink/50">
              <input
                type="file"
                accept=".csv"
                onChange={handleCsvUpload}
                className="absolute inset-0 opacity-0 cursor-pointer"
              />
              <UploadCloud className="w-8 h-8 text-amber mx-auto mb-2" />
              <p className="text-xs text-text-primary font-medium">Click to select CSV or drag file here</p>
              <p className="text-[10px] text-text-muted mt-1">Automatic address validation on upload</p>
            </div>
            <div className="flex justify-end">
              <button
                onClick={() => setShowCsvModal(false)}
                className="px-3 py-1.5 rounded-lg text-xs text-text-muted hover:text-text-primary"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
