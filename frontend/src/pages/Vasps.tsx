import React, { useState, useEffect } from 'react';
import { 
  Building2, Lock, PlusCircle, FileText, CheckCircle2, 
  Clock, ShieldAlert, ArrowRight, ExternalLink, Sparkles, Send, Eye 
} from 'lucide-react';
import toast from 'react-hot-toast';
import { api } from '../lib/api';
import { useAppStore } from '../stores/useAppStore';

export const Vasps: React.FC = () => {
  const explainMode = useAppStore((s) => s.explainMode);
  const user = useAppStore((s) => s.user);

  const [vasps, setVasps] = useState<any[]>([]);
  const [freezeRequests, setFreezeRequests] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Freeze Composer Modal State
  const [showComposer, setShowComposer] = useState(false);
  const [selectedVaspId, setSelectedVaspId] = useState<number>(1);
  const [composerForm, setComposerForm] = useState({
    case_id: 1,
    deposit_address: 'TXDemoxDepositVault9999999999999',
    suspect_wallet: 'TXYZCollectorAlpha777111111111111',
    legal_order_ref: '',
    notes: 'Urgent: Restrain account and preserve KYC identities for deposit vault.'
  });

  const loadData = async () => {
    try {
      setLoading(true);
      const [vRes, fRes] = await Promise.all([
        api.getVasps(),
        api.getFreezeRequests()
      ]);
      setVasps(vRes.vasps || []);
      setFreezeRequests(fRes.freeze_requests || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreateFreeze = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createFreezeRequest({
        case_id: composerForm.case_id,
        vasp_id: selectedVaspId,
        deposit_address: composerForm.deposit_address,
        suspect_wallet: composerForm.suspect_wallet,
        legal_order_ref: composerForm.legal_order_ref,
        notes: composerForm.notes
      });
      toast.success('Freeze request draft created successfully!');
      setShowComposer(false);
      loadData();
    } catch (e) {
      toast.error('Failed to create freeze request');
    }
  };

  const handleUpdateStatus = async (id: number, newStatus: string) => {
    try {
      await api.updateFreezeStatus(id, newStatus, 134500.0);
      toast.success(`Freeze request status transitioned to: ${newStatus}`);
      loadData();
    } catch (e) {
      toast.error('Status transition failed');
    }
  };

  return (
    <div className="space-y-4 animate-in fade-in duration-200">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-2 border-b border-hairline">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-text-primary flex items-center gap-2">
            VASP Directory & Freeze Notice Composer
            <span className="text-xs px-2 py-0.5 rounded font-mono font-bold bg-mint/15 border border-mint/30 text-mint">
              LEA FREEZE WORKFLOW
            </span>
          </h1>
          <p className="text-xs text-text-muted mt-0.5">
            Standardized legal requests served to Virtual Asset Service Providers for account restraint and log preservation.
          </p>
        </div>

        <button
          onClick={() => setShowComposer(true)}
          className="px-4 py-2 rounded-lg bg-mint text-ink font-bold text-xs hover:bg-mint-400 transition-colors flex items-center gap-1.5 shadow"
        >
          <PlusCircle className="w-4 h-4" />
          Compose Legal Freeze Request
        </button>
      </div>

      {/* Legal Authority Disclaimer */}
      <div className="p-3 bg-amber/10 border border-amber/30 rounded-lg text-xs text-amber flex items-start gap-2.5">
        <ShieldAlert className="w-4 h-4 shrink-0 mt-0.5" />
        <div>
          <span className="font-bold">Statutory Legal Disclaimer:</span> ChainNetra recommends, automates attribution, and drafts standardized notice templates.
          Formal account freezing and KYC seizure occurs under proper legal authorization by competent judicial and investigative authorities per configured statutory provisions.
        </div>
      </div>

      {/* Grid: Freeze Requests Workflow & VASP Directory */}
      <div className="space-y-5">
        {/* Active Freeze Requests Table */}
        <div className="bg-panel border border-hairline rounded-xl overflow-hidden shadow">
          <div className="p-3 border-b border-hairline flex items-center justify-between">
            <h3 className="text-xs font-bold text-text-primary tracking-wide">
              Active Freeze Requests & Workflow Status ({freezeRequests.length})
            </h3>
            <span className="text-[10px] font-mono text-text-muted">
              Workflow: Draft → Supervisor Approval → Sent → Acknowledged → Frozen
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-raised/70 border-b border-hairline text-[10px] text-text-muted uppercase">
                <tr>
                  <th className="p-3">Notice ID</th>
                  <th className="p-3">Target VASP</th>
                  <th className="p-3">Deposit Vault Address</th>
                  <th className="p-3 text-right">Victim Loss</th>
                  <th className="p-3">Legal Ref</th>
                  <th className="p-3">Current Status</th>
                  <th className="p-3 text-right">Workflow Progression</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-hairline">
                {freezeRequests.map((fr) => (
                  <tr key={fr.id} className="hover:bg-raised/40 transition-colors">
                    <td className="p-3 font-bold text-text-primary">{fr.request_number}</td>

                    <td className="p-3">
                      <div className="font-sans font-bold text-text-primary">{fr.vasp_name}</div>
                      <div className="text-[10px] text-text-muted">{fr.created_by}</div>
                    </td>

                    <td className="p-3 text-cyan truncate max-w-[140px]">
                      {fr.deposit_address}
                    </td>

                    <td className="p-3 text-right font-bold text-amber">
                      ₹{Number(fr.victim_loss_inr).toLocaleString('en-IN')}
                      <div className="text-[10px] text-text-muted font-normal">
                        ${Number(fr.victim_loss_usd).toLocaleString()} USD
                      </div>
                    </td>

                    <td className="p-3 text-[11px] text-text-muted">
                      {fr.legal_order_ref}
                    </td>

                    <td className="p-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                        fr.status === 'Frozen' ? 'bg-mint/20 text-mint border border-mint/40' :
                        fr.status === 'Sent' ? 'bg-cyan/20 text-cyan border border-cyan/40' :
                        fr.status === 'Pending Approval' ? 'bg-amber/20 text-amber border border-amber/40' :
                        'bg-raised text-text-muted border border-hairline'
                      }`}>
                        {fr.status}
                      </span>
                    </td>

                    <td className="p-3 text-right">
                      {fr.status === 'Draft' && (
                        <button
                          onClick={() => handleUpdateStatus(fr.id, 'Pending Approval')}
                          className="px-2 py-1 rounded bg-raised hover:bg-hairline text-amber border border-hairline text-xs font-semibold"
                        >
                          Submit for Approval
                        </button>
                      )}
                      {fr.status === 'Pending Approval' && (
                        <button
                          onClick={() => handleUpdateStatus(fr.id, 'Sent')}
                          className="px-2 py-1 rounded bg-amber text-ink font-bold text-xs hover:bg-amber-400"
                        >
                          Approve & Send
                        </button>
                      )}
                      {fr.status === 'Sent' && (
                        <button
                          onClick={() => handleUpdateStatus(fr.id, 'Acknowledged')}
                          className="px-2 py-1 rounded bg-cyan text-ink font-bold text-xs hover:bg-cyan-400"
                        >
                          Mark Acknowledged
                        </button>
                      )}
                      {fr.status === 'Acknowledged' && (
                        <button
                          onClick={() => handleUpdateStatus(fr.id, 'Frozen')}
                          className="px-2 py-1 rounded bg-mint text-ink font-bold text-xs hover:bg-mint-400"
                        >
                          Confirm Restraint ($134.5k)
                        </button>
                      )}
                      {fr.status === 'Frozen' && (
                        <span className="text-mint font-bold text-[11px] flex items-center justify-end gap-1">
                          <CheckCircle2 className="w-3.5 h-3.5" /> Funds Restrained
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* VASP Directory Grid */}
        <div className="space-y-3">
          <h3 className="text-xs font-bold text-text-primary tracking-wide uppercase font-mono">
            VASP Compliance Directory (8 Entities)
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
            {vasps.map((v) => (
              <div key={v.id} className="p-3.5 rounded-xl bg-panel border border-hairline hover:border-amber/40 transition-colors flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-raised border border-hairline text-text-muted">
                      {v.category}
                    </span>
                    <span className="text-[10px] font-mono text-mint font-bold">{v.response_sla}</span>
                  </div>

                  <h4 className="text-sm font-bold text-text-primary">{v.name}</h4>
                  <p className="text-[11px] text-text-muted mt-1">{v.description}</p>
                </div>

                <div className="mt-3 pt-2 border-t border-hairline font-mono text-[11px] text-text-muted space-y-1">
                  <div>Jurisdiction: <span className="text-text-primary">{v.jurisdiction}</span></div>
                  <div className="truncate">Contact: <span className="text-cyan">{v.compliance_contact}</span></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Freeze Composer Modal */}
      {showComposer && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in">
          <div className="w-full max-w-xl bg-panel border border-hairline rounded-xl shadow-2xl p-5 space-y-4">
            <h2 className="text-base font-bold text-text-primary flex items-center gap-2">
              <Lock className="w-5 h-5 text-mint" />
              Compose Standardized VASP Freeze Notice
            </h2>

            <form onSubmit={handleCreateFreeze} className="space-y-3 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-text-muted mb-1">Target VASP Entity</label>
                  <select
                    value={selectedVaspId}
                    onChange={(e) => setSelectedVaspId(Number(e.target.value))}
                    className="w-full bg-ink border border-hairline rounded-lg px-3 py-2 text-text-primary focus:border-amber focus:outline-none"
                  >
                    {vasps.map((v) => (
                      <option key={v.id} value={v.id}>{v.name} ({v.jurisdiction})</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-text-muted mb-1">Statutory Order Reference</label>
                  <input
                    type="text"
                    required
                    value={composerForm.legal_order_ref}
                    onChange={(e) => setComposerForm({ ...composerForm, legal_order_ref: e.target.value })}
                    className="w-full bg-ink border border-hairline rounded-lg px-3 py-2 text-text-primary focus:border-amber focus:outline-none font-mono"
                  />
                </div>
              </div>

              <div>
                <label className="block text-text-muted mb-1">Identified Target Deposit Address</label>
                <input
                  type="text"
                  required
                  value={composerForm.deposit_address}
                  onChange={(e) => setComposerForm({ ...composerForm, deposit_address: e.target.value })}
                  className="w-full bg-ink border border-hairline rounded-lg px-3 py-2 font-mono text-cyan focus:border-amber focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-text-muted mb-1">Originating Suspect Collector Wallet</label>
                <input
                  type="text"
                  required
                  value={composerForm.suspect_wallet}
                  onChange={(e) => setComposerForm({ ...composerForm, suspect_wallet: e.target.value })}
                  className="w-full bg-ink border border-hairline rounded-lg px-3 py-2 font-mono text-text-primary focus:border-amber focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-text-muted mb-1">Mandatory Directives to Compliance Officer</label>
                <textarea
                  rows={3}
                  value={composerForm.notes}
                  onChange={(e) => setComposerForm({ ...composerForm, notes: e.target.value })}
                  className="w-full bg-ink border border-hairline rounded-lg p-2 text-text-primary focus:border-amber focus:outline-none"
                />
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-hairline">
                <button
                  type="button"
                  onClick={() => setShowComposer(false)}
                  className="px-3 py-1.5 rounded-lg text-text-muted hover:text-text-primary"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded-lg bg-mint text-ink font-bold hover:bg-mint-400"
                >
                  Generate Freeze Draft
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
