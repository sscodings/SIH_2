# ChainNetra Tracing & Attribution Correctness Changes

This document details the forensic tracing, attribution, taint propagation, and clustering enhancements implemented across the **ChainNetra** backend.

---

## 1. Section-by-Section Changes

### Section 1: Address Normalization and `(chain, address)` Composite Keys
- **Implementation**: Created [`app/core/addresses.py`](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/backend/app/core/addresses.py) providing:
  - `display_address(chain, address)`: EVM addresses converted to EIP-55 checksum casing; Tron (Base58) and Bitcoin addresses preserved exactly.
  - `normalize(chain, address)`: EVM addresses converted to lowercase for database indexing; Tron and Bitcoin preserved exactly.
  - `node_key(chain, address)`: Returns composite string format `"{chain}:{normalized_address}"`.
- **Tracer Refactor**: Graph nodes, visited sets, edge sources/targets, and priority queue items in `tracer.py` are keyed by `node_key`. Display addresses are preserved in node metadata for UI rendering.
- **Multi-Root EVM Expansion**: When a generic EVM address or `chain="evm"` is submitted, roots are expanded across all configured EVM chains (`ethereum`, `bsc`, `polygon`, `arbitrum`).
- **Database Uniformity**: Replaced `.ilike()` with indexed exact-match lookups against `normalize(chain, address)`.

### Section 2: Stateful Per-Wallet Taint Models
- **Implementation**: Refactored `TaintModel` in [`app/engines/taint.py`](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/backend/app/engines/taint.py) with `WalletTaintLedger`.
  - **Haircut**: Proportional allocation:
    $$\text{taint\_out} = \text{out\_amount} \times \frac{\text{tainted\_in}}{\text{total\_in}}$$
    Where $\text{total\_in}$ is the wallet's actual total inflow in the temporal window.
  - **FIFO**: Chronological queue of inflow lots with tainted fractions. Outflows consume oldest lots first, propagating tainted shares and updating remaining balances.
  - **Poison**: Full contamination up to the outflow amount, strictly capped by the wallet's total tainted inflow:
    $$\text{taint\_out} = \min(\text{out\_amount}, \text{total\_tainted\_inflow})$$
- **Invariants Enforced**:
  - Propagated taint per wallet never exceeds tainted inflows for Haircut and FIFO (`tainted_out <= tainted_in`).
  - Poison model marks edge results with `overestimates=True` and documents potential value inflation.
  - Active taint model name (`haircut`, `fifo`, `poison`) is recorded on every edge.

### Section 3: Temporal Soundness and `time_window_hours`
- **Implementation**: Extended adapter protocol [`app/adapters/base.py`](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/backend/app/adapters/base.py) with both `since` and `until` datetime parameters.
- **Window Enforcement**: Outflows are only followed if they occurred after tainted arrival ($\ge \text{arrival\_time}$) and within `time_window_hours` ($\le \text{arrival\_time} + \Delta t$). Setting `time_window_hours=0` enables unlimited time bounds.
- **Arrival Propagation**: When multiple tainted inflows reach a wallet, the earliest arrival timestamp is used as the temporal anchor.

### Section 4: Generalized Peel-Chain Detection
- **Implementation**: Generalized peel-chain detection in [`app/engines/tracer.py`](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/backend/app/engines/tracer.py).
  - A hop qualifies as a peel step if one dominant output carries $\ge 80\%$ (configurable `peel_ratio`) of the tainted value to a fresh recipient, accompanied by one or more small outputs. Supports any arbitrary number of outputs $n$.
  - Minimum chain length requirement: requires $\ge 3$ consecutive peel hops to flag as a peel chain (single or double hops are ignored).
  - Bitcoin change identification is explicitly recorded as a heuristic with confidence scores.

### Section 5: Dynamic Confidence Scoring from Real Evidence
- **Implementation**: Redesigned `AttributionEngine.calculate_confidence` in [`app/engines/attribution.py`](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/backend/app/engines/attribution.py).
  - `label_source_weight`: Base source weight decayed by age:
    $$W_{label} = W_{base} \times (0.95)^{\text{years\_elapsed}}$$
  - `evidence_strength`: Computed from concrete evidence type:
    - `0.95`: Direct verified registry match (`registry_match`)
    - `0.75`: Validated multi-sweep deposit pattern (`multi_sweep_deposit`)
    - `0.60`: Fresh-wallet gas-funding cluster (`gas_funding`)
    - `0.55`: Bitcoin common-input cluster (`btc_common_input`)
    - `0.35`: Single transfer or generic cluster (`single_observation` / `generic_cluster`)
  - `cluster_support`: Computed as $(\text{matching entity members}) / (\text{cluster size})$, strictly defaulting to $0.0$ if unclustered (no hardcoded $0.95$).
  - `confidence_level`: Tiered into `VERIFIED` (registry-backed, $E \ge 0.95, W \ge 0.90$), `HIGH` ($\ge 65.0$), `MEDIUM` ($\ge 45.0$), and `LOW` ($< 45.0$).
  - Detailed metadata returned in `confidence_details` along with structured `evidence` list (transaction hashes, timestamps, counts).

### Section 6: Correct Multi-Sweep Deposit Heuristic
- **Implementation**: Replaced single-transfer VASP hot wallet association with a 4-point sweep heuristic:
  1. $\ge 3$ distinct unrelated senders (default `min_senders=3`).
  2. Forwards $\ge 90\%$ (default `sweep_ratio=0.90`) of received funds to a known VASP hot wallet.
  3. Sweeps occur consistently $\ge 2$ times (default `min_sweeps=2`) within $72$ hours of deposit.
  4. Minimal or no non-sweep outbound destinations.
- **Lower Tier Handling**: Wallets with a single transfer to a hot wallet receive the lower-confidence label `"Direct sender to VASP hot wallet"` (`confidence_level="MEDIUM"` / `"LOW"`) and are classified as customer/intermediary wallets rather than exchange infrastructure.

### Section 7: Meaningful Clustering & Service Exclusion
- **Implementation**: Updated clustering in [`app/engines/clustering.py`](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/backend/app/engines/clustering.py).
  - **Service Target Exclusion**: Transfers to known exchange hot wallets, bridges, or mixers are excluded from sweep-target clustering to avoid grouping unrelated exchange depositors.
  - **24-Hour Bounded Sweeps**: Groups senders forwarding to identical non-service targets within 24 hours using indexed SQL aggregations.
  - **Bitcoin Common-Input Ownership**: Clusters inputs spent together in the same transaction, explicitly filtering out CoinJoin-like transactions ($>3$ inputs and $\ge 3$ identical-value outputs).
  - **Gas Funding Dispersal**: Clusters fresh wallets funded by the same parent wallet within a 2-hour window.
  - **Auditability**: `ClusterMember` records `rule_formed`, `confidence`, and `evidence_tx_hashes`.

### Section 8: Curated Service Registry & Protocol Handling
- **Implementation**: Created [`app/core/service_registry.py`](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/backend/app/core/service_registry.py) with verified entries for mixers, cross-chain bridges, DEX routers, and VASPs. Removed naive `"mix"` / `"bridge"` string matching.
- **Cross-Chain Bridge Engine**: [`app/engines/crosschain.py`](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/backend/app/engines/crosschain.py) only triggers on registered bridge contracts, performs token-aware amount matching within fee tolerance ($5\%$), and flags competing candidates as `ambiguous=True` if scores fall within $5.0$ points.
- **DEX Swaps**: Traces token swaps through registered routers, recording swapped asset names, amounts, and USD values directly on edges.
- **Mixer Traversal**: Halts deterministic tracing upon entering registered mixers. Candidate withdrawals are enqueued as separate branches marked `probabilistic=True` with confidence capped at $40\%$ and decayed per hop.

### Section 9: Elimination of Hardcoded Amounts & Honest Timing
- **Clean Fallbacks**: Removed hardcoded `134500.0` and `11200000.0` amounts from case graph and freeze endpoints. Values are computed dynamically from linked complaints or rejected if unavailable.
- **Demo Delay Separation**: Removed unconditional `asyncio.sleep(0.04)`. Configurable `DEMO_STREAM_DELAY_MS` (default 0) is excluded from reported wall-clock calculations.
- **Honest Metrics**: `time_to_vasp_seconds` reports genuine execution time to first VASP hit, or `None` if no VASP is encountered. `adapter_call_count` and `adapter_time_seconds` are tracked.
- **Funds Accounting**: Reports `over_attributed_usd` if attributed sums exceed initial root funds.

### Section 10: Performance, Threading & Database Indexing
- **Composite Indexes**: Added composite indexes across all core tables in `app/db/models.py`:
  - `idx_transfers_chain_from_ts` (`chain`, `from_address`, `timestamp`)
  - `idx_transfers_chain_to_ts` (`chain`, `to_address`, `timestamp`)
  - `idx_labels_chain_address` (`chain`, `address`)
  - `idx_entity_addresses_chain_addr` (`chain`, `address`)
  - `idx_cluster_members_chain_addr` (`chain`, `address`)
- **Async & Threading Correctness**: Trace runs instantiate independent database sessions and execute sync database operations safely.
- **Trace Budgets**: Enforces limits on adapter calls (`max_adapter_calls=1000`) and execution time (`max_wall_time_sec=60.0`). When exceeded, returns partial traces with `truncated=True` and clear reason.

---

## 2. Configurable Thresholds & Defaults

| Parameter | Default Value | Description |
| :--- | :--- | :--- |
| `peel_ratio` | `0.80` (80%) | Minimum share of tainted outflow going to main output in peel-chain hop |
| `peel_min_hops` | `3` | Minimum consecutive peel hops required to flag a peel chain |
| `time_window_hours` | `72.0` | Maximum temporal lookahead window from fund arrival ($0 = \text{unlimited}$) |
| `sweep_min_senders` | `3` | Minimum distinct senders to qualify as a deposit address |
| `sweep_ratio` | `0.90` (90%) | Minimum balance swept to VASP hot wallet |
| `sweep_min_sweeps` | `2` | Minimum number of observed sweep events |
| `sweep_max_delay_hours` | `72.0` | Maximum delay between deposit and sweep |
| `bridge_fee_tolerance` | `0.05` (5%) | Allowed deviation for bridge fee deductions |
| `bridge_ambiguity_delta` | `5.0` | Score difference below which candidates are marked ambiguous |
| `mixer_max_confidence` | `0.40` (40%) | Maximum confidence ceiling for probabilistic mixer withdrawal candidates |
| `max_adapter_calls` | `1000` | Maximum blockchain adapter lookups per trace run |
| `max_wall_time_sec` | `60.0` | Hard timeout ceiling before trace truncation |
| `demo_stream_delay_ms` | `0` | Millisecond delay for animated UI demo streaming |

---

## 3. Documented False-Positive Risks

1. **Multi-Sweep Deposit Address Heuristic**:
   - *Risk*: High-volume commercial payment processors, e-commerce checkout gateways, or non-custodial aggregators may sweep funds into consolidated cold/hot wallets, resembling exchange deposit infrastructure.
   - *Mitigation*: Look for known VASP entity tags on the receiving hot wallet; single-transfer senders are tagged as intermediary senders rather than deposit infrastructure.

2. **Bitcoin Common-Input Ownership Heuristic**:
   - *Risk*: Non-custodial collaborative transactions (CoinJoin, PayJoin/BIP78, batch payout transactions) spend UTXOs belonging to distinct unrelated entities in one transaction.
   - *Mitigation*: Transactions with $>3$ inputs and $\ge 3$ identical-value outputs are detected as CoinJoin mixing and excluded from clustering.

3. **Fresh-Wallet Gas-Funding Heuristic**:
   - *Risk*: Centralized exchange withdrawal services or automated public faucets might fund new user addresses with initial native gas tokens in tight timeframes.
   - *Mitigation*: Exclude known VASP hot wallets and public faucet contracts from being treated as gas-funding syndicates.

4. **Cross-Chain Bridge Candidate Matching**:
   - *Risk*: High-throughput cross-chain bridges processing round amounts (e.g. exactly 1,000 USDT) may have multiple releases on the destination chain within the same temporal window.
   - *Mitigation*: Dynamic candidate uniqueness scoring; if two competing candidates score within $5.0$ points, both are surfaced with `ambiguous=True` rather than picking one arbitrarily.

5. **Mixer Withdrawal Linkage**:
   - *Risk*: Common pool denominations (e.g., 10 ETH, 100 USDT) have large anonymity sets.
   - *Mitigation*: Mixer withdrawal links are marked `probabilistic=True`, capped at $40\%$ confidence, and flagged as non-confirmed paths in forensic reports.

---

## 4. Known Limitations

- **Privacy Coins**: Fully private networks (Monero ring signatures/stealth addresses, Zcash shielded Sapling/Orchard pools) conceal transaction graphs and cannot be deterministically mapped.
- **Unregistered Smart Contracts**: Custom bridges, unverified DEX contracts, and newly deployed privacy mixers not catalogued in [`ServiceRegistry`](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/backend/app/core/service_registry.py) are treated as generic smart contract transfers.
- **Cross-Chain Bridge Inference**: In the absence of signed cryptographic relay attestations, cross-chain deposit-release linkages remain probabilistic heuristics based on timestamp ordering and token equivalence.
- **EVM Internal Contract Calls**: Detecting transfers routed through multi-hop complex contracts requires archive nodes with `trace_transaction` / `debug_traceTransaction` support in live production environments.
