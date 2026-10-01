import React, { useState, useEffect } from 'react';
import { 
  Webhook, Key, Terminal, Activity, CheckCircle2, 
  ExternalLink, Copy, Play, PlusCircle, Sparkles, Send 
} from 'lucide-react';
import toast from 'react-hot-toast';
import { api } from '../lib/api';
import { getApiBaseUrl } from '../lib/config';
import { useAppStore } from '../stores/useAppStore';

export const Integrations: React.FC = () => {
  const explainMode = useAppStore((s) => s.explainMode);
  const mode = useAppStore((s) => s.mode);

  const [webhooks, setWebhooks] = useState<any[]>([]);
  const [providers, setProviders] = useState<any[]>([]);
  const [newHookUrl, setNewHookUrl] = useState('');
  const [newHookName, setNewHookName] = useState('');

  const loadData = async () => {
    try {
      const [whRes, pRes] = await Promise.all([
        api.getWebhooks(),
        api.getProvidersStatus()
      ]);
      setWebhooks(whRes.webhooks || []);
      setProviders(pRes.providers || []);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleTestWebhook = async (id: number) => {
    try {
      await api.testWebhook(id);
      toast.success('Dispatched test HMAC-SHA256 payload to webhook endpoint!');
      loadData();
    } catch (e) {
      toast.error('Test dispatch failed');
    }
  };

  const handleCreateWebhook = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newHookUrl.trim()) return;
    try {
      await api.createWebhook({
        name: newHookName || 'External SIEM Endpoint',
        target_url: newHookUrl.trim()
      });
      toast.success('Webhook registered successfully!');
      setNewHookUrl('');
      setNewHookName('');
      loadData();
    } catch (e) {
      toast.error('Failed to create webhook');
    }
  };

  const curlExample = `curl -X POST "${window.location.origin}${getApiBaseUrl()}/ingest/ncrp" \\
  -H "Content-Type: application/json" \\
  -d '{
    "victim_name": "Suresh Gupta",
    "victim_state": "Uttar Pradesh",
    "fraud_type": "Investment Scam",
    "reported_wallets": ["TXYZCollectorAlpha777111111111111"],
    "amount_lost_inr": 1100000
  }'`;

  return (
    <div className="space-y-4 animate-in fade-in duration-200">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-2 border-b border-hairline">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-text-primary flex items-center gap-2">
            API Integrations & Webhook Dispatchers
            <span className="text-xs px-2 py-0.5 rounded font-mono font-bold bg-cyan/15 border border-cyan/30 text-cyan">
              ENTERPRISE INTEROPERABILITY
            </span>
          </h1>
          <p className="text-xs text-text-muted mt-0.5">
            Connect ChainNetra to police SIEM systems, state cyber cell command rooms, and automated notification channels.
          </p>
        </div>

        <a
          href="/docs"
          target="_blank"
          rel="noreferrer"
          className="px-3.5 py-2 rounded-lg bg-raised hover:bg-hairline border border-hairline text-xs font-semibold text-text-primary transition-colors flex items-center gap-1.5"
        >
          <ExternalLink className="w-3.5 h-3.5 text-cyan" />
          Interactive OpenAPI Docs (/docs)
        </a>
      </div>

      {explainMode && (
        <div className="p-3 bg-cyan/10 border border-cyan/30 rounded-lg text-xs text-cyan flex items-start gap-2.5">
          <Sparkles className="w-4 h-4 shrink-0 mt-0.5" />
          <div>
            <span className="font-bold">Interoperability Standards:</span> ChainNetra was designed to be headless and API-first.
            Every forensic trace, VASP discovery, and freeze recommendation produces structured JSON payloads signed with HMAC-SHA256 headers for direct ingestion into Law Enforcement C4I systems.
          </div>
        </div>
      )}

      {/* Blockchain Provider Connectors Health Cards */}
      <div className="space-y-2">
        <h3 className="text-xs font-bold text-text-primary uppercase tracking-wide font-mono">
          Underlying Blockchain Provider Health
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-3">
          {providers.map((p, idx) => (
            <div key={idx} className="p-3 rounded-xl bg-panel border border-hairline flex flex-col justify-between">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-bold font-mono text-text-primary">{p.chain}</span>
                <span className="w-2 h-2 rounded-full bg-mint animate-pulse" />
              </div>
              <div className="text-[11px] text-text-muted">{p.api}</div>
              <div className="mt-2 pt-1 border-t border-hairline flex justify-between items-center text-[10px] font-mono text-text-muted">
                <span>{p.has_key ? 'KEY SET' : 'DEMO/PUB'}</span>
                <span className="text-mint">{p.latency_ms}ms</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Grid: Webhooks Management & Live cURL Snippet */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Left (7 Cols): Webhook Dispatcher */}
        <div className="lg:col-span-7 bg-panel border border-hairline rounded-xl p-4 space-y-4 shadow">
          <div className="flex items-center justify-between pb-2 border-b border-hairline">
            <h3 className="text-xs font-bold text-text-primary tracking-wide flex items-center gap-2">
              <Webhook className="w-4 h-4 text-cyan" />
              Registered SIEM & Police Webhooks ({webhooks.length})
            </h3>
            <span className="text-[10px] font-mono text-text-muted">HMAC-SHA256 Signed</span>
          </div>

          {/* Webhook Register Form */}
          <form onSubmit={handleCreateWebhook} className="space-y-2 text-xs">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              <input
                type="text"
                placeholder="Receiver Name (e.g. State Cyber Cell SIEM)"
                value={newHookName}
                onChange={(e) => setNewHookName(e.target.value)}
                className="bg-ink border border-hairline rounded-lg px-3 py-1.5 text-text-primary focus:border-amber focus:outline-none"
              />
              <input
                type="url"
                required
                placeholder="https://your-endpoint.gov/webhook"
                value={newHookUrl}
                onChange={(e) => setNewHookUrl(e.target.value)}
                className="bg-ink border border-hairline rounded-lg px-3 py-1.5 font-mono text-text-primary focus:border-amber focus:outline-none"
              />
            </div>
            <button
              type="submit"
              className="px-3.5 py-1.5 rounded-lg bg-cyan text-ink font-bold text-xs hover:bg-cyan-400 transition-colors"
            >
              Register Webhook
            </button>
          </form>

          {/* Webhooks List */}
          <div className="space-y-2 pt-2">
            {webhooks.map((wh) => (
              <div key={wh.id} className="p-3 rounded-lg bg-raised/70 border border-hairline space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-text-primary text-xs">{wh.name}</span>
                  <button
                    onClick={() => handleTestWebhook(wh.id)}
                    className="px-2 py-0.5 rounded bg-raised hover:bg-hairline border border-hairline text-[10px] text-cyan font-semibold flex items-center gap-1"
                  >
                    <Send className="w-3 h-3" /> Test Dispatch
                  </button>
                </div>
                <div className="font-mono text-[11px] text-cyan truncate">{wh.target_url}</div>
                <div className="text-[10px] text-text-muted font-mono">
                  Events: {wh.events?.join(', ')}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right (5 Cols): Working cURL Snippet */}
        <div className="lg:col-span-5 bg-panel border border-hairline rounded-xl p-4 flex flex-col justify-between shadow">
          <div>
            <div className="flex items-center justify-between pb-2 border-b border-hairline mb-3">
              <h3 className="text-xs font-bold text-text-primary tracking-wide flex items-center gap-2">
                <Terminal className="w-4 h-4 text-amber" />
                Working API Ingestion cURL
              </h3>
              <button
                onClick={() => { navigator.clipboard.writeText(curlExample); toast.success('cURL snippet copied!'); }}
                className="text-text-muted hover:text-text-primary text-xs"
                title="Copy snippet"
              >
                <Copy className="w-3.5 h-3.5" />
              </button>
            </div>

            <pre className="p-3 rounded-lg bg-ink border border-hairline font-mono text-[11px] text-text-primary/90 overflow-x-auto leading-relaxed">
              {curlExample}
            </pre>
          </div>

          <div className="mt-3 p-2.5 rounded bg-raised border border-hairline text-xs text-text-muted font-mono">
            Execute this directly in any terminal to push live complaint records into ChainNetra.
          </div>
        </div>
      </div>
    </div>
  );
};
