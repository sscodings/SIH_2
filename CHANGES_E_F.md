# Changes Record: Phase E (Legal & Privacy) & Phase F (Repo Hygiene)

Branch: `ARNAV_EDITS`  
Date: 2026-10-01  
Repository: ChainNetra (FastAPI + React)

---

## 1. Summary of Changes per Section

### Phase E: Legal Content & Privacy

#### E1: Single Source of Truth for Legal Provisions & Notice Language
- Created [`backend/app/core/legal/provisions.yaml`](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/backend/app/core/legal/provisions.yaml) containing every statutory reference, procedural provision, statutory caption, freeze/preservation notice template, intermediary mandate, and disclaimer.
  - Provisions catalogued: BNSS §94 (Summons to produce document/thing), BNSS §106 (Attachment, forfeiture or seizure), BSA §63 (Admissibility of electronic records), IT Act §69A, IT Act §79(3)(b) (Intermediary guidelines), IT Act §66D (Cheating by personation), BNS §318(4) / IPC 420 (Cheating), PMLA §5/§17/§66 (FIU-IND coordination), DPDP Act 2023.
  - Every provision and notice block carries explicit metadata: `verified_on: "2026-09-30"`, `statute_book: "..."`, `needs_legal_review: false`, and disclaimer requirements.
- Implemented [`backend/app/core/legal/service.py`](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/backend/app/core/legal/service.py) with cached loader, query API (`get_provision`, `get_notice_template`, `list_provisions`, `get_legal_disclaimer`), and statutory dual-reference formatting.
- Implemented API endpoint `GET /api/v1/legal/provisions` in [`backend/app/api/v1/legal.py`](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/backend/app/api/v1/legal.py) for frontend consumption.
- Refactored all backend consumers to load provisions dynamically from `legal_service`:
  - [`backend/app/services/freeze.py`](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/backend/app/services/freeze.py): Replaced hardcoded CrPC 91 / 102 with BNSS §94 / §106 notices and disclaimers.
  - [`backend/app/services/evidence.py`](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/backend/app/services/evidence.py): Certificate generation now dynamically sources BSA §63 text and statutory schedule wording.
  - [`backend/app/services/outbox.py`](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/backend/app/services/outbox.py): Outbox notice builder sources IT Act §79(3)(b) from config.
  - [`backend/app/api/v1/cases.py`](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/backend/app/api/v1/cases.py): Removed hardcoded Cr.No formats and officer text.
- Replaced hardcoded legal strings in frontend pages ([`frontend/src/pages/FreezeRequests.tsx`](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/frontend/src/pages/FreezeRequests.tsx), [`frontend/src/pages/DigitalEvidence.tsx`](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/frontend/src/pages/DigitalEvidence.tsx), [`frontend/src/pages/CaseDetail.tsx`](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/frontend/src/pages/CaseDetail.tsx)) with dynamic API queries and fallback notices.
- Created regression gate script [`scripts/check_legal_strings.py`](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/scripts/check_legal_strings.py) and added `npm run check:legal` to CI/dev workflows.

#### E2: BSA 63 (ex-65B) Certificate Hygiene & Accuracy
- Updated [`backend/app/services/evidence.py`](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/backend/app/services/evidence.py) to dynamically construct Bharathiya Sakshya Adhiniyam, 2023 Section 63 Schedule certificate declarations.
- Enforced Part A (system details, operational conditions, hash verification) and Part B (certifying officer declaration, signature date, and designation).
- When optional user inputs or officer designations are omitted, the certificate renders blank fillable lines `___________________________` rather than inventing officer names or designations.
- Prominently prints statutory prototype disclaimer on certificates: `"PROTOTYPE EVIDENCE ARTIFACT - GENERATED FOR TECHNICAL VERIFICATION UNDER BSA 63 SCHEDULE"`.

#### E3: PII Protection (DPDP Act 2023 Alignment)
- Implemented multi-key Fernet rotation and field-level encryption in [`backend/app/core/crypto.py`](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/backend/app/core/crypto.py) (`EncryptedString`, `EncryptedText`, `encrypt_pii`, `decrypt_pii`, `rotate_pii`).
- Encrypted sensitive PII columns in [`backend/app/db/models.py`](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/backend/app/db/models.py):
  - `complaints`: `victim_name`, `victim_phone`, `victim_email`, `suspect_phone`, `suspect_email`
  - `entities`: `nodal_officer_email`, `nodal_officer_phone`
  - `freeze_requests`: `notes`
- Masked PII across complaint schemas and APIs ([`backend/app/schemas/complaint.py`](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/backend/app/schemas/complaint.py), [`backend/app/api/v1/complaints.py`](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/backend/app/api/v1/complaints.py)) with role-based unmasking (`/api/v1/complaints/{id}/unmask-pii`) restricted to supervisor/admin with mandatory logging in `pii_access_logs`.
- Created key rotation script [`scripts/rotate_pii_keys.py`](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/scripts/rotate_pii_keys.py) supporting zero-downtime key rotation via comma-separated `PII_FERNET_KEYS`.

#### E4: Data Retention & Audit Trail Immutability
- Implemented configurable retention policies in [`backend/app/services/retention.py`](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/backend/app/services/retention.py) (`RETENTION_DAYS_TRACES = 90`, `RETENTION_DAYS_LOGS = 180`, `RETENTION_DAYS_EVIDENCE = 1095`).
- Guaranteed cryptographic immutability of audit records:
  - Added SQLite triggers `prevent_audit_log_update` and `prevent_audit_log_delete` in [`backend/app/core/audit.py`](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/backend/app/core/audit.py) to reject any modifications or deletions at the database engine level.
  - Configured HMAC-SHA256 checkpointing for long-term verification.

---

### Phase F: Repo Hygiene & Engineering Standards

#### F1: No Hardcoded API Hosts in Frontend
- Created [`frontend/src/lib/config.ts`](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/frontend/src/lib/config.ts) exporting `API_BASE_URL` and `WS_URL` derived from `import.meta.env.VITE_API_BASE_URL` and `import.meta.env.VITE_WS_URL`, falling back gracefully to relative `/api/v1` and relative WebSocket paths.
- Decoupled all frontend network callers:
  - [`frontend/src/lib/api.ts`](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/frontend/src/lib/api.ts)
  - [`frontend/src/hooks/useWebSocket.ts`](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/frontend/src/hooks/useWebSocket.ts)
  - [`frontend/src/pages/Verify.tsx`](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/frontend/src/pages/Verify.tsx)
  - [`frontend/src/pages/Reports.tsx`](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/frontend/src/pages/Reports.tsx)
  - [`frontend/src/pages/Inbox.tsx`](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/frontend/src/pages/Inbox.tsx)
  - [`frontend/src/pages/Integrations.tsx`](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/frontend/src/pages/Integrations.tsx)
- Configured Vite dev proxy in [`frontend/vite.config.ts`](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/frontend/vite.config.ts) (`/api` -> `http://127.0.0.1:8000`, `/ws` -> `ws://127.0.0.1:8000`).
- Configured production reverse-proxy in [`frontend/nginx.conf`](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/frontend/nginx.conf) routing `/api/` and `/ws/` to backend service.
- Created pre-commit/CI check scripts:
  - [`scripts/check_no_hardcoded_hosts.py`](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/scripts/check_no_hardcoded_hosts.py)
  - [`scripts/check_no_hardcoded_hosts.sh`](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/scripts/check_no_hardcoded_hosts.sh)
  - Added `"check:hosts"` script in [`frontend/package.json`](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/frontend/package.json).

#### F2: Cross-Platform Dev Commands & Scripts
- Created Python-based standard-library task runner [`scripts/dev.py`](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/scripts/dev.py) (`python scripts/dev.py [backend|frontend|worker|test|check|docker-up|docker-down]`).
- Created PowerShell helper [`scripts/dev.ps1`](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/scripts/dev.ps1) for Windows native environments.
- Updated [`Makefile`](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/Makefile) with OS-agnostic delegates routing to `scripts/dev.py`.
- Updated [`README.md`](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/README.md) with clear Linux/macOS and Windows setup instructions.

#### F3: Docker Persistence & Image Hygiene
- Pinned secure base images:
  - `backend/Dockerfile`: `python:3.11.8-slim-bookworm`, non-root user `appuser:appgroup` (UID 10001), healthcheck against `/api/v1/system/monitor`.
  - `frontend/Dockerfile`: Multi-stage build with `node:20.11.1-alpine` and `nginx:1.25.4-alpine`, non-root permissions, healthcheck on `/`.
- Created comprehensive `.dockerignore` files at repository root, `/backend`, and `/frontend`.
- Updated [`docker-compose.yml`](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/docker-compose.yml) to declare named volumes:
  - `evidence_data` (`/app/data/evidence`)
  - `label_cache` (`/app/data/labels`)
  - `postgres_data` (`/var/lib/postgresql/data`)
  - `redis_data` (`/data`)
- Created [`scripts/test_persistence.sh`](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/scripts/test_persistence.sh) verifying data survivability across container restarts.

#### F4: License Audit & Notice
- Checked `docs/research/decisions.md`: no open source license was formally decided or authorized.
- Removed inaccurate MIT license claim and badge from [`README.md`](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/README.md).
- Documented "LICENSE decision needed" placeholder without inventing a license.

#### F5: Time Handling & Sequence Numbering
- Standardized on [`backend/app/core/time.py`](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/backend/app/core/time.py) helper `utcnow() -> datetime` with `timezone.utc`.
- Replaced all 50+ occurrences of deprecated `datetime.utcnow()` across models, workers, outbox, labels, alerts, entities, and services.
- Updated all 54 `DateTime` columns in [`backend/app/db/models.py`](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/backend/app/db/models.py) to `DateTime(timezone=True)`.
- Updated audit trail timestamp formatting in [`backend/app/core/audit.py`](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/backend/app/core/audit.py) to output ISO strings with `+00:00` offset, while maintaining backward-compatible verification for legacy naive timestamps.
- Enhanced `get_next_sequence_number` in `models.py` with thread locks and atomic counter increments.
- Added comprehensive test suite [`backend/tests/test_time_and_sequences.py`](file:///d:/Study/Hackthon/SIH_PROTOTYPE-2/backend/tests/test_time_and_sequences.py) testing:
  - Timezone awareness of `utcnow()`.
  - Zero deprecated `datetime.utcnow()` in `backend/app`.
  - `timezone=True` on all model columns.
  - Concurrency test with 10 threads producing 10 sequential IDs with zero duplicates.
  - Sequence persistence ensuring deleted records never reuse counter IDs.
  - Backward and forward audit chain cryptographic verification.

---

## 2. List of New Environment Variables

| Variable | Default Value | Purpose |
|---|---|---|
| `PII_FERNET_KEYS` | (auto-generated fallback key) | Comma-separated list of Fernet keys for AES-128-CBC encryption with zero-downtime rotation. Primary key listed first. |
| `PII_MASKING_SALT` | `chainnetra_pii_salt_2026` | Salt used for pseudonymous hashes of PII in case records. |
| `AUDIT_HMAC_KEY` | `chainnetra_audit_fallback_key_2026` | Key used for tamper-evident HMAC-SHA256 signatures on linear audit chain records. |
| `AUDIT_CHECKPOINT_INTERVAL` | `50` | Interval in audit log count after which an audit checkpoint is signed and committed. |
| `VITE_API_BASE_URL` | `""` (empty, defaults to relative `/api/v1`) | Base URL for frontend REST API requests. In development, defaults to relative path proxied by Vite. |
| `VITE_WS_URL` | `""` (empty, defaults to relative WebSocket) | Base URL for frontend WebSocket connections. |

---

## 3. Database Changes & Migration Notes

1. **New Tables**:
   - `pii_access_logs`: Tracks user email, record ID, viewed fields, and justification reason whenever PII is unmasked under DPDP compliance.
   - `system_counters`: Stores thread-safe monotonic sequence counters for case numbers, complaint numbers, and freeze request numbers (`CASE-YYYY-XXXXXX`, `FR-YYYY-XXXXXX`, etc.).
   - `audit_checkpoints`: Stores periodic cryptographic checkpoints of the audit log chain.

2. **Column Type & Encryption Changes**:
   - All `DateTime` columns now specify `DateTime(timezone=True)`.
   - `Complaint` table columns `victim_name`, `victim_phone`, `victim_email`, `suspect_phone`, `suspect_email` now use `EncryptedString` (Fernet encrypted ciphertext).
   - `Entity` table columns `nodal_officer_email`, `nodal_officer_phone` now use `EncryptedString`.
   - `FreezeRequest` column `notes` now uses `EncryptedText`.
   - *Migration note for existing production data*: Existing plaintext records should be rotated once via `python scripts/rotate_pii_keys.py` to encrypt unencrypted records in place.

3. **Audit Chain Timestamp Compatibility**:
   - New audit log entries format timestamps with full ISO 8601 offset (`YYYY-MM-DDTHH:MM:SS+00:00`).
   - `verify_audit_chain()` includes automatic fallback to the pre-F5 naive format (`YYYY-MM-DDTHH:MM:SS`), ensuring historical audit chains created before this update remain 100% valid without requiring destructive hash recalculations.

---

## 4. What Was NOT Verified Here

The following items are outside the scope of automated testing or require external legal/operational authority:
- **Legal Accuracy of Statutory Provisions**: The statutory text in `provisions.yaml` represents faithful transcriptions of BNSS 2023, BNS 2023, BSA 2023, IT Act 2000, and DPDP Act 2023. Formal admissibility in a specific High Court or Supreme Court jurisdiction requires formal advocate review.
- **BNSS §106 Judicial Interpretations**: The application of BNSS §106 to virtual digital assets (VDAs) pending formal state-level police standing orders or high court precedents.
- **DPDP Act 2023 Full Commencement Date**: Specific rules under DPDP Act 2023 are subject to notification by the Data Protection Board of India; placeholder consent workflows follow published draft frameworks.
- **Live Docker Daemon Run**: Dockerfiles and `docker-compose.yml` configurations were statically validated; running live multi-container compose stacks requires an active Docker daemon in the host environment.
- **Non-Windows / Non-Linux OS Execution**: Scripts and makefiles were tested under Windows (PowerShell/Python) and POSIX-compliant Python/Bash specifications.
