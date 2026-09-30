import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { 
  ShieldAlert, Clock, IndianRupee, Building2, Lock, 
  TrendingUp, PlayCircle, PlusCircle, AlertCircle, ArrowUpRight, 
  CheckCircle2, Sparkles, Filter, RefreshCw
} from 'lucide-react';
import { 
  ResponsiveContainer, PieChart, Pie, Cell, 
  BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Legend 
} from 'recharts';
import { api } from '../lib/api';
import { useAppStore } from '../stores/useAppStore';

export const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const explainMode = useAppStore((s) => s.explainMode);
  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState<any>(null);
  const [typologies, setTypologies] = useState<any[]>([]);
  const [vasps, setVasps] = useState<any[]>([]);
  const [chains, setChains] = useState<any[]>([]);
  const [responseTime, setResponseTime] = useState<any[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [sumRes, typRes, vaspRes, chainRes, respRes, alertRes] = await Promise.all([
        api.getAnalyticsSummary(),
        api.getTypologies(),
        api.getTopVasps(),
        api.getChains(),
        api.getResponseTime(),
        api.getAlerts()
      ]);
      setSummary(sumRes);
      setTypologies(typRes);
      setVasps(vaspRes);
      setChains(chainRes);
      setResponseTime(respRes.comparison || []);
      setAlerts(alertRes.alerts?.slice(0, 5) || []);
    } catch (e) {
      console.error('Dashboard load error:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSimulateComplaint = async () => {
    try {
      await api.simulateComplaint();
      loadData();
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="space-y-5 animate-in fade-in duration-200">
      {/* Page Header & Quick Actions */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-hairline">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-text-primary flex items-center gap-2">
            Forensic Command Center
            <span className="text-xs px-2 py-0.5 rounded font-mono font-medium bg-amber/10 border border-amber/30 text-amber">
              ACTIVE OPERATIONS
            </span>
          </h1>
          <p className="text-xs text-text-muted mt-1">
            Real-time cryptocurrency fraud attribution, multi-chain tracing, and VASP freeze intelligence.
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={() => navigate('/cases/1')}
            className="px-3.5 py-1.5 rounded-lg bg-amber text-ink font-bold text-xs hover:bg-amber-400 transition-colors flex items-center gap-1.5 shadow"
          >
            <PlayCircle className="w-3.5 h-3.5" />
            Launch Case Zero Demo
          </button>

          <button
            onClick={handleSimulateComplaint}
            className="px-3.5 py-1.5 rounded-lg bg-raised hover:bg-hairline text-text-primary text-xs font-semibold border border-hairline transition-colors flex items-center gap-1.5"
          >
            <PlusCircle className="w-3.5 h-3.5 text-cyan" />
            Simulate NCRP Complaint
          </button>

          <button
            onClick={loadData}
            className="p-1.5 rounded-lg bg-raised hover:bg-hairline text-text-muted hover:text-text-primary border border-hairline transition-colors"
            title="Refresh Data"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {explainMode && (
        <div className="p-3 bg-cyan/10 border border-cyan/30 rounded-lg text-xs text-cyan flex items-start gap-2.5">
          <Sparkles className="w-4 h-4 shrink-0 mt-0.5" />
          <div>
            <span className="font-bold">Investigator Quick Guidance:</span> The metrics below aggregate all complaint inflows from simulated NCRP feeds.
            The signature <span className="underline font-bold">Time-to-VASP</span> KPI demonstrates that ChainNetra finds the cash-out exchange in seconds, whereas manual blockchain analysis averages ~3 days.
          </div>
        </div>
      )}

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
        {/* Open Cases */}
        <div className="bg-panel border border-hairline rounded-xl p-3.5 flex flex-col justify-between hover:border-amber/40 transition-colors">
          <div className="flex items-center justify-between text-text-muted">
            <span className="text-[11px] font-medium">Active Cases</span>
            <ShieldAlert className="w-4 h-4 text-amber" />
          </div>
          <div className="mt-2">
            <span className="text-2xl font-bold font-mono text-text-primary">{summary?.open_cases || 5}</span>
            <span className="text-[10px] text-text-muted ml-1">/ {summary?.total_cases || 65}</span>
          </div>
          <span className="text-[10px] text-amber font-mono mt-1">+1 Priority High</span>
        </div>

        {/* Complaints Today */}
        <div className="bg-panel border border-hairline rounded-xl p-3.5 flex flex-col justify-between hover:border-cyan/40 transition-colors">
          <div className="flex items-center justify-between text-text-muted">
            <span className="text-[11px] font-medium">Complaints Today</span>
            <TrendingUp className="w-4 h-4 text-cyan" />
          </div>
          <div className="mt-2">
            <span className="text-2xl font-bold font-mono text-cyan">{summary?.complaints_today || 14}</span>
          </div>
          <span className="text-[10px] text-text-muted font-mono">NCRP / SAHYOG feed</span>
        </div>

        {/* Avg Time to VASP */}
        <div className="bg-panel border border-hairline rounded-xl p-3.5 flex flex-col justify-between hover:border-mint/40 transition-colors col-span-2 md:col-span-1">
          <div className="flex items-center justify-between text-text-muted">
            <span className="text-[11px] font-medium">Time-to-VASP</span>
            <Clock className="w-4 h-4 text-mint" />
          </div>
          <div className="mt-2">
            <span className="text-2xl font-bold font-mono text-mint">{summary?.avg_time_to_vasp_seconds || 3.1}s</span>
          </div>
          <span className="text-[10px] text-text-muted">vs 3 days manual</span>
        </div>

        {/* Total Value Traced */}
        <div className="bg-panel border border-hairline rounded-xl p-3.5 flex flex-col justify-between hover:border-amber/40 transition-colors col-span-2 md:col-span-1">
          <div className="flex items-center justify-between text-text-muted">
            <span className="text-[11px] font-medium">Value Traced (₹)</span>
            <IndianRupee className="w-4 h-4 text-amber" />
          </div>
          <div className="mt-2">
            <span className="text-lg font-bold font-mono text-text-primary">
              ₹{((summary?.total_value_traced_inr || 118600000) / 10000000).toFixed(2)} Cr
            </span>
          </div>
          <span className="text-[10px] text-text-muted font-mono">${((summary?.total_value_traced_usd || 1420500) / 1000).toFixed(0)}k USD</span>
        </div>

        {/* VASPs Identified */}
        <div className="bg-panel border border-hairline rounded-xl p-3.5 flex flex-col justify-between hover:border-cyan/40 transition-colors">
          <div className="flex items-center justify-between text-text-muted">
            <span className="text-[11px] font-medium">VASPs Pinpointed</span>
            <Building2 className="w-4 h-4 text-cyan" />
          </div>
          <div className="mt-2">
            <span className="text-2xl font-bold font-mono text-text-primary">{summary?.vasps_identified || 22}</span>
          </div>
          <span className="text-[10px] text-mint font-mono">Attribution 90%+</span>
        </div>

        {/* Freeze Requests */}
        <div className="bg-panel border border-hairline rounded-xl p-3.5 flex flex-col justify-between hover:border-coral/40 transition-colors">
          <div className="flex items-center justify-between text-text-muted">
            <span className="text-[11px] font-medium">Freeze Notices</span>
            <Lock className="w-4 h-4 text-coral" />
          </div>
          <div className="mt-2">
            <span className="text-2xl font-bold font-mono text-coral">{summary?.freeze_requests_sent || 5}</span>
          </div>
          <span className="text-[10px] text-text-muted font-mono">{summary?.freeze_requests_acknowledged || 3} acknowledged</span>
        </div>

        {/* Funds Recoverable (Dormant) */}
        <div className="bg-panel border border-hairline rounded-xl p-3.5 flex flex-col justify-between hover:border-mint/40 transition-colors col-span-2 md:col-span-1">
          <div className="flex items-center justify-between text-text-muted">
            <span className="text-[11px] font-medium">Recoverable (Dormant)</span>
            <CheckCircle2 className="w-4 h-4 text-mint" />
          </div>
          <div className="mt-2">
            <span className="text-lg font-bold font-mono text-mint">
              ₹{((summary?.funds_recoverable_inr || 3340000) / 100000).toFixed(1)} L
            </span>
          </div>
          <span className="text-[10px] text-text-muted font-mono">${(summary?.funds_recoverable_usd || 40000).toLocaleString()} USD</span>
        </div>
      </div>

      {/* Main Charts & Alert Feed Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Left 2 Cols: Forensic Charts */}
        <div className="lg:col-span-2 space-y-4">
          {/* Top Row: Fraud Typologies & Value by Chain */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Typology Donut */}
            <div className="bg-panel border border-hairline rounded-xl p-4 flex flex-col">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-xs font-bold text-text-primary tracking-wide">Fraud Typology Breakdown</h3>
                <span className="text-[10px] font-mono text-text-muted">Rule & ML Match</span>
              </div>
              <div className="h-52 w-full flex items-center justify-center">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={typologies}
                      cx="50%"
                      cy="50%"
                      innerRadius={45}
                      outerRadius={70}
                      paddingAngle={3}
                      dataKey="value"
                    >
                      {typologies.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#0D1424', borderColor: '#1F2B47', fontSize: '11px', borderRadius: '8px' }}
                      itemStyle={{ color: '#E6ECFF' }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              {/* Legend row */}
              <div className="grid grid-cols-2 gap-1.5 mt-2 text-[10px] text-text-muted font-mono">
                {typologies.slice(0, 4).map((t, idx) => (
                  <div key={idx} className="flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: t.color }} />
                    <span className="truncate">{t.name}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Traced Value by Chain */}
            <div className="bg-panel border border-hairline rounded-xl p-4 flex flex-col">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-xs font-bold text-text-primary tracking-wide">Traced Illicit Value by Chain</h3>
                <span className="text-[10px] font-mono text-text-muted">USD</span>
              </div>
              <div className="h-52 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chains}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1F2B47" opacity={0.5} />
                    <XAxis dataKey="chain" stroke="#8A97B8" fontSize={10} tickLine={false} />
                    <YAxis stroke="#8A97B8" fontSize={10} tickLine={false} tickFormatter={(val) => `$${val/1000}k`} />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#0D1424', borderColor: '#1F2B47', fontSize: '11px', borderRadius: '8px' }}
                      formatter={(val: any) => [`$${Number(val).toLocaleString()}`, 'Value']}
                    />
                    <Bar dataKey="value_usd" fill="#FFB020" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="text-[10px] text-text-muted text-center font-mono mt-2">
                Tron (TRC-20 USDT) dominates investment & task scam consolidation corridors
              </div>
            </div>
          </div>

          {/* Bottom Row: Response Time Benchmark (ChainNetra vs Manual) */}
          <div className="bg-panel border border-hairline rounded-xl p-4">
            <div className="flex items-center justify-between mb-2">
              <div>
                <h3 className="text-xs font-bold text-text-primary tracking-wide">Investigation Response Time Benchmark</h3>
                <p className="text-[11px] text-text-muted">Time taken to locate target cashout VASP: Manual Expert Tracing vs Automated ChainNetra</p>
              </div>
              <span className="px-2 py-0.5 rounded bg-mint/15 text-mint border border-mint/30 text-[10px] font-mono font-bold">
                99.8% TIME SAVING
              </span>
            </div>
            <div className="h-44 w-full mt-3">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={responseTime}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1F2B47" opacity={0.5} />
                  <XAxis dataKey="case" stroke="#8A97B8" fontSize={10} tickLine={false} />
                  <YAxis stroke="#8A97B8" fontSize={10} tickLine={false} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0D1424', borderColor: '#1F2B47', fontSize: '11px', borderRadius: '8px' }}
                  />
                  <Legend wrapperStyle={{ fontSize: '10px' }} />
                  <Bar dataKey="automated_seconds" name="ChainNetra (Seconds)" fill="#3DDC97" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="manual_hours" name="Manual Baseline (Hours / 72h avg)" fill="#FF5D5D" opacity={0.4} radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Right Col: Live Alerts Feed & Top Receiving VASPs */}
        <div className="space-y-4 flex flex-col justify-between">
          {/* Live Alert Feed */}
          <div className="bg-panel border border-hairline rounded-xl p-4 flex-1 flex flex-col">
            <div className="flex items-center justify-between pb-2 border-b border-hairline mb-3">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-coral animate-ping" />
                <h3 className="text-xs font-bold text-text-primary tracking-wide">Live Forensic Alert Feed</h3>
              </div>
              <Link to="/watchlist" className="text-[10px] text-amber hover:underline font-mono flex items-center">
                All Alerts <ArrowUpRight className="w-3 h-3 ml-0.5" />
              </Link>
            </div>

            <div className="space-y-2.5 flex-1 overflow-y-auto max-h-72 pr-1">
              {alerts.length === 0 ? (
                <div className="text-center py-8 text-text-muted text-xs">
                  No active alerts. All monitored addresses dormant.
                </div>
              ) : (
                alerts.map((al) => (
                  <div key={al.id} className="p-2.5 rounded-lg bg-raised/70 border border-hairline hover:border-hairline/80 transition-colors">
                    <div className="flex items-center justify-between mb-1">
                      <span className={`text-[9px] font-mono px-1.5 py-0.2 rounded uppercase font-bold ${
                        al.severity === 'Critical' ? 'bg-coral/20 text-coral border border-coral/40' : 'bg-amber/20 text-amber border border-amber/40'
                      }`}>
                        {al.severity}
                      </span>
                      <span className="text-[10px] text-text-muted font-mono">
                        {al.created_at ? new Date(al.created_at).toLocaleTimeString() : 'Just now'}
                      </span>
                    </div>
                    <p className="text-xs font-semibold text-text-primary line-clamp-1">{al.title}</p>
                    <p className="text-[11px] text-text-muted line-clamp-2 mt-0.5">{al.message}</p>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Top Receiving VASPs Leaderboard */}
          <div className="bg-panel border border-hairline rounded-xl p-4">
            <div className="flex items-center justify-between mb-3 pb-2 border-b border-hairline">
              <h3 className="text-xs font-bold text-text-primary tracking-wide">Top Receiving VASPs</h3>
              <Link to="/vasps" className="text-[10px] text-cyan hover:underline font-mono">
                Directory
              </Link>
            </div>
            <div className="space-y-2">
              {vasps.map((v, idx) => (
                <div key={idx} className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-mono text-text-muted w-3">{idx + 1}.</span>
                    <span className="font-medium text-text-primary">{v.vasp}</span>
                  </div>
                  <div className="flex items-center gap-2 font-mono text-[11px]">
                    <span className="text-amber font-semibold">${(v.value_usd / 1000).toFixed(0)}k</span>
                    <span className="text-[10px] text-text-muted">({v.count} hits)</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
