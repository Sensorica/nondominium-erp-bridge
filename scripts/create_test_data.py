#!/usr/bin/env python3
"""Create mock ERP products as Nondominium resources via hc-http-gw.

Usage:
    1. Start the conductor + gateway (see scripts/setup_conductor.sh)
    2. Set HC_DNA_HASH in .env
    3. python scripts/create_test_data.py
"""

from __future__ import annotations

import sys

from bridge.config import GatewayConfig
from bridge.erp_mock import MockERPClient
from bridge.gateway_client import GatewayError, HolochainGatewayClient
from bridge.mapper import product_to_economic_resource, product_to_resource_spec


def main() -> int:
    config = GatewayConfig.from_env()
    if not config.dna_hash:
        print("ERROR: HC_DNA_HASH not set. Run setup_conductor.sh and set it in .env")
        return 1

    client = HolochainGatewayClient(config)
    erp = MockERPClient()

    print(f"Gateway: {config.url}")
    print(f"Creating resources from {len(erp.get_available_products())} mock ERP products...")
    print()

    for product in erp.get_available_products():
        print(f"  Product: {product.name}")

        # 1. Create ResourceSpecification
        spec_input = product_to_resource_spec(product)
        try:
            spec_result = client.create_resource_specification(spec_input)
            print(f"    Spec created:     {spec_result.spec_hash}")
        except GatewayError as e:
            print(f"    ERROR creating spec: {e}")
            continue

        # 2. Create EconomicResource linked to the spec
        resource_input = product_to_economic_resource(product, spec_result.spec_hash)
        try:
            resource_result = client.create_economic_resource(resource_input)
            print(f"    Resource created: {resource_result.resource_hash}")
            print(
                f"    Quantity: {resource_result.resource.quantity} {resource_result.resource.unit}"
            )
        except GatewayError as e:
            print(f"    ERROR creating resource: {e}")
            continue

        print()

    print("Done!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
