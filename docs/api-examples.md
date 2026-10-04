# ChainNetra API Documentation & Working cURL Examples

All endpoints are versioned under `/api/v1`. Interactive Swagger UI is available at `http://127.0.0.1:8000/docs`.

---

## 1. Authentication

### Authenticate as Investigator
```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=investigator@demo&password=demo123"
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
  "token_type": "bearer",
  "role": "investigator",
  "name": "Insp. Vikramaditya"
}
```

---

## 2. Ingestion & Complaints

### Simulate Incoming NCRP Complaint
```bash
curl -X POST http://127.0.0.1:8000/api/v1/complaints/simulate \
  -H "Authorization: Bearer <TOKEN>"
```

### Ingest NCRP Complaint Direct
```bash
curl -X POST http://127.0.0.1:8000/api/v1/ingest/ncrp \
  -H "Content-Type: application/json" \
  -d '{
    "victim_name": "Rajesh Kumar",
    "victim_state": "Maharashtra",
    "fraud_type": "investment_scam",
    "reported_wallet": "TX9aDemoCollectorTronAddr001",
    "amount_lost_inr": 250000.0,
    "description": "Telegram Crypto Doubling Investment Fraud"
  }'
```

---

## 3. Forensic Tracing & Graph

### Start Automated Trace on Case
```bash
curl -X POST http://127.0.0.1:8000/api/v1/cases/1/trace \
  -H "Content-Type: application/json" \
  -d '{
    "max_depth": 6,
    "min_value_usd": 50.0,
    "taint_model": "haircut",
    "stop_at_first_vasp": true,
    "include_cross_chain": true
  }'
```

### Fetch Fund-Flow Graph Elements
```bash
curl -X GET http://127.0.0.1:8000/api/v1/cases/1/graph
```

### Fetch Nearest VASP Attribution & Confidence Breakdown
```bash
curl -X GET http://127.0.0.1:8000/api/v1/cases/1/attribution
```

---

## 4. Evidence Verification & Audit Integrity

### Verify Tamper-Evident Report Hash
```bash
curl -X GET http://127.0.0.1:8000/api/v1/verify/5a1e2f9b8c0d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f
```

### Verify Hash-Chained Audit Log
```bash
curl -X GET http://127.0.0.1:8000/api/v1/audit-log/verify
```

Response:
```json
{
  "valid": true,
  "count": 5,
  "message": "All 5 audit entries verified intact with valid SHA-256 chain of custody."
}
```

---

## 5. Webhooks & Watchlist

### Simulate Watchlist Movement Alert
```bash
curl -X POST http://127.0.0.1:8000/api/v1/watchlist/simulate-movement
```
