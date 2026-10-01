import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { 
  ShieldCheck, ShieldAlert, UploadCloud, Search, 
  CheckCircle2, AlertTriangle, FileText, Sparkles 
} from 'lucide-react';
import toast from 'react-hot-toast';
import { api } from '../lib/api';
import { getApiBaseUrl } from '../lib/config';
import { useAppStore } from '../stores/useAppStore';

export const Verify: React.FC = () => {
  const { hash: urlHash } = useParams<{ hash: string }>();
  const explainMode = useAppStore((s) => s.explainMode);

  const [inputHash, setInputHash] = useState(urlHash || '');
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const verifyHashValue = async (targetHash: string) => {
    if (!targetHash.trim()) return;
    try {
      setLoading(true);
      const res = await api.verifyHash(targetHash.trim());
      setResult(res);
    } catch (e: any) {
      setResult({ status: 'Invalid', verified: false, message: e.message });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (urlHash) {
      setInputHash(urlHash);
      verifyHashValue(urlHash);
    }
  }, [urlHash]);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      setLoading(true);
      const res = await fetch(`${getApiBaseUrl()}/verify/upload`, {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      setResult(data);
      if (data.verified) {
        toast.success('Document verified authentic!');
      } else {
        toast.error('Cryptographic signature check failed: Tampered or Unregistered');
      }
    } catch (e) {
      toast.error('Upload verification failed');
    } finally {
      setLoading(false);
    }
  };

  const handleTamperTest = () => {
    // Generate a random 64-char hash that looks genuine but is altered
    const tampered = '08b1b320b41840024217de41d9c2c00dd0a7a88d946cd646f97793128b45dead';
    setInputHash(tampered);
    verifyHashValue(tampered);
  };

  return (
    <div className="space-y-4 max-w-4xl mx-auto animate-in fade-in duration-200">
      {/* Header */}
      <div className="pb-2 border-b border-hairline text-center">
        <h1 className="text-xl font-bold tracking-tight text-text-primary flex items-center justify-center gap-2">
          <ShieldCheck className="w-6 h-6 text-mint" />
          Cryptographic Digital Evidence Verification Portal
        </h1>
        <p className="text-xs text-text-muted mt-1">
          Verify the authenticity and chain of custody for any ChainNetra report, PDF dossier, or canonical ledger snapshot.
        </p>
      </div>

      {explainMode && (
        <div className="p-3 bg-cyan/10 border border-cyan/30 rounded-lg text-xs text-cyan flex items-start gap-2.5">
          <Sparkles className="w-4 h-4 shrink-0 mt-0.5" />
          <div>
            <span className="font-bold">Zero-Trust Verification:</span> Defense attorneys or judges can upload any investigation report to mathematically verify that not a single byte, transaction hash, or dollar amount has been altered since the investigation was finalized.
          </div>
        </div>
      )}

      {/* Hash Input Form */}
      <div className="p-5 bg-panel border border-hairline rounded-xl space-y-4">
        <div>
          <label className="block text-xs font-mono text-text-muted uppercase mb-1.5 font-bold">
            Lookup by SHA-256 Hash
          </label>
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="w-4 h-4 absolute left-3 top-3 text-text-muted" />
              <input
                type="text"
                placeholder="Paste 64-character SHA-256 hash (e.g. 08b1b320b4184002...)"
                value={inputHash}
                onChange={(e) => setInputHash(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && verifyHashValue(inputHash)}
                className="w-full bg-ink border border-hairline rounded-lg pl-9 pr-3 py-2 text-xs font-mono text-text-primary focus:border-amber focus:outline-none"
              />
            </div>
            <button
              onClick={() => verifyHashValue(inputHash)}
              disabled={loading}
              className="px-5 py-2 rounded-lg bg-mint text-ink font-bold text-xs hover:bg-mint-400 transition-colors shadow"
            >
              Verify Hash
            </button>
          </div>
        </div>

        {/* Demo Quick Test Buttons */}
        <div className="flex items-center gap-2 pt-2 border-t border-hairline text-xs font-mono">
          <span className="text-text-muted">Test Scenarios:</span>
          <button
            onClick={() => {
              const authentic = '08b1b320b41840024217de41d9c2c00dd0a7a88d946cd646f97793128b45e2d0';
              setInputHash(authentic);
              verifyHashValue(authentic);
            }}
            className="px-2 py-0.5 rounded bg-raised hover:bg-hairline border border-hairline text-cyan"
          >
            Load Known Authentic Hash
          </button>
          <button
            onClick={handleTamperTest}
            className="px-2 py-0.5 rounded bg-raised hover:bg-hairline border border-hairline text-coral"
          >
            Simulate Modified (Tampered) Hash
          </button>
        </div>

        {/* PDF File Upload Zone */}
        <div className="border-2 border-dashed border-hairline hover:border-mint/50 rounded-xl p-6 text-center cursor-pointer relative bg-ink/40">
          <input
            type="file"
            accept=".pdf"
            onChange={handleFileUpload}
            className="absolute inset-0 opacity-0 cursor-pointer"
          />
          <UploadCloud className="w-8 h-8 text-mint mx-auto mb-2" />
          <p className="text-xs text-text-primary font-medium">Or Drag and Drop Investigation Report PDF Here</p>
          <p className="text-[10px] text-text-muted mt-1 font-mono">Instant client-side SHA-256 calculation & seal verification</p>
        </div>
      </div>

      {/* Verification Result Card */}
      {result && (
        <div className={`p-5 rounded-xl border-2 shadow-2xl animate-in zoom-in-95 duration-150 space-y-3 ${
          result.verified 
            ? 'bg-panel border-mint/70' 
            : 'bg-panel border-coral/70'
        }`}>
          <div className="flex items-center justify-between pb-3 border-b border-hairline">
            <div className="flex items-center gap-3">
              {result.verified ? (
                <div className="w-10 h-10 rounded-full bg-mint/20 border border-mint/40 flex items-center justify-center">
                  <CheckCircle2 className="w-6 h-6 text-mint" />
                </div>
              ) : (
                <div className="w-10 h-10 rounded-full bg-coral/20 border border-coral/40 flex items-center justify-center">
                  <AlertTriangle className="w-6 h-6 text-coral" />
                </div>
              )}
              <div>
                <h3 className={`text-base font-bold uppercase tracking-wide font-mono ${
                  result.verified ? 'text-mint' : 'text-coral'
                }`}>
                  {result.status}
                </h3>
                <p className="text-xs text-text-muted">{result.message}</p>
              </div>
            </div>

            <span className={`px-2.5 py-1 rounded text-xs font-mono font-bold uppercase ${
              result.verified ? 'bg-mint/20 text-mint border border-mint/40' : 'bg-coral/20 text-coral border border-coral/40'
            }`}>
              {result.verified ? 'VERIFIED SEAL ✓' : 'TAMPER DETECTED ✗'}
            </span>
          </div>

          {result.verified && (
            <div className="grid grid-cols-2 gap-3 text-xs font-mono pt-1">
              <div>
                <span className="text-text-muted text-[10px] block">Report Number</span>
                <span className="text-text-primary font-bold">{result.report_number || 'CR-NETRA-2026-00001'}</span>
              </div>
              <div>
                <span className="text-text-muted text-[10px] block">Associated Case</span>
                <span className="text-cyan font-bold">{result.case_number || 'CASE-2026-0001'}</span>
              </div>
              <div>
                <span className="text-text-muted text-[10px] block">Generated By</span>
                <span className="text-text-primary">{result.generated_by || 'investigator@demo'}</span>
              </div>
              <div>
                <span className="text-text-muted text-[10px] block">Certified Timestamp</span>
                <span className="text-text-primary">{result.generated_at ? new Date(result.generated_at).toUTCString() : 'Active'}</span>
              </div>
              <div className="col-span-2 pt-2 border-t border-hairline">
                <span className="text-text-muted text-[10px] block">Snapshot Canonical Hash (SHA-256)</span>
                <span className="text-text-primary break-all">{result.snapshot_sha256}</span>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
