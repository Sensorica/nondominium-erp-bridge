#!/usr/bin/env python3
"""Sync ERP inventory to Nondominium via hc-http-gw.

Usage:
    1. Start the conductor + gateway (see scripts/setup_conductor.sh)
    2. Set HC_DNA_HASH in .env
    3. python scripts/sync_inventory.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from bridge.config import GatewayConfig
from bridge.erp_mock import MockERPClient
from bridge.gateway_client import HolochainGatewayClient
from bridge.sync import NondominiumBridge


def main() -> int:
    config = GatewayConfig.from_env()
    if not config.dna_hash:
        print("ERROR: HC_DNA_HASH not set. Run setup_conductor.sh and set it in .env")
        return 1

    gateway = HolochainGatewayClient(config)
    erp = MockERPClient()
    bridge = NondominiumBridge(
        erp_client=erp,
        gateway_client=gateway,
        state_path=Path(".sync_state.json"),
    )

    print(f"Gateway: {config.url}")
    print(f"Products available: {len(erp.get_available_products())}")
    print()

    result = bridge.sync_inventory()

    print(f"Specs created:     {result.specs_created}")
    print(f"Resources created: {result.resources_created}")
    print(f"Skipped:           {result.skipped}")
    if result.errors:
        print(f"Errors:            {len(result.errors)}")
        for err in result.errors:
            print(f"  - {err}")
    else:
        print("Errors:            0")

    print()
    print("Done!")
    return 1 if result.errors else 0


if __name__ == "__main__":
    sys.exit(main())
