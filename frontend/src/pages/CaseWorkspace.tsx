import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { api } from '../lib/api';
import { useAppStore } from '../stores/useAppStore';

export const CaseWorkspace: React.FC = () => {
  const { id = '1' } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const explainMode = useAppStore((s) => s.explainMode);

  // Active Tab: overview | fundflow | wallets | evidence | report
  const [activeTab, setActiveTab] = useState<'fundflow' | 'overview' | 'wallets' | 'evidence' | 'report'>('fundflow');

  // Zoom & Filter State
  const [zoomLevel, setZoomLevel] = useState(100);
  const [dustFilterActive, setDustFilterActive] = useState(true);
  const [isLegendOpen, setIsLegendOpen] = useState(true);

  // Timeline scrubber state
  const [isPlaying, setIsPlaying] = useState(false);
  const [timelineVal, setTimelineVal] = useState(85);
  const [scrubberTimeText, setScrubberTimeText] = useState('Oct 24, 11:24 AM');

  // Selected node for drill-down inspection
  const [selectedNodeId, setSelectedNodeId] = useState<string>('node-8');

  // Case details
  const [caseDetails, setCaseDetails] = useState<any>({
    case_number: 'CN-2024-0944',
    title: 'Pune Telegram Task Fraud',
    fir_number: 'FIR-184-PUNE-SOUTH',
    station: 'MAHARASHTRA CYBER HQ',
    officer: 'Insp. R. Sharma',
    token: 'USDT (TRC20 → ERC20)',
    amount_inr: 1450000,
    amount_usd: 17320,
    status: 'Exchange Identified'
  });

  // Scrubber animation
  useEffect(() => {
    let interval: any;
    if (isPlaying) {
      interval = setInterval(() => {
        setTimelineVal((prev) => {
          const next = prev >= 100 ? 0 : prev + 1;
          updateTimeLabel(next);
          return next;
        });
      }, 150);
    }
    return () => clearInterval(interval);
  }, [isPlaying]);

  const updateTimeLabel = (val: number) => {
    const startMin = 9 * 60 + 12;
    const totalMinutes = 153;
    const currentTotalMin = Math.round(startMin + (totalMinutes * (val / 100)));
    const hours = Math.floor(currentTotalMin / 60);
    const minutes = currentTotalMin % 60;
    const formattedMins = minutes < 10 ? '0' + minutes : minutes;
    setScrubberTimeText(`Oct 24, ${hours < 10 ? '0' + hours : hours}:${formattedMins} AM`);
  };

  const handleZoom = (delta: number) => {
    setZoomLevel((prev) => Math.max(50, Math.min(180, prev + delta)));
  };

  return (
    <div className="flex flex-col w-full gap-6 animate-in fade-in duration-150">
      {/* Case Meta & Canvas Header Bar */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 bg-surface-container-lowest px-6 py-4 rounded-xl shadow-sm border border-surface-container">
        <div className="flex flex-col">
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="font-headline-md text-lg font-bold text-on-surface">
              Case #{caseDetails.case_number} • Transaction Flow Graph
            </h1>
            <span className="bg-secondary-container/40 text-on-secondary-fixed text-[11px] px-2.5 py-0.5 rounded-full font-semibold flex items-center gap-1 border border-secondary-container">
              <span className="w-1.5 h-1.5 rounded-full bg-secondary"></span>
              Evidentiary Stage II
            </span>
          </div>

          <div className="flex items-center gap-3 mt-1 text-on-surface-variant text-xs font-mono flex-wrap">
            <span>Target: <strong className="text-on-surface font-sans font-semibold">USDT (TRC20 → ERC20)</strong></span>
            <span>•</span>
            <span>Total Displaced: <strong className="text-on-surface font-sans font-semibold">₹14,50,000 (~$17,320)</strong></span>
            <span>•</span>
            <span>Investigation Node: <span className="text-primary font-semibold font-mono">DEL-CY-08</span></span>
          </div>
        </div>

        <div className="flex items-center gap-3 self-end md:self-auto">
          <button
            onClick={() => {
              toast.success('Attached flow graph to FIR #184-PUNE-SOUTH Evidence Docket');
            }}
            className="h-9 px-4 rounded-lg bg-surface-container-low text-on-surface text-xs font-semibold flex items-center gap-1.5 hover:bg-surface-container transition-colors border border-surface-container"
            type="button"
          >
            <span className="material-symbols-outlined text-[16px] text-secondary">verified</span>
            <span>Attach to FIR</span>
          </button>

          <button
            onClick={() => {
              toast.success('Next hops scan completed. Terminal Exchange confirmed.');
            }}
            className="h-9 px-4 rounded-lg bg-primary-container text-on-primary text-xs font-semibold flex items-center gap-1.5 hover:bg-primary transition-colors shadow-xs"
            type="button"
          >
            <span className="material-symbols-outlined text-[16px]">alt_route</span>
            <span>Identify Next Hops</span>
          </button>
        </div>
      </div>

      {/* Primary Tab Navigation Strip */}
      <div className="flex items-center gap-8 bg-surface-container-lowest px-6 rounded-xl shadow-sm border border-surface-container">
        {[
          { key: 'fundflow', label: 'Fund Flow', icon: 'account_tree' },
          { key: 'overview', label: 'Overview', icon: 'dashboard' },
          { key: 'wallets', label: 'Wallets', icon: 'account_balance_wallet', badge: '8' },
          { key: 'evidence', label: 'Evidence & Logs', icon: 'history_edu' },
          { key: 'report', label: 'Report', icon: 'description', badge: 'Draft' },
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key as any)}
            className={`relative py-4 text-xs font-semibold flex items-center gap-2 transition-colors ${
              activeTab === tab.key 
                ? 'text-primary font-bold' 
                : 'text-on-surface-variant hover:text-on-surface'
            }`}
            type="button"
          >
            <span className={`material-symbols-outlined text-[18px] ${activeTab === tab.key ? 'text-primary' : 'text-outline'}`}>
              {tab.icon}
            </span>
            <span>{tab.label}</span>
            {tab.badge && (
              <span className={`px-2 py-0.5 rounded-full text-[10px] font-mono ${
                activeTab === tab.key 
                  ? 'bg-primary-container text-on-primary' 
                  : 'bg-surface-container text-tertiary'
              }`}>
                {tab.badge}
              </span>
            )}
            {activeTab === tab.key && (
              <span className="absolute bottom-0 left-0 right-0 h-[3px] bg-primary-container rounded-t-full" />
            )}
          </button>
        ))}
      </div>

      {/* TAB 1: FUND FLOW GRAPH CANVAS */}
      {activeTab === 'fundflow' && (
        <div className="flex flex-col gap-6">
          {/* Main Visual Forensic Graph Viewport */}
          <div className="relative w-full h-[660px] bg-surface-container-lowest rounded-xl shadow-sm overflow-hidden select-none flex flex-col justify-between border border-surface-container">
            {/* Floating Top Toolbar */}
            <div className="absolute top-4 left-1/2 -translate-x-1/2 z-20 flex items-center gap-2 bg-surface-container-lowest/95 backdrop-blur px-4 py-1.5 rounded-full shadow-md border border-surface-container">
              {/* Zoom Controls */}
              <div className="flex items-center bg-surface-container-low rounded-lg p-0.5">
                <button
                  onClick={() => handleZoom(-15)}
                  className="w-7 h-7 flex items-center justify-center text-on-surface-variant hover:text-on-surface hover:bg-surface-container-lowest rounded transition-colors"
                  title="Zoom Out"
                  type="button"
                >
                  <span className="material-symbols-outlined text-[16px]">remove</span>
                </button>
                <span className="font-mono text-xs px-2 text-on-surface font-semibold min-w-[50px] text-center">
                  {zoomLevel}%
                </span>
                <button
                  onClick={() => handleZoom(15)}
                  className="w-7 h-7 flex items-center justify-center text-on-surface-variant hover:text-on-surface hover:bg-surface-container-lowest rounded transition-colors"
                  title="Zoom In"
                  type="button"
                >
                  <span className="material-symbols-outlined text-[16px]">add</span>
                </button>
              </div>

              <div className="w-px h-5 bg-surface-container-high mx-1" />

              <button
                onClick={() => setZoomLevel(100)}
                className="h-7 px-2.5 rounded-lg bg-surface-container-low text-on-surface text-xs font-semibold hover:bg-surface-container flex items-center gap-1 transition-colors"
                type="button"
              >
                <span className="material-symbols-outlined text-[15px]">fit_screen</span>
                <span>Fit Screen</span>
              </button>

              <button
                onClick={() => {
                  setDustFilterActive(!dustFilterActive);
                  toast.success(dustFilterActive ? 'Dust Filter Disabled (<$100)' : 'Dust Filter Enabled (<$100)');
                }}
                className={`h-7 px-2.5 rounded-lg text-xs font-semibold flex items-center gap-1 transition-colors ${
                  dustFilterActive 
                    ? 'bg-secondary-container/40 text-secondary border border-secondary-container' 
                    : 'bg-surface-container-low text-on-surface'
                }`}
                type="button"
              >
                <span className="material-symbols-outlined text-[15px] text-secondary">filter_alt</span>
                <span>Dust Filter (&lt;$100)</span>
                <span className="w-1.5 h-1.5 rounded-full bg-secondary ml-0.5"></span>
              </button>

              <div className="w-px h-5 bg-surface-container-high mx-1" />

              <button
                onClick={() => window.print()}
                className="h-7 px-2.5 rounded-lg bg-primary-container text-on-primary text-xs font-semibold hover:bg-primary flex items-center gap-1 transition-colors shadow-xs"
                type="button"
              >
                <span className="material-symbols-outlined text-[15px]">file_download</span>
                <span>Export SVG</span>
              </button>
            </div>

            {/* Graph Canvas Container (Scalable Viewport) */}
            <div className="w-full h-full relative overflow-auto cursor-grab active:cursor-grabbing p-12 flex items-center justify-center forensic-grid">
              <div 
                className="relative w-[1340px] h-[520px] transition-transform duration-200 origin-center"
                style={{ transform: `scale(${zoomLevel / 100})` }}
              >
                {/* SVG Connections and Edges */}
                <svg className="absolute inset-0 w-full h-full pointer-events-none" xmlns="http://www.w3.org/2000/svg">
                  <defs>
                    <marker id="arrow-solid" markerHeight="6" markerWidth="6" orient="auto-start-reverse" refX="8" refY="5" viewBox="0 0 10 10">
                      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#727782"></path>
                    </marker>
                    <marker id="arrow-blue" markerHeight="6" markerWidth="6" orient="auto-start-reverse" refX="8" refY="5" viewBox="0 0 10 10">
                      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#01549b"></path>
                    </marker>
                    <marker id="arrow-teal" markerHeight="6" markerWidth="6" orient="auto-start-reverse" refX="8" refY="5" viewBox="0 0 10 10">
                      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#006b5f"></path>
                    </marker>
                  </defs>

                  {/* Hop 1 -> 2: Victim to Scammer Primary */}
                  <path d="M 140 230 C 185 230, 205 170, 245 170" fill="none" markerEnd="url(#arrow-solid)" opacity="0.85" stroke="#727782" strokeWidth="2"></path>
                  {/* Hop 2 -> 3: Scammer Primary to Splitter */}
                  <path d="M 370 170 C 400 170, 410 240, 440 240" fill="none" markerEnd="url(#arrow-solid)" opacity="0.8" stroke="#ba1a1a" strokeWidth="2"></path>
                  {/* Hop 3 -> 4: Splitter to Mule Wallet A */}
                  <path d="M 560 220 C 585 220, 595 130, 625 130" fill="none" markerEnd="url(#arrow-solid)" opacity="0.8" stroke="#727782" strokeWidth="2"></path>
                  {/* Hop 3 -> 6: Splitter Branch to Mule Wallet B */}
                  <path d="M 560 260 C 585 260, 595 350, 625 350" fill="none" markerEnd="url(#arrow-solid)" opacity="0.8" stroke="#727782" strokeWidth="2"></path>
                  {/* Hop 4 -> 5: Mule Wallet A to Bridge Contract (CROSS CHAIN HOP) */}
                  <path d="M 750 130 C 785 130, 795 200, 825 200" fill="none" markerEnd="url(#arrow-blue)" stroke="#01549b" strokeDasharray="6,4" strokeWidth="2.5"></path>
                  {/* Hop 6 -> 7: Mule Wallet B to Consolidator */}
                  <path d="M 750 350 C 885 350, 910 280, 940 280" fill="none" markerEnd="url(#arrow-solid)" opacity="0.85" stroke="#727782" strokeWidth="2"></path>
                  {/* Hop 5 -> 7: Bridge Contract to Consolidator */}
                  <path d="M 945 200 C 970 200, 950 250, 960 250" fill="none" markerEnd="url(#arrow-solid)" stroke="#01549b" strokeWidth="2"></path>
                  {/* Hop 7 -> 8: Consolidator to Final Exchange Node */}
                  <path d="M 1060 265 C 1095 265, 1105 265, 1135 265" fill="none" markerEnd="url(#arrow-teal)" stroke="#006b5f" strokeWidth="3"></path>
                </svg>

                {/* Transaction Edge Amount Pills */}
                <div className="absolute left-[175px] top-[185px] bg-surface-container-high px-2 py-0.5 rounded text-on-surface font-mono text-[11px] font-semibold shadow-xs border border-surface-container">
                  ₹14,50,000
                </div>
                <div className="absolute left-[390px] top-[195px] bg-surface-container-high px-2 py-0.5 rounded text-on-surface font-mono text-[11px] font-semibold shadow-xs border border-surface-container">
                  17,320 USDT
                </div>
                <div className="absolute left-[565px] top-[160px] bg-surface-container-high px-2 py-0.5 rounded text-on-surface font-mono text-[11px] font-semibold shadow-xs border border-surface-container">
                  ₹9,20,000
                </div>
                <div className="absolute left-[565px] top-[295px] bg-surface-container-high px-2 py-0.5 rounded text-on-surface font-mono text-[11px] font-semibold shadow-xs border border-surface-container">
                  ₹5,30,000
                </div>
                <div className="absolute left-[760px] top-[150px] bg-primary-fixed text-on-primary-fixed px-2 py-0.5 rounded text-[11px] font-mono font-semibold shadow-xs flex items-center gap-1">
                  <span className="material-symbols-outlined text-[13px]">swap_calls</span>
                  <span>$11,000 (Tron → ETH)</span>
                </div>
                <div className="absolute left-[815px] top-[335px] bg-surface-container-high px-2 py-0.5 rounded text-on-surface font-mono text-[11px] font-semibold shadow-xs border border-surface-container">
                  $6,320 USDT
                </div>
                <div className="absolute left-[1065px] top-[235px] bg-secondary-container text-on-secondary-fixed px-2 py-0.5 rounded text-[11px] font-mono font-semibold shadow-xs">
                  $12,400 USDT
                </div>

                {/* 8 Forensic Nodes */}
                {/* NODE 1: Victim */}
                <div 
                  onClick={() => setSelectedNodeId('node-1')}
                  className="absolute left-[20px] top-[185px] w-[125px] flex flex-col items-center group cursor-pointer"
                >
                  <div className="w-14 h-14 rounded-xl bg-surface-container flex items-center justify-center text-primary shadow-sm group-hover:scale-105 transition-transform relative border border-surface-container-high">
                    <span className="material-symbols-outlined text-[28px]">account_balance_wallet</span>
                    <span className="absolute -top-1.5 -right-1.5 w-5 h-5 bg-primary text-on-primary rounded-full flex items-center justify-center text-[10px] font-bold" title="Tron Ledger (TRC-20)">TR</span>
                  </div>
                  <div className="mt-2 text-center">
                    <span className="text-[10px] text-primary uppercase font-bold tracking-wider">Victim</span>
                    <div className="font-mono text-xs text-on-surface font-medium truncate max-w-[120px]">0x89c2...41a0</div>
                    <span className="text-[11px] text-on-surface-variant">FIR Complainant</span>
                  </div>
                </div>

                {/* NODE 2: Scammer Wallet 1 */}
                <div 
                  onClick={() => setSelectedNodeId('node-2')}
                  className="absolute left-[250px] top-[125px] w-[125px] flex flex-col items-center group cursor-pointer"
                >
                  <div className="w-14 h-14 rounded-xl bg-error-container/50 flex items-center justify-center text-error shadow-sm group-hover:scale-105 transition-transform relative border border-error/20">
                    <span className="material-symbols-outlined text-[28px]">warning</span>
                    <span className="absolute -top-1 -right-1 w-3.5 h-3.5 bg-error rounded-full animate-ping"></span>
                    <span className="absolute -top-1 -right-1 w-3.5 h-3.5 bg-error rounded-full"></span>
                  </div>
                  <div className="mt-2 text-center">
                    <span className="text-[10px] text-error uppercase font-bold tracking-wider">Scammer Primary</span>
                    <div className="font-mono text-xs text-on-surface font-medium truncate max-w-[120px]">TJ8wK...7xL9</div>
                    <span className="text-[11px] text-error font-medium">High Risk Suspect</span>
                  </div>
                </div>

                {/* NODE 3: Splitter */}
                <div 
                  onClick={() => setSelectedNodeId('node-3')}
                  className="absolute left-[445px] top-[195px] w-[120px] flex flex-col items-center group cursor-pointer"
                >
                  <div className="w-13 h-13 p-3 rounded-xl bg-surface-container-high flex items-center justify-center text-on-surface shadow-sm group-hover:scale-105 transition-transform border border-surface-container">
                    <span className="material-symbols-outlined text-[26px]">call_split</span>
                  </div>
                  <div className="mt-2 text-center">
                    <span className="text-[10px] text-on-surface-variant uppercase font-semibold">Splitter</span>
                    <div className="font-mono text-xs text-on-surface font-medium truncate max-w-[115px]">0x4bE...12D8</div>
                    <span className="text-[11px] text-on-surface-variant">Peel Address</span>
                  </div>
                </div>

                {/* NODE 4: Mule Wallet A */}
                <div 
                  onClick={() => setSelectedNodeId('node-4')}
                  className="absolute left-[635px] top-[85px] w-[120px] flex flex-col items-center group cursor-pointer"
                >
                  <div className="w-13 h-13 p-3 rounded-xl bg-surface-container flex items-center justify-center text-on-surface-variant shadow-sm group-hover:scale-105 transition-transform border border-surface-container">
                    <span className="material-symbols-outlined text-[24px]">person_alert</span>
                  </div>
                  <div className="mt-2 text-center">
                    <span className="text-[10px] text-on-surface-variant uppercase font-semibold">Mule Wallet A</span>
                    <div className="font-mono text-xs text-on-surface font-medium truncate max-w-[115px]">0x81C...93bA</div>
                    <span className="text-[11px] text-on-surface-variant">Transit Layer 1</span>
                  </div>
                </div>

                {/* NODE 5: Bridge Contract (Cross-Chain Stargate) */}
                <div 
                  onClick={() => setSelectedNodeId('node-5')}
                  className="absolute left-[830px] top-[155px] w-[125px] flex flex-col items-center group cursor-pointer"
                >
                  <div className="w-14 h-14 rounded-xl bg-primary-fixed flex items-center justify-center text-primary shadow-sm group-hover:scale-105 transition-transform relative border border-primary-fixed-dim">
                    <span className="material-symbols-outlined text-[28px]">hub</span>
                    <span className="absolute -bottom-1 bg-primary text-on-primary text-[9px] px-1.5 rounded-full uppercase tracking-widest font-semibold">Cross</span>
                  </div>
                  <div className="mt-2 text-center">
                    <span className="text-[10px] text-primary uppercase font-bold">Bridge Contract</span>
                    <div className="text-xs text-on-surface font-semibold">Stargate Router</div>
                    <span className="text-[11px] text-on-surface-variant">Tron → ETH Mainnet</span>
                  </div>
                </div>

                {/* NODE 6: Mule Wallet B */}
                <div 
                  onClick={() => setSelectedNodeId('node-6')}
                  className="absolute left-[635px] top-[305px] w-[120px] flex flex-col items-center group cursor-pointer"
                >
                  <div className="w-13 h-13 p-3 rounded-xl bg-surface-container flex items-center justify-center text-on-surface-variant shadow-sm group-hover:scale-105 transition-transform border border-surface-container">
                    <span className="material-symbols-outlined text-[24px]">person</span>
                  </div>
                  <div className="mt-2 text-center">
                    <span className="text-[10px] text-on-surface-variant uppercase font-semibold">Mule Wallet B</span>
                    <div className="font-mono text-xs text-on-surface font-medium truncate max-w-[115px]">0x33A...eE21</div>
                    <span className="text-[11px] text-on-surface-variant">Transit Layer 2</span>
                  </div>
                </div>

                {/* NODE 7: Consolidator */}
                <div 
                  onClick={() => setSelectedNodeId('node-7')}
                  className="absolute left-[945px] top-[220px] w-[120px] flex flex-col items-center group cursor-pointer"
                >
                  <div className="w-13 h-13 p-3 rounded-xl bg-surface-container-highest flex items-center justify-center text-on-surface shadow-sm group-hover:scale-105 transition-transform border border-surface-container">
                    <span className="material-symbols-outlined text-[26px]">merge_type</span>
                  </div>
                  <div className="mt-2 text-center">
                    <span className="text-[10px] text-on-surface uppercase font-semibold">Consolidator</span>
                    <div className="font-mono text-xs text-on-surface font-medium truncate max-w-[115px]">0x7a3...e21</div>
                    <span className="text-[11px] text-on-surface-variant">Aggregator Pool</span>
                  </div>
                </div>

                {/* NODE 8: Exchange Found (Binance Hot Wallet) */}
                <div 
                  onClick={() => setSelectedNodeId('node-8')}
                  className="absolute left-[1140px] top-[200px] w-[185px] flex flex-col items-center group cursor-pointer"
                >
                  <div className="w-16 h-16 rounded-2xl bg-secondary text-on-secondary flex items-center justify-center shadow-md group-hover:scale-105 transition-transform relative ring-4 ring-secondary/20">
                    <span className="material-symbols-outlined text-[32px]">account_balance</span>
                    <span className="absolute -top-1.5 -right-1.5 w-6 h-6 bg-surface-container-lowest text-secondary rounded-full flex items-center justify-center shadow-xs">
                      <span className="material-symbols-outlined text-[16px] font-bold">check_circle</span>
                    </span>
                  </div>
                  <div className="mt-2 text-center bg-secondary-container/40 p-2.5 rounded-xl w-full border border-secondary-container">
                    <span className="text-[10px] text-on-secondary-fixed uppercase font-bold tracking-wider flex items-center justify-center gap-1">
                      <span className="material-symbols-outlined text-[14px]">assured_workload</span>
                      Exchange Found
                    </span>
                    <div className="text-xs text-on-surface font-bold mt-0.5 truncate">Binance Global</div>
                    <div className="font-mono text-[11px] text-on-surface-variant">Deposit Hot Wallet</div>
                    <span className="text-[10px] text-secondary font-semibold mt-1 inline-block bg-secondary-container/60 px-2 py-0.5 rounded">
                      Action: Sec 91 CrPC
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Floating Interactive Legend (Bottom Left) */}
            <div className="absolute bottom-16 left-4 z-20">
              <div className="bg-surface-container-lowest/95 backdrop-blur rounded-xl p-3 shadow-md border border-surface-container transition-all">
                <div className="flex items-center justify-between gap-4 mb-2 pb-1.5 border-b border-surface-container">
                  <span className="text-[10px] uppercase tracking-wider text-on-surface-variant font-bold">
                    Graph Taxonomy
                  </span>
                  <button 
                    onClick={() => setIsLegendOpen(!isLegendOpen)}
                    className="text-on-surface-variant hover:text-on-surface"
                    type="button"
                  >
                    <span className="material-symbols-outlined text-[16px]">
                      {isLegendOpen ? 'expand_less' : 'expand_more'}
                    </span>
                  </button>
                </div>
                {isLegendOpen && (
                  <div className="flex flex-col gap-1.5 text-xs text-on-surface">
                    <div className="flex items-center gap-2">
                      <span className="w-3 h-3 rounded-full bg-primary shrink-0"></span>
                      <span>Victim Origin</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="w-3 h-3 rounded-full bg-error shrink-0"></span>
                      <span>Suspect / Threat</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="w-3 h-3 rounded-full bg-outline shrink-0"></span>
                      <span>Mule / Splitter</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="w-3 h-3 rounded-full bg-secondary shrink-0"></span>
                      <span>VASP / Exchange (Actionable)</span>
                    </div>
                    <div className="flex items-center gap-2 pt-0.5">
                      <div className="w-4 h-0 border-t-2 border-dashed border-primary shrink-0"></div>
                      <span>Cross-chain Hop (Bridge)</span>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Forensic Chronology Scrubber Slider (Bottom) */}
            <div className="w-full bg-surface-container-lowest/95 backdrop-blur px-6 py-2.5 z-20 flex flex-col gap-1.5 border-t border-surface-container">
              <div className="flex items-center justify-between text-xs text-on-surface-variant">
                <div className="flex items-center gap-3">
                  <button 
                    onClick={() => setIsPlaying(!isPlaying)}
                    className="w-7 h-7 rounded-full bg-primary text-on-primary flex items-center justify-center hover:bg-primary-container transition-colors shadow-xs"
                    type="button"
                  >
                    <span className="material-symbols-outlined text-[18px]">
                      {isPlaying ? 'pause' : 'play_arrow'}
                    </span>
                  </button>
                  <span className="text-xs font-semibold text-on-surface">Ledger Timeline Playback</span>
                </div>

                <div className="flex items-center gap-6 font-mono text-xs">
                  <span>Start: <strong className="text-on-surface font-sans">Oct 24, 09:12 AM</strong></span>
                  <span className="hidden sm:inline">•</span>
                  <span className="text-secondary font-semibold font-sans">Current: <strong className="font-mono text-on-surface">{scrubberTimeText}</strong></span>
                  <span className="hidden sm:inline">•</span>
                  <span>Terminal Deposit: <strong className="text-on-surface font-sans">Oct 24, 11:45 AM</strong></span>
                </div>
              </div>

              <div className="relative flex items-center w-full py-1">
                <input 
                  type="range"
                  min="0"
                  max="100"
                  value={timelineVal}
                  onChange={(e) => {
                    const val = Number(e.target.value);
                    setTimelineVal(val);
                    updateTimeLabel(val);
                  }}
                  className="w-full h-1.5 bg-surface-container rounded-lg appearance-none cursor-pointer accent-primary focus:outline-none"
                />
              </div>
            </div>
          </div>

          {/* Central Evidentiary Card: Exchange Identified (Matches chainnetra_exchange_identified) */}
          <div className="bg-surface-container-lowest rounded-xl p-8 shadow-sm relative overflow-hidden border border-surface-container">
            <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-6 pb-6 border-b border-surface-container">
              <div className="flex items-start gap-4">
                <div className="w-14 h-14 rounded-xl bg-secondary/10 flex items-center justify-center shrink-0">
                  <span className="material-symbols-outlined text-secondary text-[32px]">account_balance</span>
                </div>
                <div className="flex flex-col">
                  <div className="flex items-center gap-3 flex-wrap">
                    <h2 className="font-headline-lg text-xl font-bold text-on-surface">DemoX Exchange (Global) / Binance Custody</h2>
                    <div className="inline-flex items-center gap-1 bg-secondary/10 text-secondary px-3 py-0.5 rounded-full text-xs font-semibold">
                      <span className="material-symbols-outlined text-[14px]">check_circle</span>
                      <span>Verified Custodian</span>
                    </div>
                  </div>
                  <span className="text-xs text-on-surface-variant mt-1">
                    Stolen victim funds successfully traced and deposited into VASP-controlled custodial deposit gateway.
                  </span>
                </div>
              </div>

              <div className="flex flex-col items-start lg:items-end gap-1 bg-surface-container-low p-3 rounded-lg shrink-0 border border-surface-container">
                <span className="text-[10px] text-outline uppercase tracking-wider font-semibold">Jurisdiction &amp; Legal Registry</span>
                <span className="font-mono text-xs text-on-surface font-semibold">Seychelles • FIU-IND 9021</span>
                <span className="text-[11px] text-secondary font-medium">Active Nodal Officer Designated</span>
              </div>
            </div>

            {/* Core Forensic Metric Strip */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 py-6 border-b border-surface-container items-center">
              {/* Metric 1 */}
              <div className="flex flex-col gap-1">
                <span className="text-[10px] text-outline uppercase tracking-wider font-semibold">Analysis Vector</span>
                <div className="flex items-baseline gap-1 mt-1">
                  <span className="text-3xl font-bold text-primary">4</span>
                  <span className="text-sm font-semibold text-on-surface">Hops</span>
                </div>
                <span className="text-[11px] text-on-surface-variant">Direct peel-chain cascade</span>
              </div>

              {/* Metric 2: Confidence Gauge */}
              <div className="flex items-center gap-4">
                <div className="relative w-16 h-16 shrink-0 flex items-center justify-center">
                  <svg className="w-full h-full -rotate-90 transform" viewBox="0 0 36 36">
                    <path className="text-surface-container" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="currentColor" strokeWidth="3.5"></path>
                    <path className="text-secondary" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="currentColor" strokeDasharray="92, 100" strokeLinecap="round" strokeWidth="3.5"></path>
                  </svg>
                  <span className="absolute text-sm font-bold text-on-surface">92%</span>
                </div>
                <div className="flex flex-col">
                  <span className="text-[10px] text-outline uppercase tracking-wider font-semibold">Attribution</span>
                  <span className="text-xs font-semibold text-secondary mt-0.5">High Certainty</span>
                  <span className="text-[11px] text-on-surface-variant">Deterministic match</span>
                </div>
              </div>

              {/* Metric 3: Target Deposit Wallet */}
              <div className="flex flex-col gap-1">
                <span className="text-[10px] text-outline uppercase tracking-wider font-semibold">Target Deposit Wallet</span>
                <div className="flex items-center gap-2 mt-1">
                  <span className="font-mono text-xs text-on-surface bg-surface-container-low px-2 py-0.5 rounded border border-surface-container">
                    0x3f5C...f0bE
                  </span>
                  <button 
                    onClick={() => {
                      navigator.clipboard.writeText('0x3f5CE5FBFe3E9af3971dD833D26bA9b5C936f0bE');
                      toast.success('Deposit address copied');
                    }}
                    className="p-1 rounded text-outline hover:text-primary transition-colors"
                  >
                    <span className="material-symbols-outlined text-[16px]">content_copy</span>
                  </button>
                </div>
                <span className="text-[11px] text-on-surface-variant">Ethereum (ERC-20 USDT)</span>
              </div>

              {/* Metric 4: Estimated Balance */}
              <div className="flex flex-col gap-1">
                <span className="text-[10px] text-outline uppercase tracking-wider font-semibold">Estimated Balance</span>
                <div className="text-lg font-bold text-on-surface mt-1">
                  ₹14,50,000
                </div>
                <span className="font-mono text-xs text-secondary font-semibold">~17,200 USDT</span>
              </div>
            </div>

            {/* Evidentiary Findings: Why we think so */}
            <div className="pt-6">
              <div className="flex items-center gap-2 mb-4">
                <span className="material-symbols-outlined text-primary text-[18px]">verified</span>
                <h3 className="text-sm font-bold text-on-surface">Why we think so</h3>
              </div>

              <div className="space-y-3">
                <div className="flex items-start gap-3">
                  <div className="w-5 h-5 rounded-full bg-surface-container flex items-center justify-center shrink-0 mt-0.5 text-xs font-bold text-primary">
                    1
                  </div>
                  <p className="text-xs text-on-surface leading-relaxed">
                    Deposit address matches known <strong className="text-on-surface">DemoX hot wallet cluster pattern</strong> (<span className="font-mono text-[11px] bg-surface-container-low px-1 py-0.5 rounded text-tertiary">Cluster ID: DX-TRC20-04</span>).
                  </p>
                </div>

                <div className="flex items-start gap-3">
                  <div className="w-5 h-5 rounded-full bg-surface-container flex items-center justify-center shrink-0 mt-0.5 text-xs font-bold text-primary">
                    2
                  </div>
                  <p className="text-xs text-on-surface leading-relaxed">
                    Transaction confirmed at block height <span className="font-mono text-[11px] bg-surface-container-low px-1 py-0.5 rounded">#61,209,412</span> with identical deposit memo tag <span className="font-mono text-[11px] bg-surface-container-low px-1 py-0.5 rounded font-semibold">#983144</span>.
                  </p>
                </div>

                <div className="flex items-start gap-3">
                  <div className="w-5 h-5 rounded-full bg-surface-container flex items-center justify-center shrink-0 mt-0.5 text-xs font-bold text-primary">
                    3
                  </div>
                  <p className="text-xs text-on-surface leading-relaxed">
                    API attribution verified against <strong className="text-on-surface">FIU-IND registered VASP database</strong> with <strong className="text-secondary">99.4% nodal certainty</strong>.
                  </p>
                </div>
              </div>
            </div>

            {/* Operational Action Controls */}
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4 mt-8 pt-4 border-t border-surface-container">
              <div className="flex items-center gap-1.5 text-on-surface-variant text-xs">
                <span className="material-symbols-outlined text-[16px] text-tertiary">lock</span>
                <span>Statutory format compliant with Criminal Procedure Code</span>
              </div>

              <div className="flex items-center gap-3 w-full sm:w-auto">
                <button
                  onClick={() => navigate('/wallet/tron/TJ8wK9vZmB2pQ5aN8cXyZ3rP1kLmN7xL9')}
                  className="px-4 py-2.5 rounded-lg bg-surface-container-low text-on-surface hover:bg-surface-container text-xs font-semibold transition-all border border-surface-container"
                  type="button"
                >
                  Inspect Scammer Dossier
                </button>

                <button
                  onClick={() => navigate('/vasps')}
                  className="px-5 py-2.5 rounded-lg bg-primary-container text-on-primary hover:bg-primary text-xs font-semibold transition-all flex items-center gap-2 shadow-sm"
                  type="button"
                >
                  <span className="material-symbols-outlined text-[16px]">gavel</span>
                  <span>Draft Freeze Request (Sec 91 CrPC)</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: CASE OVERVIEW (Matches chainnetra_case_overview) */}
      {activeTab === 'overview' && (
        <div className="flex flex-col gap-6">
          <div className="bg-surface-container-lowest rounded-xl p-8 shadow-sm border border-surface-container">
            <div className="flex items-center justify-between pb-6 mb-6 border-b border-surface-container">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-surface-container flex items-center justify-center text-primary">
                  <span className="material-symbols-outlined text-[22px]">subject</span>
                </div>
                <div>
                  <h2 className="font-headline-md text-lg font-bold text-on-surface">Case Summary &amp; FIR Baseline</h2>
                  <p className="text-xs text-on-surface-variant">Core FIR baseline details and reported vector description</p>
                </div>
              </div>
              <span className="font-mono text-xs px-2.5 py-1 rounded bg-secondary-container/40 text-secondary font-semibold">
                STATUS: TRACED
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-y-6 gap-x-12 text-xs">
              <div className="flex items-start gap-4">
                <div className="w-7 h-7 rounded-full bg-surface-container flex items-center justify-center shrink-0 text-primary">
                  <span className="material-symbols-outlined text-[16px]">person</span>
                </div>
                <div>
                  <span className="text-[10px] uppercase tracking-wider text-outline font-semibold block mb-0.5">
                    Complainant / FIR Record
                  </span>
                  <p className="text-sm font-semibold text-primary">Victim: Suresh Kulkarni</p>
                  <p className="text-on-surface-variant mt-0.5">FIR #184/2024 registered under Sec 66D IT Act &amp; 420 IPC.</p>
                </div>
              </div>

              <div className="flex items-start gap-4">
                <div className="w-7 h-7 rounded-full bg-surface-container flex items-center justify-center shrink-0 text-primary">
                  <span className="material-symbols-outlined text-[16px]">psychology</span>
                </div>
                <div>
                  <span className="text-[10px] uppercase tracking-wider text-outline font-semibold block mb-0.5">
                    Modus Operandi
                  </span>
                  <p className="text-sm font-semibold text-on-surface">Telegram Task Scam (30% Daily Return Guarantee)</p>
                  <p className="text-on-surface-variant mt-0.5">Victim recruited via encrypted channel for rating Google Maps locations.</p>
                </div>
              </div>

              <div className="flex items-start gap-4">
                <div className="w-7 h-7 rounded-full bg-surface-container flex items-center justify-center shrink-0 text-primary">
                  <span className="material-symbols-outlined text-[16px]">payments</span>
                </div>
                <div>
                  <span className="text-[10px] uppercase tracking-wider text-outline font-semibold block mb-0.5">
                    Source Inflow
                  </span>
                  <p className="text-sm font-semibold text-on-surface">Initial Deposit: ₹14,50,000</p>
                  <p className="text-on-surface-variant mt-0.5">Sent via bank NEFT/UPI to scammer gateway on Oct 24, 09:12 IST.</p>
                </div>
              </div>

              <div className="flex items-start gap-4">
                <div className="w-7 h-7 rounded-full bg-surface-container flex items-center justify-center shrink-0 text-secondary">
                  <span className="material-symbols-outlined text-[16px]">verified</span>
                </div>
                <div>
                  <span className="text-[10px] uppercase tracking-wider text-outline font-semibold block mb-0.5">
                    Current Resolution Stage
                  </span>
                  <p className="text-sm font-semibold text-secondary">Terminal Custodian Identified (Binance Global)</p>
                  <p className="text-on-surface-variant mt-0.5">Internal UID: 983144 • Ready for Sec 91 CrPC notice dispatch.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: WALLETS */}
      {activeTab === 'wallets' && (
        <div className="bg-surface-container-lowest rounded-xl p-6 shadow-sm border border-surface-container">
          <h2 className="text-base font-bold text-on-surface mb-4">8 Wallets Mapped in Cascade</h2>
          <div className="divide-y divide-surface-container text-xs">
            {[
              { role: 'Victim Complainant', addr: '0x89c2...41a0', chain: 'Tron', bal: '0 USDT', type: 'Origin' },
              { role: 'Scammer Primary Collector', addr: 'TJ8wK9vZmB2pQ5aN8cXyZ3rP1kLmN7xL9', chain: 'Tron', bal: '98,400 USDT', type: 'High Risk' },
              { role: 'Peel Splitter Node', addr: '0x4bE12D83a6cE811F79cE841D124806a282912D8', chain: 'Tron', bal: '1,200 USDT', type: 'Mule' },
              { role: 'Mule Wallet A (Transit Layer 1)', addr: '0x81C7b542031Bf1A39bA932E5049b4911E39293bA', chain: 'Tron', bal: '340 USDT', type: 'Mule' },
              { role: 'Bridge Stargate Router', addr: '0x2F6DB5...Bridge', chain: 'Tron → ETH', bal: 'N/A', type: 'Bridge' },
              { role: 'Mule Wallet B (Transit Layer 2)', addr: '0x33AeE21...91', chain: 'Ethereum', bal: '520 USDT', type: 'Mule' },
              { role: 'Aggregator Pool Node', addr: '0x7a3...e21', chain: 'Ethereum', bal: '2,400 USDT', type: 'Aggregator' },
              { role: 'Binance Custodial Deposit Gateway', addr: '0x3f5CE5FBFe3E9af3971dD833D26bA9b5C936f0bE', chain: 'Ethereum', bal: '17,200 USDT', type: 'VASP' },
            ].map((w, idx) => (
              <div key={idx} className="py-3.5 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="font-bold text-primary text-xs w-6">{idx + 1}.</span>
                  <div>
                    <span className="font-semibold text-on-surface">{w.role}</span>
                    <div className="font-mono text-outline text-[11px]">{w.addr}</div>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <span className="text-[11px] font-mono text-on-surface-variant">{w.chain}</span>
                  <span className="font-bold text-on-surface">{w.bal}</span>
                  <button 
                    onClick={() => navigate(`/wallet/tron/${w.addr}`)}
                    className="text-xs text-primary font-semibold hover:underline"
                  >
                    Dossier →
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 4: EVIDENCE & LOGS */}
      {activeTab === 'evidence' && (
        <div className="bg-surface-container-lowest rounded-xl p-6 shadow-sm border border-surface-container space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-on-surface">Tamper-Evident Ledger Audit Log</h2>
            <span className="font-mono text-xs text-secondary font-semibold">CCTNS State Vault Anchored</span>
          </div>
          <div className="space-y-3 text-xs">
            <div className="p-3 rounded-lg bg-surface-container-low flex items-center justify-between border border-surface-container">
              <div>
                <span className="font-bold text-on-surface">Block Checkpoint Anchored</span>
                <p className="text-outline text-[11px]">Polygon PoS #62,912,410 • Cryptographic Merkle Root Seal</p>
              </div>
              <span className="font-mono text-primary text-[11px]">SHA256: 7c9e...b201</span>
            </div>
            <div className="p-3 rounded-lg bg-surface-container-low flex items-center justify-between border border-surface-container">
              <div>
                <span className="font-bold text-on-surface">1930 Triage Verification</span>
                <p className="text-outline text-[11px]">NCRB portal synchronized with complaint token #NCRP-2024-99182</p>
              </div>
              <span className="text-secondary font-semibold">CONFIRMED</span>
            </div>
          </div>
        </div>
      )}

      {/* TAB 5: REPORT DRAFT */}
      {activeTab === 'report' && (
        <div className="bg-surface-container-lowest rounded-xl p-8 shadow-sm border border-surface-container flex flex-col items-center">
          <span className="material-symbols-outlined text-4xl text-primary mb-2">description</span>
          <h2 className="text-lg font-bold text-on-surface">Section 65B Certified Forensic Report Ready</h2>
          <p className="text-xs text-outline mt-1 mb-6 text-center max-w-md">
            All 4 hops, VASP deposit hashes, and Indian Evidence Act certificates compiled into official Form VIII CR-IT.
          </p>
          <button
            onClick={() => navigate('/reports')}
            className="px-6 py-2.5 rounded-lg bg-primary-container text-on-primary text-xs font-semibold hover:bg-primary transition-all flex items-center gap-2"
          >
            <span className="material-symbols-outlined text-[16px]">visibility</span>
            <span>Open Court-Admissible Dossier</span>
          </button>
        </div>
      )}
    </div>
  );
};
