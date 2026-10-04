#!/usr/bin/env python3
"""
Standalone Forensic Audit Tamper Simulation Script.
Modifies a target SQLite DB directly without going through the application.
Used strictly for offline demo verification of tamper detection.
"""

import sys
import os
import sqlite3
import json

def simulate_tamper(db_path: str):
    if not os.path.exists(db_path):
        print(f"Error: Target database not found at {db_path}")
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT id, entry_hash, details FROM audit_logs ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    if not row:
        print("No audit log entries found to tamper with.")
        conn.close()
        sys.exit(1)

    log_id, entry_hash, details = row
    print(f"Original Entry #{log_id} Hash: {entry_hash}")
    print(f"Original Details: {details}")

    tampered_details = json.dumps({"tampered": True, "illegal_override": "Modified by unauthorized attacker directly in DB"})
    cursor.execute("UPDATE audit_logs SET details = ? WHERE id = ?", (tampered_details, log_id))
    conn.commit()
    conn.close()

    print(f"Successfully simulated offline database tampering on entry #{log_id}.")
    print("When verified via the API or audit verifier, tamper detection will trigger.")

if __name__ == "__main__":
    target_db = sys.argv[1] if len(sys.argv) > 1 else "chainnetra.db"
    simulate_tamper(target_db)
