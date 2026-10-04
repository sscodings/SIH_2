import React, { useState } from 'react';
import toast from 'react-hot-toast';

export const Integrations: React.FC = () => {
  const [testingNcrp, setTestingNcrp] = useState(false);
  const [ncrpOk, setNcrpOk] = useState(false);
  const [testingSahyog, setTestingSahyog] = useState(false);
  const [sahyogOk, setSahyogOk] = useState(false);
  const [copiedCurl, setCopiedCurl] = useState(false);

  const curlPayload = `curl -X POST https://api.chainnetra.police.gov.in/v2/statutory/sec91/freeze-notice \\
  -H "X-Authority-Badge: DL-CRIME-SPEC-4912" \\
  -H "X-HMAC-SHA256: 9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08" \\
  -H "Content-Type: application/json" \\
  -d '{
    "statutory_reference": {
      "act_section": "Section 91, Code of Criminal Procedure (CrPC)",
      "fir_number": "FIR-2024-ND-00892",
      "investigating_officer": "Insp. R. Sharma (ID: 04912)",
      "jurisdiction": "Cyber Crime Unit, Special Cell, New Delhi"
    },
    "target_entity": {
      "blockchain": "TRON",
      "token_contract": "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t",
      "suspect_wallet": "TLyqzVGLV1srkB7dToTAwdg29TFBDg554u",
      "attributed_cluster": "High-Yield Investment Fraud Mule Ring B"
    },
    "statutory_directive": {
      "requested_action": "FREEZE_AND_DISCLOSE_KYC",
      "compliance_window_hours": 24,
      "evidence_hash_ipfs": "QmZtmD2qt8fJpq3CLDHcgDZiu65xVpY30X839GkUeRkYQ5",
      "automated_cctns_diary_ref": "CCTNS-DEL-2024-CR-44109"
    }
  }'`;

  const handleTestNcrp = () => {
    setTestingNcrp(true);
    setTimeout(() => {
      setTestingNcrp(false);
      setNcrpOk(true);
      toast.success('NCRP 1930 Bridge Test: 200 OK (38ms latency)');
      setTimeout(() => setNcrpOk(false), 3000);
    }, 600);
  };

  const handleTestSahyog = () => {
    setTestingSahyog(true);
    setTimeout(() => {
      setTestingSahyog(false);
      setSahyogOk(true);
      toast.success('I4C Gateway Handshake: Mutual Aid Node Verified (19ms)');
      setTimeout(() => setSahyogOk(false), 3000);
    }, 550);
  };

  const handleCopyCurl = () => {
    navigator.clipboard.writeText(curlPayload);
    setCopiedCurl(true);
    toast.success('Section 91 cURL command copied to clipboard');
    setTimeout(() => setCopiedCurl(false), 2000);
  };

  return (
    <div className="flex flex-col w-full pb-16 animate-in fade-in duration-200">
      <div className="space-y-8 max-w-[1400px] mx-auto w-full">
        {/* Header Section */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 pb-2">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded bg-surface-container-high text-on-surface-variant text-label-sm tracking-widest uppercase font-semibold">
              <span className="material-symbols-outlined text-sm text-primary">hub</span>
              Operational Infrastructure
            </div>
            <h1 className="text-display-lg text-on-surface font-semibold tracking-tight">
              System Integrations &amp; Data Feeds
            </h1>
            <p className="text-body-lg text-on-surface-variant max-w-3xl">
              Direct government portal bridges, blockchain telemetry RPC nodes, and statutory legal dispatch gateways.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-surface-container-lowest shadow-sm border border-outline-variant/60">
              <span className="w-2.5 h-2.5 rounded-full bg-secondary animate-pulse"></span>
              <span className="text-label-md text-on-surface font-semibold">Uptime: 99.98%</span>
              <span className="text-outline-variant">•</span>
              <span className="font-code-sm text-on-surface-variant font-mono">TLS 1.3 Strict</span>
            </div>
          </div>
        </div>

        {/* 4 Connector Cards (2x2 Grid) */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Card 1: NCRP Portal */}
          <div className="bg-surface-container-lowest rounded-xl p-7 shadow-sm border border-outline-variant/60 hover:shadow-md transition-all duration-200 flex flex-col justify-between">
            <div className="space-y-5">
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-center gap-3.5">
                  <div className="w-12 h-12 rounded-xl bg-surface-container flex items-center justify-center text-primary shadow-sm">
                    <span className="material-symbols-outlined text-2xl">assured_workload</span>
                  </div>
                  <div>
                    <h2 className="text-headline-md text-on-surface font-semibold">NCRP Portal</h2>
                    <span className="text-label-sm text-on-surface-variant">
                      National Cyber Crime Reporting Portal (MHA)
                    </span>
                  </div>
                </div>
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-secondary-container/40 text-secondary text-label-md font-semibold">
                  <span className="w-2 h-2 rounded-full bg-secondary"></span>
                  Connected
                </span>
              </div>
              <p className="text-body-md text-on-surface-variant leading-relaxed">
                Automated ingestion of daily victim complaints registered under 1930 helpline and cybercrime.gov.in.
              </p>
              <div className="grid grid-cols-2 gap-4 py-2 px-3.5 rounded-lg bg-surface-container-low font-code-sm border border-outline-variant/30">
                <div>
                  <div className="text-on-surface-variant text-[10px] tracking-wide uppercase text-label-sm font-semibold">
                    Poll Interval
                  </div>
                  <div className="text-on-surface font-semibold font-mono">120s (Event Push)</div>
                </div>
                <div>
                  <div className="text-on-surface-variant text-[10px] tracking-wide uppercase text-label-sm font-semibold">
                    Queue Backlog
                  </div>
                  <div className="text-secondary font-semibold font-mono">0 Complaints</div>
                </div>
              </div>
            </div>
            <div className="flex items-center justify-between pt-6 mt-6 border-t border-outline-variant/40">
              <button
                onClick={handleTestNcrp}
                className="px-4 py-2 rounded-lg bg-surface-container-low hover:bg-surface-container text-on-surface text-label-md font-semibold transition-colors flex items-center gap-2 border border-outline-variant/30"
                type="button"
              >
                {testingNcrp ? (
                  <>
                    <span className="material-symbols-outlined text-base animate-spin text-primary">sync</span>
                    <span>Verifying 1930 Bridge...</span>
                  </>
                ) : ncrpOk ? (
                  <>
                    <span className="material-symbols-outlined text-base text-secondary">check_circle</span>
                    <span className="text-secondary">200 OK (38ms)</span>
                  </>
                ) : (
                  <>
                    <span className="material-symbols-outlined text-base text-primary">network_ping</span>
                    <span>Test Connection</span>
                  </>
                )}
              </button>
              <button
                onClick={() => toast.success('NCRP Auto-Sync is active: polling every 120 seconds')}
                className="text-label-md text-primary hover:text-primary-container inline-flex items-center gap-1 transition-colors font-semibold"
                type="button"
              >
                <span>Sync Settings</span>
                <span className="material-symbols-outlined text-sm">arrow_forward</span>
              </button>
            </div>
          </div>

          {/* Card 2: SAHYOG / I4C Gateway */}
          <div className="bg-surface-container-lowest rounded-xl p-7 shadow-sm border border-outline-variant/60 hover:shadow-md transition-all duration-200 flex flex-col justify-between">
            <div className="space-y-5">
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-center gap-3.5">
                  <div className="w-12 h-12 rounded-xl bg-surface-container flex items-center justify-center text-primary shadow-sm">
                    <span className="material-symbols-outlined text-2xl">shield</span>
                  </div>
                  <div>
                    <h2 className="text-headline-md text-on-surface font-semibold">SAHYOG / I4C Gateway</h2>
                    <span className="text-label-sm text-on-surface-variant">
                      Indian Cyber Crime Coordination Centre
                    </span>
                  </div>
                </div>
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-secondary-container/40 text-secondary text-label-md font-semibold">
                  <span className="w-2 h-2 rounded-full bg-secondary"></span>
                  Connected
                </span>
              </div>
              <p className="text-body-md text-on-surface-variant leading-relaxed">
                Inter-agency coordination portal for cross-state police collaboration and centralized suspect repository.
              </p>
              <div className="grid grid-cols-2 gap-4 py-2 px-3.5 rounded-lg bg-surface-container-low font-code-sm border border-outline-variant/30">
                <div>
                  <div className="text-on-surface-variant text-[10px] tracking-wide uppercase text-label-sm font-semibold">
                    Routing Node
                  </div>
                  <div className="text-on-surface font-semibold truncate font-mono">DL-HQ-I4C-GATEWAY-02</div>
                </div>
                <div>
                  <div className="text-on-surface-variant text-[10px] tracking-wide uppercase text-label-sm font-semibold">
                    Mutual Aid Queries
                  </div>
                  <div className="text-primary font-semibold font-mono">14 Active</div>
                </div>
              </div>
            </div>
            <div className="flex items-center justify-between pt-6 mt-6 border-t border-outline-variant/40">
              <button
                onClick={handleTestSahyog}
                className="px-4 py-2 rounded-lg bg-surface-container-low hover:bg-surface-container text-on-surface text-label-md font-semibold transition-colors flex items-center gap-2 border border-outline-variant/30"
                type="button"
              >
                {testingSahyog ? (
                  <>
                    <span className="material-symbols-outlined text-base animate-spin text-primary">sync</span>
                    <span>Handshaking I4C...</span>
                  </>
                ) : sahyogOk ? (
                  <>
                    <span className="material-symbols-outlined text-base text-secondary">check_circle</span>
                    <span className="text-secondary">Node Verified (19ms)</span>
                  </>
                ) : (
                  <>
                    <span className="material-symbols-outlined text-base text-primary">network_ping</span>
                    <span>Test Connection</span>
                  </>
                )}
              </button>
              <button
                onClick={() => toast.success('I4C Mutual Aid Key: SHA256#9841...Valid until 31-DEC-2025')}
                className="text-label-md text-primary hover:text-primary-container inline-flex items-center gap-1 transition-colors font-semibold"
                type="button"
              >
                <span>Audit Key</span>
                <span className="material-symbols-outlined text-sm">key</span>
              </button>
            </div>
          </div>

          {/* Card 3: Blockchain RPC & Indexer Nodes */}
          <div className="bg-surface-container-lowest rounded-xl p-7 shadow-sm border border-outline-variant/60 hover:shadow-md transition-all duration-200 flex flex-col justify-between">
            <div className="space-y-5">
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-center gap-3.5">
                  <div className="w-12 h-12 rounded-xl bg-surface-container flex items-center justify-center text-primary shadow-sm">
                    <span className="material-symbols-outlined text-2xl">account_tree</span>
                  </div>
                  <div>
                    <h2 className="text-headline-md text-on-surface font-semibold">Blockchain RPC &amp; Indexers</h2>
                    <span className="text-label-sm text-on-surface-variant">Decentralized Ledger Telemetry</span>
                  </div>
                </div>
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-secondary-container/40 text-secondary text-label-md font-semibold">
                  <span className="w-2 h-2 rounded-full bg-secondary"></span>
                  Active Mode
                </span>
              </div>
              <p className="text-body-md text-on-surface-variant leading-relaxed">
                Multi-chain evidentiary indexers covering Tron (TRC-20), Ethereum, BNB Smart Chain, and Polygon PoS.
              </p>
              <div className="grid grid-cols-2 gap-4 py-2 px-3.5 rounded-lg bg-surface-container-low font-code-sm border border-outline-variant/30">
                <div>
                  <div className="text-on-surface-variant text-[10px] tracking-wide uppercase text-label-sm font-semibold">
                    Active Chains
                  </div>
                  <div className="text-on-surface font-semibold font-mono">TRON • ETH • BSC • MATIC</div>
                </div>
                <div>
                  <div className="text-on-surface-variant text-[10px] tracking-wide uppercase text-label-sm font-semibold">
                    Block Index Lag
                  </div>
                  <div className="text-secondary font-semibold font-mono">0 blocks (Realtime)</div>
                </div>
              </div>
            </div>
            <div className="flex items-center justify-between pt-6 mt-6 border-t border-outline-variant/40">
              <button
                onClick={() => toast.success('Connected to Mainnet RPC Cluster (4 dedicated archival nodes)')}
                className="px-4 py-2 rounded-lg bg-primary text-on-primary text-label-md font-semibold hover:bg-primary-container transition-colors shadow-sm flex items-center gap-2"
                type="button"
              >
                <span className="material-symbols-outlined text-base">swap_horiz</span>
                <span>Switch to Mainnet RPC</span>
              </button>
              <div className="text-label-md text-primary inline-flex items-center gap-1.5 font-semibold">
                <span className="w-1.5 h-1.5 rounded-full bg-secondary"></span>
                <span>Node Latency (14ms)</span>
              </div>
            </div>
          </div>

          {/* Card 4: Automated Webhook & FIR Sync */}
          <div className="bg-surface-container-lowest rounded-xl p-7 shadow-sm border border-outline-variant/60 hover:shadow-md transition-all duration-200 flex flex-col justify-between">
            <div className="space-y-5">
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-center gap-3.5">
                  <div className="w-12 h-12 rounded-xl bg-surface-container flex items-center justify-center text-primary shadow-sm">
                    <span className="material-symbols-outlined text-2xl">webhook</span>
                  </div>
                  <div>
                    <h2 className="text-headline-md text-on-surface font-semibold">Automated Webhook &amp; FIR Sync</h2>
                    <span className="text-label-sm text-on-surface-variant">Statutory Police Records Daemon</span>
                  </div>
                </div>
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-secondary-container/40 text-secondary text-label-md font-semibold">
                  <span className="w-2 h-2 rounded-full bg-secondary"></span>
                  Active
                </span>
              </div>
              <p className="text-body-md text-on-surface-variant leading-relaxed">
                Real-time webhook notifications for frozen wallet confirmations and automated CCTNS crime diary updates.
              </p>
              <div className="grid grid-cols-2 gap-4 py-2 px-3.5 rounded-lg bg-surface-container-low font-code-sm border border-outline-variant/30">
                <div>
                  <div className="text-on-surface-variant text-[10px] tracking-wide uppercase text-label-sm font-semibold">
                    CCTNS State Relay
                  </div>
                  <div className="text-on-surface font-semibold truncate font-mono">Active • Sec 91 CrPC</div>
                </div>
                <div>
                  <div className="text-on-surface-variant text-[10px] tracking-wide uppercase text-label-sm font-semibold">
                    Delivery Rate
                  </div>
                  <div className="text-secondary font-semibold font-mono">100.0% (24h)</div>
                </div>
              </div>
            </div>
            <div className="flex items-center justify-between pt-6 mt-6 border-t border-outline-variant/40">
              <button
                onClick={() => toast.success('Webhook endpoint configuration updated')}
                className="px-4 py-2 rounded-lg bg-surface-container-low hover:bg-surface-container text-on-surface text-label-md font-semibold transition-colors flex items-center gap-2 border border-outline-variant/30"
                type="button"
              >
                <span className="material-symbols-outlined text-base text-primary">settings_ethernet</span>
                <span>Configure Endpoints</span>
              </button>
              <button
                onClick={() => toast.success('Showing last 50 webhook delivery packets (100% delivered)')}
                className="text-label-md text-primary hover:text-primary-container inline-flex items-center gap-1 transition-colors font-semibold"
                type="button"
              >
                <span>View Webhook Logs</span>
                <span className="material-symbols-outlined text-sm">history</span>
              </button>
            </div>
          </div>
        </div>

        {/* Statutory API Request Sandbox Card */}
        <div className="bg-surface-container-lowest rounded-xl p-7 shadow-sm border border-outline-variant/60 space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-primary text-xl">terminal</span>
                <h3 className="text-headline-sm text-on-surface font-semibold">
                  Sample Statutory API Request (Sec 91 Ingestion)
                </h3>
              </div>
              <p className="text-body-sm text-on-surface-variant">
                Standard serialized payload for legal freezing summons and transaction disclosure directives under Section 91 of the Code of Criminal Procedure.
              </p>
            </div>
            <div className="flex items-center gap-3">
              <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-surface-container-high text-on-surface font-code-sm font-mono">
                <span className="material-symbols-outlined text-xs text-secondary">verified</span>
                SHA-256 Authenticated Endpoint
              </div>
              <button
                onClick={handleCopyCurl}
                className="px-3.5 py-1.5 rounded-lg bg-primary text-on-primary text-label-md font-semibold hover:bg-primary-container transition-colors shadow-sm flex items-center gap-1.5"
                type="button"
              >
                <span className="material-symbols-outlined text-sm">content_copy</span>
                <span>{copiedCurl ? 'Copied!' : 'Copy cURL'}</span>
              </button>
            </div>
          </div>

          {/* Code Box */}
          <div className="relative bg-surface-container-low rounded-lg p-5 font-code-sm overflow-x-auto border border-outline-variant/40 shadow-inner text-on-surface font-mono">
            <pre className="leading-relaxed">
              <span className="text-tertiary font-bold">POST</span> /v2/statutory/sec91/freeze-notice{'\n'}
              <span className="text-outline">Host:</span> api.chainnetra.police.gov.in{'\n'}
              <span className="text-outline">X-Authority-Badge:</span>{' '}
              <span className="text-secondary font-semibold">"DL-CRIME-SPEC-4912"</span>{'\n'}
              <span className="text-outline">X-HMAC-SHA256:</span>{' '}
              9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08{'\n'}
              <span className="text-outline">Content-Type:</span> application/json{'\n'}
              {'\n'}
              {`{
  `}<span className="text-primary font-semibold">"statutory_reference"</span>{`: {
    `}<span className="text-on-surface-variant">"act_section"</span>{`: `}<span className="text-secondary">"Section 91, Code of Criminal Procedure (CrPC)"</span>{`,
    `}<span className="text-on-surface-variant">"fir_number"</span>{`: `}<span className="text-secondary">"FIR-2024-ND-00892"</span>{`,
    `}<span className="text-on-surface-variant">"investigating_officer"</span>{`: `}<span className="text-secondary">"Insp. R. Sharma (ID: 04912)"</span>{`,
    `}<span className="text-on-surface-variant">"jurisdiction"</span>{`: `}<span className="text-secondary">"Cyber Crime Unit, Special Cell, New Delhi"</span>{`
  },
  `}<span className="text-primary font-semibold">"target_entity"</span>{`: {
    `}<span className="text-on-surface-variant">"blockchain"</span>{`: `}<span className="text-secondary">"TRON"</span>{`,
    `}<span className="text-on-surface-variant">"token_contract"</span>{`: `}<span className="text-secondary">"TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"</span>{`, `}<span className="text-outline">// USDT Tether</span>{`
    `}<span className="text-on-surface-variant">"suspect_wallet"</span>{`: `}<span className="text-secondary font-semibold">"TLyqzVGLV1srkB7dToTAwdg29TFBDg554u"</span>{`,
    `}<span className="text-on-surface-variant">"attributed_cluster"</span>{`: `}<span className="text-secondary">"High-Yield Investment Fraud Mule Ring B"</span>{`
  },
  `}<span className="text-primary font-semibold">"statutory_directive"</span>{`: {
    `}<span className="text-on-surface-variant">"requested_action"</span>{`: `}<span className="text-error font-semibold">"FREEZE_AND_DISCLOSE_KYC"</span>{`,
    `}<span className="text-on-surface-variant">"compliance_window_hours"</span>{`: 24,
    `}<span className="text-on-surface-variant">"evidence_hash_ipfs"</span>{`: `}<span className="text-secondary">"QmZtmD2qt8fJpq3CLDHcgDZiu65xVpY30X839GkUeRkYQ5"</span>{`,
    `}<span className="text-on-surface-variant">"automated_cctns_diary_ref"</span>{`: `}<span className="text-secondary">"CCTNS-DEL-2024-CR-44109"</span>{`
  }
}`}
            </pre>
          </div>

          {/* Footer Info Strip */}
          <div className="flex flex-wrap items-center justify-between text-on-surface-variant text-body-sm pt-2">
            <div className="flex items-center gap-4">
              <span className="flex items-center gap-1.5">
                <span className="material-symbols-outlined text-base text-secondary">lock</span>
                Encrypted with Ministry of Home Affairs Root Certificate
              </span>
              <span className="hidden sm:inline text-outline-variant">•</span>
              <span className="flex items-center gap-1.5">
                <span className="material-symbols-outlined text-base text-primary">schedule</span>
                Idempotency Key Guaranteed
              </span>
            </div>
            <div className="font-code-sm text-outline font-mono">
              API Specs v2.4.1 (Gov-Gov Spec)
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
