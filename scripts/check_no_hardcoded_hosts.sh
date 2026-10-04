#!/usr/bin/env bash
# Hygiene check: Fails if 'localhost', '127.0.0.1', or ':8000' appears in frontend/src/

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TARGET_DIR="${REPO_ROOT}/frontend/src"

echo "Checking for hardcoded API hosts in ${TARGET_DIR}..."

VIOLATIONS=$(grep -rnE "(localhost|127\.0\.0\.1|:8000)" "${TARGET_DIR}" || true)

if [ -n "${VIOLATIONS}" ]; then
    echo "ERROR: Hardcoded host violations detected in frontend/src/:"
    echo "${VIOLATIONS}"
    echo "All frontend API and WebSocket URLs must use src/lib/config.ts."
    exit 1
fi

echo "PASSED: Zero hardcoded host violations found in frontend/src/."
exit 0
