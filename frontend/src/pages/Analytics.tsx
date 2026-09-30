import React, { useState, useEffect } from 'react';
import { 
  BarChart3, TrendingUp, IndianRupee, ShieldAlert, 
  Building2, MapPin, Sparkles, Filter 
} from 'lucide-react';
import { 
  ResponsiveContainer, BarChart, Bar, XAxis, 
  YAxis, Tooltip, CartesianGrid, Legend, LineChart, Line, PieChart, Pie, Cell 
} from 'recharts';
import { api } from '../lib/api';
import { useAppStore } from '../stores/useAppStore';

export const Analytics: React.FC = () => {
  const explainMode = useAppStore((s) => s.explainMode);
  const [summary, setSummary] = useState<any>(null);
  const [typologies, setTypologies] = useState<any[]>([]);
  const [vasps, setVasps] = useState<any[]>([]);
  const [stateWise, setStateWise] = useState<any[]>([]);
  const [responseTime, setResponseTime] = useState<any[]>([]);

  useEffect(() => {
    const loadAnalytics = async () => {
      try {
        const [sumRes, typRes, vaspRes, stateRes, respRes] = await Promise.all([
          api.getAnalyticsSummary(),
          api.getTypologies(),
          api.getTopVasps(),
          api.getStateWise(),
          api.getResponseTime()
        ]);
        setSummary(sumRes);
        setTypologies(typRes);
        setVasps(vaspRes);
        setStateWise(stateRes);
        setResponseTime(respRes.comparison || []);
      } catch (e) {
        console.error(e);
      }
    };
    loadAnalytics();
  }, []);

  return (
    <div className="space-y-4 animate-in fade-in duration-200">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-2 border-b border-hairline">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-text-primary flex items-center gap-2">
            Forensic Intelligence & Fraud Typology Analytics
            <span className="text-xs px-2 py-0.5 rounded font-mono font-bold bg-amber/15 border border-amber/30 text-amber">
              SUPERVISORY OVERSIGHT
            </span>
          </h1>
          <p className="text-xs text-text-muted mt-0.5">
            Macro trends, state-wise crime density, VASP receiving leaderboards, and recovery metrics.
          </p>
        </div>
      </div>

      {explainMode && (
        <div className="p-3 bg-cyan/10 border border-cyan/30 rounded-lg text-xs text-cyan flex items-start gap-2.5">
          <Sparkles className="w-4 h-4 shrink-0 mt-0.5" />
          <div>
            <span className="font-bold">Supervisory Intelligence:</span> This page gives senior police leadership (SPs and ADGs) an overarching operational perspective.
            Highlighting which foreign exchanges receive the highest volume of stolen Indian funds enables targeted diplomatic and FIU-IND notices.
          </div>
        </div>
      )}

      {/* Top Metric Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="p-4 bg-panel border border-hairline rounded-xl">
          <span className="text-[10px] font-mono text-text-muted uppercase">Cumulative Crime Value Traced</span>
          <div className="text-2xl font-bold font-mono text-amber mt-1">₹11.86 Crore</div>
          <span className="text-[10px] text-text-muted font-mono">$1,420,500 USD across 65 cases</span>
        </div>

        <div className="p-4 bg-panel border border-hairline rounded-xl">
          <span className="text-[10px] font-mono text-text-muted uppercase">Freeze Success Rate</span>
          <div className="text-2xl font-bold font-mono text-mint mt-1">78.4%</div>
          <span className="text-[10px] text-mint font-mono">Within 4-hour SLA window</span>
        </div>

        <div className="p-4 bg-panel border border-hairline rounded-xl">
          <span className="text-[10px] font-mono text-text-muted uppercase">Avg Hops to Cash-out VASP</span>
          <div className="text-2xl font-bold font-mono text-cyan mt-1">3.4 Hops</div>
          <span className="text-[10px] text-text-muted">Multi-layered mule consolidation</span>
        </div>

        <div className="p-4 bg-panel border border-hairline rounded-xl">
          <span className="text-[10px] font-mono text-text-muted uppercase">Funds in Tumblers / Mixers</span>
          <div className="text-2xl font-bold font-mono text-coral mt-1">11.2%</div>
          <span className="text-[10px] text-coral font-mono">Probabilistic tracking required</span>
        </div>
      </div>

      {/* Grid: Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* State-wise Distribution */}
        <div className="bg-panel border border-hairline rounded-xl p-4 flex flex-col">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-xs font-bold text-text-primary tracking-wide">
              State-Wise NCRP Complaint Volume
            </h3>
            <span className="text-[10px] font-mono text-text-muted">India Jurisdictions</span>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={stateWise.slice(0, 8)} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#1F2B47" opacity={0.5} />
                <XAxis type="number" stroke="#8A97B8" fontSize={10} />
                <YAxis dataKey="state" type="category" stroke="#8A97B8" fontSize={10} width={90} tickLine={false} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0D1424', borderColor: '#1F2B47', fontSize: '11px', borderRadius: '8px' }}
                />
                <Bar dataKey="complaints" fill="#FFB020" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* VASP Receiving Leaderboard */}
        <div className="bg-panel border border-hairline rounded-xl p-4 flex flex-col">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-xs font-bold text-text-primary tracking-wide">
              Top Fraud Inflow Receiving VASPs ($ USD)
            </h3>
            <span className="text-[10px] font-mono text-text-muted">Exchange Destinations</span>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={vasps}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1F2B47" opacity={0.5} />
                <XAxis dataKey="vasp" stroke="#8A97B8" fontSize={10} tickLine={false} />
                <YAxis stroke="#8A97B8" fontSize={10} tickLine={false} tickFormatter={(v) => `$${v/1000}k`} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0D1424', borderColor: '#1F2B47', fontSize: '11px', borderRadius: '8px' }}
                />
                <Bar dataKey="value_usd" fill="#22D3EE" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};
