import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

import toast from 'react-hot-toast';
import { api } from '../lib/api';
import { useAppStore } from '../stores/useAppStore';

export const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const explainMode = useAppStore((s) => s.explainMode);
  
  const [viewMode, setViewMode] = useState<'executive' | 'command'>('executive');
  const [isTraceModalOpen, setIsTraceModalOpen] = useState(false);
  const [traceAddress, setTraceAddress] = useState('TJ8wK9vZmB2pQ5aN8cXyZ3rP1kLmN7xL9');
  const [traceFir, setTraceFir] = useState('FIR-2024-8831-DEL');
  const [traceDepth, setTraceDepth] = useState('6');
  const [bridgeTracking, setBridgeTracking] = useState(true);
  const [isSubmittingTrace, setIsSubmittingTrace] = useState(false);

  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const loadData = async () => {
    try {
      setLoading(true);
      const res = await api.getAnalyticsSummary();
      setSummary(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSimulateNcrp = async () => {
    try {
      toast.loading('Simulating inbound NCRP complaint...', { id: 'sim' });
      await api.simulateComplaint();
      toast.success('New complaint NCRP-2024-99184 received and triaged!', { id: 'sim' });
      loadData();
    } catch {
      toast.error('Simulation failed', { id: 'sim' });
    }
  };

  const handleStartTrace = () => {
    setIsSubmittingTrace(true);
    setTimeout(() => {
      setIsSubmittingTrace(false);
      setIsTraceModalOpen(false);
      toast.success('Automated trace initiated for ' + traceAddress.slice(0, 10) + '...');
      navigate('/cases/1');
    }, 800);
  };

  return (
    <div className="flex flex-col w-full gap-8 animate-in fade-in duration-150">
      {/* Top Greeting & Action Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 pb-2">
        <div className="space-y-1">
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-primary-fixed text-on-primary-fixed uppercase tracking-wider">
              Nodal LEA Terminal
            </span>
            <span className="text-outline text-xs">•</span>
            <span className="text-[11px] font-mono text-outline">STATION #DL-SPEC-09</span>
          </div>

          <h1 className="font-headline-lg text-[28px] font-semibold text-on-surface tracking-tight">
            Good morning, Inspector Sharma
          </h1>
          
          <p className="font-body-lg text-[15px] text-on-surface-variant flex items-center gap-2">
            <span>Cyber Crime Unit, Special Cell</span>
            <span className="w-1.5 h-1.5 rounded-full bg-secondary"></span>
            <span className="font-label-md text-xs text-secondary font-semibold">Station Master Node Active</span>
          </p>
        </div>

        {/* View Switcher & Primary Action */}
        <div className="flex items-center gap-3 flex-wrap">
          {/* View Mode Toggle */}
          <div className="inline-flex p-1 bg-surface-container rounded-xl shadow-xs">
            <button
              onClick={() => setViewMode('executive')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                viewMode === 'executive'
                  ? 'bg-surface-container-lowest text-primary shadow-xs'
                  : 'text-on-surface-variant hover:text-on-surface'
              }`}
            >
              Executive View
            </button>
            <button
              onClick={() => setViewMode('command')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                viewMode === 'command'
                  ? 'bg-surface-container-lowest text-primary shadow-xs'
                  : 'text-on-surface-variant hover:text-on-surface'
              }`}
            >
              Command Center
            </button>
          </div>

          {/* Simulate Complaint */}
          <button
            onClick={handleSimulateNcrp}
            className="inline-flex items-center gap-2 px-4 py-2.5 bg-surface-container-lowest text-on-surface font-label-md text-xs font-semibold rounded-xl shadow-sm hover:bg-surface-container transition-all"
            type="button"
            title="Simulate incoming NCRP / 1930 fraud report"
          >
            <span className="material-symbols-outlined text-[18px] text-secondary">sync</span>
            <span>Simulate Inflow</span>
          </button>

          {/* Primary Action: Start New Trace */}
          <button
            onClick={() => setIsTraceModalOpen(true)}
            className="inline-flex items-center gap-2 px-6 py-2.5 bg-primary-container text-on-primary font-label-md text-xs font-semibold rounded-xl shadow-sm hover:bg-primary transition-all active:scale-[0.99]"
            type="button"
          >
            <span className="material-symbols-outlined text-[18px]">add_circle</span>
            <span>Start New Trace</span>
          </button>
        </div>
      </div>

      {/* VIEW 1: EXECUTIVE BRIEFING VIEW (Matches chainnetra_dashboard) */}
      {viewMode === 'executive' && (
        <div className="flex flex-col gap-8">
          {/* Row of 3 Large KPI Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* KPI 1 */}
            <div className="bg-surface-container-lowest rounded-xl p-7 shadow-sm transition-transform hover:-translate-y-0.5 border border-surface-container">
              <div className="flex items-center justify-between mb-4">
                <span className="font-label-md text-xs font-semibold text-on-surface-variant uppercase tracking-wider">
                  Open Cases
                </span>
                <span className="p-2 rounded-lg bg-surface-container-high text-primary flex items-center justify-center">
                  <span className="material-symbols-outlined text-[20px]">folder_open</span>
                </span>
              </div>
              <div className="font-display-lg text-[32px] font-bold text-on-surface mb-2 tracking-tight">
                {summary?.open_cases || 142}
              </div>
              <div className="font-body-md text-xs text-on-surface-variant flex items-center gap-2">
                <span className="text-secondary font-semibold">+12 this week</span>
                <span className="text-outline-variant">•</span>
                <span>28 priority</span>
              </div>
            </div>

            {/* KPI 2 */}
            <div className="bg-surface-container-lowest rounded-xl p-7 shadow-sm transition-transform hover:-translate-y-0.5 border border-surface-container">
              <div className="flex items-center justify-between mb-4">
                <span className="font-label-md text-xs font-semibold text-on-surface-variant uppercase tracking-wider">
                  Average Time to Find Exchange
                </span>
                <span className="p-2 rounded-lg bg-secondary-container/40 text-secondary flex items-center justify-center">
                  <span className="material-symbols-outlined text-[20px]">speed</span>
                </span>
              </div>
              <div className="font-display-lg text-[32px] font-bold text-on-surface mb-2 tracking-tight">
                38 min
              </div>
              <div className="font-body-md text-xs text-on-surface-variant">
                vs 3 days manual baseline <span className="text-secondary font-semibold">(94% automated)</span>
              </div>
            </div>

            {/* KPI 3 */}
            <div className="bg-surface-container-lowest rounded-xl p-7 shadow-sm transition-transform hover:-translate-y-0.5 border border-surface-container">
              <div className="flex items-center justify-between mb-4">
                <span className="font-label-md text-xs font-semibold text-on-surface-variant uppercase tracking-wider">
                  Funds Traced
                </span>
                <span className="p-2 rounded-lg bg-surface-container-high text-primary flex items-center justify-center">
                  <span className="material-symbols-outlined text-[20px]">account_balance_wallet</span>
                </span>
              </div>
              <div className="font-display-lg text-[32px] font-bold text-on-surface mb-2 tracking-tight">
                ₹48.6 Cr
              </div>
              <div className="font-body-md text-xs text-on-surface-variant">
                Across Tron, Ethereum, BSC &amp; Bitcoin
              </div>
            </div>
          </div>

          {/* Main Section: Calm Visual SVG Chart */}
          <div className="bg-surface-container-lowest rounded-xl p-7 shadow-sm border border-surface-container space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <h2 className="font-headline-md text-lg font-bold text-on-surface">Complaints this month</h2>
                <p className="font-body-md text-xs text-on-surface-variant mt-0.5">October 1 to October 30 forensic inflow ledger</p>
              </div>
              <div className="flex items-center gap-6">
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full bg-primary-container"></span>
                  <span className="font-label-sm text-xs font-medium text-on-surface-variant">FIR Registered</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full bg-secondary"></span>
                  <span className="font-label-sm text-xs font-medium text-on-surface-variant">Exchange Freezes</span>
                </div>
              </div>
            </div>

            {/* Clean Calm SVG Line Trendline */}
            <div className="w-full pt-4 pb-2">
              <svg className="w-full h-48 overflow-visible" preserveAspectRatio="none" viewBox="0 0 1000 240">
                <defs>
                  <linearGradient id="primaryGradient" x1="0%" x2="0%" y1="0%" y2="100%">
                    <stop offset="0%" stopColor="#2F6DB5" stopOpacity="0.18"></stop>
                    <stop offset="100%" stopColor="#2F6DB5" stopOpacity="0.0"></stop>
                  </linearGradient>
                  <linearGradient id="tealGradient" x1="0%" x2="0%" y1="0%" y2="100%">
                    <stop offset="0%" stopColor="#1C9C8C" stopOpacity="0.12"></stop>
                    <stop offset="100%" stopColor="#1C9C8C" stopOpacity="0.0"></stop>
                  </linearGradient>
                </defs>
                {/* Horizontal Grid Lines */}
                <line stroke="#E4EFFF" strokeWidth="1" x1="0" x2="1000" y1="20" y2="20"></line>
                <line stroke="#E4EFFF" strokeWidth="1" x1="0" x2="1000" y1="80" y2="80"></line>
                <line stroke="#E4EFFF" strokeWidth="1" x1="0" x2="1000" y1="140" y2="140"></line>
                <line stroke="#E4EFFF" strokeWidth="1" x1="0" x2="1000" y1="200" y2="200"></line>
                
                {/* Filled Trend Areas */}
                <path d="M 0 190 Q 150 170 300 130 T 600 110 T 850 70 T 1000 45 L 1000 210 L 0 210 Z" fill="url(#primaryGradient)"></path>
                <path d="M 0 205 Q 160 195 320 180 T 620 160 T 860 120 T 1000 100 L 1000 210 L 0 210 Z" fill="url(#tealGradient)"></path>
                
                {/* Primary Curve */}
                <path d="M 0 190 Q 150 170 300 130 T 600 110 T 850 70 T 1000 45" fill="none" stroke="#2F6DB5" strokeLinecap="round" strokeWidth="2.5"></path>
                {/* Secondary Freezes Curve */}
                <path d="M 0 205 Q 160 195 320 180 T 620 160 T 860 120 T 1000 100" fill="none" stroke="#1C9C8C" strokeDasharray="4 4" strokeLinecap="round" strokeWidth="2"></path>
                
                {/* Data Nodes */}
                <circle cx="300" cy="130" fill="#FFFFFF" r="4.5" stroke="#2F6DB5" strokeWidth="2.5"></circle>
                <circle cx="600" cy="110" fill="#FFFFFF" r="4.5" stroke="#2F6DB5" strokeWidth="2.5"></circle>
                <circle cx="850" cy="70" fill="#FFFFFF" r="4.5" stroke="#2F6DB5" strokeWidth="2.5"></circle>
                <circle cx="1000" cy="45" fill="#2F6DB5" r="5" stroke="#FFFFFF" strokeWidth="2"></circle>
                <circle cx="620" cy="160" fill="#FFFFFF" r="3.5" stroke="#1C9C8C" strokeWidth="2"></circle>
                <circle cx="860" cy="120" fill="#FFFFFF" r="3.5" stroke="#1C9C8C" strokeWidth="2"></circle>
              </svg>
              {/* Timeline X-Axis Labels */}
              <div className="flex justify-between items-center text-on-surface-variant font-label-sm text-xs pt-4 px-1">
                <span>Oct 1</span>
                <span>Oct 7</span>
                <span>Oct 14</span>
                <span>Oct 21</span>
                <span>Oct 28</span>
                <span className="font-semibold text-primary">Oct 30 (Today)</span>
              </div>
            </div>
          </div>

          {/* Recent Cases Card (Strict 64px Rows, 4 Rows) */}
          <div className="bg-surface-container-lowest rounded-xl p-7 shadow-sm border border-surface-container space-y-4">
            <div className="flex items-center justify-between pb-2">
              <h2 className="font-headline-md text-lg font-bold text-on-surface">Recent Cases</h2>
              <button 
                onClick={() => navigate('/cases/1')}
                className="font-label-md text-xs font-semibold text-primary flex items-center gap-1 hover:underline"
              >
                <span>View all active cases</span>
                <span className="material-symbols-outlined text-[16px]">arrow_forward</span>
              </button>
            </div>
            
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-surface-container-low text-on-surface-variant font-label-sm text-[11px] uppercase tracking-wider">
                    <th className="py-3 px-4 font-semibold rounded-l-lg">Case Reference</th>
                    <th className="py-3 px-4 font-semibold">Incident Details</th>
                    <th className="py-3 px-4 font-semibold">Primary Chain</th>
                    <th className="py-3 px-4 font-semibold">Funds Traced</th>
                    <th className="py-3 px-4 font-semibold rounded-r-lg">Status</th>
                  </tr>
                </thead>
                <tbody className="text-on-surface font-body-md text-xs">
                  {/* Row 1 */}
                  <tr 
                    onClick={() => navigate('/cases/1')}
                    className="h-16 hover:bg-surface-container-low/50 transition-colors cursor-pointer border-b border-surface-container/50"
                  >
                    <td className="px-4">
                      <span className="font-code-md text-xs font-semibold text-primary">#CN-2024-0944</span>
                    </td>
                    <td className="px-4 font-medium">Pune Telegram Task Fraud</td>
                    <td className="px-4">
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-surface-container text-on-surface font-label-sm text-[11px]">
                        <span className="w-1.5 h-1.5 rounded-full bg-primary"></span>
                        Tron (TRC20)
                      </span>
                    </td>
                    <td className="px-4 font-medium font-code-md text-on-surface">₹42.50 Lakh</td>
                    <td className="px-4">
                      <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-secondary-container/40 text-secondary font-label-sm text-[11px] font-semibold">
                        <span className="material-symbols-outlined text-[14px]">verified</span>
                        VASP Identified
                      </span>
                    </td>
                  </tr>

                  {/* Row 2 */}
                  <tr 
                    onClick={() => navigate('/cases/1')}
                    className="h-16 hover:bg-surface-container-low/50 transition-colors cursor-pointer border-b border-surface-container/50"
                  >
                    <td className="px-4">
                      <span className="font-code-md text-xs font-semibold text-primary">#CN-2024-0941</span>
                    </td>
                    <td className="px-4 font-medium">Bengaluru Digital Arrest Scam</td>
                    <td className="px-4">
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-surface-container text-on-surface font-label-sm text-[11px]">
                        <span className="w-1.5 h-1.5 rounded-full bg-tertiary"></span>
                        Ethereum
                      </span>
                    </td>
                    <td className="px-4 font-medium font-code-md text-on-surface">₹1.20 Crore</td>
                    <td className="px-4">
                      <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-error-container text-on-error-container font-label-sm text-[11px] font-semibold">
                        <span className="material-symbols-outlined text-[14px]">lock_clock</span>
                        Freeze Pending
                      </span>
                    </td>
                  </tr>

                  {/* Row 3 */}
                  <tr 
                    onClick={() => navigate('/cases/1')}
                    className="h-16 hover:bg-surface-container-low/50 transition-colors cursor-pointer border-b border-surface-container/50"
                  >
                    <td className="px-4">
                      <span className="font-code-md text-xs font-semibold text-primary">#CN-2024-0938</span>
                    </td>
                    <td className="px-4 font-medium">Mumbai Stock Investment Scheme</td>
                    <td className="px-4">
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-surface-container text-on-surface font-label-sm text-[11px]">
                        <span className="w-1.5 h-1.5 rounded-full bg-primary"></span>
                        Tron (TRC20)
                      </span>
                    </td>
                    <td className="px-4 font-medium font-code-md text-on-surface">₹18.00 Lakh</td>
                    <td className="px-4">
                      <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-tertiary-fixed text-on-tertiary-fixed-variant font-label-sm text-[11px] font-semibold">
                        <span className="material-symbols-outlined text-[14px]">alt_route</span>
                        Cross-chain Hop
                      </span>
                    </td>
                  </tr>

                  {/* Row 4 */}
                  <tr 
                    onClick={() => navigate('/cases/1')}
                    className="h-16 hover:bg-surface-container-low/50 transition-colors cursor-pointer"
                  >
                    <td className="px-4">
                      <span className="font-code-md text-xs font-semibold text-primary">#CN-2024-0929</span>
                    </td>
                    <td className="px-4 font-medium">Delhi Job Portal Extortion</td>
                    <td className="px-4">
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-surface-container text-on-surface font-label-sm text-[11px]">
                        <span className="w-1.5 h-1.5 rounded-full bg-secondary"></span>
                        BNB Chain
                      </span>
                    </td>
                    <td className="px-4 font-medium font-code-md text-on-surface">₹8.50 Lakh</td>
                    <td className="px-4">
                      <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-secondary-container/40 text-secondary font-label-sm text-[11px] font-semibold">
                        <span className="material-symbols-outlined text-[14px]">account_balance</span>
                        Exchange Identified
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* VIEW 2: COMMAND CENTER LIVE STREAM (Matches chainnetra_command_center_1) */}
      {viewMode === 'command' && (
        <div className="flex flex-col gap-8">
          {/* Row of 5 KPI Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
            <div className="bg-surface-container-lowest rounded-xl p-5 shadow-sm border border-surface-container flex flex-col justify-between">
              <div className="flex items-center justify-between mb-2">
                <span className="font-label-md text-xs text-outline">Open Cases</span>
                <span className="material-symbols-outlined text-primary text-lg">folder</span>
              </div>
              <div>
                <div className="text-2xl font-bold text-on-surface">142</div>
                <div className="text-[11px] text-error font-semibold mt-1">28 High Priority</div>
              </div>
            </div>

            <div className="bg-surface-container-lowest rounded-xl p-5 shadow-sm border border-surface-container flex flex-col justify-between">
              <div className="flex items-center justify-between mb-2">
                <span className="font-label-md text-xs text-outline">Complaints Today</span>
                <span className="material-symbols-outlined text-primary text-lg">inbox</span>
              </div>
              <div>
                <div className="text-2xl font-bold text-on-surface">37</div>
                <div className="text-[11px] text-secondary font-semibold mt-1">21 auto-triaged</div>
              </div>
            </div>

            <div className="bg-surface-container-lowest rounded-xl p-5 shadow-sm border border-surface-container flex flex-col justify-between">
              <div className="flex items-center justify-between mb-2">
                <span className="font-label-md text-xs text-outline">Avg. Time to VASP</span>
                <span className="material-symbols-outlined text-secondary text-lg">bolt</span>
              </div>
              <div>
                <div className="text-2xl font-bold text-on-surface">38m</div>
                <div className="text-[11px] text-secondary font-semibold mt-1">94% automated</div>
              </div>
            </div>

            <div className="bg-surface-container-lowest rounded-xl p-5 shadow-sm border border-surface-container flex flex-col justify-between">
              <div className="flex items-center justify-between mb-2">
                <span className="font-label-md text-xs text-outline">Total Value Traced</span>
                <span className="material-symbols-outlined text-primary text-lg">currency_rupee</span>
              </div>
              <div>
                <div className="text-2xl font-bold text-on-surface">₹48.6 Cr</div>
                <div className="text-[11px] text-outline font-mono mt-1">4,210 txns</div>
              </div>
            </div>

            <div className="bg-surface-container-lowest rounded-xl p-5 shadow-sm border border-surface-container flex flex-col justify-between">
              <div className="flex items-center justify-between mb-2">
                <span className="font-label-md text-xs text-outline">Freeze Requests</span>
                <span className="material-symbols-outlined text-secondary text-lg">gavel</span>
              </div>
              <div>
                <div className="text-2xl font-bold text-on-surface">89</div>
                <div className="text-[11px] text-secondary font-semibold mt-1">₹31.2 Cr Locked</div>
              </div>
            </div>
          </div>

          {/* 2 Analytical Panels: Modus Operandi & Top VASP Inflows */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Donut Chart: Modus Operandi Breakdown */}
            <div className="lg:col-span-5 bg-surface-container-lowest rounded-xl p-6 shadow-sm border border-surface-container flex flex-col justify-between">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="font-headline-sm text-sm font-bold text-on-surface">Modus Operandi Breakdown</h3>
                  <p className="text-xs text-outline">Categorized via NCRP narrative & victim NLP</p>
                </div>
                <span className="material-symbols-outlined text-outline text-base">info</span>
              </div>

              <div className="flex flex-col sm:flex-row items-center gap-6 my-auto py-2">
                {/* SVG Donut */}
                <div className="relative w-40 h-40 shrink-0 flex items-center justify-center">
                  <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
                    <circle className="text-surface-container" cx="50" cy="50" fill="transparent" r="40" stroke="currentColor" strokeWidth="12"></circle>
                    <circle cx="50" cy="50" fill="transparent" r="40" stroke="#2F6DB5" strokeDasharray="95.5 251.32" strokeDashoffset="0" strokeWidth="12"></circle>
                    <circle cx="50" cy="50" fill="transparent" r="40" stroke="#006b5f" strokeDasharray="67.8 251.32" strokeDashoffset="-95.5" strokeWidth="12"></circle>
                    <circle cx="50" cy="50" fill="transparent" r="40" stroke="#D9901A" strokeDasharray="45.2 251.32" strokeDashoffset="-163.3" strokeWidth="12"></circle>
                    <circle cx="50" cy="50" fill="transparent" r="40" stroke="#ba1a1a" strokeDasharray="27.6 251.32" strokeDashoffset="-208.5" strokeWidth="12"></circle>
                  </svg>
                  <div className="absolute inset-0 flex flex-col items-center justify-center text-center pointer-events-none">
                    <span className="text-[10px] uppercase text-outline font-semibold">Total</span>
                    <span className="text-lg font-bold text-on-surface">1,248</span>
                    <span className="text-[10px] text-secondary font-semibold">30 Days</span>
                  </div>
                </div>

                {/* Legend */}
                <div className="flex flex-col gap-2 w-full text-xs">
                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-sm bg-[#2F6DB5]"></span>Task Scam</span>
                    <span className="font-semibold text-on-surface">38%</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-sm bg-[#006b5f]"></span>Fake Investment</span>
                    <span className="font-semibold text-on-surface">27%</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-sm bg-[#D9901A]"></span>Digital Arrest</span>
                    <span className="font-semibold text-on-surface">18%</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-sm bg-[#ba1a1a]"></span>Sextortion</span>
                    <span className="font-semibold text-on-surface">11%</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Top VASP Inflows Progress Bars */}
            <div className="lg:col-span-7 bg-surface-container-lowest rounded-xl p-6 shadow-sm border border-surface-container flex flex-col justify-between">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="font-headline-sm text-sm font-bold text-on-surface">Top VASP Inflows</h3>
                  <p className="text-xs text-outline">Virtual Asset Service Providers per PMLA / FIU-IND</p>
                </div>
                <button onClick={() => navigate('/vasps')} className="text-xs text-primary font-semibold hover:underline">
                  VASP Directory →
                </button>
              </div>

              <div className="flex flex-col gap-3.5">
                <div>
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="font-semibold text-on-surface">1. Binance (Global)</span>
                    <span className="font-mono text-on-surface">₹18.4 Cr (38%)</span>
                  </div>
                  <div className="w-full bg-surface-container rounded-full h-2">
                    <div className="bg-primary-container h-2 rounded-full" style={{ width: '38%' }}></div>
                  </div>
                </div>

                <div>
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="font-semibold text-on-surface">2. Bybit</span>
                    <span className="font-mono text-on-surface">₹11.2 Cr (23%)</span>
                  </div>
                  <div className="w-full bg-surface-container rounded-full h-2">
                    <div className="bg-primary-container h-2 rounded-full" style={{ width: '23%' }}></div>
                  </div>
                </div>

                <div>
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="font-semibold text-on-surface">3. WazirX (India)</span>
                    <span className="font-mono text-on-surface">₹8.1 Cr (17%)</span>
                  </div>
                  <div className="w-full bg-surface-container rounded-full h-2">
                    <div className="bg-secondary h-2 rounded-full" style={{ width: '17%' }}></div>
                  </div>
                </div>

                <div>
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="font-semibold text-on-surface">4. Bitget</span>
                    <span className="font-mono text-on-surface">₹5.9 Cr (12%)</span>
                  </div>
                  <div className="w-full bg-surface-container rounded-full h-2">
                    <div className="bg-primary-container h-2 rounded-full" style={{ width: '12%' }}></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* START NEW TRACE MODAL (Matches chainnetra_start_new_trace) */}
      {isTraceModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-inverse-surface/40 backdrop-blur-xs">
          <div className="bg-surface-container-lowest rounded-xl max-w-xl w-full p-7 shadow-xl space-y-6 border border-surface-container animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between pb-2 border-b border-surface-container">
              <div>
                <span className="text-[10px] font-semibold text-primary uppercase tracking-wider">Module 01 • Reconstitution</span>
                <h3 className="font-headline-md text-lg font-bold text-on-surface">Start New Blockchain Trace</h3>
              </div>
              <button 
                onClick={() => setIsTraceModalOpen(false)}
                className="text-on-surface-variant hover:text-on-surface p-1 rounded-lg"
                type="button"
              >
                <span className="material-symbols-outlined text-[20px]">close</span>
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-on-surface mb-1">
                  NCRB / FIR Reference <span className="text-error">*</span>
                </label>
                <input 
                  value={traceFir}
                  onChange={(e) => setTraceFir(e.target.value)}
                  className="w-full h-11 px-3 bg-surface-container-low rounded-lg text-xs text-on-surface font-sans focus:outline-none focus:ring-1 focus:ring-primary border border-surface-container"
                  placeholder="e.g. FIR-2024-8831-DEL"
                  type="text"
                />
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="text-xs font-semibold text-on-surface">
                    Victim Reported Scammer Wallet Address <span className="text-error">*</span>
                  </label>
                  <button 
                    onClick={() => setTraceAddress('')}
                    className="text-[11px] text-primary hover:underline"
                    type="button"
                  >
                    Clear
                  </button>
                </div>
                <div className="relative">
                  <input 
                    value={traceAddress}
                    onChange={(e) => setTraceAddress(e.target.value)}
                    className="w-full h-11 pl-3 pr-10 bg-surface-container-low rounded-lg text-xs font-mono text-on-surface focus:outline-none focus:ring-1 focus:ring-primary border border-surface-container"
                    placeholder="0x... or T..."
                    type="text"
                  />
                  <button 
                    type="button"
                    onClick={() => {
                      navigator.clipboard.writeText(traceAddress);
                      toast.success('Address copied');
                    }}
                    className="absolute right-2.5 top-1/2 -translate-y-1/2 text-outline hover:text-primary"
                  >
                    <span className="material-symbols-outlined text-[16px]">content_copy</span>
                  </button>
                </div>
                <div className="mt-1 flex items-center gap-1.5 text-[11px] text-secondary font-medium">
                  <span className="w-1.5 h-1.5 rounded-full bg-secondary"></span>
                  <span>Detected: Tron (TRC20 - USDT Network)</span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3 pt-1">
                <div>
                  <label className="block text-xs font-semibold text-on-surface mb-1">Trace Depth</label>
                  <select 
                    value={traceDepth}
                    onChange={(e) => setTraceDepth(e.target.value)}
                    className="w-full h-10 px-3 bg-surface-container-low rounded-lg text-xs text-on-surface border border-surface-container"
                  >
                    <option value="6">6 hops (Standard)</option>
                    <option value="8">8 hops (Deep Audit)</option>
                    <option value="12">12 hops (Aggressive)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-on-surface mb-1">Cross-Chain Bridges</label>
                  <button
                    type="button"
                    onClick={() => setBridgeTracking(!bridgeTracking)}
                    className={`w-full h-10 px-3 rounded-lg text-xs font-semibold flex items-center justify-between border ${
                      bridgeTracking 
                        ? 'bg-secondary-container/30 text-secondary border-secondary-container' 
                        : 'bg-surface-container-low text-outline border-surface-container'
                    }`}
                  >
                    <span>{bridgeTracking ? 'Auto Track' : 'Off'}</span>
                    <span className="material-symbols-outlined text-[16px]">
                      {bridgeTracking ? 'toggle_on' : 'toggle_off'}
                    </span>
                  </button>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 pt-3 border-t border-surface-container">
              <button 
                onClick={() => setIsTraceModalOpen(false)}
                className="px-4 py-2 rounded-lg bg-surface-container text-xs font-semibold text-on-surface hover:bg-surface-container-high transition-colors"
                type="button"
              >
                Cancel
              </button>
              <button 
                onClick={handleStartTrace}
                disabled={isSubmittingTrace || !traceAddress.trim()}
                className="px-5 py-2 rounded-lg bg-primary-container text-xs font-semibold text-on-primary hover:bg-primary transition-all flex items-center gap-1.5 disabled:opacity-50"
                type="button"
              >
                {isSubmittingTrace ? (
                  <>
                    <span className="material-symbols-outlined text-[16px] animate-spin">sync</span>
                    <span>Scanning Ledgers...</span>
                  </>
                ) : (
                  <>
                    <span className="material-symbols-outlined text-[16px]">alt_route</span>
                    <span>Begin Automated Hop Scan</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
