# ChainNetra Gaps & Changes Log

**Date**: 2026-10-01  
**Branch**: `ARNAV_EDITS`  
**Base Commit**: `1d2773a` $\rightarrow$ `5dc6f3d` $\rightarrow$ Phase 3  

---

## 1. Summary of Changes by Section

### Section 1: Label Ingestion & Attribution Data Pipeline
- **Modules Created/Modified**: `backend/app/labels/` (`base.py`, `ofac.py`, `fiu.py`, `exchange_csv.py`, `service.py`, `sync.py`, `commercial.py`), `backend/app/api/v1/entities.py`.
- **Key Enhancements**:
  - Golden test passed on `docs/research/ofac_sample.xml`: precisely parses 234 digital currency addresses with XML namespaces (`FeatureTypeID=1432`).
  - FIU-IND VASP parliamentary snapshot (47 entities) ingested with staleness indicators and empty nodal contact warnings.
  - Exchange CSV loader ingests 30 addresses; handles historical validity (`valid_from`, `valid_to`), superseded mappings (Unocoin BTC `1PSh1go1ZBvULhGV4BsekEaVAAESa2fNWp` marked `valid_to="2023-06-23"`, Bybit `0x1Db92e...` inactive).
  - Multi-tier conflict resolution prioritizing authoritative weights (`government_sanctions` > `regulatory_fiu` > `exchange_self_disclosure`).
  - Admin-only label submission (`POST /api/v1/labels`) and supervisor approval endpoint (`POST /api/v1/labels/{id}/approve`).

### Section 2: Complaint Ingestion Pipeline & Verification
- **Modules Created/Modified**: `backend/app/services/complaint_source.py`, `backend/app/services/file_drop.py`, `backend/app/services/outbox.py`, `backend/app/api/v1/ingest.py`, `backend/app/core/pii.py`.
- **Key Enhancements**:
  - `ComplaintSource` ABC and `MockNcrpSource` implementing deterministic fixture ingestion.
  - Contract-first specification in `docs/integration-contract.md`.
  - Format validation strictly overrides advisory chain hints with audit warnings (e.g. `SYN-0009` Tron address with `ETH` hint correctly assigned to `tron`).
  - Strict Tron Base58Check checksum validation (rejects corrupt checksums like `SYN-0011`).
  - Relational cross-complaint linking using indexed `complaint_wallets` table; raises `NEW_LINKED_COMPLAINT` alert (e.g. `SYN-0008` links to `SYN-0001`).
  - Pre-triage known VASP protection: `SYN-0012` flagged with `vasp_flag="reported wallet is a known VASP"`, preventing automated sweeps of exchange pools.
  - Fernet symmetric encryption of complainant PII at rest (`victim_ref`); unmasked only for `supervisor` and `admin` roles, masked as `"REDACTED"` for `investigator`.
  - Scoped REST ingestion (`POST /api/v1/ingest/complaints`) with `X-API-Key`, clock skew verification ($\le 300\text{s}$), and HMAC-SHA256 signature verification.
  - File drop watcher polling `/data/drop/`, routing valid files to `processed/` and corrupt batches to `failed/` with `<file>.err` sidecars.

### Section 3: Job Queue, Postgres & Infrastructure
- **Modules Created/Modified**: `backend/app/worker.py`, `backend/app/services/queue.py`, `backend/alembic/`, `backend/alembic.ini`, `docker-compose.yml`, `backend/Dockerfile`.
- **Key Enhancements**:
  - `arq` + Redis asynchronous trace worker with exponential backoff on `AdapterError`.
  - Startup sweeper (`sweep_stuck_jobs`) marking orphaned or timed-out running jobs ($> 30\text{ minutes}$) as `failed`.
  - Thread-safe locked sequence generator `SystemCounter` (`CASE-2026-001001`, `FR-2026-001001`, `NCRP-2026-001001`), eliminating count-based race conditions.
  - Cleaned `backend/Dockerfile` by removing premature `RUN seed` and `RUN train` build steps.
  - Updated `docker-compose.yml` orchestrating `api`, `worker`, `postgres`, `redis`, and `frontend` with healthchecks and named volumes.
  - Configured Alembic with initial schema migration (`001_initial_schema.py`).

### Section 4: Scheduler, Monitoring & Alerts Lifecycle
- **Modules Created/Modified**: `backend/app/worker.py` (cron routines), `backend/app/api/v1/alerts.py`.
- **Key Enhancements**:
  - `arq` cron scheduler running periodic tasks:
    - Watchlist monitoring every `WATCHLIST_MONITOR_INTERVAL_SECONDS` with per-wallet deduplication.
    - Daily label synchronization (`sync_labels_job`).
    - Periodic asset price cache refresh (`refresh_prices_job`).
    - Stuck-job sweeper every 20 minutes (`sweep_stuck_jobs`).
    - Periodic tamper-evident audit checkpoints (`create_audit_checkpoint_job`).
  - Decisions.md item 4 severity mapping applied to alerts:
    - Sanctioned entity hit $\rightarrow$ `Critical`
    - Mixer interaction $\rightarrow$ `High`
    - VASP transfer $\rightarrow$ `High`
    - New inflow $\rightarrow$ `Medium`
    - New linked complaint $\rightarrow$ `Medium`
  - Alert resolution and acknowledgment endpoints (`POST /alerts/{id}/ack`, `POST /alerts/{id}/resolve`).
  - System monitor health endpoint (`GET /api/v1/alerts/monitor/status`).

### Section 5: Address Validation & EVM Multi-Chain
- **Modules Created/Modified**: `backend/app/core/addresses.py`, `backend/app/core/validators.py`.
- **Key Enhancements**:
  - Tron Base58Check (`0x41` prefix, SHA256 checksum).
  - Bitcoin Base58Check (P2PKH, P2SH) and Bech32/Bech32m (P2WPKH, P2WSH, P2TR).
  - EVM EIP-55 checksum validation (accepts all-lowercase, rejects incorrect mixed-case).
  - Multi-chain candidate resolution for bare EVM addresses across Ethereum, Polygon, and Arbitrum.

### Section 6: HTTP Client, Rate Limiting & Provider Map
- **Modules Created/Modified**: `backend/app/adapters/http.py`, `backend/app/adapters/evm.py`, `backend/app/adapters/tron.py`, `backend/app/services/pricing.py`, `backend/app/api/v1/system.py`.
- **Key Enhancements**:
  - Provider token buckets: Etherscan (3 RPS global), TronGrid (10 QPS), CoinGecko (60 RPM).
  - CoinGecko monthly quota tracking (9,000 requests cap, raises `QuotaExhausted`).
  - USDT and USDC hardcoded at $1.00 peg (0 API calls).
  - Circuit breaker (trips after 5 consecutive failures, 30s probe reset).
  - Full pagination loop honoring `ADAPTER_MAX_PAGES` and setting `truncated=True` when capped.
  - Admin-only metrics endpoint (`GET /api/v1/system/metrics`).

---

## 2. New Environment Variables

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `CHAINNETRA_MODE` | `DEMO` | Operating mode: `DEMO` (offline deterministic) or `LIVE` (production). |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL for `arq` job queue and rate limiting. |
| `DATABASE_URL` | `sqlite:///./chainnetra.db` | PostgreSQL required in LIVE mode; SQLite allowed for DEMO/tests. |
| `WATCHLIST_MONITOR_INTERVAL_SECONDS` | `300` | Polling cadence (in seconds) for monitored watchlist wallets. |
| `AUTO_CASE_MIN_PRIORITY` | `High` | Priority threshold for automatic case creation from complaints. |
| `PII_ENCRYPTION_KEY` | `None` (derived from SECRET_KEY) | 32-byte URL-safe base64 key for Fernet complainant encryption. |
| `DROP_DIR` | `None` (defaults to `data/drop`) | Directory path polled by file drop watcher. |
| `ETHERSCAN_RPS` | `3.0` | Global rate limit across all Etherscan V2 chains. |
| `TRONGRID_QPS` | `10.0` | Query rate limit for TronGrid API. |
| `COINGECKO_RPM` | `60.0` | Requests per minute for CoinGecko pricing oracle. |
| `COINGECKO_MONTHLY_BUDGET` | `9000` | Maximum monthly API calls before raising `QuotaExhausted`. |

---

## 3. Not Verifiable Here (Production Dependencies & Unknowns)

The following items cannot be fully verified in this local/sandbox environment and must be checked prior to real LEA deployment:
1. **Real NCRP / CFCFRMS Endpoints & Credentials**:
   - Official REST/SOAP API specifications and mTLS client certificates from I4C/MoHA have not been released publicly.
2. **SAHYOG Production Intermediary Portal Specs**:
   - SAHYOG outbound notice formats are governed by intermediary-specific compliance portals under IT Act Section 79(3)(b). Real submission requires liaison with authorized nodal officers.
3. **FIU-IND Nodal Officer Directory**:
   - Official direct email addresses and phone numbers for VDA SP compliance officers are not published in parliamentary records; must be provisioned via an authorized LEA directory.
4. **Commercial Threat Intelligence API Keys**:
   - Chainalysis, TRM Labs, and Elliptic commercial endpoints are mocked/disabled until active LEA enterprise licenses are provisioned.
5. **Etherscan Free Tier Coverage of Binance Smart Chain (BSC)**:
   - BSC mapping currently defaults to `ChainUnsupported` unless served via an explorer provider like Blockscout or a paid Etherscan multi-chain plan.
6. **Production Network Latency & Provider Rate Limits**:
   - Production throughput under real multi-thousand transfer volume will depend on commercial RPC limits and cloud Redis persistence latency.
