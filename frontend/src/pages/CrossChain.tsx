import React, { useState } from 'react';
import { GitBranch, ArrowRight, Shield, Sparkles, ExternalLink, Filter } from 'lucide-react';
import { useAppStore } from '../stores/useAppStore';

export const CrossChain: React.FC = () => {
  const explainMode = useAppStore((s) => s.explainMode);

  // Cross-chain bridge matched events dataset
  const [crossChainEvents] = useState([
    {
      id: 1,
      source_chain: 'Tron',
      source_tx: 'c2_peel_large_to_bridge',
      destination_chain: 'BSC',
      destination_tx: 'c2_bsc_bridge_release_tx99',
      bridge_name: 'SwiftBridge',
      source_token: 'USDT',
      destination_token: 'USDT',
      deposit_amount: 45000.0,
      released_amount: 44950.0,
      time_delta_seconds: 300,
      confidence: 96.5,
      case_id: 'CASE-2026-0002',
      case_title: 'Task-Based Part-Time Job Fraud'
    },
    {
      id: 2,
      source_chain: 'Ethereum',
      source_tx: 'c4_eth_swaplab_router_deposit',
      destination_chain: 'Arbitrum',
      destination_tx: 'c4_arbitrum_bridge_release_tx',
      bridge_name: 'Arbitrum One Gateway',
      source_token: 'ETH',
      destination_token: 'ETH',
      deposit_amount: 35.0,
      released_amount: 35.0,
      time_delta_seconds: 7200,
      confidence: 94.2,
      case_id: 'CASE-2026-0004',
      case_title: 'Hospital Ransomware Attack'
    },
    {
      id: 3,
      source_chain: 'Tron',
      source_tx: 'tx_bridge_tron_poly_098',
      destination_chain: 'Polygon',
      destination_tx: 'tx_poly_release_mule_881',
      bridge_name: 'Polygon PoS Bridge',
      source_token: 'USDT',
      destination_token: 'USDT',
      deposit_amount: 22000.0,
      released_amount: 21980.0,
      time_delta_seconds: 640,
      confidence: 98.1,
      case_id: 'CASE-2025-0018',
      case_title: 'Pig-Butchering Dating Scam'
    }
  ]);

  return (
    <div className="space-y-4 animate-in fade-in duration-200">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-2 border-b border-hairline">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-text-primary flex items-center gap-2">
            Cross-Chain Analytics & Bridge Matching
            <span className="text-xs px-2 py-0.5 rounded font-mono font-bold bg-violet/15 border border-violet/30 text-violet">
              MULTI-LEDGER RECONCILIATION
            </span>
          </h1>
          <p className="text-xs text-text-muted mt-0.5">
            Automated correlation of lock/mint and burn/release bridge transactions across heterogeneous chains.
          </p>
        </div>
      </div>

      {explainMode && (
        <div className="p-3 bg-violet/10 border border-violet/30 rounded-lg text-xs text-violet flex items-start gap-2.5">
          <Sparkles className="w-4 h-4 shrink-0 mt-0.5" />
          <div>
            <span className="font-bold">Cross-Chain Heuristic Explained:</span> Criminals frequently bridge USDT from Tron to BSC or Ethereum to evade single-ledger tracking.
            ChainNetra matches outbound bridge deposits to incoming destination releases using a multi-factor scoring function:
            amount equivalence (within gas fee tolerance), timestamp proximity, and bridge contract identity.
          </div>
        </div>
      )}

      {/* Visual Flow Overview (Chain-to-Chain Matrix) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div className="p-4 rounded-xl bg-panel border border-hairline space-y-2">
          <div className="text-[11px] font-mono text-text-muted uppercase">Primary Origin Chain</div>
          <div className="text-2xl font-bold font-mono text-red-400">TRON (TRC-20)</div>
          <div className="text-xs text-text-muted">68% of all fraud inflows originate here</div>
        </div>
        <div className="p-4 rounded-xl bg-panel border border-hairline space-y-2 flex flex-col justify-center items-center text-center">
          <GitBranch className="w-6 h-6 text-violet animate-pulse" />
          <div className="text-xs font-bold text-violet font-mono uppercase">Decentralized Bridges</div>
          <div className="text-[10px] text-text-muted">SwiftBridge • Arbitrum Gateway • Polygon PoS</div>
        </div>
        <div className="p-4 rounded-xl bg-panel border border-hairline space-y-2">
          <div className="text-[11px] font-mono text-text-muted uppercase">Target Cash-out Chains</div>
          <div className="text-2xl font-bold font-mono text-yellow-400">BSC & ARBITRUM</div>
          <div className="text-xs text-text-muted">Low fee off-ramps for offshore VASPs</div>
        </div>
      </div>

      {/* Matched Cross-Chain Events Table */}
      <div className="bg-panel border border-hairline rounded-xl overflow-hidden shadow">
        <div className="p-3 border-b border-hairline flex items-center justify-between">
          <h3 className="text-xs font-bold text-text-primary tracking-wide">
            Matched Cross-Chain Bridge & Swap Dispatches
          </h3>
          <span className="text-[10px] font-mono text-text-muted">
            Algorithm Confidence: Amount Match (50%) + Time Window (30%) + Uniqueness (20%)
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-raised/70 border-b border-hairline text-[10px] text-text-muted uppercase">
              <tr>
                <th className="p-3">Case Association</th>
                <th className="p-3">Source Deposit</th>
                <th className="p-3 text-center">Bridge Corridor</th>
                <th className="p-3">Destination Release</th>
                <th className="p-3 text-right">Volume</th>
                <th className="p-3 text-center">Time Delta</th>
                <th className="p-3 text-right">Confidence Score</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-hairline">
              {crossChainEvents.map((evt) => (
                <tr key={evt.id} className="hover:bg-raised/40 transition-colors">
                  <td className="p-3">
                    <div className="font-bold text-text-primary">{evt.case_id}</div>
                    <div className="text-[10px] text-text-muted font-sans truncate max-w-[140px]">{evt.case_title}</div>
                  </td>

                  <td className="p-3">
                    <div className="font-bold text-red-400">{evt.source_chain}</div>
                    <div className="text-[10px] text-cyan truncate max-w-[120px]">{evt.source_tx}</div>
                  </td>

                  <td className="p-3 text-center">
                    <span className="px-2 py-0.5 rounded bg-violet/15 text-violet border border-violet/30 font-bold text-[10px] inline-flex items-center gap-1">
                      {evt.bridge_name} <ArrowRight className="w-3 h-3" />
                    </span>
                  </td>

                  <td className="p-3">
                    <div className="font-bold text-yellow-400">{evt.destination_chain}</div>
                    <div className="text-[10px] text-cyan truncate max-w-[120px]">{evt.destination_tx}</div>
                  </td>

                  <td className="p-3 text-right font-bold text-amber">
                    ${Number(evt.deposit_amount).toLocaleString()} {evt.source_token}
                  </td>

                  <td className="p-3 text-center text-text-muted">
                    {Math.round(evt.time_delta_seconds / 60)} mins
                  </td>

                  <td className="p-3 text-right">
                    <span className="px-2 py-0.5 rounded bg-mint/15 text-mint border border-mint/30 font-bold text-[11px]">
                      {evt.confidence}%
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
