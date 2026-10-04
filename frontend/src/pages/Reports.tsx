import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { api } from '../lib/api';

export const Reports: React.FC = () => {
  const navigate = useNavigate();
  const [copiedHash, setCopiedHash] = useState(false);
  const [reports, setReports] = useState<any[]>([]);
  const [viewMode, setViewMode] = useState<'dossier' | 'archive'>('dossier');

  const sha256Fingerprint = '7c9e81f5c6b4129e9d5012a8848fc771649d21ab66904ef2c39e09983a92b01';

  useEffect(() => {
    api.getReports().then((res) => {
      if (res && res.reports) {
        setReports(res.reports);
      }
    }).catch(() => {});
  }, []);

  const handleCopyHash = () => {
    navigator.clipboard.writeText(sha256Fingerprint);
    setCopiedHash(true);
    toast.success('Cryptographic SHA-256 fingerprint copied');
    setTimeout(() => setCopiedHash(false), 2000);
  };

  const handlePrint = () => {
    window.print();
  };

  const handleDownloadPdf = () => {
    toast.success('Generating cryptographically sealed Section 65B Evidence Dossier PDF');
  };

  const handleEmailProsecutor = () => {
    toast.success('Dispatching secured dossier packet to Public Prosecutor e-Court portal (pp.cybercourt@gov.in)');
  };

  return (
    <div className="flex flex-col w-full pb-16 animate-in fade-in duration-200">
      {/* Header Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
        <div className="flex flex-col">
          <div className="flex items-center gap-2 text-on-surface-variant mb-1 font-mono">
            <span className="text-code-sm uppercase tracking-wider font-semibold">FIR NO: CR-402/24</span>
            <span className="text-outline">/</span>
            <span className="text-label-sm text-secondary font-semibold">DIGITALLY NOTARIZED</span>
          </div>
          <h1 className="text-headline-lg text-on-surface font-semibold tracking-tight">Court-Admissible Evidence Dossier</h1>
        </div>

        <div className="flex items-center gap-3">
          <div className="inline-flex p-1 bg-surface-container rounded-lg border border-outline-variant/50">
            <button
              onClick={() => setViewMode('dossier')}
              className={`px-3 py-1.5 text-label-md rounded font-semibold transition-all ${
                viewMode === 'dossier'
                  ? 'bg-surface-container-lowest text-primary shadow-sm'
                  : 'text-on-surface-variant hover:text-on-surface'
              }`}
            >
              Dossier Preview
            </button>
            <button
              onClick={() => setViewMode('archive')}
              className={`px-3 py-1.5 text-label-md rounded font-semibold transition-all ${
                viewMode === 'archive'
                  ? 'bg-surface-container-lowest text-primary shadow-sm'
                  : 'text-on-surface-variant hover:text-on-surface'
              }`}
            >
              Report Archive ({reports.length > 0 ? reports.length : 3})
            </button>
          </div>

          <button
            onClick={handlePrint}
            className="px-4 py-2 bg-surface-container-high hover:bg-surface-container text-on-surface rounded font-label-md text-label-md flex items-center gap-2 transition-colors border border-outline-variant/40"
            type="button"
          >
            <span className="material-symbols-outlined text-base">print</span>
            <span>Print Dispatch</span>
          </button>
          <button
            onClick={() => navigate('/verify')}
            className="px-4 py-2 bg-primary hover:bg-primary-container text-on-primary rounded font-label-md text-label-md flex items-center gap-2 shadow-sm transition-colors font-semibold"
            type="button"
          >
            <span className="material-symbols-outlined text-base">verified</span>
            <span>Cryptographically Sealed</span>
          </button>
        </div>
      </div>

      {viewMode === 'dossier' ? (
        <div className="grid grid-cols-1 xl:grid-cols-12 gap-8 items-start">
          {/* Main Printable Dossier Card (8 Cols) */}
          <div className="xl:col-span-8 flex flex-col items-center">
            <div className="w-full max-w-[840px] bg-surface-container-lowest rounded-xl shadow-md border border-outline-variant/60 p-8 md:p-10 flex flex-col text-on-surface relative">
              {/* Institutional Header */}
              <div className="flex items-center justify-between pb-6 mb-6 bg-surface-container-low/40 border border-outline-variant/40 p-4 rounded-lg">
                <div className="flex items-center gap-3.5">
                  <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center text-primary">
                    <span className="material-symbols-outlined text-3xl">shield</span>
                  </div>
                  <div className="flex flex-col">
                    <span className="text-label-sm text-on-surface-variant tracking-wider uppercase font-semibold">
                      Cyber Crime Investigation Cell
                    </span>
                    <span className="text-headline-sm text-on-surface tracking-tight uppercase font-bold">
                      Crime Investigation Department (CID)
                    </span>
                    <span className="font-code-sm text-outline font-mono">
                      State Police Cyber Command • Nodal Centre
                    </span>
                  </div>
                </div>
                <div className="text-right">
                  <span className="inline-block px-2.5 py-1 bg-surface-container-high text-on-surface font-code-sm rounded font-mono font-bold">
                    FORM VIII - CR-IT
                  </span>
                  <p className="text-label-sm text-outline mt-1 font-semibold">CONFIDENTIAL // LEA ONLY</p>
                </div>
              </div>

              {/* Title */}
              <div className="text-center py-2 mb-6 border-b border-outline-variant/30 pb-4">
                <h2 className="text-headline-md text-primary font-bold uppercase tracking-tight">
                  Cryptocurrency Forensic Trace &amp; Evidentiary Audit Report
                </h2>
                <div className="flex items-center justify-center gap-2 mt-1 text-on-surface-variant font-code-sm font-mono flex-wrap">
                  <span>
                    Case Ref: <strong className="text-on-surface font-semibold">#CN-2024-0944</strong>
                  </span>
                  <span>•</span>
                  <span>Pune Telegram Task Scam</span>
                  <span>•</span>
                  <span>Generated: 24 Oct 2024, 11:45 IST</span>
                </div>
              </div>

              {/* Section 1: Executive Summary */}
              <div className="mb-6">
                <div className="flex items-center justify-between bg-surface-container-low px-3 py-1.5 rounded mb-2 border border-outline-variant/30">
                  <span className="text-label-sm text-on-surface-variant uppercase tracking-wider font-semibold">
                    1. Executive Summary &amp; Modus Operandi
                  </span>
                  <span className="font-code-sm text-outline font-mono">Section 65B Certified</span>
                </div>
                <p className="text-body-md text-on-surface leading-relaxed text-justify bg-surface-bright p-3.5 rounded-lg border border-outline-variant/20">
                  Victim transferred an initial aggregate sum of <strong>45,000 USDT</strong> following deceptive part-time job solicitations hosted on encrypted channels. Forensic telemetry isolates the primary source address and establishes a systematic <strong>4-hop obfuscation peel-chain</strong>. Split transactions consolidated rapidly at Hop 3 through an regional aggregator before final termination at a designated VASP deposit gateway (Binance Custodial UID: 8192019) mapped to jurisdictional accounts.
                </p>
              </div>

              {/* Section 2: Fund Movement Flow */}
              <div className="mb-6">
                <div className="flex items-center justify-between bg-surface-container-low px-3 py-1.5 rounded mb-3 border border-outline-variant/30">
                  <span className="text-label-sm text-on-surface-variant uppercase tracking-wider font-semibold">
                    2. Fund Movement Flow (Hop Reconstruction)
                  </span>
                  <span className="text-label-sm text-secondary font-semibold">Verified Trail Match: 100%</span>
                </div>
                <div className="bg-surface-container-low/30 border border-outline-variant/30 rounded-lg p-4 flex flex-col gap-3">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-center relative">
                    <div className="bg-surface-container-lowest p-3 rounded-lg shadow-sm border border-outline-variant/40 flex flex-col items-center">
                      <span className="text-label-sm text-error uppercase font-bold">Victim Origin</span>
                      <span className="font-code-sm text-on-surface-variant truncate w-full mt-1 font-mono">0x3b89...42f1</span>
                      <span className="text-headline-sm text-on-surface font-semibold mt-1">45,000 USDT</span>
                      <span className="text-label-sm text-outline mt-0.5">≈ ₹37,57,500</span>
                    </div>
                    <div className="bg-surface-container-lowest p-3 rounded-lg shadow-sm border border-outline-variant/40 flex flex-col items-center">
                      <span className="text-label-sm text-tertiary uppercase font-bold">Hop 1 (Peel Split)</span>
                      <span className="font-code-sm text-on-surface-variant truncate w-full mt-1 font-mono">0x91da...810a</span>
                      <span className="text-headline-sm text-on-surface font-semibold mt-1">44,850 USDT</span>
                      <span className="text-label-sm text-outline mt-0.5">Split -150 Fee</span>
                    </div>
                    <div className="bg-surface-container-lowest p-3 rounded-lg shadow-sm border border-outline-variant/40 flex flex-col items-center">
                      <span className="text-label-sm text-tertiary uppercase font-bold">Hop 2-3 (Mix Pool)</span>
                      <span className="font-code-sm text-on-surface-variant truncate w-full mt-1 font-mono">0x62cc...e099</span>
                      <span className="text-headline-sm text-on-surface font-semibold mt-1">44,720 USDT</span>
                      <span className="text-label-sm text-outline mt-0.5">Aggregator Node</span>
                    </div>
                    <div className="bg-surface-container-lowest p-3 rounded-lg shadow-sm border-2 border-secondary/50 flex flex-col items-center">
                      <span className="text-label-sm text-secondary uppercase font-bold">Final Terminus</span>
                      <span className="font-code-sm text-on-surface-variant truncate w-full mt-1 font-mono">Binance Hot #14</span>
                      <span className="text-headline-sm text-on-surface font-semibold mt-1">44,650 USDT</span>
                      <span className="text-label-sm text-error font-semibold mt-0.5">Freeze Notice Req.</span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between text-outline px-2 pt-1">
                    <div className="flex items-center gap-1 font-code-sm font-mono">
                      <span className="material-symbols-outlined text-sm">hub</span>
                      <span>Polygon PoS • Chain ID: 137</span>
                    </div>
                    <div className="flex items-center gap-1 font-code-sm font-mono">
                      <span className="material-symbols-outlined text-sm">timer</span>
                      <span>Total Elapsed Time: 1 hr 14 mins</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Section 3: Evidentiary Ledger Table */}
              <div className="mb-6">
                <div className="flex items-center justify-between bg-surface-container-low px-3 py-1.5 rounded mb-2 border border-outline-variant/30">
                  <span className="text-label-sm text-on-surface-variant uppercase tracking-wider font-semibold">
                    3. Evidentiary Ledger Table
                  </span>
                  <span className="font-code-sm text-outline font-mono">4 Confirmed Records</span>
                </div>
                <div className="overflow-x-auto border border-outline-variant/40 rounded-lg">
                  <table className="w-full text-left text-body-sm">
                    <thead className="bg-surface-container-low text-on-surface-variant uppercase text-label-sm">
                      <tr>
                        <th className="py-2.5 px-3">Step</th>
                        <th className="py-2.5 px-3">Timestamp (IST)</th>
                        <th className="py-2.5 px-3">Tx Hash (Polygon)</th>
                        <th className="py-2.5 px-3">Sender → Target</th>
                        <th className="py-2.5 px-3 text-right">Amount (USDT / INR)</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-outline-variant/20 font-mono">
                      <tr className="hover:bg-surface-container-low/40">
                        <td className="py-2 px-3 font-semibold text-primary">Hop 1</td>
                        <td className="py-2 px-3 font-code-sm text-outline">24/10 09:32:14</td>
                        <td className="py-2 px-3 font-code-sm text-primary">0x91a2...f381</td>
                        <td className="py-2 px-3 font-code-sm">0x3b89 → 0x91da</td>
                        <td className="py-2 px-3 text-right font-code-sm">
                          45,000 (<span className="text-outline">₹37.5L</span>)
                        </td>
                      </tr>
                      <tr className="hover:bg-surface-container-low/40">
                        <td className="py-2 px-3 font-semibold text-primary">Hop 2</td>
                        <td className="py-2 px-3 font-code-sm text-outline">24/10 09:54:02</td>
                        <td className="py-2 px-3 font-code-sm text-primary">0x8cf1...48a2</td>
                        <td className="py-2 px-3 font-code-sm">0x91da → 0x41e8</td>
                        <td className="py-2 px-3 text-right font-code-sm">
                          44,850 (<span className="text-outline">₹37.4L</span>)
                        </td>
                      </tr>
                      <tr className="hover:bg-surface-container-low/40">
                        <td className="py-2 px-3 font-semibold text-primary">Hop 3</td>
                        <td className="py-2 px-3 font-code-sm text-outline">24/10 10:18:45</td>
                        <td className="py-2 px-3 font-code-sm text-primary">0x33e9...01bf</td>
                        <td className="py-2 px-3 font-code-sm">0x41e8 → 0x62cc</td>
                        <td className="py-2 px-3 text-right font-code-sm">
                          44,720 (<span className="text-outline">₹37.3L</span>)
                        </td>
                      </tr>
                      <tr className="hover:bg-surface-container-low/40">
                        <td className="py-2 px-3 font-semibold text-secondary font-bold">Hop 4</td>
                        <td className="py-2 px-3 font-code-sm text-outline">24/10 10:46:11</td>
                        <td className="py-2 px-3 font-code-sm text-primary">0xbb52...98c1</td>
                        <td className="py-2 px-3 font-code-sm">
                          0x62cc → <span className="text-secondary font-semibold">Binance_Hot</span>
                        </td>
                        <td className="py-2 px-3 text-right font-code-sm font-semibold">
                          44,650 (<span className="text-outline">₹37.2L</span>)
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Notary Seal & Signatory Box */}
              <div className="mt-4 pt-6 bg-surface-container-low/30 border border-outline-variant/40 p-4 rounded-lg flex items-center justify-between flex-wrap gap-4">
                <div className="flex items-center gap-4">
                  <div className="w-16 h-16 bg-surface-container-lowest border border-outline-variant/60 p-1.5 rounded shadow-sm flex items-center justify-center">
                    <svg className="w-full h-full text-on-surface fill-current" viewBox="0 0 100 100">
                      <rect height="30" width="30" x="0" y="0"></rect>
                      <rect fill="white" height="20" width="20" x="5" y="5"></rect>
                      <rect height="12" width="12" x="9" y="9"></rect>
                      <rect height="30" width="30" x="70" y="0"></rect>
                      <rect fill="white" height="20" width="20" x="75" y="5"></rect>
                      <rect height="12" width="12" x="79" y="9"></rect>
                      <rect height="30" width="30" x="0" y="70"></rect>
                      <rect fill="white" height="20" width="20" x="5" y="75"></rect>
                      <rect height="12" width="12" x="9" y="79"></rect>
                      <circle cx="50" cy="50" r="8"></circle>
                      <rect height="8" width="8" x="40" y="20"></rect>
                      <rect height="14" width="8" x="40" y="70"></rect>
                      <rect height="8" width="12" x="70" y="50"></rect>
                      <rect height="8" width="10" x="25" y="45"></rect>
                    </svg>
                  </div>
                  <div className="flex flex-col">
                    <span className="text-label-sm text-on-surface font-semibold uppercase">Tamper Verification Node</span>
                    <span className="text-body-sm text-outline max-w-xs leading-tight mt-0.5">
                      Scan to verify tamper-proof authenticity on State Police Ledger.
                    </span>
                    <span className="font-code-sm text-secondary font-mono mt-1 font-semibold">
                      BLOCK_SEAL_HASH: 0x8a9018f...21c
                    </span>
                  </div>
                </div>
                <div className="flex flex-col items-end">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="material-symbols-outlined text-secondary text-2xl">verified_user</span>
                    <span className="text-headline-sm text-on-surface font-bold tracking-tight">R. Sharma</span>
                  </div>
                  <span className="text-label-sm text-outline uppercase font-semibold">Inspector, Cyber Crime CID</span>
                  <span className="font-code-sm text-outline font-mono">PIN ID: MH-POL-98218</span>
                  <span className="font-code-sm text-secondary font-semibold font-mono mt-1">
                    DSC Token Issued: NIC-CA
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Right Console: Verification & VASP Action (4 Cols) */}
          <div className="xl:col-span-4 flex flex-col gap-6">
            <div className="bg-surface-container-lowest rounded-xl shadow-sm border border-outline-variant/60 p-7 flex flex-col">
              <h2 className="text-headline-sm text-on-surface font-semibold pb-3 border-b border-outline-variant/30">
                Forensic Integrity &amp; Verification
              </h2>

              <div className="bg-secondary/10 border border-secondary/20 rounded-lg p-4 flex items-start gap-3 my-4">
                <span className="material-symbols-outlined text-secondary text-2xl shrink-0 mt-0.5">check_circle</span>
                <div className="flex flex-col">
                  <span className="text-label-md text-on-secondary-container font-semibold">
                    Authentic. Immutable State Record.
                  </span>
                  <span className="text-body-sm text-on-surface-variant mt-0.5">
                    This report matches the cryptographic snapshot preserved at origin.
                  </span>
                  <span className="font-code-sm text-secondary font-semibold font-mono mt-1">
                    Ledger Checkpoint: Block #66,419,021
                  </span>
                </div>
              </div>

              <div className="flex flex-col gap-3 py-2 text-body-sm">
                <div className="flex justify-between items-center py-1 border-b border-outline-variant/20">
                  <span className="text-outline">Report ID</span>
                  <span className="font-code-sm text-on-surface font-semibold font-mono">CN-REP-2024-88219</span>
                </div>
                <div className="flex justify-between items-center py-1 border-b border-outline-variant/20">
                  <span className="text-outline">Generated Timestamp</span>
                  <span className="font-code-sm text-on-surface font-mono">24 Oct 2024, 11:45 IST</span>
                </div>
                <div className="flex justify-between items-center py-1 border-b border-outline-variant/20">
                  <span className="text-outline">Investigating Officer</span>
                  <span className="text-label-md text-on-surface font-semibold">Insp. R. Sharma (Cyber Unit)</span>
                </div>

                <div className="flex flex-col gap-1.5 py-2">
                  <div className="flex items-center justify-between">
                    <span className="text-outline text-label-sm uppercase font-semibold">
                      Cryptographic Fingerprint (SHA-256)
                    </span>
                    <button
                      onClick={handleCopyHash}
                      className="text-primary hover:text-primary-container font-code-sm flex items-center gap-1 font-mono font-semibold"
                      type="button"
                    >
                      <span className="material-symbols-outlined text-sm">content_copy</span>
                      <span>{copiedHash ? 'Copied!' : 'Copy'}</span>
                    </button>
                  </div>
                  <div className="bg-surface-container-low border border-outline-variant/40 p-2.5 rounded text-on-surface font-code-sm break-all select-all font-mono leading-normal">
                    {sha256Fingerprint}
                  </div>
                </div>

                <div className="bg-surface-container-high/40 border border-outline-variant/40 p-3 rounded-lg mt-1 flex items-start gap-2.5">
                  <span className="material-symbols-outlined text-primary text-lg shrink-0 mt-0.5">gavel</span>
                  <div className="flex flex-col text-body-sm">
                    <span className="text-label-sm text-primary uppercase font-bold">Statutory Admissibility</span>
                    <p className="text-on-surface-variant text-xs mt-0.5 leading-snug">
                      Certified under Sec 65B Indian Evidence Act / Sec 63 Bharatiya Sakshya Adhiniyam (BSA). Preserves hash-tree continuity for submission in Hon'ble Special Courts.
                    </p>
                  </div>
                </div>
              </div>

              <div className="flex flex-col gap-2.5 mt-5 pt-3 border-t border-outline-variant/30">
                <button
                  onClick={handleDownloadPdf}
                  className="w-full py-2.5 px-4 bg-primary hover:bg-primary-container text-on-primary rounded-lg text-label-md font-semibold flex items-center justify-center gap-2 shadow-sm transition-colors"
                  type="button"
                >
                  <span className="material-symbols-outlined text-lg leading-none">download</span>
                  <span>Download Signed PDF</span>
                </button>
                <button
                  onClick={handleEmailProsecutor}
                  className="w-full py-2.5 px-4 bg-surface-container hover:bg-surface-container-high text-on-surface rounded-lg text-label-md font-semibold flex items-center justify-center gap-2 transition-colors border border-outline-variant/40"
                  type="button"
                >
                  <span className="material-symbols-outlined text-lg leading-none">send</span>
                  <span>Email to Public Prosecutor</span>
                </button>
                <button
                  onClick={() => navigate('/verify')}
                  className="w-full py-2 px-4 bg-surface-container-low hover:bg-surface-container text-on-surface-variant rounded-lg text-label-sm uppercase tracking-wider font-semibold flex items-center justify-center gap-1.5 transition-colors border border-outline-variant/30"
                  type="button"
                >
                  <span className="material-symbols-outlined text-base">manage_search</span>
                  <span>Verify Another Report Hash</span>
                </button>
              </div>
            </div>

            {/* VASP Freeze Order Status Card */}
            <div className="bg-surface-container-lowest rounded-xl shadow-sm border border-outline-variant/60 p-6 flex flex-col">
              <h3 className="text-headline-sm text-on-surface font-semibold mb-3">VASP Freeze Order Status</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 bg-surface-container-low border border-outline-variant/40 rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded bg-surface-container-lowest flex items-center justify-center text-primary font-bold font-code-sm font-mono">
                      BN
                    </div>
                    <div className="flex flex-col">
                      <span className="text-label-md text-on-surface font-semibold">Binance Compliance</span>
                      <span className="font-code-sm text-outline font-mono">Notice Ref: LEA-IN-8921</span>
                    </div>
                  </div>
                  <span className="px-2 py-0.5 bg-secondary-fixed text-on-secondary-fixed rounded text-label-sm font-semibold">
                    ACKNOWLEDGED
                  </span>
                </div>
                <div className="p-3 bg-surface-container-low/60 border border-outline-variant/40 rounded-lg flex items-center justify-between">
                  <div className="flex flex-col">
                    <span className="text-label-sm text-on-surface font-semibold">Tether Treasury Blacklist Request</span>
                    <span className="font-code-sm text-outline font-mono">USDT Contract (TRC20/ERC20)</span>
                  </div>
                  <span className="px-2 py-0.5 bg-surface-container-high text-on-surface-variant rounded text-label-sm font-semibold">
                    UNDER REVIEW
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : (
        /* Report Archive View */
        <div className="bg-surface-container-lowest rounded-xl shadow-sm border border-outline-variant/60 overflow-hidden">
          <div className="p-5 border-b border-outline-variant/30 flex items-center justify-between">
            <h2 className="text-headline-sm text-on-surface font-semibold">Case Dossier Archive</h2>
            <span className="text-label-sm text-outline font-mono">SHA-256 Tamper Sealed</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead className="bg-surface-container-low text-label-sm uppercase text-outline">
                <tr>
                  <th className="py-3 px-4">Report Number</th>
                  <th className="py-3 px-4">Associated Case</th>
                  <th className="py-3 px-4">SHA-256 Fingerprint</th>
                  <th className="py-3 px-4">Generated Date</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-outline-variant/20 font-mono text-body-sm">
                <tr className="hover:bg-surface-container-low/40">
                  <td className="py-3 px-4 font-semibold text-primary">CN-REP-2024-88219</td>
                  <td className="py-3 px-4 text-on-surface font-sans">#CN-0944 (Pune Telegram Scam)</td>
                  <td className="py-3 px-4 text-outline font-code-sm truncate max-w-xs">
                    7c9e81f5c6b4129e9d5012a8848fc771649d21ab66904ef2c39e09983a92b01
                  </td>
                  <td className="py-3 px-4 text-on-surface-variant">24 Oct 2024</td>
                  <td className="py-3 px-4 text-right font-sans">
                    <button
                      onClick={() => setViewMode('dossier')}
                      className="px-3 py-1 bg-primary text-on-primary rounded text-label-sm font-semibold hover:bg-primary-container"
                    >
                      View Dossier
                    </button>
                  </td>
                </tr>
                <tr className="hover:bg-surface-container-low/40">
                  <td className="py-3 px-4 font-semibold text-primary">CN-REP-2024-88212</td>
                  <td className="py-3 px-4 text-on-surface font-sans">#CN-0918 (WFH Cyber Fraud)</td>
                  <td className="py-3 px-4 text-outline font-code-sm truncate max-w-xs">
                    4f9a01bce239088192a0912cb849102938471209384029384019283401928301
                  </td>
                  <td className="py-3 px-4 text-on-surface-variant">23 Oct 2024</td>
                  <td className="py-3 px-4 text-right font-sans">
                    <button
                      onClick={() => setViewMode('dossier')}
                      className="px-3 py-1 bg-surface-container text-on-surface rounded text-label-sm font-semibold hover:bg-surface-container-high"
                    >
                      View Dossier
                    </button>
                  </td>
                </tr>
                <tr className="hover:bg-surface-container-low/40">
                  <td className="py-3 px-4 font-semibold text-primary">CN-REP-2024-88190</td>
                  <td className="py-3 px-4 text-on-surface font-sans">#CN-0960 (Fake Trading Protocol)</td>
                  <td className="py-3 px-4 text-outline font-code-sm truncate max-w-xs">
                    a190283cbe901238471928301928301928301928301928301928301928301928
                  </td>
                  <td className="py-3 px-4 text-on-surface-variant">21 Oct 2024</td>
                  <td className="py-3 px-4 text-right font-sans">
                    <button
                      onClick={() => setViewMode('dossier')}
                      className="px-3 py-1 bg-surface-container text-on-surface rounded text-label-sm font-semibold hover:bg-surface-container-high"
                    >
                      View Dossier
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
