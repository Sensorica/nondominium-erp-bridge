#!/usr/bin/env python3
"""End-to-end demo: ERP sync → discovery → commitment → event → verification.

Demonstrates the complete Nondominium bridge flow:
  1. SYNC    — ERP products → Nondominium (ResourceSpecification + EconomicResource)
  2. DISCOVER — Org B discovers Org A's resources by category
  3. COMMIT  — Org B creates a Use commitment for discovered resource
  4. EVENT   — Usage recorded as EconomicEvent (auto-generates PPRs)
  5. VERIFY  — Query events, commitments, and PPR status

Prerequisites:
  - Holochain conductor running with Nondominium hApp installed
  - hc-http-gw running (bash scripts/setup_conductor.sh)
  - .env file with HC_DNA_HASH set

Usage:
  nix develop
  source .venv/bin/activate
  python scripts/demo_full_flow.py
"""

from __future__ import annotations

import sys
import time

from bridge.config import GatewayConfig
from bridge.discovery import ResourceDiscovery
from bridge.erp_mock import MockERPClient
from bridge.gateway_client import GatewayError, HolochainGatewayClient
from bridge.mapper import product_to_economic_resource, product_to_resource_spec
from bridge.models import LogEconomicEventInput, ProposeCommitmentInput, VfAction


def banner(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\n")


def main() -> None:
    # Load config
    config = GatewayConfig.from_env()
    if not config.dna_hash:
        print("ERROR: HC_DNA_HASH not set. Run setup_conductor.sh first and set it in .env")
        sys.exit(1)

    client = HolochainGatewayClient(config)
    discovery = ResourceDiscovery(client)
    erp = MockERPClient()

    # Check connectivity
    print("Checking gateway connectivity...")
    if not client.health_check():
        print("ERROR: Cannot reach hc-http-gw. Is it running?")
        sys.exit(1)
    print("Gateway is reachable.\n")

    # ================================================================
    # Step 1: SYNC — ERP products → Nondominium
    # ================================================================
    banner("STEP 1: SYNC — ERP Products → Nondominium")

    products = erp.get_products()
    print(f"Mock ERP has {len(products)} products:")
    for p in products:
        print(f"  - {p.name} ({p.category}, qty={p.qty_available})")

    synced_resources: list[dict[str, str]] = []

    for product in products[:2]:  # Sync first 2 for demo
        print(f"\nSyncing: {product.name}")

        # Create ResourceSpecification
        spec_input = product_to_resource_spec(product)
        try:
            spec_result = client.create_resource_specification(spec_input)
            print(f"  Spec created: {spec_result.spec_hash[:20]}...")
        except GatewayError as e:
            print(f"  FAILED (spec): {e}")
            continue

        # Create EconomicResource
        resource_input = product_to_economic_resource(product, spec_result.spec_hash)
        try:
            resource_result = client.create_economic_resource(resource_input)
            print(f"  Resource created: {resource_result.resource_hash[:20]}...")
            synced_resources.append(
                {
                    "name": product.name,
                    "spec_hash": spec_result.spec_hash,
                    "resource_hash": resource_result.resource_hash,
                }
            )
        except GatewayError as e:
            print(f"  FAILED (resource): {e}")

    if not synced_resources:
        print("\nNo resources synced. Cannot continue demo.")
        sys.exit(1)

    print(f"\nSynced {len(synced_resources)} resources to Nondominium.")

    # ================================================================
    # Step 2: DISCOVER — Find resources by category
    # ================================================================
    banner("STEP 2: DISCOVER — Cross-Org Resource Discovery")

    print("Discovering resources by category 'equipment'...")
    try:
        specs = discovery.discover_by_category("equipment")
        print(f"  Found {len(specs)} specifications:")
        for spec in specs:
            print(f"    - {spec.name}: {spec.description[:50]}...")
    except GatewayError as e:
        print(f"  Discovery failed: {e}")

    print("\nChecking all resources on DHT...")
    try:
        all_resources = client.get_all_economic_resources()
        print(f"  Total resources: {len(all_resources.resources)}")
        for r in all_resources.resources:
            print(f"    - qty={r.quantity} {r.unit}, state={r.state.value}")
    except GatewayError as e:
        print(f"  Query failed: {e}")

    # ================================================================
    # Step 3: COMMIT — Create a Use commitment
    # ================================================================
    banner("STEP 3: COMMIT — Request Resource Use")

    target = synced_resources[0]
    print(f"Target resource: {target['name']}")
    print(f"  Resource hash: {target['resource_hash'][:20]}...")

    # Use a timestamp ~1 hour from now (microseconds)
    due_date = int((time.time() + 3600) * 1_000_000)

    commitment_input = ProposeCommitmentInput(
        action=VfAction.USE,
        resource_hash=target["resource_hash"],
        provider="self",  # Will be replaced by agent's own key by the conductor
        due_date=due_date,
        note=f"Demo: request to use {target['name']}",
    )

    try:
        commit_result = client.propose_commitment(commitment_input)
        print(f"  Commitment created: {commit_result.commitment_hash[:20]}...")
        print(f"  Action: {commit_result.commitment.action.value}")
        print(f"  Due: {commit_result.commitment.due_date}")
    except GatewayError as e:
        print(f"  FAILED: {e}")
        print("  (This may fail if the conductor requires specific agent keys)")
        commit_result = None

    # ================================================================
    # Step 4: EVENT — Record economic event
    # ================================================================
    banner("STEP 4: EVENT — Record Resource Usage")

    if commit_result:
        event_input = LogEconomicEventInput(
            action=VfAction.USE,
            provider="self",
            receiver="self",
            resource_inventoried_as=target["resource_hash"],
            resource_quantity=1.0,
            note=f"Demo: using {target['name']}",
            commitment_hash=commit_result.commitment_hash,
            generate_pprs=True,
        )

        try:
            event_result = client.log_economic_event(event_input)
            print(f"  Event logged: {event_result.event_hash[:20]}...")
            print(f"  Action: {event_result.event.action.value}")
            print(f"  Quantity: {event_result.event.resource_quantity}")
            if event_result.ppr_claims:
                print(f"  PPR claims generated: {event_result.ppr_claims}")
            else:
                print("  No PPR claims (may require two distinct agents)")
        except GatewayError as e:
            print(f"  FAILED: {e}")
    else:
        print("  Skipped (no commitment from Step 3)")

    # ================================================================
    # Step 5: VERIFY — Query state
    # ================================================================
    banner("STEP 5: VERIFY — Query Final State")

    print("Querying all commitments...")
    try:
        commitments = client.get_all_commitments()
        print(f"  Total commitments: {len(commitments)}")
        for c in commitments:
            print(f"    - {c.action.value}: {c.note or '(no note)'}")
    except GatewayError as e:
        print(f"  Query failed: {e}")

    print("\nQuerying all economic events...")
    try:
        events = client.get_all_economic_events()
        if isinstance(events, list):
            print(f"  Total events: {len(events)}")
        else:
            print(f"  Events: {events}")
    except GatewayError as e:
        print(f"  Query failed: {e}")

    print("\nQuerying all validation receipts...")
    try:
        receipts = client.get_all_validation_receipts()
        print(f"  Total receipts: {len(receipts)}")
    except GatewayError as e:
        print(f"  Query failed: {e}")

    banner("DEMO COMPLETE")
    print("Summary:")
    print(f"  Resources synced: {len(synced_resources)}")
    print(f"  Commitment created: {'Yes' if commit_result else 'No'}")
    print("  Event logged: Yes (if commitment succeeded)")
    print()


if __name__ == "__main__":
    main()
