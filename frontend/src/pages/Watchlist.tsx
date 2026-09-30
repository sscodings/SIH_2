import React, { useState, useEffect } from 'react';
import { 
  EyeOff, Bell, PlusCircle, Play, CheckCircle2, 
  Trash2, ShieldAlert, ArrowUpRight, Sparkles 
} from 'lucide-react';
import toast from 'react-hot-toast';
import { api } from '../lib/api';
import { useAppStore } from '../stores/useAppStore';

export const Watchlist: React.FC = () => {
  const explainMode = useAppStore((s) => s.explainMode);
  const clearUnreadAlerts = useAppStore((s) => s.clearUnreadAlerts);

  const [watchlist, setWatchlist] = useState<any[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // New Watchlist Item Modal
  const [showAddModal, setShowAddModal] = useState(false);
  const [newAddr, setNewAddr] = useState('');
  const [newChain, setNewChain] = useState('tron');
  const [newLabel, setNewLabel] = useState('');
  const [newReason, setNewReason] = useState('High-risk suspect holding');

  const loadData = async () => {
    try {
      setLoading(true);
      const [wRes, aRes] = await Promise.all([
        api.getWatchlist(),
        api.getAlerts()
      ]);
      setWatchlist(wRes.items || []);
      setAlerts(aRes.alerts || []);
      clearUnreadAlerts();
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSimulateMovement = async () => {
    try {
      const res = await api.simulateMovement();
      toast.error(`ALERT TRIGGERED: Monitored wallet moved $${res.alert.amount_usd.toLocaleString()}!`, { duration: 5000 });
      loadData();
    } catch (e) {
      toast.error('Simulation failed');
    }
  };

  const handleAddSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.addToWatchlist({
        address: newAddr.trim(),
        chain: newChain,
        label: newLabel,
        reason: newReason
      });
      toast.success('Address placed on 24/7 mempool watchlist!');
      setShowAddModal(false);
      setNewAddr('');
      setNewLabel('');
      loadData();
    } catch (e) {
      toast.error('Failed to add to watchlist');
    }
  };

  const handleRemove = async (id: number) => {
    try {
      await api.removeFromWatchlist(id);
      toast('Target removed from active watchlist');
      loadData();
    } catch (e) {
      toast.error('Failed to remove');
    }
  };

  const handleAck = async (id: number) => {
    try {
      await api.ackAlert(id);
      toast.success('Alert marked as acknowledged');
      loadData();
    } catch (e) {
      toast.error('Failed to acknowledge');
    }
  };

  return (
    <div className="space-y-4 animate-in fade-in duration-200">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-2 border-b border-hairline">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-text-primary flex items-center gap-2">
            Mempool Watchlist & Real-Time Alert Dispatch
            <span className="text-xs px-2 py-0.5 rounded font-mono font-bold bg-amber/15 border border-amber/30 text-amber">
              24/7 CONTINUOUS MONITORING
            </span>
          </h1>
          <p className="text-xs text-text-muted mt-0.5">
            Automated monitoring of dormant suspect balances, tumbler entries, and sudden VASP deposits.
          </p>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2">
          <button
            onClick={handleSimulateMovement}
            className="px-3.5 py-1.5 rounded-lg bg-coral text-white font-bold text-xs hover:bg-coral-600 transition-colors flex items-center gap-1.5 shadow animate-pulse"
            title="Simulate sudden illicit fund movement to test alert dispatching"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            Simulate Movement Event
          </button>

          <button
            onClick={() => setShowAddModal(true)}
            className="px-3.5 py-1.5 rounded-lg bg-raised hover:bg-hairline text-text-primary text-xs font-semibold border border-hairline transition-colors flex items-center gap-1.5"
          >
            <PlusCircle className="w-3.5 h-3.5 text-amber" />
            Add Wallet to Watch
          </button>
        </div>
      </div>

      {explainMode && (
        <div className="p-3 bg-cyan/10 border border-cyan/30 rounded-lg text-xs text-cyan flex items-start gap-2.5">
          <Sparkles className="w-4 h-4 shrink-0 mt-0.5" />
          <div>
            <span className="font-bold">Investigator Workflow:</span> Suspects often leave funds dormant for weeks until police heat cools down.
            Placing an address on the Watchlist ensures the moment an unspent balance moves, ChainNetra instantly fires an alert to notify investigating officers and dispatch automated SIEM webhooks.
          </div>
        </div>
      )}

      {/* Grid: Watchlist Table & Live Alerts Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Left (7 Cols): Monitored Addresses Table */}
        <div className="lg:col-span-7 bg-panel border border-hairline rounded-xl overflow-hidden shadow">
          <div className="p-3 border-b border-hairline flex items-center justify-between">
            <h3 className="text-xs font-bold text-text-primary tracking-wide">
              Active Monitored Wallets ({watchlist.length})
            </h3>
            <span className="text-[10px] font-mono text-text-muted">Threshold: &gt; $50 USD</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-raised/70 border-b border-hairline text-[10px] text-text-muted uppercase">
                <tr>
                  <th className="p-3">Target Address</th>
                  <th className="p-3">Chain</th>
                  <th className="p-3">Label / Reason</th>
                  <th className="p-3">Alert Rules</th>
                  <th className="p-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-hairline">
                {watchlist.map((w) => (
                  <tr key={w.id} className="hover:bg-raised/40 transition-colors">
                    <td className="p-3 text-cyan truncate max-w-[160px]">
                      {w.address}
                    </td>

                    <td className="p-3 uppercase font-bold text-amber">
                      {w.chain}
                    </td>

                    <td className="p-3">
                      <div className="text-text-primary font-sans font-medium">{w.label || 'Mule Target'}</div>
                      <div className="text-[10px] text-text-muted truncate max-w-[130px]">{w.reason}</div>
                    </td>

                    <td className="p-3">
                      <span className="px-1.5 py-0.2 rounded bg-ink border border-hairline text-[9px] text-mint">
                        Outflows &gt; $50
                      </span>
                    </td>

                    <td className="p-3 text-right">
                      <button
                        onClick={() => handleRemove(w.id)}
                        className="text-text-muted hover:text-coral transition-colors p-1"
                        title="Remove from watchlist"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right (5 Cols): Live Alerts Feed */}
        <div className="lg:col-span-5 bg-panel border border-hairline rounded-xl flex flex-col shadow">
          <div className="p-3 border-b border-hairline flex items-center justify-between">
            <h3 className="text-xs font-bold text-text-primary tracking-wide flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-coral animate-ping" />
              Real-Time Alert Feed ({alerts.length})
            </h3>
            <span className="text-[10px] font-mono text-text-muted">Instant WebSocket Delivery</span>
          </div>

          <div className="p-3 space-y-2.5 overflow-y-auto max-h-[500px]">
            {alerts.length === 0 ? (
              <div className="text-center py-10 text-text-muted text-xs">
                No alerts logged.
              </div>
            ) : (
              alerts.map((al) => (
                <div 
                  key={al.id} 
                  className={`p-3 rounded-lg border transition-colors ${
                    al.is_acknowledged 
                      ? 'bg-ink/60 border-hairline opacity-60' 
                      : 'bg-raised/70 border-coral/40 shadow-sm'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className={`px-1.5 py-0.2 rounded font-mono text-[9px] uppercase font-bold ${
                      al.severity === 'Critical' ? 'bg-coral/20 text-coral' : 'bg-amber/20 text-amber'
                    }`}>
                      {al.type} • {al.severity}
                    </span>
                    <span className="text-[10px] text-text-muted font-mono">
                      {new Date(al.created_at).toLocaleTimeString()}
                    </span>
                  </div>

                  <h4 className="text-xs font-bold text-text-primary">{al.title}</h4>
                  <p className="text-[11px] text-text-muted mt-1 leading-relaxed">{al.message}</p>

                  <div className="flex items-center justify-between mt-2.5 pt-2 border-t border-hairline/60">
                    <span className="text-[10px] font-mono text-cyan truncate max-w-[180px]">
                      {al.address}
                    </span>

                    {!al.is_acknowledged ? (
                      <button
                        onClick={() => handleAck(al.id)}
                        className="px-2 py-0.5 rounded bg-raised hover:bg-hairline border border-hairline text-[10px] text-mint font-semibold flex items-center gap-1"
                      >
                        <CheckCircle2 className="w-3 h-3" /> Acknowledge
                      </button>
                    ) : (
                      <span className="text-[10px] text-text-muted font-mono">Acknowledged ✓</span>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Add to Watchlist Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in">
          <div className="w-full max-w-md bg-panel border border-hairline rounded-xl shadow-2xl p-5 space-y-4">
            <h2 className="text-base font-bold text-text-primary">Add Wallet to Active Mempool Watchlist</h2>
            <form onSubmit={handleAddSubmit} className="space-y-3 text-xs">
              <div>
                <label className="block text-text-muted mb-1">Blockchain Network</label>
                <select
                  value={newChain}
                  onChange={(e) => setNewChain(e.target.value)}
                  className="w-full bg-ink border border-hairline rounded-lg px-3 py-2 text-text-primary focus:border-amber focus:outline-none"
                >
                  <option value="tron">Tron (TRC-20)</option>
                  <option value="ethereum">Ethereum (ERC-20)</option>
                  <option value="bsc">BSC (BEP-20)</option>
                  <option value="bitcoin">Bitcoin</option>
                  <option value="arbitrum">Arbitrum</option>
                </select>
              </div>

              <div>
                <label className="block text-text-muted mb-1">Target Wallet Address</label>
                <input
                  type="text"
                  required
                  placeholder="Paste T..., 0x..., or bc1... wallet address"
                  value={newAddr}
                  onChange={(e) => setNewAddr(e.target.value)}
                  className="w-full bg-ink border border-hairline rounded-lg px-3 py-2 font-mono text-text-primary focus:border-amber focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-text-muted mb-1">Label / Alias</label>
                <input
                  type="text"
                  placeholder="e.g. Scammer Dormant Reserve"
                  value={newLabel}
                  onChange={(e) => setNewLabel(e.target.value)}
                  className="w-full bg-ink border border-hairline rounded-lg px-3 py-2 text-text-primary focus:border-amber focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-text-muted mb-1">Reason for Monitoring</label>
                <input
                  type="text"
                  value={newReason}
                  onChange={(e) => setNewReason(e.target.value)}
                  className="w-full bg-ink border border-hairline rounded-lg px-3 py-2 text-text-primary focus:border-amber focus:outline-none"
                />
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-hairline">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-3 py-1.5 rounded-lg text-text-muted hover:text-text-primary"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded-lg bg-amber text-ink font-bold hover:bg-amber-400"
                >
                  Activate Watch
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
