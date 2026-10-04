import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { useAppStore } from '../stores/useAppStore';

export const CrossChain: React.FC = () => {
  const navigate = useNavigate();
  const explainMode = useAppStore((s) => s.explainMode);

  // Cross-chain bridge matched events dataset
  const [crossChainEvents] = useState([
    {
      id: 1,
      source_chain: 'Tron (TRC-20)',
      source_tx: 'TJ8wK9...c2_peel_large_to_bridge',
      destination_chain: 'Ethereum Mainnet',
      destination_tx: '0x81C7b...eth_swaplab_release',
      bridge_name: 'Stargate Router V2',
      source_token: 'USDT',
      destination_token: 'USDT',
      deposit_amount: 11000.0,
      released_amount: 10982.0,
      time_delta_seconds: 180,
      confidence: 98.4,
      case_id: 'CN-2024-0944',
      case_title: 'Pune Telegram Task Fraud'
    },
    {
      id: 2,
      source_chain: 'Ethereum',
      source_tx: '0x4bE12...eth_swaplab_router',
      destination_chain: 'Arbitrum One',
      destination_tx: '0x33Ae...arbitrum_bridge_release',
      bridge_name: 'Arbitrum One Gateway',
      source_token: 'ETH',
      destination_token: 'ETH',
      deposit_amount: 35.0,
      released_amount: 35.0,
      time_delta_seconds: 7200,
      confidence: 94.2,
      case_id: 'CN-2024-0941',
      case_title: 'Bengaluru Digital Arrest Scam'
    },
    {
      id: 3,
      source_chain: 'Tron',
      source_tx: 'TL1b4P...bridge_tron_poly',
      destination_chain: 'Polygon PoS',
      destination_tx: '0x7a3e...poly_release_mule',
      bridge_name: 'Polygon PoS Bridge',
      source_token: 'USDT',
      destination_token: 'USDT',
      deposit_amount: 22000.0,
      released_amount: 21980.0,
      time_delta_seconds: 640,
      confidence: 98.1,
      case_id: 'CN-2024-0938',
      case_title: 'Mumbai Stock Investment Scheme'
    }
  ]);

  return (
    <div className="flex flex-col w-full gap-6 animate-in fade-in duration-150">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-surface-container">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-primary-fixed text-on-primary-fixed uppercase tracking-wider">
              Cross-Ledger Forensics
            </span>
            <span className="text-outline text-xs">•</span>
            <span className="text-[11px] font-mono text-outline">MULTI-CHAIN ROUTER CORRELATION</span>
          </div>
          <h1 className="font-headline-lg text-2xl font-bold text-on-surface tracking-tight">
            Cross-Chain Analytics &amp; Bridge Matching
          </h1>
          <p className="font-body-md text-xs text-on-surface-variant mt-0.5">
            Automated correlation of lock/mint and burn/release bridge transactions across heterogeneous chains.
          </p>
        </div>

        <button
          onClick={() => navigate('/cases/1')}
          className="px-4 py-2 bg-primary-container text-on-primary text-xs font-semibold rounded-lg hover:bg-primary transition-all flex items-center gap-1.5 self-start md:self-auto shadow-xs"
        >
          <span className="material-symbols-outlined text-[16px]">account_tree</span>
          <span>View Interactive Hop Graph</span>
        </button>
      </div>

      {explainMode && (
        <div className="p-4 bg-surface-container-lowest border-l-4 border-primary rounded-xl shadow-sm text-xs space-y-1">
          <div className="flex items-center gap-2 font-bold text-primary">
            <span className="material-symbols-outlined text-[18px]">info</span>
            <span>Cross-Chain Heuristic Explained</span>
          </div>
          <p className="text-on-surface-variant leading-relaxed">
            Perpetrators frequently convert Tron TRC-20 USDT into EVM native tokens or transfer assets via cross-chain bridges (such as Stargate, Multichain, or Arbitrum One) to evade single-ledger tracking.
            ChainNetra deterministically links these hops by matching outbound bridge deposits to incoming destination releases using timestamp proximity, amount equivalence (with gas haircut compensation), and registered bridge pool contracts.
          </p>
        </div>
      )}

      {/* Visual Flow Overview (3 Cards) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="p-6 rounded-xl bg-surface-container-lowest border border-surface-container shadow-sm space-y-2">
          <div className="text-[11px] font-mono text-outline uppercase font-semibold">Primary Origin Chain</div>
          <div className="text-2xl font-bold font-mono text-error">TRON (TRC-20)</div>
          <div className="text-xs text-on-surface-variant">68% of all fraud inflows originate here</div>
        </div>

        <div className="p-6 rounded-xl bg-surface-container-lowest border border-surface-container shadow-sm space-y-2 flex flex-col justify-center items-center text-center">
          <span className="material-symbols-outlined text-3xl text-primary animate-pulse">hub</span>
          <div className="text-xs font-bold text-primary uppercase tracking-wide">Decentralized Bridge Routers</div>
          <div className="text-[11px] text-outline font-mono">Stargate Router • Arbitrum Gateway • Polygon PoS</div>
        </div>

        <div className="p-6 rounded-xl bg-surface-container-lowest border border-surface-container shadow-sm space-y-2">
          <div className="text-[11px] font-mono text-outline uppercase font-semibold">Destination Settlement</div>
          <div className="text-2xl font-bold font-mono text-secondary">Binance / DemoX</div>
          <div className="text-xs text-on-surface-variant">88% terminate at custodial exchange deposit addresses</div>
        </div>
      </div>

      {/* Bridge Events Table */}
      <div className="bg-surface-container-lowest rounded-xl shadow-sm p-6 border border-surface-container space-y-4">
        <div className="flex items-center justify-between pb-2 border-b border-surface-container">
          <h2 className="text-sm font-bold text-on-surface">Reconciled Bridge Hops &amp; Cashout Links</h2>
          <span className="text-[11px] font-mono text-secondary font-semibold">
            {crossChainEvents.length} Active Cross-Chain Traversal Paths
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-surface-container-low text-on-surface-variant font-label-sm text-[11px] uppercase tracking-wider">
                <th className="py-2.5 px-3 rounded-l-lg">Case Reference</th>
                <th className="py-2.5 px-3">Bridge Protocol</th>
                <th className="py-2.5 px-3">Source &rarr; Target</th>
                <th className="py-2.5 px-3">Amount Reconciled</th>
                <th className="py-2.5 px-3">Correlation Confidence</th>
                <th className="py-2.5 px-3 text-right rounded-r-lg">Forensic Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-container">
              {crossChainEvents.map((evt) => (
                <tr key={evt.id} className="h-16 hover:bg-surface-container-low/40 transition-colors">
                  <td className="px-3 font-medium">
                    <span className="font-mono text-primary font-semibold">#{evt.case_id}</span>
                    <div className="text-outline text-[11px]">{evt.case_title}</div>
                  </td>

                  <td className="px-3">
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-surface-container font-mono text-[11px] font-semibold text-on-surface">
                      <span className="material-symbols-outlined text-[13px] text-primary">swap_calls</span>
                      {evt.bridge_name}
                    </span>
                  </td>

                  <td className="px-3">
                    <div className="flex items-center gap-1 font-semibold text-on-surface">
                      <span>{evt.source_chain}</span>
                      <span className="text-outline">&rarr;</span>
                      <span className="text-secondary">{evt.destination_chain}</span>
                    </div>
                  </td>

                  <td className="px-3 font-mono font-semibold text-on-surface">
                    ${evt.deposit_amount.toLocaleString()} {evt.source_token}
                  </td>

                  <td className="px-3">
                    <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-secondary-container/40 text-secondary font-semibold text-[11px]">
                      <span className="material-symbols-outlined text-[12px]">verified</span>
                      {evt.confidence}% Deterministic
                    </span>
                  </td>

                  <td className="px-3 text-right">
                    <button
                      onClick={() => navigate('/cases/1')}
                      className="inline-flex items-center gap-1 text-primary hover:text-primary-container font-semibold transition-colors"
                    >
                      <span>Inspect Graph</span>
                      <span className="material-symbols-outlined text-[15px]">arrow_forward</span>
                    </button>
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
