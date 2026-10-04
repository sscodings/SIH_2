# Decisions (DRAFT defaults. Owner must confirm or edit each)

1. Bare EVM address: trace all in-scope chains automatically, ranked by activity.
2. Auto-create case above priority threshold: TODO (owner to set; suggest "high").
3. EVM chains/tokens in scope: Ethereum, Polygon, Arbitrum (+ BSC only if free key covers it, else via Blockscout); tokens USDT, USDC.
4. Alert channels: WebSocket + webhook (email optional). Severity map:
   sanctioned hit=critical, mixer=high, move to registered/unregistered VASP=high,
   new inflow=medium, new linked complaint=medium.
5. Unmasked victim PII visible to supervisor and admin only.
6. Demo infra: docker compose (Postgres + Redis) on a laptop.
7. Queue: arq (async, fits FastAPI). Read arq cron + Redis-lock pattern before implementing.
8. Integration contract: NCRP/CFCFRMS has no public third-party API found. Adapter is mocked;
   real spec pending. SAHYOG is an IT-Act s.79(3)(b) takedown-notice portal, not a complaint feed.

## Data provenance
- fiu_vasp_list.csv: Lok Sabha Unstarred Q.966, 2 Dec 2024, Annexure-A (47 VDA SPs). SNAPSHOT, out of date (~50 by Oct 2025). Nodal officer contacts not published; left empty.
- ofac_sample.*: from SDN_ADVANCED.XML (OFAC Sanctions List Service), list updated 2026-09-29.
- exchange_addresses.csv: Binance (Binance blog, snapshot 2022-11-10) and Bybit (Bybit help center) addresses copied verbatim from official pages. STALE snapshots; verified_date blank until checked on explorer. Missing: OKX, KuCoin, WazirX, CoinDCX. Do not invent.
- sample_complaint.csv: header only; awaiting one anonymized row from mentor.
