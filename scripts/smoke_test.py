#!/usr/bin/env python3
"""Smoke test against a live hc-http-gw instance.

Usage:
    1. Start the conductor + gateway (see scripts/setup_conductor.sh)
    2. Set HC_DNA_HASH in .env
    3. python scripts/smoke_test.py
"""

from __future__ import annotations

import sys

from bridge.config import GatewayConfig
from bridge.gateway_client import GatewayError, HolochainGatewayClient
from bridge.models import ResourceSpecificationInput


def main() -> int:
    config = GatewayConfig.from_env()
    if not config.dna_hash:
        print("ERROR: HC_DNA_HASH not set. Run setup_conductor.sh and set it in .env")
        return 1

    client = HolochainGatewayClient(config)
    print(f"Gateway: {config.url}")
    print(f"DNA hash: {config.dna_hash}")
    print(f"App ID: {config.app_id}")
    print()

    # 1. Health check
    print("1. Health check...")
    try:
        healthy = client.health_check()
        print(f"   Gateway reachable: {healthy}")
        if not healthy:
            print("   ERROR: Gateway not reachable. Is hc-http-gw running?")
            return 1
    except Exception as e:
        print(f"   ERROR: {e}")
        return 1

    # 2. Read all resource specifications
    print("2. Reading all resource specifications...")
    try:
        specs = client.get_all_resource_specifications()
        print(f"   Found {len(specs.specifications)} specifications")
        for spec in specs.specifications:
            print(f"   - {spec.name} [{spec.category}]")
    except GatewayError as e:
        print(f"   ERROR: {e}")
        return 1

    # 3. Create a test resource specification
    print("3. Creating test resource specification...")
    try:
        result = client.create_resource_specification(
            ResourceSpecificationInput(
                name="Smoke Test Item",
                description="Created by smoke_test.py",
                category="test",
                tags=["smoke-test"],
            )
        )
        print(f"   Created: {result.spec.name} (hash: {result.spec_hash})")
    except GatewayError as e:
        print(f"   ERROR: {e}")
        return 1

    # 4. Read all economic resources
    print("4. Reading all economic resources...")
    try:
        resources = client.get_all_economic_resources()
        print(f"   Found {len(resources.resources)} resources")
        for res in resources.resources:
            print(f"   - {res.quantity} {res.unit} [{res.state.value}]")
    except GatewayError as e:
        print(f"   ERROR: {e}")
        return 1

    print()
    print("Smoke test passed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
