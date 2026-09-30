# ChainNetra Changes & Audit Log

## Issue 1: Add `requirements.txt`
- Created `backend/requirements.txt` with pinned versions matching the actual imported backend packages: `fastapi==0.110.0`, `uvicorn[standard]==0.28.0`, `sqlalchemy>=2.0.25,<2.1.0`, `pydantic>=2.6.0,<3.0.0`, `pydantic-settings>=2.2.0,<3.0.0`, `python-jose[cryptography]==3.3.0`, `bcrypt==4.1.2`, `httpx>=0.27.0,<0.29.0`, `networkx>=3.2.1`, `scikit-learn>=1.4.0,<1.7.0`, `numpy>=1.26.0,<2.3.0`, `pandas>=2.2.0,<2.3.0`, `joblib>=1.3.0,<1.7.0`, `reportlab>=4.1.0,<5.1.0`, `qrcode[pil]>=7.4.2,<8.3.0`, `python-multipart>=0.0.9`, `pytest>=8.0.0`, `pytest-asyncio>=0.23.0`, and `websockets>=12.0`.
- Verified installation in a clean virtual environment without dependency conflicts.

## Issue 2: Fix Import Path Mismatch
- Standardized execution from inside `backend/` (matching Dockerfile and production standards).
- Scripted rewrite of all 38+ Python files converting `backend.app.*` to `app.*` across adapters, api, core, db, engines, ml, services, and tests.
- Added `__init__.py` files to `backend/app/`, `backend/app/adapters/`, `backend/app/api/`, `backend/app/api/v1/`, `backend/app/core/`, `backend/app/db/`, `backend/app/engines/`, `backend/app/ml/`, `backend/app/services/`, and `backend/tests/`.
- Created `backend/pytest.ini` configuring `pythonpath = .`.
- Updated `Makefile` to be cross-platform across Windows and Unix environments without hardcoded `venv/Scripts` or `start cmd`.
- Updated `README.md` to document running commands from inside `backend/`.
- Verified `python -c "import app.main"`, `python -m app.db.seed`, and FastAPI `/docs` served successfully.

## Issue 3: Wire ML Models into Risk Scoring & Honest Model Card
- Implemented lazy singleton model manager (`MLModelManager`) in `app/engines/risk.py` with graceful failure handling if `.joblib` model files or model cards are missing.
- Aligned feature extraction with the 11 features defined in `app/ml/train.py`, persisting `feature_order` in `model_card.json` and dynamically constructing inference DataFrames matching this order.
- Blended RandomForest role predictions (`ml_role`, `ml_confidence`) and IsolationForest anomaly scores (`anomaly_score`) into `calculate_wallet_risk` output and added transparent, explainable factor items to the `factors` list.
- Updated `app/ml/train.py` and `model_card.json` with honest held-out split evaluation and clear caveat disclosures (synthetic training data, triage aid, non-adversarial).
- Exposed the caveat in `app/api/v1/admin.py` for `/api/v1/admin/model-card`.

## Issue 4: Strict LIVE Mode without Demo Fallbacks
- Introduced `AdapterError` in `app/adapters/base.py`.
- Removed all `demo_fallback` invocations in `evm.py`, `tron.py`, and `bitcoin.py`.
- Enforced that `DemoAdapter` is only returned by `app/adapters/factory.py` when `CHAINNETRA_MODE=DEMO`.
- Implemented retry with exponential backoff (up to 3 attempts) in live adapters, raising `AdapterError` on unrecoverable HTTP/rate limit/timeout/payload failures.
- Updated `TracingEngine` in `app/engines/tracer.py` to catch `AdapterError`, record incomplete branches in `incomplete_branches` with address, chain, and reason, set `is_complete: False`, and continue exploring other branches.

## Issue 5: Real Live Blockchain Adapters & Pricing Service
- Implemented `app/services/pricing.py` with 1.0 constant pegs for stablecoins (USDT, USDC, DAI, BUSD, FDUSD), CoinGecko API integration for volatile assets (ETH, BTC, TRX, BNB, POL, ARB), and a 60-second in-memory cache. Price lookup failures strictly raise `AdapterError`.
- `TronAdapter` (`app/adapters/tron.py`): Querying TronGrid TRC-20 and native TRX transfers, respecting `direction` (`only_from`/`only_to`), `since` timestamp filtering, pagination via `meta.fingerprint`, and setting `truncated=True` if max page limit is reached.
- `EvmAdapter` (`app/adapters/evm.py`): Migrated to unified Etherscan API V2 (`https://api.etherscan.io/v2/api` with `chainid`), aggregating `tokentx` (ERC-20), `txlist` (native), and `txlistinternal`, filtering by direction and `since`, and flagging pagination truncation.
- `BitcoinAdapter` (`app/adapters/bitcoin.py`): Querying Blockstream Esplora API, parsing `vin`/`vout`, attributing outputs to inputs, detecting multi-input transactions (`multi_input=True`), and supporting pagination.
- Added configuration variables `COINGECKO_BASE_URL`, `ADAPTER_MAX_PAGES`, `ADAPTER_TIMEOUT`, and `ETHERSCAN_API_KEY` to `app/core/config.py` and `.env.example`.

## Issue 6: Replace Circular Tests
- Built `backend/tests/conftest.py` with an isolated in-memory SQLite database fixture (`sqlite:///:memory:`) that spins up a clean schema per test session and overrides FastAPI's `get_db` dependency.
- Added hand-built graph test fixtures (`suspect -> mule -> mule -> exchange hot wallet`) with mocked adapters injected via `app.adapters.factory.register_adapter`.
- Added test coverage for:
  - Taint propagation models (`haircut`, `fifo`, `poison`) edge cases (zero inflow, zero outflow).
  - Tracer behavior (`stop_at_first_vasp`, max depth, incomplete branch handling on `AdapterError`).
  - Cross-chain bridge heuristics (matching, non-matching, time proximity).
  - Mixer withdrawal candidate matching.
  - Freeze request lifecycle workflow.
  - Ingestion address validation with real Tron Base58, Ethereum EIP-55, and Bitcoin Bech32/Legacy addresses.
  - API smoke tests using `TestClient` for cases, freeze requests, verification, and end-to-end demo mode.
  - Adapter tests using `httpx.MockTransport` covering direction, since filter, pagination, truncation, and pricing.
- Verified that all 19 tests pass via `pytest -q` with zero dependence on `chainnetra.db`.

---

## Known Limitations
1. **Public API Rate Limits**: In LIVE mode, public free-tier endpoints for Etherscan and TronGrid are subject to strict rate limits (e.g., 5 requests/sec for free Etherscan keys). High concurrency tracing across deep graphs should be provisioned with paid API keys configured in `.env`.
2. **CoinGecko Free API Tier**: The pricing service uses CoinGecko's public demo endpoint with a 60-second in-memory cache; under high-frequency fresh-asset lookups, a CoinGecko Pro API key or enterprise oracle should be configured.
3. **Bitcoin Multi-Output Heuristic**: The Bitcoin adapter attributes outputs in a 1-to-many model to primary inputs; complex CoinJoin transactions are flagged with `multi_input=True` but still require heuristic probabilistic scoring.
