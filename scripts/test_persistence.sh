#!/usr/bin/env bash
# Hygiene check F3: Tests Docker volume persistence across container restarts.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${REPO_ROOT}"

echo "=== Docker Volume Persistence Test ==="

# Check docker availability
if ! command -v docker &> /dev/null; then
    echo "Docker not available in current environment; skipping live execution."
    exit 0
fi

echo "1. Bringing up docker compose stack..."
docker compose up -d --build

echo "Waiting for backend service to become healthy..."
sleep 15

# Authenticate
echo "2. Authenticating as admin..."
LOGIN_RES=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin@demo","password":"demo123"}')
TOKEN=$(echo "${LOGIN_RES}" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "${TOKEN}" ]; then
    echo "Failed to authenticate against local Docker backend: ${LOGIN_RES}"
    docker compose down
    exit 1
fi

echo "3. Creating persistence test case..."
CASE_RES=$(curl -s -X POST "http://localhost:8000/api/v1/cases" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"title":"Docker Persistence Verification Case","primary_chain":"tron","primary_address":"TVssLZco7KSwkQ3NwsuwQPRxUVjXfVwYY2","priority":"High"}')

CASE_NUM=$(echo "${CASE_RES}" | grep -o '"case_number":"[^"]*' | cut -d'"' -f4)
echo "Created case: ${CASE_NUM}"

echo "4. Stopping containers with 'docker compose down' (preserving volumes)..."
docker compose down

echo "5. Restarting containers..."
docker compose up -d

echo "Waiting for services to become healthy again..."
sleep 15

echo "6. Re-authenticating..."
LOGIN_RES_2=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin@demo","password":"demo123"}')
TOKEN_2=$(echo "${LOGIN_RES_2}" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

echo "7. Verifying case still exists..."
CASES_LIST=$(curl -s -X GET "http://localhost:8000/api/v1/cases" -H "Authorization: Bearer ${TOKEN_2}")

if echo "${CASES_LIST}" | grep -q "${CASE_NUM}"; then
    echo "SUCCESS: Case ${CASE_NUM} persisted across container restarts!"
else
    echo "FAILURE: Case ${CASE_NUM} was lost after container restart."
    docker compose down
    exit 1
fi

echo "Cleaning up..."
docker compose down

echo "PASSED: Docker volume persistence verified."
exit 0
