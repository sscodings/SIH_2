import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  Shield, AlertTriangle, Copy, ExternalLink, Activity, 
  ArrowDownLeft, ArrowUpRight, Clock, Network, CheckCircle2, Sparkles 
} from 'lucide-react';
import { 
  ResponsiveContainer, RadarChart, PolarGrid, 
  PolarAngleAxis, PolarRadiusAxis, Radar 
} from 'recharts';
import toast from 'react-hot-toast';
import { api } from '../lib/api';
import { useAppStore } from '../stores/useAppStore';

export const WalletProfile: React.FC = () => {
  const { chain = 'tron', address = 'TXDemoxHotWalletPrimary88888888888' } = useParams<{ chain: string; address: string }>();
  const navigate = useNavigate();
  const explainMode = useAppStore((s) => s.explainMode);

  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);

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

  // Transform features into radar chart format
  const radarData = profile?.risk?.features ? [
    { subject: 'Fan-In (Depositors)', value: Math.min(100, (profile.risk.features.fan_in || 1) * 8) },
    { subject: 'Fan-Out (Sweeps)', value: Math.min(100, (profile.risk.features.fan_out || 1) * 12) },
    { subject: 'Pass-Through %', value: Math.min(100, (profile.risk.features.pass_through_ratio || 0.5) * 100) },
    { subject: 'Burstiness', value: Math.min(100, (profile.risk.features.burstiness || 1) * 8) },
    { subject: 'Round Amounts', value: Math.min(100, (profile.risk.features.round_amount_ratio || 0.2) * 100) },
    { subject: 'Mixer Exposure', value: profile.risk.features.mixer_exposure ? 100 : 10 }
  ] : [
    { subject: 'Fan-In', value: 80 },
    { subject: 'Fan-Out', value: 60 },
    { subject: 'Pass-Through', value: 95 },
    { subject: 'Burstiness', value: 70 },
    { subject: 'Round Amounts', value: 40 },
    { subject: 'Mixer Exposure', value: 10 }
  ];

  const copyToClipboard = () => {
    navigator.clipboard.writeText(address);
    toast.success('Address copied to clipboard');
  };

  return (
    <div className="space-y-4 animate-in fade-in duration-200">
      {/* Wallet Header */}
      <div className="p-4 bg-panel border border-hairline rounded-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-amber/15 border border-amber/30 flex items-center justify-center shrink-0">
            <Shield className="w-6 h-6 text-amber" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-mono font-bold text-cyan">{address}</span>
              <button onClick={copyToClipboard} className="text-text-muted hover:text-text-primary p-1">
                <Copy className="w-3.5 h-3.5" />
              </button>
            </div>
            <div className="flex items-center gap-3 text-xs text-text-muted font-mono mt-1">
              <span className="uppercase font-bold text-amber">{chain}</span>
              <span>•</span>
              <span>Role: <strong className="text-text-primary">{profile?.summary?.entity_label || 'Suspect Layering Wallet'}</strong></span>
              <span>•</span>
              <span>Tx Count: <strong>{profile?.summary?.tx_count || 12}</strong></span>
            </div>
          </div>
        </div>

        {/* Risk Gauge Badge */}
        <div className="flex items-center gap-3 bg-raised/70 px-4 py-2 rounded-xl border border-hairline shrink-0">
          <div className="text-right font-mono">
            <div className="text-[10px] text-text-muted uppercase">Forensic Risk Score</div>
            <div className="text-2xl font-bold text-coral">{profile?.risk?.risk_score || 85.0} / 100</div>
          </div>
          <span className={`px-2.5 py-1 rounded text-xs font-mono font-bold uppercase ${
            (profile?.risk?.risk_score || 85) >= 70 ? 'bg-coral/20 text-coral border border-coral/40' : 'bg-amber/20 text-amber'
          }`}>
            {profile?.risk?.risk_level || 'Critical'} Risk
          </span>
        </div>
      </div>

      {explainMode && (
        <div className="p-3 bg-cyan/10 border border-cyan/30 rounded-lg text-xs text-cyan flex items-start gap-2.5">
          <Sparkles className="w-4 h-4 shrink-0 mt-0.5" />
          <div>
            <span className="font-bold">Fingerprint Interpretation:</span> The radar chart visualizes the mathematical behavioral footprint of this wallet.
            High pass-through percentage combined with rapid burstiness strongly distinguishes professional money mules from legitimate cryptocurrency traders.
          </div>
        </div>
      )}

      {/* Grid: Radar Fingerprint & Top Contributing Factors */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Radar Behavioral Fingerprint */}
        <div className="bg-panel border border-hairline rounded-xl p-4 flex flex-col">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-xs font-bold text-text-primary tracking-wide">
              Behavioral Fingerprint (12 Forensic Signals)
            </h3>
            <span className="text-[10px] font-mono text-text-muted">Normalized 0-100</span>
          </div>

          <div className="h-64 w-full flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={radarData}>
                <PolarGrid stroke="#1F2B47" />
                <PolarAngleAxis dataKey="subject" stroke="#8A97B8" tick={{ fontSize: 10 }} />
                <PolarRadiusAxis stroke="#1F2B47" angle={30} domain={[0, 100]} />
                <Radar name="Wallet Profile" dataKey="value" stroke="#FFB020" fill="#FFB020" fillOpacity={0.3} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
          <div className="text-center font-mono text-[10px] text-text-muted mt-1">
            Distinctive high-velocity mule signature: rapid fan-out following multi-victim consolidation
          </div>
        </div>

        {/* Explainability: Top 5 Contributing Factors */}
        <div className="bg-panel border border-hairline rounded-xl p-4 flex flex-col justify-between">
          <div>
            <h3 className="text-xs font-bold text-text-primary tracking-wide mb-3">
              AI/ML Explainability: Top 5 Risk Factors
            </h3>

            <div className="space-y-2.5">
              {(profile?.risk?.top_factors || [
                { feature: 'Rapid Pass-Through Velocity', value: '98.5% swept in < 30 mins', impact: '+25', why: 'Characteristic of intermediary mule laundering address' },
                { feature: 'High Fan-In Concentration', value: '9 distinct victim senders', impact: '+20', why: 'Direct consolidation hub receiving multi-complainant proceeds' },
                { feature: 'Cross-Chain Bridge Interaction', value: 'SwiftBridge Tron->BSC', impact: '+15', why: 'Attempting ledger obfuscation via bridging protocol' },
                { feature: 'Burstiness Coefficient', value: '14.2 tx/day', impact: '+15', why: 'Unusual burst of high-frequency transfers' },
                { feature: 'Dormant Holdings Retained', value: '$40,000 USDT static', impact: '+10', why: 'Freeze candidate holding unspent crime proceeds' }
              ]).map((f: any, idx: number) => (
                <div key={idx} className="p-2.5 rounded-lg bg-raised/60 border border-hairline flex items-center justify-between text-xs">
                  <div>
                    <div className="font-semibold text-text-primary flex items-center gap-1.5">
                      <span>{f.feature}</span>
                      <span className="text-[10px] font-mono text-cyan">({f.value})</span>
                    </div>
                    <p className="text-[11px] text-text-muted mt-0.5">{f.why}</p>
                  </div>
                  <span className="px-2 py-0.5 rounded bg-coral/20 text-coral font-mono text-xs font-bold shrink-0">
                    {f.impact}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Linked Complaints & Cluster Membership */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Linked Complaints */}
        <div className="bg-panel border border-hairline rounded-xl p-4">
          <h3 className="text-xs font-bold text-text-primary tracking-wide mb-3">
            Linked NCRP Victim Complaints
          </h3>
          <div className="space-y-2">
            {(profile?.linked_complaints?.length ? profile.linked_complaints : [
              { complaint_number: 'NCRP-2026-000101', victim_name: 'Aarav Mehta', amount_lost_inr: 1850000, fraud_type: 'Investment Scam' },
              { complaint_number: 'NCRP-2026-000103', victim_name: 'Rohit Verma', amount_lost_inr: 980000, fraud_type: 'Investment Scam' }
            ]).map((c: any, idx: number) => (
              <div key={idx} className="p-2.5 rounded bg-raised border border-hairline flex items-center justify-between text-xs">
                <div>
                  <span className="font-mono font-bold text-cyan">{c.complaint_number}</span>
                  <div className="text-[11px] text-text-muted">{c.victim_name} • {c.fraud_type}</div>
                </div>
                <div className="font-mono font-bold text-amber">
                  ₹{Number(c.amount_lost_inr).toLocaleString('en-IN')}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Cluster Membership */}
        <div className="bg-panel border border-hairline rounded-xl p-4">
          <h3 className="text-xs font-bold text-text-primary tracking-wide mb-3">
            Forensic Cluster Association
          </h3>
          <div className="p-3 rounded-lg bg-raised border border-cyan/30 space-y-2 text-xs">
            <div className="flex items-center justify-between">
              <span className="font-bold text-cyan">Syndicate Cluster #09</span>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-panel text-text-muted">Common Sweep</span>
            </div>
            <p className="text-text-muted text-[11px]">
              This wallet forms part of an identified 5-member syndicate cluster that sweeps funds into common offshore VASP corridors.
            </p>
            <button
              onClick={() => navigate('/linking')}
              className="text-xs text-amber hover:underline font-mono inline-flex items-center gap-1 pt-1"
            >
              View on Evidence Board →
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
