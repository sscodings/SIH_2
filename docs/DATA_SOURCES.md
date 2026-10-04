# ChainNetra Data Sources & Provenance Registry

**Document Version**: 1.0.0  
**Last Verified Date**: 2026-09-30  
**Compliance Standard**: DRAFT DUAL-USE INTELLIGENCE & FORENSIC SPECIFICATION  

---

## 1. Primary Intelligence Sources

### 1.1 OFAC Specially Designated Nationals (SDN) List
- **Source**: U.S. Department of the Treasury, Office of Foreign Assets Control (OFAC)
- **URL**: `https://www.treasury.gov/ofac/downloads/sanctions/1.0/sdn_advanced.xml`
- **License / Terms**: U.S. Public Domain (U.S. Government Work)
- **Update Cadence**: Updated continuously upon executive sanctions designations (snapshot in repo dated 2026-09-29)
- **Ingestion Adapter**: `app.labels.ofac.OfacXmlParser`
- **Scope**: Parses digital currency features (`FeatureTypeID=1432`) extracting cryptocurrency ticker symbols and checksummed wallet addresses.
- **Coverage in Snapshot**: 234 digital currency addresses parsed from sample fragment `docs/research/ofac_sample.xml` (198 Tron Base58Check, 7 legacy Bitcoin Base58Check, 21 EVM EIP-55, 8 miscellaneous).
- **Known Gaps & Limitations**:
  - Live XML file (`SDN_ADVANCED.XML`) is $\approx 127\text{ MB}$; parsing in production requires streamed XML SAX/iterparse parsing to prevent heap exhaustion.
  - OFAC records do not include cluster co-membership or chain re-assignments; addresses are mapped strictly to the stated ticker.

---

### 1.2 FIU-IND Registered Virtual Asset Service Providers (VDA SPs)
- **Source**: Financial Intelligence Unit - India (FIU-IND), Ministry of Finance, Government of India
- **Reference**: Lok Sabha Unstarred Question No. 966, Answered on 2 December 2024, Annexure-A
- **URL**: Parliament of India Lok Sabha repository
- **License / Terms**: Government Open Data / Parliamentary Record
- **Update Cadence**: Periodic official notifications (snapshot dated 2024-12-02)
- **Ingestion Adapter**: `app.labels.fiu.FiuVaspService`
- **Scope**: 47 registered Virtual Digital Asset Service Providers (VDA SPs), including CoinDCX, WazirX, CoinSwitch (Neblio), Mudrex, Unocoin, Binance, and KuCoin.
- **Coverage**: 47 legal entities with registration codes, brand aliases, and incorporation dates.
- **Known Gaps & Limitations**:
  - **Staleness**: This list is a static parliamentary snapshot from December 2024. Over 50 entities were reported registered by late 2025.
  - **No Nodal Officer Contacts**: The official parliamentary annexure does **NOT** publish nodal officer email addresses or telephone numbers. ChainNetra strictly initializes these fields as empty strings (`TODO: Official LEA Nodal Directory Pending`) and **never invents fake contacts**.
  - **No Deposit Addresses**: FIU-IND registration records do not publish on-chain deposit or hot-wallet addresses.

---

### 1.3 Verified Exchange Addresses (Exchange CSV)
- **Source**: Binance Official Blog Proof-of-Reserves Self-Disclosure & Bybit Help Center
- **URLs**:
  - Binance: `https://www.binance.com/en/blog/community/our-commitment-to-transparency-2895840147147652626`
  - Bybit: Official Help Center Reserve Announcement
- **License / Terms**: Corporate Self-Disclosure / Public Transparency Statements
- **Update Cadence**: Ad-hoc corporate disclosures
- **Snapshot Date**: 2022-11-10
- **Ingestion Adapter**: `app.labels.exchange_csv.ExchangeCsvParser`
- **Scope & Coverage**: 30 address records covering Tron, Bitcoin, and Ethereum.
- **Known Gaps & Limitations**:
  - **Extreme Staleness**: The Binance and Bybit snapshots date back to November 2022. Wallet operational roles rotate frequently.
  - **Missing Exchanges**: No official self-disclosure addresses available in this repository for OKX, KuCoin, WazirX, or CoinDCX. ChainNetra leaves these absent rather than fabricating dummy addresses.
  - **Activity Verification**: Only 1 Tron hot-wallet address (`TV6MuMXfmLbBqPZvBHdwFsDnQeVfnmiuSi`) has verified explorer activity. Superseded addresses (e.g. Unocoin BTC `1PSh1go1ZBvULhGV4BsekEaVAAESa2fNWp` valid to `2023-06-23` and Bybit `0x1Db92e...` marked inactive) are preserved with status `superseded` or `inactive`.

---

## 2. Ingestion & Case Origin Datasets

### 2.1 National Cybercrime Reporting Portal (NCRP) / CFCFRMS
- **Source**: Ministry of Home Affairs (I4C / MoHA), Government of India
- **URL**: Internal Law Enforcement Portal (`cybercrime.gov.in`)
- **Status**: **No public third-party REST/SOAP API exists** as of September 2026.
- **Integration Design**: Contract-first architecture defined in `docs/integration-contract.md` utilizing:
  - `MockNcrpSource`: Deterministic fixture loader using `docs/research/sample_complaint.csv`.
  - Batch File Drop Watcher: Polls `/data/drop/` with automated `processed/` and `failed/` routing.
  - Secure REST API: `POST /api/v1/ingest/complaints` with scoped API key and HMAC-SHA256 signature verification.
- **Synthetic Fixtures**: Test fixtures `SYN-0001` through `SYN-0012` in `tests/fixtures/sample_complaint.csv` exercise edge cases (bad checksums, format overrides, missing amounts, VASP hot wallet reporting, and sanctions alerts).

---

### 2.2 SAHYOG Portal
- **Source**: Ministry of Home Affairs (MoHA) & Ministry of Electronics and Information Technology (MeitY)
- **Legal Mandate**: Section 79(3)(b) of the Information Technology Act, 2000
- **Status**: SAHYOG is strictly an **outbound notice and intermediary compliance coordination portal**. It is **NOT** an inbound complaint feed.
- **Implementation**: Outbound export only (`generate_sahyog_notice`), clearly marked with:
  > `"DISCLAIMER: UNVERIFIED PROTOTYPE EXPORT - GENERATED FOR INTERMEDIARY COORDINATION UNDER IT ACT S.79(3)(b)"`

---

## 3. Blockchain Data Providers & Oracles

| Provider | Purpose | Rate Limit / Quota | Failure Behavior |
| :--- | :--- | :--- | :--- |
| **TronGrid** | Tron transfers & balances | 10 QPS (100k requests/day free tier) | Circuit breaker opens on 5 consecutive failures; fallback to cached responses. |
| **Etherscan V2** | Ethereum, Polygon, Arbitrum transfers | 3 RPS global across all chains (100k requests/day free tier) | Rate limited $\to$ retry with exponential backoff & jitter; unsupported chain $\to$ `ChainUnsupported`. |
| **Blockstream Esplora** | Bitcoin UTXO transfers | Public REST API | Retries with backoff; pagination capped at configured limits. |
| **CoinGecko** | Historical & spot asset pricing | 60 RPM, 9,000 monthly request budget (Demo tier cap 10,000) | Hard quota tracking; raises `QuotaExhausted` when monthly budget reached; USDT/USDC pegged at $1.00 (0 API calls). |
