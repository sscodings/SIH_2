# ChainNetra Integration Contract

**Document Version**: 1.0.0-PROTOTYPE  
**Schema Version**: `chainnetra.complaints.v1`  
**Date**: 2026-09-30  
**Status**: DRAFT CONTRACT-FIRST SPECIFICATION

---

## 1. Executive Summary & Legal Grounding

1. **National Cybercrime Reporting Portal (NCRP) / CFCFRMS**:
   - Status: As of September 2026, no verified public third-party REST/SOAP API exists for direct third-party LEA integration.
   - Design: ChainNetra provides a pluggable `ComplaintSource` abstract interface backed by a deterministic mock adapter (`MockNcrpSource`), file-drop watcher, and secure REST ingestion pipeline.
   - Production Readiness: Full schema contract defined below ready for real webhook/mTLS endpoint provisioning once official MoHA/I4C specifications are released.

2. **SAHYOG (IT Act Section 79(3)(b))**:
   - Clarification: SAHYOG is a takedown-notice and intermediary coordination portal governed by Section 79(3)(b) of the Information Technology Act, 2000. It is **NOT** a raw complaint ingest feed.
   - Inbound: Strictly prohibited.
   - Outbound: Optional outbound notice export formatted for intermediary compliance officers, clearly stamped as *UNVERIFIED PROTOTYPE EXPORT*.

---

## 2. Ingestion Pipeline Channels

All inbound complaint channels route into a single unified verification pipeline:
1. **REST API**: `POST /api/v1/ingest/complaints`
2. **Batch File Drop**: Directory watcher polling `/data/drop/` with `processed/` and `failed/` isolation.
3. **Pull Connector Interface**: Scheduled poller implementing `ComplaintSource`.

---

## 3. REST API Contract & Security Specification

### Endpoint
`POST /api/v1/ingest/complaints`

### Authentication & Authorization
- **API Key**: Scoped key with `ingest:write` capability, transmitted via header `X-API-Key`. Keys are SHA-256 hashed and rotatable.
- **HMAC Signature**: `X-Signature-SHA256 = HMAC-SHA256(secret_key, timestamp + "." + request_body)`.
- **Timestamp Skew Window**: Transmitted via `X-Timestamp` (UNIX epoch in seconds or ISO-8601). Replay window strictly rejects requests with clock skew $> 300$ seconds (5 minutes).
- **Idempotency**: Transmitted via `Idempotency-Key` header or composite `(source_system, complaint_number)`. Resubmissions return HTTP 200 with status `"duplicate"`.

### CSV Contract Headers

| CSV Column | Normalized Canonical Field | Type | Description / Rules |
| :--- | :--- | :--- | :--- |
| `complaint_id` | `complaint_number` | string | Idempotency key scoped to `source_system`. |
| `data_origin` | `data_origin` | enum | `REAL` or `SYNTHETIC`. Synthetic rows excluded from analytics unless DEMO mode. |
| `state` | `victim_state` | string | State of complainant. |
| `category` | `fraud_type` | string | Fraud category (Investment fraud, Job scam, etc.). |
| `amount_inr` | `amount_lost_inr` | float / null | Lost amount in INR. Blank sets `amount_unknown=True` (never defaults to 0). |
| `incident_date` | `incident_at` | datetime | Lower time bound for forward transaction tracing. |
| `victim_id_masked` | `victim_ref` | string | Pre-masked identifier. Encrypted at rest via Fernet. |
| `suspect_wallet_address` | `reported_wallet` | string | Checksum-validated cryptocurrency address. |
| `chain` | `chain_hint` | string | Advisory hint. Format validation overrides hint on disagreement with audit log. |
| `txn_hash` | `txn_hash` | string | Payment tx hash. Normalized per chain (Tron/BTC: 64 hex; EVM: 0x + 64 hex). |
| `bank_or_exchange_named`| `claimed_vasp_hint` | string | Cross-checked against FIU registry. Never treated as direct label evidence. |

---

## 4. Cross-Complaint Linking & Deduplication

- The previous legacy `contains` string search is permanently replaced with the relational `complaint_wallets` table:
  ```sql
  CREATE TABLE complaint_wallets (
      id SERIAL PRIMARY KEY,
      complaint_id INTEGER REFERENCES complaints(id),
      chain VARCHAR(50) NOT NULL,
      normalized_address VARCHAR(255) NOT NULL,
      is_primary BOOLEAN DEFAULT TRUE,
      created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
  );
  CREATE INDEX ix_complaint_wallets_chain_addr ON complaint_wallets (chain, normalized_address);
  ```
- Any wallet matching existing complaints generates bi-directional linkages in `linked_complaint_ids` and emits a `MEDIUM` severity alert: `"New Linked Complaint Discovered"`.

---

## 5. Automated Triage & Case Generation

- **Threshold**: Evaluated against `settings.AUTO_CASE_MIN_PRIORITY` (default `"High"`).
- **VASP Wallet Protection**: If `suspect_wallet_address` matches an active verified VASP exchange label, the complaint is tagged `"reported wallet is a known VASP"` and automated tracing is blocked to prevent sweeping broad exchange pool wallets.
- **Sanctioned Hit**: If the wallet matches OFAC SDN list, a `CRITICAL` severity alert is raised immediately.
