# ChainNetra Privacy Policy & Data Inventory (DPDP Alignment)

> [!WARNING]
> **Legal Review Required; Compliance Not Asserted**
> The Digital Personal Data Protection (DPDP) Rules were notified in November 2025. Core data-fiduciary statutory obligations commence around mid-May 2027 (~May 2027, confirm). Section 17 may exempt notified State instrumentalities for crime investigation and sovereign processing. However, ChainNetra does NOT rely on exemptions and does NOT claim legal compliance until formally certified by competent legal counsel.

---

## 1. Data Inventory

| Data Class | Data Elements | Purpose & Lawful Basis | Storage State & Protection | Access Roles |
| :--- | :--- | :--- | :--- | :--- |
| **Victim Identifiers** | Masked reference (`V****2256`), victim state, reported loss figures | Crime investigation attribution and recovery tracking | Encrypted at rest via `MultiFernet` (`victim_ref`); masked by default | Masked: All roles.<br>Unmasked: Supervisor / Admin only (mandatory logged justification). |
| **Suspect & Mule Wallets** | Cryptocurrency addresses, transaction hashes, timestamps, token amounts | Forensic blockchain tracing and VASP attribution | Public ledger data stored in relational DB; append-only audit trail | Investigator, Supervisor, Admin |
| **Investigating Officers (IO)** | Name, designation, police station, contact email/phone | Statutory freeze notice issuance and Magistrate reporting | Encrypted at rest (`EncryptedString`); access restricted | Case IO, Supervisor, Admin |
| **VASP Compliance Contacts** | Exchange names, registered FIU entity IDs, nodal officer emails | Outbound statutory freeze notices and preservation requests | Relational DB (`entities.properties`) | Investigator, Supervisor, Admin |
| **Audit Trails & PII Logs** | User emails, timestamps, unmasking justifications, SHA-256 hashes | Evidentiary integrity and compliance accountability | Cryptographically chained audit logs with HMAC-SHA256 | Supervisor, Admin |

---

## 2. Access Control & Separation of Duties

- **Default Masking**: All personal identifiers (`victim_name`, `victim_ref`, IO contact details) are masked by default across API endpoints, UI screens, PDF evidence reports, and server logs.
- **Unmasking Authorization**: Unmasking is restricted to `Supervisor` and `Admin` roles. Any unmasking request requires a mandatory non-empty `reason` string and is immutably logged to `pii_access_logs`.
- **Log Scrubbing**: A dedicated `PIIRedactionFilter` intercepts application and debug logs, stripping 12-digit Aadhaar patterns, 10-digit Indian phone numbers, and personal email addresses.

---

## 3. Retention & Automated Purge Policy

- **Retention Windows**: As recorded in `docs/research/decisions.md`, specific retention periods per data class have not yet been approved by project leadership. The system therefore defaults to **"no automatic purge"** and emits a warning at startup.
- **Legal Hold**: Records flagged with `legal_hold = True` are exempted from all automated deletion and anonymization routines to preserve court admissibility.
- **Purge Actions**: When automated purging is executed, records are anonymized (scrubbing personal references and notes) and the action is recorded in the immutable audit log.

---

## 4. Personal Data Breach Response Runbook

In the event of a suspected or confirmed compromise of personal data:

1. **Immediate Containment**:
   - Rotate `PII_FERNET_KEYS` using MultiFernet key rotation.
   - Invalidate compromised user sessions and refresh tokens via `revoked_tokens`.
2. **Investigation & Assessment**:
   - Assess scope of compromised records from `audit_logs` and `pii_access_logs`.
3. **Statutory Notification Timelines**:
   - **Data Protection Board of India (DPBI)**: Mandatory notice within statutory window (*timeline to be confirmed against notified DPDP Rules; placeholder: within prescribed notification hours*).
   - **Affected Data Principals (Victims/Signatories)**: Inform without undue delay as required by DPDP rules.
4. **Emergency Contacts**:
   - **Data Protection Officer (DPO) Placeholder**: `[dpo-contact@chainnetra.internal - TODO: Appoint DPO]`
   - **State Cyber Command / CERT-In Liaison**: `[cert-liaison@statepolice.gov.in - TODO: Confirm contact]`
   - **Legal Counsel**: `[legal-counsel@chainnetra.internal - TODO: Assign legal review]`
