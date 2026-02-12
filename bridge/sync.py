"""Inventory sync pipeline: ERP products -> Nondominium resources.

Orchestrates the full sync flow:
1. Get available products from ERP
2. Skip already-synced products (idempotency via SyncState)
3. Map -> create spec -> map -> create resource (per product)
4. Handle errors per-item (continue on failure)
5. Persist sync state and return SyncResult
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from bridge.erp_mock import MockERPClient, MockProduct
from bridge.gateway_client import GatewayError, HolochainGatewayClient
from bridge.mapper import product_to_economic_resource, product_to_resource_spec

logger = logging.getLogger(__name__)


@dataclass
class SyncResult:
    """Outcome of a sync run."""

    specs_created: int = 0
    resources_created: int = 0
    skipped: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def total_processed(self) -> int:
        return self.specs_created + self.skipped + len(self.errors)


class SyncState:
    """JSON-file persistence mapping product_id -> (spec_hash, resource_hash).

    Provides idempotency: products already synced are skipped on subsequent runs.
    """

    def __init__(self, path: Path) -> None:
        self._path = path
        self._data: dict[str, dict[str, str]] = {}
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            self._data = json.loads(self._path.read_text())

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(self._data, indent=2))

    def is_synced(self, product_id: int) -> bool:
        return str(product_id) in self._data

    def record(self, product_id: int, spec_hash: str, resource_hash: str) -> None:
        self._data[str(product_id)] = {
            "spec_hash": spec_hash,
            "resource_hash": resource_hash,
        }

    def get_entry(self, product_id: int) -> dict[str, str] | None:
        return self._data.get(str(product_id))

    def as_dict(self) -> dict[str, Any]:
        return dict(self._data)


class NondominiumBridge:
    """Composes ERP client + gateway client + mapper into a sync pipeline."""

    def __init__(
        self,
        erp_client: MockERPClient,
        gateway_client: HolochainGatewayClient,
        state_path: Path | None = None,
    ) -> None:
        self.erp = erp_client
        self.gateway = gateway_client
        self.state = SyncState(state_path or Path(".sync_state.json"))

    def sync_inventory(self) -> SyncResult:
        """Sync all available ERP products to Nondominium.

        Returns a SyncResult summarizing what happened.
        """
        result = SyncResult()
        products = self.erp.get_available_products()

        for product in products:
            self._sync_product(product, result)

        self.state.save()
        return result

    def _sync_product(self, product: MockProduct, result: SyncResult) -> None:
        """Sync a single product. Updates result in-place."""
        if self.state.is_synced(product.id):
            logger.info("Skipping already-synced product %d: %s", product.id, product.name)
            result.skipped += 1
            return

        # Create ResourceSpecification
        spec_input = product_to_resource_spec(product)
        try:
            spec_output = self.gateway.create_resource_specification(spec_input)
        except GatewayError as exc:
            msg = f"Product {product.id} ({product.name}): spec creation failed: {exc}"
            logger.error(msg)
            result.errors.append(msg)
            return

        result.specs_created += 1
        spec_hash = spec_output.spec_hash

        # Create EconomicResource linked to the spec
        resource_input = product_to_economic_resource(product, spec_hash)
        try:
            resource_output = self.gateway.create_economic_resource(resource_input)
        except GatewayError as exc:
            msg = f"Product {product.id} ({product.name}): resource creation failed: {exc}"
            logger.error(msg)
            result.errors.append(msg)
            return

        result.resources_created += 1
        self.state.record(product.id, spec_hash, resource_output.resource_hash)
        logger.info(
            "Synced product %d (%s): spec=%s resource=%s",
            product.id,
            product.name,
            spec_hash,
            resource_output.resource_hash,
        )
