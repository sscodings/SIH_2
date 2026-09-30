import React, { useState, useEffect } from 'react';
import { 
  Settings as SettingsIcon, ShieldCheck, Tag, Cpu, 
  CheckCircle2, AlertTriangle, PlusCircle, Trash2, Sparkles, RefreshCw, Lock 
} from 'lucide-react';
import toast from 'react-hot-toast';
import { api } from '../lib/api';
import { useAppStore } from '../stores/useAppStore';

export const Admin: React.FC = () => {
  const explainMode = useAppStore((s) => s.explainMode);
  const mode = useAppStore((s) => s.mode);
  const setMode = useAppStore((s) => s.setMode);

  const [activeTab, setActiveTab] = useState<'audit' | 'labels' | 'settings' | 'model'>('audit');

  // Audit Log State
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [chainIntegrity, setChainIntegrity] = useState<any>(null);

  // Labels State
  const [labels, setLabels] = useState<any[]>([]);
  const [newLabelAddr, setNewLabelAddr] = useState('');
  const [newLabelEntity, setNewLabelEntity] = useState('');
  const [newLabelChain, setNewLabelChain] = useState('tron');

  // Settings State
  const [usdInr, setUsdInr] = useState('83.50');

  // Model Card
  const [modelCard, setModelCard] = useState<any>(null);

  const loadAdminData = async () => {
    try {
      const [auditRes, checkRes, labelRes, setRes, cardRes] = await Promise.all([
        api.getAuditLog(),
        api.verifyAuditChain(),
        api.getLabels(),
        api.getSettings(),
        api.getModelCard()
      ]);
      setAuditLogs(auditRes.logs || []);
      setChainIntegrity(checkRes);
      setLabels(labelRes.labels || []);
      if (setRes.USD_INR) setUsdInr(setRes.USD_INR);
      setModelCard(cardRes);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadAdminData();
  }, []);

  const handleVerifyChain = async () => {
    try {
      const res = await api.verifyAuditChain();
      setChainIntegrity(res);
      if (res.valid) {
        toast.success(`Audit chain verified: All ${res.count} records intact!`);
      } else {
        toast.error(`TAMPER DETECTED: ${res.reason}`);
      }
    } catch (e) {
      toast.error('Verification failed');
    }
  };

  const handleSimulateTamper = async () => {
    try {
      await api.tamperAuditLog();
      toast.error('Simulated row edit! Re-verifying chain...');
      const check = await api.verifyAuditChain();
      setChainIntegrity(check);
    } catch (e) {
      toast.error('Tamper test failed');
    }
  };

  const handleAddLabel = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newLabelAddr.trim() || !newLabelEntity.trim()) return;
    try {
      await api.createLabel({
        address: newLabelAddr.trim(),
        chain: newLabelChain,
        entity: newLabelEntity.trim(),
        category: 'VASP Deposit Address'
      });
      toast.success('Label added to registry!');
      setNewLabelAddr('');
      setNewLabelEntity('');
      loadAdminData();
    } catch (e) {
      toast.error('Failed to add label');
    }
  };

  const handleDeleteLabel = async (id: number) => {
    try {
      await api.deleteLabel(id);
      toast('Label deleted');
      loadAdminData();
    } catch (e) {
      toast.error('Delete failed');
    }
  };

  return (
    <div className="space-y-4 animate-in fade-in duration-200">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-2 border-b border-hairline">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-text-primary flex items-center gap-2">
            System Administration & Cryptographic Audit
            <span className="text-xs px-2 py-0.5 rounded font-mono font-bold bg-amber/15 border border-amber/30 text-amber">
              ADMIN CONTROL PANEL
            </span>
          </h1>
          <p className="text-xs text-text-muted mt-0.5">
            Cryptographic chain-of-custody audit logs, forensic label management, and ML classifier model cards.
          </p>
        </div>

        {/* Tab Buttons */}
        <div className="flex items-center gap-1 bg-raised p-1 rounded-lg border border-hairline text-xs font-mono">
          <button
            onClick={() => setActiveTab('audit')}
            className={`px-3 py-1 rounded-md transition-colors ${activeTab === 'audit' ? 'bg-amber text-ink font-bold' : 'text-text-muted hover:text-text-primary'}`}
          >
            Audit Log Chain
          </button>
          <button
            onClick={() => setActiveTab('labels')}
            className={`px-3 py-1 rounded-md transition-colors ${activeTab === 'labels' ? 'bg-amber text-ink font-bold' : 'text-text-muted hover:text-text-primary'}`}
          >
            Label Manager
          </button>
          <button
            onClick={() => setActiveTab('model')}
            className={`px-3 py-1 rounded-md transition-colors ${activeTab === 'model' ? 'bg-amber text-ink font-bold' : 'text-text-muted hover:text-text-primary'}`}
          >
            ML Model Card
          </button>
          <button
            onClick={() => setActiveTab('settings')}
            className={`px-3 py-1 rounded-md transition-colors ${activeTab === 'settings' ? 'bg-amber text-ink font-bold' : 'text-text-muted hover:text-text-primary'}`}
          >
            Config Settings
          </button>
        </div>
      </div>

      {/* TAB 1: AUDIT LOG WITH HASH CHAIN */}
      {activeTab === 'audit' && (
        <div className="space-y-4">
          {/* Integrity Status Card */}
          <div className="p-4 rounded-xl bg-panel border border-hairline flex flex-col md:flex-row md:items-center justify-between gap-3 shadow">
            <div className="flex items-center gap-3">
              {chainIntegrity?.valid ? (
                <div className="w-10 h-10 rounded-full bg-mint/20 border border-mint/40 flex items-center justify-center">
                  <CheckCircle2 className="w-6 h-6 text-mint" />
                </div>
              ) : (
                <div className="w-10 h-10 rounded-full bg-coral/20 border border-coral/40 flex items-center justify-center">
                  <AlertTriangle className="w-6 h-6 text-coral" />
                </div>
              )}
              <div>
                <h3 className="text-sm font-bold text-text-primary flex items-center gap-2">
                  Hash Chain of Custody Integrity: {chainIntegrity?.valid ? (
                    <span className="text-mint font-mono font-bold">VERIFIED ✓</span>
                  ) : (
                    <span className="text-coral font-mono font-bold">COMPROMISED ✗</span>
                  )}
                </h3>
                <p className="text-xs text-text-muted mt-0.5">{chainIntegrity?.message || chainIntegrity?.reason}</p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={handleVerifyChain}
                className="px-3.5 py-1.5 rounded-lg bg-mint text-ink font-bold text-xs hover:bg-mint-400 transition-colors shadow flex items-center gap-1.5"
              >
                <ShieldCheck className="w-3.5 h-3.5" /> Verify Chain
              </button>

              <button
                onClick={handleSimulateTamper}
                className="px-3 py-1.5 rounded-lg bg-raised hover:bg-hairline text-coral border border-hairline text-xs font-semibold transition-colors"
                title="Simulate unauthorized SQL edit to demonstrate tamper detection"
              >
                Simulate Tamper
              </button>
            </div>
          </div>

          {/* Audit Log Entries Table */}
          <div className="bg-panel border border-hairline rounded-xl overflow-hidden shadow">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-raised/70 border-b border-hairline text-[10px] text-text-muted uppercase">
                  <tr>
                    <th className="p-3">ID</th>
                    <th className="p-3">Timestamp</th>
                    <th className="p-3">Actor</th>
                    <th className="p-3">Forensic Action</th>
                    <th className="p-3">Entity</th>
                    <th className="p-3">Previous Hash</th>
                    <th className="p-3">Entry Hash (SHA-256)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-hairline">
                  {auditLogs.map((log) => (
                    <tr key={log.id} className="hover:bg-raised/40 transition-colors">
                      <td className="p-3 font-bold text-text-primary">#{log.id}</td>
                      <td className="p-3 text-text-muted">{new Date(log.timestamp).toLocaleTimeString()}</td>
                      <td className="p-3 text-cyan">{log.user_email}</td>
                      <td className="p-3 font-semibold text-text-primary">{log.action}</td>
                      <td className="p-3 text-text-muted">{log.entity_type} {log.entity_id}</td>
                      <td className="p-3 text-text-muted truncate max-w-[120px]" title={log.prev_hash}>{log.prev_hash}</td>
                      <td className="p-3 text-mint truncate max-w-[120px]" title={log.entry_hash}>{log.entry_hash}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: LABELS MANAGER */}
      {activeTab === 'labels' && (
        <div className="space-y-4">
          <form onSubmit={handleAddLabel} className="p-4 bg-panel border border-hairline rounded-xl grid grid-cols-1 md:grid-cols-4 gap-3 text-xs">
            <input
              type="text"
              required
              placeholder="Wallet Address (T... or 0x...)"
              value={newLabelAddr}
              onChange={(e) => setNewLabelAddr(e.target.value)}
              className="bg-ink border border-hairline rounded-lg px-3 py-1.5 font-mono text-text-primary focus:border-amber focus:outline-none"
            />
            <input
              type="text"
              required
              placeholder="Entity Name (e.g. Apex OTC Desk)"
              value={newLabelEntity}
              onChange={(e) => setNewLabelEntity(e.target.value)}
              className="bg-ink border border-hairline rounded-lg px-3 py-1.5 text-text-primary focus:border-amber focus:outline-none"
            />
            <select
              value={newLabelChain}
              onChange={(e) => setNewLabelChain(e.target.value)}
              className="bg-ink border border-hairline rounded-lg px-3 py-1.5 text-text-primary focus:border-amber focus:outline-none"
            >
              <option value="tron">Tron</option>
              <option value="ethereum">Ethereum</option>
              <option value="bsc">BSC</option>
              <option value="bitcoin">Bitcoin</option>
            </select>
            <button
              type="submit"
              className="px-4 py-1.5 rounded-lg bg-amber text-ink font-bold hover:bg-amber-400"
            >
              Add Label
            </button>
          </form>

          <div className="bg-panel border border-hairline rounded-xl overflow-hidden shadow">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-raised/70 border-b border-hairline text-[10px] text-text-muted uppercase">
                <tr>
                  <th className="p-3">Address</th>
                  <th className="p-3">Chain</th>
                  <th className="p-3">Entity</th>
                  <th className="p-3">Category</th>
                  <th className="p-3">Source & Weight</th>
                  <th className="p-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-hairline">
                {labels.map((lbl) => (
                  <tr key={lbl.id} className="hover:bg-raised/40">
                    <td className="p-3 text-cyan truncate max-w-[150px]">{lbl.address}</td>
                    <td className="p-3 uppercase text-amber">{lbl.chain}</td>
                    <td className="p-3 font-bold text-text-primary">{lbl.entity}</td>
                    <td className="p-3 text-text-muted">{lbl.category}</td>
                    <td className="p-3 text-text-muted">{lbl.source} ({(lbl.confidence * 100).toFixed(0)}%)</td>
                    <td className="p-3 text-right">
                      <button onClick={() => handleDeleteLabel(lbl.id)} className="text-text-muted hover:text-coral">
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 3: MODEL CARD */}
      {activeTab === 'model' && (
        <div className="p-5 bg-panel border border-hairline rounded-xl space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-hairline">
            <div>
              <h3 className="text-base font-bold text-text-primary flex items-center gap-2">
                <Cpu className="w-5 h-5 text-amber" />
                {modelCard?.model_name || 'ChainNetra Forensic Classifier'}
              </h3>
              <p className="text-xs text-text-muted mt-0.5">
                Multi-class RandomForest and IsolationForest trained on synthetic forensic topologies.
              </p>
            </div>
            <span className="px-3 py-1 rounded bg-mint/15 text-mint border border-mint/30 font-mono text-xs font-bold">
              Accuracy: {((modelCard?.accuracy || 1.0) * 100).toFixed(1)}%
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
            <div className="p-3 bg-raised/50 rounded-lg border border-hairline space-y-2">
              <h4 className="font-bold text-amber">Training Dataset Overview</h4>
              <div>Samples: <span className="text-text-primary">{modelCard?.training_samples || 2000} synthetic records</span></div>
              <div>Classes: <span className="text-text-primary">{modelCard?.classes?.join(', ')}</span></div>
              <div className="text-[10px] text-text-muted mt-2">
                Synthetic ground-truth scenarios include Case Zero, Task fraud peel chains, Sextortion mixers, and Ransomware bridges.
              </div>
            </div>

            <div className="p-3 bg-raised/50 rounded-lg border border-hairline space-y-2">
              <h4 className="font-bold text-cyan">Feature Importances</h4>
              <div className="space-y-1 text-[11px]">
                {modelCard?.feature_importances && Object.entries(modelCard.feature_importances).slice(0, 5).map(([k, v]: any) => (
                  <div key={k} className="flex justify-between">
                    <span className="text-text-muted">{k}:</span>
                    <span className="text-text-primary font-bold">{(v * 100).toFixed(1)}%</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 4: CONFIG SETTINGS */}
      {activeTab === 'settings' && (
        <div className="p-5 bg-panel border border-hairline rounded-xl space-y-4 max-w-xl">
          <h3 className="text-sm font-bold text-text-primary">System Settings</h3>
          <div className="space-y-3 text-xs">
            <div>
              <label className="block text-text-muted mb-1">Operating Mode</label>
              <div className="flex gap-2 font-mono">
                <button
                  type="button"
                  onClick={() => setMode('DEMO')}
                  className={`px-4 py-2 rounded-lg border font-bold ${mode === 'DEMO' ? 'bg-amber text-ink border-amber' : 'bg-raised text-text-muted border-hairline'}`}
                >
                  DEMO MODE (Offline Synthetic)
                </button>
                <button
                  type="button"
                  onClick={() => setMode('LIVE')}
                  className={`px-4 py-2 rounded-lg border font-bold ${mode === 'LIVE' ? 'bg-mint text-ink border-mint' : 'bg-raised text-text-muted border-hairline'}`}
                >
                  LIVE MODE (Public APIs)
                </button>
              </div>
            </div>

            <div>
              <label className="block text-text-muted mb-1">Static USD to INR Conversion Rate</label>
              <input
                type="text"
                value={usdInr}
                onChange={(e) => setUsdInr(e.target.value)}
                className="w-full bg-ink border border-hairline rounded-lg px-3 py-2 font-mono text-text-primary focus:border-amber focus:outline-none"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
