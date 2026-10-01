import React from 'react';
import { Eye, Shield, Zap, Lock, FileCheck, Layers, GitBranch, ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export const About: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="space-y-8 max-w-5xl mx-auto py-4 animate-in fade-in duration-200">
      {/* Hero Banner */}
      <div className="text-center space-y-3">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber/15 border border-amber/30 text-amber text-xs font-mono font-bold">
          <Eye className="w-3.5 h-3.5" /> CHAINNETRA FORENSIC PLATFORM
        </div>
        <h1 className="text-3xl md:text-4xl font-extrabold text-text-primary tracking-tight">
          Real-Time Crypto Fraud Attribution & Freeze Intelligence
        </h1>
        <p className="text-sm md:text-base text-text-muted max-w-2xl mx-auto leading-relaxed">
          Turning a days-long manual expert tracing task into a minutes-long automated forensic workflow so proceeds of cybercrime can be frozen before they vanish.
        </p>

        <div className="pt-2 flex justify-center gap-3">
          <button
            onClick={() => navigate('/cases/1')}
            className="px-5 py-2.5 rounded-xl bg-amber text-ink font-bold text-xs hover:bg-amber-400 transition-colors shadow-lg flex items-center gap-2"
          >
            Launch Case Zero Demo <ArrowRight className="w-4 h-4" />
          </button>
          <button
            onClick={() => navigate('/inbox')}
            className="px-4 py-2.5 rounded-xl bg-raised hover:bg-hairline text-text-primary text-xs font-semibold border border-hairline transition-colors"
          >
            Explore Complaint Feed
          </button>
        </div>
      </div>

      {/* Problem vs Solution Comparison */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="p-5 rounded-2xl bg-panel border border-coral/30 space-y-3">
          <h3 className="text-sm font-bold text-coral uppercase tracking-wider font-mono flex items-center gap-2">
            <Shield className="w-4 h-4" /> The Law Enforcement Bottleneck
          </h3>
          <ul className="space-y-2 text-xs text-text-muted leading-relaxed">
            <li>• Scammers exploit non-custodial burner wallets and rapid layering across Tron, EVM, and bridges.</li>
            <li>• Manual blockchain forensics requires scarce, expensive specialized experts.</li>
            <li>• Investigations take 3 to 7 days, by which time funds have already been off-ramped to fiat.</li>
            <li>• Separate police stations in different states file duplicate FIRs against identical syndicates without knowing.</li>
          </ul>
        </div>

        <div className="p-5 rounded-2xl bg-panel border border-mint/30 space-y-3">
          <h3 className="text-sm font-bold text-mint uppercase tracking-wider font-mono flex items-center gap-2">
            <Zap className="w-4 h-4" /> The ChainNetra Breakthrough
          </h3>
          <ul className="space-y-2 text-xs text-text-muted leading-relaxed">
            <li>• Automated First-VASP-Hit tracing algorithm explores flows in priority order by tainted value.</li>
            <li>• Reduces attribution response time from ~3 days to under 3 seconds.</li>
            <li>• 1-Click standardized freeze notice generator citing verified statutory provisions and transaction hashes.</li>
            <li>• Tamper-evident evidence reports with SHA-256 seal and QR verification portal.</li>
          </ul>
        </div>
      </div>

      {/* Architecture Diagram (SVG) */}
      <div className="p-6 rounded-2xl bg-panel border border-hairline space-y-4">
        <h3 className="text-sm font-bold text-text-primary tracking-wide text-center uppercase font-mono">
          ChainNetra End-to-End Forensic Architecture
        </h3>

        <div className="w-full overflow-x-auto py-2">
          <svg viewBox="0 0 860 220" className="w-full min-w-[700px] h-auto">
            {/* Input Ingestion */}
            <rect x="20" y="40" width="160" height="140" rx="10" fill="#0D1424" stroke="#22D3EE" strokeWidth="1.5" />
            <text x="100" y="70" fill="#22D3EE" fontSize="12" fontWeight="bold" textAnchor="middle" fontFamily="Space Grotesk">NCRP / SAHYOG</text>
            <text x="100" y="95" fill="#8A97B8" fontSize="10" textAnchor="middle">Citizen FIR Reports</text>
            <text x="100" y="115" fill="#8A97B8" fontSize="10" textAnchor="middle">CSV Bulk Upload</text>
            <text x="100" y="135" fill="#8A97B8" fontSize="10" textAnchor="middle">Chain Auto-Detect</text>

            {/* Arrow 1 */}
            <line x1="180" y1="110" x2="240" y2="110" stroke="#FFB020" strokeWidth="2" strokeDasharray="4 2" />

            {/* Core Engine */}
            <rect x="240" y="20" width="220" height="180" rx="10" fill="#121B30" stroke="#FFB020" strokeWidth="2" />
            <text x="350" y="50" fill="#FFB020" fontSize="13" fontWeight="bold" textAnchor="middle" fontFamily="Space Grotesk">ChainNetra Forensics</text>
            <text x="350" y="75" fill="#E6ECFF" fontSize="10" textAnchor="middle">Priority First-VASP Engine</text>
            <text x="350" y="95" fill="#E6ECFF" fontSize="10" textAnchor="middle">Taint: Haircut / FIFO / Poison</text>
            <text x="350" y="115" fill="#E6ECFF" fontSize="10" textAnchor="middle">Cross-Chain Bridge Matcher</text>
            <text x="350" y="135" fill="#E6ECFF" fontSize="10" textAnchor="middle">RandomForest Role Classifier</text>
            <text x="350" y="155" fill="#E6ECFF" fontSize="10" textAnchor="middle">Syndicate Clustering Heuristic</text>

            {/* Arrow 2 */}
            <line x1="460" y1="110" x2="520" y2="110" stroke="#FFB020" strokeWidth="2" strokeDasharray="4 2" />

            {/* Actionable Outputs */}
            <rect x="520" y="40" width="160" height="140" rx="10" fill="#0D1424" stroke="#3DDC97" strokeWidth="1.5" />
            <text x="600" y="70" fill="#3DDC97" fontSize="12" fontWeight="bold" textAnchor="middle" fontFamily="Space Grotesk">VASP Attribution</text>
            <text x="600" y="95" fill="#8A97B8" fontSize="10" textAnchor="middle">Deposit Vault Identified</text>
            <text x="600" y="115" fill="#8A97B8" fontSize="10" textAnchor="middle">Confidence Score &gt; 90%</text>
            <text x="600" y="135" fill="#8A97B8" fontSize="10" textAnchor="middle">Draft Legal Freeze Order</text>

            {/* Arrow 3 */}
            <line x1="680" y1="110" x2="720" y2="110" stroke="#3DDC97" strokeWidth="2" />

            {/* Evidence & Report */}
            <rect x="720" y="40" width="120" height="140" rx="10" fill="#0D1424" stroke="#FF5D5D" strokeWidth="1.5" />
            <text x="780" y="70" fill="#FF5D5D" fontSize="11" fontWeight="bold" textAnchor="middle" fontFamily="Space Grotesk">Evidence Seal</text>
            <text x="780" y="95" fill="#8A97B8" fontSize="9" textAnchor="middle">A4 PDF Report</text>
            <text x="780" y="115" fill="#8A97B8" fontSize="9" textAnchor="middle">SHA-256 Seal</text>
            <text x="780" y="135" fill="#8A97B8" fontSize="9" textAnchor="middle">QR Verify Link</text>
          </svg>
        </div>
      </div>

      {/* Honest Limitations Section */}
      <div className="p-5 rounded-2xl bg-panel border border-hairline space-y-2">
        <h3 className="text-xs font-bold text-amber uppercase tracking-wider font-mono">
          Product Transparency & Forensic Limitations
        </h3>
        <p className="text-xs text-text-muted leading-relaxed">
          1. <strong>Inference vs Absolute Proof:</strong> Blockchain attribution is an evidence-based heuristic inference derived from cluster behavior, deposit sweeps, and known public labels. Formal forfeiture requires compliance confirmation from the target VASP.
          <br />
          2. <strong>Mixer and Privacy Protocols:</strong> Privacy pools break deterministic graph traversal. Mixer candidates in ChainNetra represent probabilistic matching based on equal denominations and timing correlations.
          <br />
          3. <strong>Prototype Synthetic Ground Truth:</strong> All entities in Demo Mode (DemoX, NovaTrade, Zenith, VeilMix) are synthetic entities created for offline demonstration.
        </p>
      </div>
    </div>
  );
};
