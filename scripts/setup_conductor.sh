#!/usr/bin/env bash
# Setup a Holochain sandbox conductor with Nondominium hApp and hc-http-gw.
#
# Prerequisites:
#   - Nix dev shell: nix develop (from the bridge repo root)
#   - nondominium.happ built: cd ../nondominium && npm run build:happ
#
# Usage:
#   nix develop   # if not already in the dev shell
#   bash scripts/setup_conductor.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
NONDOMINIUM_DIR="${PROJECT_DIR}/../nondominium"
HAPP_PATH="${NONDOMINIUM_DIR}/workdir/nondominium.happ"
SANDBOX_DIR="${PROJECT_DIR}/.local/sandbox"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=== Nondominium ERP Bridge - Conductor Setup ===${NC}"
echo

# 1. Check prerequisites
echo "Checking prerequisites..."

if ! command -v holochain &>/dev/null; then
    echo -e "${RED}ERROR: 'holochain' not found. Enter the Nix dev shell first:${NC}"
    echo "  nix develop"
    exit 1
fi

if ! command -v hc &>/dev/null; then
    echo -e "${RED}ERROR: 'hc' CLI not found.${NC}"
    exit 1
fi

if [ ! -f "$HAPP_PATH" ]; then
    echo -e "${RED}ERROR: nondominium.happ not found at ${HAPP_PATH}${NC}"
    echo "Build it first:"
    echo "  cd ${NONDOMINIUM_DIR} && npm run build:happ"
    exit 1
fi

echo -e "${GREEN}  holochain: $(holochain --version 2>/dev/null || echo 'found')${NC}"
echo -e "${GREEN}  hApp: ${HAPP_PATH}${NC}"
echo

# 2. Create sandbox
echo "Creating sandbox conductor..."

hc sandbox clean 2>/dev/null || true
rm -rf "$SANDBOX_DIR"
mkdir -p "$(dirname "$SANDBOX_DIR")"
echo "pass" | hc sandbox --piped generate "$HAPP_PATH" \
    --run 0 \
    --directories "$SANDBOX_DIR" \
    2>&1 | tee /tmp/hc-sandbox-output.txt &

CONDUCTOR_PID=$!
echo "Conductor PID: $CONDUCTOR_PID"
echo

# 3. Wait for conductor to start and discover admin WebSocket port
echo "Waiting for conductor to start..."
ADMIN_PORT=""
for i in $(seq 1 30); do
    ADMIN_PORT=$(grep -oP '"admin_port":\K[0-9]+' /tmp/hc-sandbox-output.txt 2>/dev/null | tail -1 || true)
    if [ -n "$ADMIN_PORT" ] && [ "$ADMIN_PORT" != "0" ]; then
        break
    fi
    ADMIN_PORT=""
    sleep 1
done
if [ -z "$ADMIN_PORT" ]; then
    echo -e "${RED}ERROR: Conductor did not report admin port within 30 seconds${NC}"
    echo "  Check /tmp/hc-sandbox-output.txt for errors."
    exit 1
fi
export HC_GW_ADMIN_WS_URL="ws://127.0.0.1:${ADMIN_PORT}"
echo -e "${GREEN}  Admin WS URL: ${HC_GW_ADMIN_WS_URL}${NC}"
echo

# 4. Discover DNA hash
echo -e "${YELLOW}=== IMPORTANT ===${NC}"
echo "To discover the DNA hash, run in another terminal:"
echo "  hc sandbox call list-apps --directories ${SANDBOX_DIR}"
echo
echo "Then set it in your .env file:"
echo "  HC_DNA_HASH=<the hash from the output above>"
echo

# 5. List allowed zome functions for hc-http-gw
# --- zome_resource functions ---
ALLOWED_FNS="create_resource_specification,get_all_resource_specifications"
ALLOWED_FNS="${ALLOWED_FNS},get_latest_resource_specification,get_resource_specification_with_rules"
ALLOWED_FNS="${ALLOWED_FNS},get_resource_specifications_by_category,get_resource_specifications_by_tag"
ALLOWED_FNS="${ALLOWED_FNS},get_my_resource_specifications,get_resource_specification_profile"
ALLOWED_FNS="${ALLOWED_FNS},create_economic_resource,get_all_economic_resources"
ALLOWED_FNS="${ALLOWED_FNS},get_latest_economic_resource,get_resources_by_specification"
ALLOWED_FNS="${ALLOWED_FNS},get_my_economic_resources,get_economic_resource_profile"
ALLOWED_FNS="${ALLOWED_FNS},get_agent_economic_resources,check_first_resource_requirement"
ALLOWED_FNS="${ALLOWED_FNS},transfer_custody,update_resource_state"
ALLOWED_FNS="${ALLOWED_FNS},update_resource_specification,update_economic_resource"
ALLOWED_FNS="${ALLOWED_FNS},create_governance_rule,get_all_governance_rules"
ALLOWED_FNS="${ALLOWED_FNS},get_latest_governance_rule,update_governance_rule"
ALLOWED_FNS="${ALLOWED_FNS},get_governance_rule_profile,get_my_governance_rules"
ALLOWED_FNS="${ALLOWED_FNS},get_governance_rules_by_type"

# --- zome_gouvernance functions ---
ALLOWED_FNS="${ALLOWED_FNS},propose_commitment,get_all_commitments,get_commitments_for_agent"
ALLOWED_FNS="${ALLOWED_FNS},claim_commitment,get_all_claims,get_claims_for_commitment"
ALLOWED_FNS="${ALLOWED_FNS},log_economic_event,log_initial_transfer"
ALLOWED_FNS="${ALLOWED_FNS},get_all_economic_events,get_events_for_resource,get_events_for_agent"
ALLOWED_FNS="${ALLOWED_FNS},create_validation_receipt,get_validation_history,get_all_validation_receipts"
ALLOWED_FNS="${ALLOWED_FNS},create_resource_validation,check_validation_status"
ALLOWED_FNS="${ALLOWED_FNS},issue_participation_receipts,get_my_participation_claims,derive_reputation_summary"

# 6. Start hc-http-gw
echo "Starting hc-http-gw..."
echo "  Admin WS URL: ${HC_GW_ADMIN_WS_URL}"
echo "  Allowed functions: ${ALLOWED_FNS}"
echo

if command -v hc-http-gw &>/dev/null; then
    HC_GW_ADMIN_WS_URL="$HC_GW_ADMIN_WS_URL" \
        HC_GW_ALLOWED_FNS_nondominium="$ALLOWED_FNS" \
        hc-http-gw \
        --port 8888 &
    GW_PID=$!
    echo "hc-http-gw PID: $GW_PID"
    echo
    echo -e "${GREEN}Gateway running at http://127.0.0.1:8888${NC}"
else
    echo -e "${YELLOW}hc-http-gw not found. Install with:${NC}"
    echo "  cargo install holochain_http_gateway"
    echo
    echo "Or start it manually with:"
    echo "  HC_GW_ADMIN_WS_URL=\"${HC_GW_ADMIN_WS_URL}\" HC_GW_ALLOWED_FNS_nondominium=\"${ALLOWED_FNS}\" hc-http-gw --port 8888"
fi

echo
echo -e "${GREEN}=== Setup complete ===${NC}"
echo "Conductor is running. Press Ctrl+C to stop."
echo

wait "$CONDUCTOR_PID"
