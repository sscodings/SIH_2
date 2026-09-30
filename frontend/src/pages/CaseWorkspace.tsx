import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import cytoscape from 'cytoscape';
import fcose from 'cytoscape-fcose';
import { 
  Play, Square, RefreshCw, ZoomIn, ZoomOut, Maximize2, 
  Download, Search, Filter, Shield, AlertTriangle, Building2, 
  Clock, IndianRupee, Lock, Eye, Copy, ExternalLink, Sparkles, 
  ChevronDown, ChevronUp, FastForward, PlayCircle, PauseCircle, 
  Send, UserCheck, CheckCircle2, Sliders, ArrowRight
} from 'lucide-react';
import toast from 'react-hot-toast';
import { api } from '../lib/api';
import { useWebSocket } from '../hooks/useWebSocket';
import { useAppStore } from '../stores/useAppStore';

// Register cytoscape extensions
try {
  cytoscape.use(fcose);
} catch (e) {
  // Already registered
}

export const CaseWorkspace: React.FC = () => {
  const { id = '1' } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const explainMode = useAppStore((s) => s.explainMode);
  const presentationMode = useAppStore((s) => s.presentationMode);
  const setNarration = useAppStore((s) => s.setNarration);

  // Case Data State
  const [caseData, setCaseData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [graphData, setGraphData] = useState<any>({ nodes: [], edges: [], attributions: [] });
  const [attribution, setAttribution] = useState<any>(null);
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [selectedNode, setSelectedNode] = useState<any>(null);

  // Trace Job State
  const [isTracing, setIsTracing] = useState(false);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [traceCounters, setTraceCounters] = useState({ hops: 0, wallets: 1, valueTraced: 134500 });
  const [radarAngle, setRadarAngle] = useState(0);

  // Trace Controls
  const [maxDepth, setMaxDepth] = useState(6);
  const [minValueUsd, setMinValueUsd] = useState(50);
  const [taintModel, setTaintModel] = useState('haircut');
  const [stopAtFirstVasp, setStopAtFirstVasp] = useState(true);
  const [layoutMode, setLayoutMode] = useState<'fcose' | 'breadthfirst' | 'concentric'>('breadthfirst');

  // Replay Scrubber State
  const [isPlayingReplay, setIsPlayingReplay] = useState(false);
  const [replaySpeed, setReplaySpeed] = useState(1);
  const [replayProgress, setReplayProgress] = useState(100);
  const [timelineEdges, setTimelineEdges] = useState<any[]>([]);

  // UI Panels State
  const [bottomTableOpen, setBottomTableOpen] = useState(true);
  const [evidenceMarked, setEvidenceMarked] = useState<Record<string, boolean>>({});
  const [newNote, setNewNote] = useState('');

  // Cytoscape Canvas Ref
  const cyContainerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);

  // Load Case Details
  const loadCase = async () => {
    try {
      setLoading(true);
      const [cRes, gRes, aRes, rRes, tRes] = await Promise.all([
        api.getCase(id),
        api.getCaseGraph(id),
        api.getCaseAttribution(id),
        api.getCaseRecommendations(id),
        api.getCaseTimeline(id)
      ]);
      setCaseData(cRes);
      setGraphData(gRes);
      if (aRes.attributed) setAttribution(aRes);
      setRecommendations(rRes.recommendations || []);
      setTimelineEdges(tRes.timeline || []);
    } catch (e) {
      console.error('Failed to load case:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCase();
  }, [id]);

  // WebSocket Live Events
  useWebSocket(`trace:${id}`, (event, data) => {
    if (event === 'trace_started') {
      setIsTracing(true);
      setNarration(`Initiated forensic trace on root suspect wallet ${data.start_address.slice(0, 10)}...`);
    } else if (event === 'hop_discovered') {
      setTraceCounters((prev) => ({
        hops: Math.max(prev.hops, data.depth || 1),
        wallets: prev.wallets + 1,
        valueTraced: prev.valueTraced
      }));
      if (data.narration) setNarration(data.narration);
      // Dynamically add node/edge to cytoscape if running
      if (cyRef.current) {
        try {
          const cy = cyRef.current;
          if (data.node && !cy.getElementById(data.node.id).length) {
            cy.add({
              group: 'nodes',
              data: {
                id: data.node.id,
                label: data.node.label || data.node.address.slice(0, 8),
                entity_type: data.node.entity_type,
                risk_level: data.node.risk_level,
                chain: data.node.chain,
                value_usd: data.node.value_usd,
                address: data.node.address
              }
            });
          }
          if (data.edge && !cy.getElementById(data.edge.id).length) {
            cy.add({
              group: 'edges',
              data: {
                id: data.edge.id,
                source: data.edge.source,
                target: data.edge.target,
                label: `$${Number(data.edge.amount_usd).toLocaleString()}`,
                amount_usd: data.edge.amount_usd,
                is_cross_chain: data.edge.is_cross_chain
              }
            });
          }
          cy.layout({ name: layoutMode, animate: true, animationDuration: 300 } as any).run();
        } catch (err) {
          console.error('Cy add error:', err);
        }
      }
    } else if (event === 'vasp_found') {
      setAttribution(data);
      setNarration(`VASP Attributed! Deposit identified at ${data.vasp_name} (${data.confidence_score}% confidence).`);
    } else if (event === 'trace_complete') {
      setIsTracing(false);
      loadCase();
      setNarration(`Trace completed! Identified ${data.attributions?.length || 1} destination VASP corridors.`);
      toast.success('Trace complete: Nearest VASP identified!');
    }
  });

  // Initialize and Render Cytoscape Graph
  useEffect(() => {
    if (!cyContainerRef.current) return;

    const nodes = (graphData.nodes || []).map((n: any) => ({
      group: 'nodes' as const,
      data: {
        id: n.id,
        label: n.label || `${n.address.slice(0, 6)}...${n.address.slice(-4)}`,
        entity_type: n.entity_type || 'Unknown',
        risk_level: n.risk_level || 'Low',
        chain: n.chain || 'tron',
        value_usd: n.value_usd || 0,
        address: n.address
      }
    }));

    const edges = (graphData.edges || []).map((e: any) => ({
      group: 'edges' as const,
      data: {
        id: e.id,
        source: e.source,
        target: e.target,
        label: `$${Number(e.amount_usd).toLocaleString()}`,
        amount_usd: e.amount_usd,
        is_cross_chain: e.is_cross_chain
      }
    }));

    const cy = cytoscape({
      container: cyContainerRef.current,
      elements: [...nodes, ...edges],
      style: [
        {
          selector: 'node',
          style: {
            'label': 'data(label)',
            'color': '#E6ECFF',
            'font-family': 'Space Grotesk, sans-serif',
            'font-size': '10px',
            'text-valign': 'bottom',
            'text-margin-y': 5,
            'background-color': '#0D1424',
            'border-width': 2.5,
            'border-color': '#FFB020',
            'width': 36,
            'height': 36,
            'transition-property': 'background-color, border-color, width, height',
            'transition-duration': 0.2
          }
        },
        // Node Type Specific Colors & Rings
        {
          selector: 'node[entity_type *= "VASP"]',
          style: {
            'border-color': '#3DDC97',
            'background-color': '#121B30',
            'width': 44,
            'height': 44,
            'border-width': 3.5
          }
        },
        {
          selector: 'node[entity_type *= "Mixer"]',
          style: {
            'border-color': '#FF5D5D',
            'background-color': '#1a0d14',
            'width': 42,
            'height': 42
          }
        },
        {
          selector: 'node[entity_type *= "Bridge"]',
          style: {
            'border-color': '#8B7CFF',
            'border-style': 'dashed',
            'background-color': '#15132b'
          }
        },
        {
          selector: 'node[entity_type *= "Dormant"]',
          style: {
            'border-color': '#3DDC97',
            'background-color': '#0b261b',
            'border-style': 'dotted'
          }
        },
        {
          selector: 'node:selected',
          style: {
            'border-color': '#22D3EE',
            'border-width': 4
          }
        },
        // Edges
        {
          selector: 'edge',
          style: {
            'width': 'mapData(amount_usd, 50, 150000, 1.5, 6)',
            'line-color': '#FFB020',
            'target-arrow-color': '#FFB020',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'opacity': 0.85,
            'label': 'data(label)',
            'font-size': '8.5px',
            'font-family': 'JetBrains Mono, monospace',
            'color': '#8A97B8',
            'text-rotation': 'autorotate',
            'text-background-color': '#070B14',
            'text-background-opacity': 0.8,
            'text-background-padding': '2px'
          }
        },
        {
          selector: 'edge[is_cross_chain = "true"]',
          style: {
            'line-color': '#8B7CFF',
            'target-arrow-color': '#8B7CFF',
            'line-style': 'dashed'
          }
        }
      ],
      layout: {
        name: layoutMode === 'breadthfirst' ? 'breadthfirst' : (layoutMode === 'fcose' ? 'fcose' : 'concentric'),
        directed: true,
        padding: 40,
        animate: true,
        animationDuration: 400
      } as any
    });

    cy.on('tap', 'node', (evt) => {
      const node = evt.target;
      setSelectedNode(node.data());
    });

    cyRef.current = cy;

    return () => {
      cy.destroy();
    };
  }, [graphData, layoutMode]);

  // Start Trace Trigger
  const handleStartTrace = async () => {
    try {
      setIsTracing(true);
      const res = await api.startTrace(id, {
        max_depth: maxDepth,
        min_value_usd: minValueUsd,
        taint_model: taintModel,
        stop_at_first_vasp: stopAtFirstVasp
      });
      setActiveJobId(res.job_id);
      toast.success('Live forensic tracing started! Tracking fund flows...');
    } catch (e) {
      setIsTracing(false);
      toast.error('Failed to launch trace job');
    }
  };

  const handleCancelTrace = async () => {
    if (!activeJobId) return;
    try {
      await api.cancelTrace(id, activeJobId);
      setIsTracing(false);
      toast('Trace cancelled by investigator');
    } catch (e) {
      console.error(e);
    }
  };

  const handleHighlightShortestPath = () => {
    if (!cyRef.current) return;
    const cy = cyRef.current;
    const root = cy.nodes().roots()[0];
    const vaspNode = cy.nodes('[entity_type *= "VASP"]').first();
    if (root && vaspNode.length) {
      const dijkstra = (cy.elements() as any).dijkstra({ root: root });
      const path = dijkstra.pathTo(vaspNode);
      cy.elements().removeClass('highlighted');
      path.addClass('highlighted');
      path.style({
        'line-color': '#3DDC97',
        'target-arrow-color': '#3DDC97',
        'border-color': '#3DDC97',
        'border-width': 4
      });
      cy.fit(path, 60);
      toast.success('Highlighted direct laundering path to target VASP!');
    }
  };

  const handleAddNote = async () => {
    if (!newNote.trim()) return;
    try {
      await api.addCaseNote(id, newNote);
      setNewNote('');
      loadCase();
      toast.success('Case note recorded in audit log');
    } catch (e) {
      toast.error('Failed to save note');
    }
  };

  const handleExportPng = () => {
    if (!cyRef.current) return;
    const png = cyRef.current.png({ full: true, bg: '#070B14' });
    const a = document.createElement('a');
    a.href = png;
    a.download = `Case-${id}-fund-flow-graph.png`;
    a.click();
    toast.success('Graph snapshot exported (PNG)');
  };

  return (
    <div className="flex-1 flex flex-col gap-3 min-h-[calc(100vh-5rem)] animate-in fade-in duration-200">
      {/* Top Banner: Case Overview & Time-to-Freeze Ring Clock */}
      <div className="bg-panel border border-hairline rounded-xl p-3.5 flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Left: Case Info */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-amber/15 border border-amber/30 flex items-center justify-center shrink-0">
            <Eye className="w-5 h-5 text-amber" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-sm font-bold text-text-primary">{caseData?.case_number || 'CASE-2026-0001'}: {caseData?.title}</h1>
              <span className="px-2 py-0.5 rounded font-mono text-[10px] font-bold bg-coral/20 text-coral border border-coral/40 uppercase">
                {caseData?.priority || 'Critical'}
              </span>
            </div>
            <div className="flex items-center gap-3 text-xs text-text-muted font-mono mt-0.5">
              <span>Primary: <span className="text-cyan">{caseData?.primary_address?.slice(0, 12)}...</span></span>
              <span>•</span>
              <span className="uppercase text-amber">{caseData?.primary_chain}</span>
              <span>•</span>
              <span>{caseData?.complaints?.length || 9} Linked Victims</span>
            </div>
          </div>
        </div>

        {/* Center: Time-to-Freeze Signature Ring Clock */}
        <div className="flex items-center gap-4 bg-raised/70 px-4 py-2 rounded-xl border border-hairline shrink-0">
          <div className="relative w-11 h-11 flex items-center justify-center">
            {/* SVG Ring Timer */}
            <svg className="w-full h-full transform -rotate-90">
              <circle cx="22" cy="22" r="18" stroke="#1F2B47" strokeWidth="3" fill="none" />
              <circle 
                cx="22" cy="22" r="18" 
                stroke="#3DDC97" strokeWidth="3" strokeDasharray="113" strokeDashoffset="25" 
                fill="none" className="transition-all duration-1000"
              />
            </svg>
            <Clock className="w-4 h-4 text-mint absolute" />
          </div>
          <div>
            <div className="text-[10px] font-mono text-text-muted uppercase">Time-To-VASP Attribution</div>
            <div className="text-base font-bold font-mono text-mint">
              {caseData?.time_to_vasp_seconds ? `${caseData.time_to_vasp_seconds}s` : '2.85s'}
            </div>
            <div className="text-[10px] text-text-muted">Manual avg ≈ 3 days vs ChainNetra 2.8s</div>
          </div>
        </div>

        {/* Right: Quick Action Buttons */}
        <div className="flex items-center gap-2">
          {!isTracing ? (
            <button
              onClick={handleStartTrace}
              className="px-4 py-2 rounded-lg bg-amber text-ink font-bold text-xs hover:bg-amber-400 transition-colors flex items-center gap-1.5 shadow"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              Start Automated Trace
            </button>
          ) : (
            <button
              onClick={handleCancelTrace}
              className="px-4 py-2 rounded-lg bg-coral text-white font-bold text-xs hover:bg-coral-600 transition-colors flex items-center gap-1.5 animate-pulse"
            >
              <Square className="w-3.5 h-3.5 fill-current" />
              Cancel Trace
            </button>
          )}

          <button
            onClick={() => navigate('/vasps')}
            className="px-3.5 py-2 rounded-lg bg-raised hover:bg-hairline border border-hairline text-xs font-semibold text-text-primary transition-colors flex items-center gap-1.5"
          >
            <Lock className="w-3.5 h-3.5 text-coral" />
            Freeze Request
          </button>
        </div>
      </div>

      {/* Main 3-Pane Forensic Workspace */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-3 min-h-[560px]">
        {/* LEFT PANE (3 Cols): Case Details, Linked Complaints, Timeline, Notes */}
        <div className="lg:col-span-3 bg-panel border border-hairline rounded-xl p-3.5 flex flex-col gap-3 overflow-y-auto max-h-[750px]">
          <div>
            <h3 className="text-xs font-bold text-text-primary uppercase tracking-wider font-mono mb-2">Case Dossier</h3>
            <p className="text-xs text-text-muted leading-relaxed">
              {caseData?.description}
            </p>
          </div>

          {/* Trace Parameters Controls */}
          <div className="p-3 bg-raised/50 rounded-lg border border-hairline space-y-2.5">
            <div className="flex items-center justify-between text-xs font-bold text-text-primary">
              <span className="flex items-center gap-1.5">
                <Sliders className="w-3.5 h-3.5 text-amber" /> Trace Parameters
              </span>
            </div>

            <div>
              <div className="flex justify-between text-[11px] text-text-muted mb-1">
                <span>Max Depth</span>
                <span className="font-mono text-text-primary">{maxDepth} Hops</span>
              </div>
              <input
                type="range"
                min="1"
                max="10"
                value={maxDepth}
                onChange={(e) => setMaxDepth(Number(e.target.value))}
                className="w-full accent-amber"
              />
            </div>

            <div className="grid grid-cols-2 gap-2 text-[11px]">
              <div>
                <label className="text-text-muted block mb-0.5">Taint Model</label>
                <select
                  value={taintModel}
                  onChange={(e) => setTaintModel(e.target.value)}
                  className="w-full bg-ink border border-hairline rounded p-1 text-text-primary"
                >
                  <option value="haircut">Haircut (Proportional)</option>
                  <option value="fifo">FIFO (First-In)</option>
                  <option value="poison">Poison (100%)</option>
                </select>
              </div>

              <div>
                <label className="text-text-muted block mb-0.5">Min Value ($)</label>
                <input
                  type="number"
                  value={minValueUsd}
                  onChange={(e) => setMinValueUsd(Number(e.target.value))}
                  className="w-full bg-ink border border-hairline rounded p-1 font-mono text-text-primary"
                />
              </div>
            </div>

            <div className="flex items-center justify-between pt-1">
              <label className="text-[11px] text-text-muted">Stop at first VASP</label>
              <input
                type="checkbox"
                checked={stopAtFirstVasp}
                onChange={(e) => setStopAtFirstVasp(e.target.checked)}
                className="rounded bg-ink border-hairline text-amber focus:ring-0"
              />
            </div>
          </div>

          {/* Linked Complaints List */}
          <div className="space-y-1.5">
            <h4 className="text-[11px] font-mono text-text-muted uppercase font-bold">
              Linked Victim Inflows ({caseData?.complaints?.length || 0})
            </h4>
            <div className="space-y-1 max-h-40 overflow-y-auto pr-1">
              {caseData?.complaints?.map((c: any) => (
                <div key={c.id} className="p-2 rounded bg-ink/70 border border-hairline text-xs flex justify-between items-center">
                  <div>
                    <div className="font-mono text-text-primary font-bold">{c.complaint_number}</div>
                    <div className="text-[10px] text-text-muted">{c.victim_name}</div>
                  </div>
                  <div className="text-right font-mono text-amber">
                    ₹{(c.amount_lost_inr / 100000).toFixed(1)}L
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Case Notes & Audit */}
          <div className="space-y-2 pt-2 border-t border-hairline flex-1 flex flex-col justify-end">
            <h4 className="text-[11px] font-mono text-text-muted uppercase font-bold">Investigator Notes</h4>
            <div className="flex gap-1.5">
              <input
                type="text"
                placeholder="Log observation to audit chain..."
                value={newNote}
                onChange={(e) => setNewNote(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleAddNote()}
                className="flex-1 bg-ink border border-hairline rounded-lg px-2.5 py-1 text-xs text-text-primary focus:border-amber focus:outline-none font-mono"
              />
              <button
                onClick={handleAddNote}
                className="px-2.5 py-1 rounded-lg bg-raised hover:bg-hairline border border-hairline text-xs text-amber"
              >
                Save
              </button>
            </div>
          </div>
        </div>

        {/* CENTER PANE (6 Cols): Cytoscape Graph Canvas with Radar Loader */}
        <div className="lg:col-span-6 bg-panel border border-hairline rounded-xl flex flex-col relative overflow-hidden">
          {/* Canvas Toolbar */}
          <div className="p-2.5 border-b border-hairline bg-raised/40 flex items-center justify-between gap-2 z-10">
            {/* Layout selector */}
            <div className="flex items-center gap-1 text-xs">
              <span className="text-[11px] font-mono text-text-muted">Layout:</span>
              <button
                onClick={() => setLayoutMode('breadthfirst')}
                className={`px-2 py-0.5 rounded text-[11px] ${layoutMode === 'breadthfirst' ? 'bg-amber text-ink font-bold' : 'text-text-muted hover:text-text-primary'}`}
              >
                Flow (LTR)
              </button>
              <button
                onClick={() => setLayoutMode('fcose')}
                className={`px-2 py-0.5 rounded text-[11px] ${layoutMode === 'fcose' ? 'bg-amber text-ink font-bold' : 'text-text-muted hover:text-text-primary'}`}
              >
                Force (fCoSE)
              </button>
              <button
                onClick={() => setLayoutMode('concentric')}
                className={`px-2 py-0.5 rounded text-[11px] ${layoutMode === 'concentric' ? 'bg-amber text-ink font-bold' : 'text-text-muted hover:text-text-primary'}`}
              >
                Radial
              </button>
            </div>

            {/* Canvas Actions */}
            <div className="flex items-center gap-1.5">
              <button
                onClick={handleHighlightShortestPath}
                className="px-2.5 py-1 rounded bg-mint/15 text-mint border border-mint/30 hover:bg-mint/20 text-xs font-semibold flex items-center gap-1"
                title="Highlight shortest direct path to nearest VASP"
              >
                <ArrowRight className="w-3 h-3" /> Path to VASP
              </button>

              <button
                onClick={() => cyRef.current?.zoom(cyRef.current.zoom() * 1.2)}
                className="p-1 rounded hover:bg-raised text-text-muted hover:text-text-primary"
                title="Zoom In"
              >
                <ZoomIn className="w-4 h-4" />
              </button>
              <button
                onClick={() => cyRef.current?.zoom(cyRef.current.zoom() * 0.8)}
                className="p-1 rounded hover:bg-raised text-text-muted hover:text-text-primary"
                title="Zoom Out"
              >
                <ZoomOut className="w-4 h-4" />
              </button>
              <button
                onClick={() => cyRef.current?.fit(undefined, 30)}
                className="p-1 rounded hover:bg-raised text-text-muted hover:text-text-primary"
                title="Fit to Screen"
              >
                <Maximize2 className="w-4 h-4" />
              </button>
              <button
                onClick={handleExportPng}
                className="p-1 rounded hover:bg-raised text-text-muted hover:text-text-primary"
                title="Export High-Res PNG"
              >
                <Download className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Cytoscape Container */}
          <div className="flex-1 relative w-full h-[520px] bg-ink forensic-grid">
            <div ref={cyContainerRef} className="w-full h-full" />

            {/* Radar Sweep Loader (Active during trace) */}
            {isTracing && (
              <div className="absolute inset-0 pointer-events-none flex items-center justify-center bg-black/40 backdrop-blur-[1px]">
                {/* Rotating Conic Gradient Radar */}
                <div className="relative w-72 h-72 rounded-full border border-amber/30 flex items-center justify-center overflow-hidden">
                  <div className="absolute inset-0 radar-sweep-element rounded-full" />
                  <div className="w-52 h-52 rounded-full border border-amber/20 absolute" />
                  <div className="w-32 h-32 rounded-full border border-cyan/20 absolute" />
                  <div className="w-16 h-16 rounded-full border border-mint/20 absolute" />
                  
                  {/* Central Metrics Card */}
                  <div className="z-10 bg-panel/90 border border-amber/40 rounded-xl p-3 text-center shadow-2xl">
                    <p className="text-[10px] font-mono text-amber font-bold uppercase tracking-wider animate-pulse">
                      Forensic Radar Sweeping...
                    </p>
                    <div className="flex gap-4 mt-2 font-mono text-xs">
                      <div>
                        <span className="text-text-muted text-[10px] block">Hops</span>
                        <span className="font-bold text-text-primary">{traceCounters.hops}</span>
                      </div>
                      <div>
                        <span className="text-text-muted text-[10px] block">Wallets</span>
                        <span className="font-bold text-cyan">{traceCounters.wallets}</span>
                      </div>
                      <div>
                        <span className="text-text-muted text-[10px] block">Traced</span>
                        <span className="font-bold text-amber">${(traceCounters.valueTraced / 1000).toFixed(0)}k</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* RIGHT PANE (3 Cols): Nearest VASP Card, Funds Status, Recommendations, Inspector */}
        <div className="lg:col-span-3 bg-panel border border-hairline rounded-xl p-3.5 flex flex-col gap-3 overflow-y-auto max-h-[750px]">
          {/* NEAREST VASP FOUND CARD (Hero Attribution Moment) */}
          <div className="p-3.5 rounded-xl bg-gradient-to-b from-mint/15 to-panel border-2 border-mint/50 shadow-xl space-y-2.5 relative overflow-hidden">
            <div className="flex items-center justify-between">
              <span className="px-2 py-0.5 rounded bg-mint/20 text-mint border border-mint/40 font-mono text-[10px] font-bold uppercase flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" /> VASP PINPOINTED
              </span>
              <span className="text-[10px] font-mono text-text-muted">{attribution?.hops || 4} Hops</span>
            </div>

            <div>
              <h3 className="text-base font-bold text-text-primary tracking-wide">
                {attribution?.vasp_name || 'DemoX Exchange'}
              </h3>
              <p className="text-[11px] text-text-muted">
                {attribution?.category || 'Centralized Exchange'} • Direct Deposit Sweep
              </p>
            </div>

            {/* Confidence Breakdown Bar */}
            <div className="space-y-1">
              <div className="flex justify-between text-xs font-mono">
                <span className="text-text-muted">Attribution Confidence</span>
                <span className="font-bold text-mint">{attribution?.confidence_score || attribution?.confidence || 92.4}%</span>
              </div>
              <div className="w-full h-2 rounded-full bg-ink overflow-hidden flex">
                <div style={{ width: '45%' }} className="bg-amber" title="Source Reliability Weight (45%)" />
                <div style={{ width: '30%' }} className="bg-cyan" title="Evidence Strength Heuristic (30%)" />
                <div style={{ width: '15%' }} className="bg-mint" title="Cluster Support (15%)" />
                <div style={{ width: '10%' }} className="bg-hairline" title="Hop Decay (-2%/hop)" />
              </div>
              <div className="flex justify-between text-[9px] font-mono text-text-muted">
                <span>Src: 0.98</span>
                <span>Evid: 1.0</span>
                <span>Clust: 0.95</span>
                <span>-0.08 Hops</span>
              </div>
            </div>

            {/* Deposit Details */}
            <div className="p-2 rounded bg-ink/70 border border-hairline font-mono text-[11px] space-y-1">
              <div className="flex justify-between">
                <span className="text-text-muted">Deposit Vault:</span>
                <span className="text-cyan truncate max-w-[120px]">{attribution?.deposit_address || 'TXDemox...'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-muted">Value:</span>
                <span className="text-text-primary font-bold">${Number(attribution?.amount || 133500).toLocaleString()} USDT</span>
              </div>
            </div>

            <button
              onClick={() => navigate('/vasps')}
              className="w-full py-1.5 rounded-lg bg-mint text-ink font-bold text-xs hover:bg-mint-400 transition-colors flex items-center justify-center gap-1 shadow"
            >
              Compose Freeze Request <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Funds Status Card */}
          <div className="p-3 bg-raised/40 rounded-lg border border-hairline space-y-2">
            <h4 className="text-[11px] font-mono text-text-muted uppercase font-bold">Funds Liquidation Status</h4>
            <div className="space-y-1.5 text-xs font-mono">
              <div className="flex justify-between">
                <span className="text-text-muted">Total Traced:</span>
                <span className="text-text-primary font-bold">${Number(graphData.funds_status?.total_traced_usd || 134500).toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-mint flex items-center gap-1">• Reached VASPs:</span>
                <span className="text-mint font-bold">${Number(graphData.funds_status?.vasp_amount_usd || 133500).toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-coral flex items-center gap-1">• In Mixers:</span>
                <span className="text-coral font-bold">${Number(graphData.funds_status?.mixer_amount_usd || 0).toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-cyan flex items-center gap-1">• Dormant (Recoverable):</span>
                <span className="text-cyan font-bold">${Number(graphData.funds_status?.dormant_amount_usd || 0).toLocaleString()}</span>
              </div>
            </div>
          </div>

          {/* Node Inspector (When user clicks node) */}
          {selectedNode ? (
            <div className="p-3 bg-ink rounded-lg border border-cyan/40 space-y-2 animate-in fade-in">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-bold text-cyan font-mono uppercase">Node Inspector</h4>
                <button onClick={() => setSelectedNode(null)} className="text-[10px] text-text-muted hover:text-text-primary">
                  Close
                </button>
              </div>
              <div className="font-mono text-xs space-y-1 text-text-primary">
                <div>
                  <span className="text-text-muted text-[10px] block">Address</span>
                  <div className="flex items-center justify-between text-cyan">
                    <span className="truncate max-w-[160px]">{selectedNode.address}</span>
                    <button 
                      onClick={() => { navigator.clipboard.writeText(selectedNode.address); toast.success('Address copied!'); }}
                      className="text-text-muted hover:text-text-primary"
                    >
                      <Copy className="w-3 h-3" />
                    </button>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-1 text-[11px] pt-1 border-t border-hairline">
                  <div>
                    <span className="text-text-muted text-[10px] block">Entity Type</span>
                    <span>{selectedNode.entity_type}</span>
                  </div>
                  <div>
                    <span className="text-text-muted text-[10px] block">Chain</span>
                    <span className="uppercase">{selectedNode.chain}</span>
                  </div>
                </div>
                <div className="pt-1">
                  <span className="text-text-muted text-[10px] block">Risk Classification</span>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                    selectedNode.risk_level === 'Critical' ? 'bg-coral/20 text-coral' : 'bg-amber/20 text-amber'
                  }`}>
                    {selectedNode.risk_level} Risk
                  </span>
                </div>
              </div>
              <button
                onClick={() => navigate(`/wallet/${selectedNode.chain}/${selectedNode.address}`)}
                className="w-full py-1 text-xs rounded bg-raised hover:bg-hairline border border-hairline text-text-primary font-medium"
              >
                Open Full Wallet Profile
              </button>
            </div>
          ) : (
            <div className="p-3 bg-raised/20 rounded-lg border border-hairline text-center text-xs text-text-muted">
              Click any node on canvas to view full forensic inspection details.
            </div>
          )}

          {/* Recommended Priority Actions */}
          <div className="space-y-2">
            <h4 className="text-[11px] font-mono text-text-muted uppercase font-bold">Recommended Next Steps</h4>
            <div className="space-y-1.5">
              {recommendations.slice(0, 3).map((r: any, idx: number) => (
                <div key={idx} className="p-2 rounded bg-ink border border-hairline hover:border-amber/40 transition-colors">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-coral/20 text-coral uppercase font-bold">
                      {r.priority}
                    </span>
                    <span className="text-[10px] text-text-muted">{r.urgency_badge}</span>
                  </div>
                  <h5 className="text-xs font-semibold text-text-primary">{r.title}</h5>
                  <p className="text-[11px] text-text-muted mt-0.5 line-clamp-2">{r.description}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* BOTTOM PANE: Collapsible Money Flow Replay Scrubber & Transactions Table */}
      <div className="bg-panel border border-hairline rounded-xl overflow-hidden shadow-lg">
        {/* Scrubber Bar Controls */}
        <div className="p-3 bg-raised/70 border-b border-hairline flex flex-col md:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setIsPlayingReplay(!isPlayingReplay)}
              className="p-1.5 rounded-lg bg-amber text-ink font-bold hover:bg-amber-400 transition-colors flex items-center gap-1 text-xs shadow"
            >
              {isPlayingReplay ? <PauseCircle className="w-4 h-4" /> : <PlayCircle className="w-4 h-4" />}
              <span>{isPlayingReplay ? 'Pause' : 'Money Flow Replay'}</span>
            </button>

            <div className="flex items-center gap-1 text-xs font-mono text-text-muted">
              <span>Speed:</span>
              {[1, 2, 4, 8].map((s) => (
                <button
                  key={s}
                  onClick={() => setReplaySpeed(s)}
                  className={`px-1.5 py-0.5 rounded text-[10px] ${replaySpeed === s ? 'bg-amber text-ink font-bold' : 'bg-ink text-text-muted'}`}
                >
                  {s}×
                </button>
              ))}
            </div>
          </div>

          {/* Timeline Slider */}
          <div className="flex-1 max-w-xl flex items-center gap-3 w-full">
            <span className="text-[10px] font-mono text-text-muted shrink-0">T0: Inflow</span>
            <input
              type="range"
              min="0"
              max="100"
              value={replayProgress}
              onChange={(e) => setReplayProgress(Number(e.target.value))}
              className="w-full accent-amber"
            />
            <span className="text-[10px] font-mono text-mint shrink-0">T+5h: DemoX VASP</span>
          </div>

          <button
            onClick={() => setBottomTableOpen(!bottomTableOpen)}
            className="flex items-center gap-1 text-xs text-text-muted hover:text-text-primary font-mono"
          >
            <span>{bottomTableOpen ? 'Hide' : 'Show'} Transaction Table</span>
            {bottomTableOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        </div>

        {/* Collapsible Transaction Hop Table */}
        {bottomTableOpen && (
          <div className="overflow-x-auto max-h-48 p-2">
            <table className="w-full text-left text-xs font-mono">
              <thead className="text-[10px] text-text-muted uppercase border-b border-hairline">
                <tr>
                  <th className="p-2">Tx Hash</th>
                  <th className="p-2">Timestamp</th>
                  <th className="p-2">From Address</th>
                  <th className="p-2">To Address</th>
                  <th className="p-2 text-right">Amount</th>
                  <th className="p-2">Chain</th>
                  <th className="p-2">Cross-Chain</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-hairline">
                {(graphData.edges || []).map((e: any, idx: number) => (
                  <tr key={idx} className="hover:bg-raised/40">
                    <td className="p-2 text-cyan truncate max-w-[120px]">{e.tx_hash}</td>
                    <td className="p-2 text-text-muted">{new Date(e.timestamp).toLocaleTimeString()}</td>
                    <td className="p-2 truncate max-w-[140px] text-text-muted">{e.source}</td>
                    <td className="p-2 truncate max-w-[140px] text-text-primary">{e.target}</td>
                    <td className="p-2 text-right font-bold text-amber">
                      ${Number(e.amount_usd).toLocaleString()} {e.token}
                    </td>
                    <td className="p-2 uppercase">{e.chain}</td>
                    <td className="p-2">
                      {e.is_cross_chain ? (
                        <span className="px-1.5 py-0.2 rounded bg-violet/20 text-violet font-bold text-[9px]">
                          BRIDGE
                        </span>
                      ) : (
                        <span className="text-text-muted text-[10px]">Direct</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
