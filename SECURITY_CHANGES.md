# ChainNetra Security Hardening & Implementation Report

## Executive Summary
This document summarizes the comprehensive security enhancements implemented across ChainNetra's FastAPI backend and React frontend. All 11 targeted security sections have been fully implemented, integrated, and verified against automated test suites (`34/34` passing tests).

---

## 1. Summary of Changes by Section

### Section 1: Authentication & Route Protection
- Implemented `require_user` and `require_role(*roles)` dependencies in [security.py](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/backend/app/core/security.py).
- Enforced router-level dependencies across all endpoints (`cases`, `complaints`, `wallets`, `entities`, `watchlist`, `alerts`, `freeze`, `reports`, `analytics`, `admin`, `webhooks`, `system`).
- Defined strict public allowlist (`POST /auth/login`, `POST /auth/refresh`, `GET /verify/{hash}`, `POST /verify/upload`, `GET /`). Added in-memory rate limiting to public endpoints.
- Updated `get_current_user` to return `401 Unauthorized` for missing/unknown/inactive users or tokens missing `sub`/`role` claims.
- Verified with [test_auth_routes.py](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/backend/tests/test_auth_routes.py) dynamically testing all registered routes against unauthenticated and unauthorized access.

### Section 2: Identity Sourced Exclusively from JWT
- Stripped `user_email`, `author_email`, and `created_by` from all Pydantic request models.
- Derived creator, editor, approver, and audit identities strictly from `current_user.email`.
- Replaced all hardcoded `"investigator@demo"` / `"supervisor@demo"` fallback strings in API routers and services.

### Section 3: Elimination of Tamper Endpoint
- Removed `POST /admin/audit-log/tamper-test` from the application API.
- Created standalone verification script [scripts/demo_tamper.py](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/scripts/demo_tamper.py) for offline demo testing.

### Section 4: Freeze Workflow State Machine & Separation of Duties
- Implemented state machine transitions in [freeze.py](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/backend/app/services/freeze.py):
  - `Draft -> Pending Approval -> Approved -> Sent -> Acknowledged -> Frozen`
  - Rejection paths: `Pending Approval -> Rejected`, `Sent -> Rejected`, `Acknowledged -> Rejected`.
  - Illegal state jumps return `409 Conflict`.
- Enforced separation of duties: The creator of a freeze request cannot approve or reject their own request (`403 Forbidden`).
- Restricted approval and frozen amount finalization to supervisors/admins (`frozen_amount_usd <= victim_loss_usd`).
- Added `approved_by` and `approved_at` timestamps, writing audit entries on all state transitions.

### Section 5: WebSocket Authentication & Topic Scoping
- Enforced JWT authentication on WebSocket handshake via query param `?token=` (rejects with close code `4401` on invalid/missing tokens) in [ws.py](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/backend/app/core/ws.py).
- Eliminated `"all"` broadcast leakage; clients only receive messages for explicitly subscribed topics.
- Enforced permission checks for `trace:{case_id}` subscriptions.
- Added message size limit (64 KB), connection message rate limits, and idle timeouts.
- Updated [useWebSocket.ts](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/frontend/src/hooks/useWebSocket.ts) with dynamic base URL and authentication tokens.

### Section 6: Secrets & Configuration Hardening
- Updated [config.py](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/backend/app/core/config.py):
  - In `MODE=LIVE`, startup is halted if `SECRET_KEY`, `WEBHOOK_SECRET`, or `AUDIT_HMAC_KEY` are missing, shorter than 32/16 bytes, or match known demo keys.
  - In `MODE=DEMO`, random cryptographic keys are generated at startup with warning logs.
- Cleaned [.env.example](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/.env.example) and [docker-compose.yml](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/docker-compose.yml) using placeholders (`SECRET_KEY=change-me`).
- Webhook creation generates a 24-byte random secret shown once to the creator and stored securely.
- Updated [seed.py](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/backend/app/db/seed.py) to refuse seeding default passwords when `MODE=LIVE`.

### Section 7: Webhooks SSRF & Delivery Integrity
- Added SSRF IP filtering in [webhooks.py](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/backend/app/services/webhooks.py) blocking loopback, private, link-local, and cloud metadata ranges (`127.0.0.0/8`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `169.254.0.0/16`, `::1`, `fc00::/7`).
- Implemented DNS resolution checks, disabled redirects (`follow_redirects=False`), and added domain allowlisting support.
- Replaced fake 200 responses with honest delivery tracking and exponential retry backoff (3 attempts).
- Signed payloads with HMAC-SHA256 and attached `X-ChainNetra-Timestamp` replay protection headers.

### Section 8: CORS, Token Lifecycles & Security Headers
- Configured environment-controlled `CORS_ORIGINS` (disallowing wildcard credentials).
- Reduced `ACCESS_TOKEN_EXPIRE_MINUTES` to 30. Added 7-day refresh tokens stored as SHA-256 hashes in `UserRefreshToken`.
- Added `/auth/logout` endpoint that revokes refresh tokens and adds access token `jti` to `RevokedToken`.
- Updated frontend client [api.ts](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/frontend/src/lib/api.ts) to manage access tokens in memory and use HttpOnly refresh cookies with auto-retry on 401.
- Added brute-force lockout (15 minutes after 5 failed attempts) and rate limiting on login.
- Added `SecurityHeadersMiddleware` setting `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, and `Content-Security-Policy`.

### Section 9: Repository Hygiene & Dependency Auditing
- Removed `chainnetra.db` and generated PDFs from git tracking via `git rm --cached`.
- Added database files, WAL files, PDF reports, and environment secrets to [.gitignore](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/.gitignore).
- Added `pip-audit` and `npm audit` targets to [Makefile](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/Makefile).
- Created [SECURITY.md](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/SECURITY.md).

### Section 10: Audit Log Cryptographic Integrity & Immutability
- Added HMAC-SHA256 signatures per audit entry in [audit.py](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/backend/app/core/audit.py) using `AUDIT_HMAC_KEY`.
- Serialized audit writes with `BEGIN IMMEDIATE` transactions and unique `prev_hash` constraints.
- Created SQLite database triggers preventing `UPDATE` and `DELETE` on `audit_logs`.
- Added periodic signed checkpoints every N entries and exposed `GET /audit-log/checkpoints`.

### Section 11: Input Validation & Sanitization
- Implemented checksum-aware cryptocurrency address validation for EVM (EIP-55), Tron (Base58Check), and Bitcoin (Base58Check & Bech32) in [validators.py](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/backend/app/core/validators.py).
- Enforced limit and skip parameter bounds (`limit <= 200`, `skip >= 0`) across listing routes.
- Enforced CSV file size limits (5 MB), row caps (5,000 rows), and content-type validation in [ingest.py](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/backend/app/services/ingest.py).
- Sanitized filenames on verify upload and report download routes, strictly confining file resolution to designated storage paths to prevent path traversal.

---

## 2. Role Matrix Reference

| Role | Permitted Actions |
|---|---|
| **Investigator** | Cases (Read/Write), Traces (Run/Cancel), Notes, Freeze (Draft creation only), Reports (Generate/Read), Complaints (Read/Write), Wallets (Read), Watchlist (Read/Write), Alerts (Read/Ack), Entities (Read). |
| **Supervisor** | All Investigator permissions + Freeze (Approve/Reject/Send/Freeze), Analytics (Read), Audit Log (Read/Verify). |
| **Admin** | All Supervisor permissions + Labels (Create/Import/Delete), System Settings (Read/Write), Webhooks (Manage/Test), Users & API Keys (Manage). |

---

## 3. Required Environment Variables

| Variable | Required in LIVE | Default in DEMO | Description |
|---|:---:|:---:|---|
| `CHAINNETRA_MODE` | Yes | `DEMO` | Platform mode (`DEMO` or `LIVE`). |
| `SECRET_KEY` | Yes (>= 32 chars) | Random Hex (32 bytes) | Secret key for JWT access token encoding. |
| `WEBHOOK_SECRET` | Yes (>= 16 chars) | Random Hex (16 bytes) | Fallback default webhook signing secret. |
| `AUDIT_HMAC_KEY` | Yes (>= 16 chars) | Random Hex (32 bytes) | Key used for HMAC signatures on audit log entries. |
| `CORS_ORIGINS` | No | `http://localhost:5173,...` | Allowed CORS origins. |
| `DATABASE_URL` | No | `sqlite:///./chainnetra.db` | SQLAlchemy database connection URI. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `30` | Access token lifespan in minutes. |
| `REFRESH_TOKEN_EXPIRE_DAYS` | No | `7` | Refresh token lifespan in days. |

---

## 4. Residual Risks & Recommended Actions

> [!WARNING]
> ### 1. Git History Secret Leaks
> Any demo credentials or secrets committed to prior git commits must be treated as compromised. To permanently purge historical secrets from git history, run `git-filter-repo` (do NOT run without coordinating with repository collaborators):
> ```bash
> pip install git-filter-repo
> git filter-repo --invert-paths --path chainnetra.db --path backend/app/reports_storage
> ```

> [!NOTE]
> ### 2. External Audit Anchoring
> While the internal HMAC-SHA256 signature chain and SQLite triggers protect against unauthorized modifications within the application and standard SQL, a database administrator with direct root host access and the `AUDIT_HMAC_KEY` could rewrite historical records. For full legal admissibility in high-stakes court cases, periodic checkpoints exported via `GET /api/v1/audit-log/checkpoints` should be anchored to an external timestamping authority or public ledger (e.g. OpenTimestamps / RFC 3161 TSA).

---

## 5. Verification & Test Execution Status
- **Test Command**: `pytest -q`
- **Results**: **34 passed, 0 failed** in 45.09s
- **Included Tests**:
  - `test_every_route_requires_auth_or_is_in_allowlist`: 100% route coverage verification.
  - `test_rbac_wrong_role_forbidden_on_admin_routes`: RBAC authorization enforcement.
  - `test_identity_comes_from_jwt_only`: Body spoofing immunity.
  - `test_freeze_state_machine_and_separation_of_duties`: State transitions and self-approval block.
  - `test_websocket_authentication_and_scoping`: WS JWT enforcement and topic scoping.
  - `test_live_mode_startup_fails_on_weak_or_missing_secrets`: Secret strength validation.
  - `test_webhook_ssrf_blocks_private_and_loopback_ips`: Anti-SSRF enforcement.
  - `test_webhook_honest_delivery_recording`: Truthful error and retry logging.
  - `test_auth_refresh_rotation_and_revocation`: Refresh token rotation and logout revocation.
  - `test_audit_log_hmac_tamper_detection`: SQLite immutability trigger & HMAC verification.
  - `test_input_validation_address_and_path_traversal`: Address formats and path traversal prevention.
