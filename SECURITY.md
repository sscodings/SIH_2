# Security Policy & Architecture

## Security Overview
ChainNetra is a real-time cryptocurrency forensic attribution and evidence platform designed for law enforcement agencies. Given the sensitivity of financial intelligence, legal freeze workflows, and forensic chain-of-custody data, strict security controls and cryptographic integrity guarantees are enforced at all application layers.

---

## Role Matrix & Access Control
ChainNetra implements strict Role-Based Access Control (RBAC) with a hierarchical role matrix:
- **Admin**: Full administrative authority over platform configuration, users, webhooks, and label repositories.
- **Supervisor**: Supervisory authority over freeze order approvals, dispatch, analytics, and cryptographic audit logs.
- **Investigator**: Case management, multi-chain tracing, note taking, and draft preparation.

| Capability / Resource | Investigator | Supervisor | Admin |
|---|:---:|:---:|:---:|
| `cases:read`, `cases:write` | ✅ | ✅ | ✅ |
| `traces:run`, `traces:cancel` | ✅ | ✅ | ✅ |
| `notes:write` | ✅ | ✅ | ✅ |
| `freeze:draft` (Create draft) | ✅ | ✅ | ✅ |
| `reports:generate`, `reports:read` | ✅ | ✅ | ✅ |
| `complaints:read`, `complaints:write` | ✅ | ✅ | ✅ |
| `wallets:read`, `entities:read` | ✅ | ✅ | ✅ |
| `watchlist:read`, `watchlist:write` | ✅ | ✅ | ✅ |
| `alerts:read`, `alerts:ack` | ✅ | ✅ | ✅ |
| `freeze:approve`, `freeze:reject` | ❌ | ✅ | ✅ |
| `freeze:send`, `freeze:finalize` | ❌ | ✅ | ✅ |
| `analytics:read` | ❌ | ✅ | ✅ |
| `audit:read`, `audit:verify` | ❌ | ✅ | ✅ |
| `labels:write`, `labels:delete` | ❌ | ❌ | ✅ |
| `settings:read`, `settings:write` | ❌ | ❌ | ✅ |
| `webhooks:manage`, `webhooks:test` | ❌ | ❌ | ✅ |
| `users:manage`, `api_keys:manage` | ❌ | ❌ | ✅ |

### Separation of Duties
- **Freeze Orders**: The investigator who drafts a freeze request is strictly forbidden from approving or rejecting that request (`403 Forbidden`). Only a distinct supervisor or administrator can approve/reject.

---

## Secrets & Authentication Management
- **Token Lifecycles**: Short-lived JWT Access Tokens (30 minutes) with random `jti` identifiers checked against a revocation table on every request.
- **Refresh Token Rotation**: Refresh tokens are stored hashed (SHA-256) in the database and delivered in `HttpOnly`, `SameSite=Strict`, `Secure` cookies. Used refresh tokens are immediately revoked upon rotation.
- **Brute Force Protection**: Account lockout (15 minutes) and rate limiting after 5 consecutive failed login attempts.
- **Environment Modes**:
  - `MODE=DEMO`: Generates ephemeral random secrets at startup with clear warnings.
  - `MODE=LIVE`: Refuses to start if `SECRET_KEY`, `WEBHOOK_SECRET`, or `AUDIT_HMAC_KEY` are missing, shorter than 32/16 bytes, or match known demo keys.

---

## Cryptographic Audit Trail & Tamper Evidence
- Every administrative change, login, case creation, trace, and freeze state transition is written to an append-only audit log.
- **Linear Hash Chain**: Entries form a cryptographic SHA-256 hash chain where `entry_hash = SHA256(prev_hash | timestamp | user | action | entity | details)`.
- **HMAC Signatures**: Each entry is signed with HMAC-SHA256 using `AUDIT_HMAC_KEY`, preventing database tampering by unauthorized parties.
- **Database Immutability Triggers**: SQLite engine triggers prevent `UPDATE` or `DELETE` operations on `audit_logs`.
- **Checkpoints**: Periodic signed checkpoints (`AuditCheckpoint`) are generated every N entries for external anchoring.

---

## Webhook Security & SSRF Protection
- **Anti-SSRF Validation**: Webhook URLs are validated at creation and dispatch against private, loopback, link-local, and cloud metadata IP ranges (`127.0.0.0/8`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `169.254.0.0/16`, `::1`, `fc00::/7`).
- **DNS Rebinding & Redirect Protection**: Connect-time IP resolution and `follow_redirects=False`.
- **Replay Protection**: Webhook payloads are signed with HMAC-SHA256 and sent with `X-ChainNetra-Timestamp` and `X-ChainNetra-Signature` headers.

---

## Reporting Vulnerabilities
If you discover a security vulnerability in ChainNetra, please report it immediately to the security team:
- **Email**: `security@chainnetra.gov.in` / `compliance@chainnetra.local`
- **PGP Key**: Available upon request.
- Please do not disclose vulnerabilities publicly until a patch has been released.
