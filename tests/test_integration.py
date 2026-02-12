"""Integration tests against a live Holochain conductor + hc-http-gw.

These tests require real infrastructure:
    1. nix develop
    2. bash scripts/setup_conductor.sh   (conductor + gateway)
    3. Set HC_DNA_HASH in .env

Run with:
    pytest -m integration          # only integration tests
    pytest -m "not integration"    # skip them (default)
"""

from __future__ import annotations

import uuid

import pytest

from bridge.config import GatewayConfig
from bridge.erp_mock import MockERPClient
from bridge.gateway_client import GatewayError, HolochainGatewayClient
from bridge.models import (
    EconomicResourceInput,
    ResourceSpecificationInput,
    ResourceState,
    UpdateResourceStateInput,
)
from bridge.sync import NondominiumBridge

pytestmark = pytest.mark.integration


def _uid() -> str:
    """Short unique suffix to avoid collisions across test runs."""
    return uuid.uuid4().hex[:8]


# --- Fixtures ---


@pytest.fixture(scope="module")
def config() -> GatewayConfig:
    cfg = GatewayConfig.from_env()
    if not cfg.dna_hash:
        pytest.skip("HC_DNA_HASH not set — no live conductor available")
    return cfg


@pytest.fixture(scope="module")
def client(config: GatewayConfig) -> HolochainGatewayClient:
    return HolochainGatewayClient(config)


@pytest.fixture(scope="module")
def live_check(client: HolochainGatewayClient) -> None:
    """Skip the entire module if the gateway is unreachable."""
    if not client.health_check():
        pytest.skip("hc-http-gw not reachable — is the conductor running?")


# --- Gateway connectivity ---


class TestGatewayConnectivity:
    def test_health_check(self, live_check: None, client: HolochainGatewayClient):
        assert client.health_check() is True


# --- ResourceSpecification CRUD ---


class TestResourceSpecification:
    def test_create_and_get_all(self, live_check: None, client: HolochainGatewayClient):
        """Create a spec and verify it appears in the list."""
        tag = _uid()
        spec_input = ResourceSpecificationInput(
            name=f"Integration Test Spec {tag}",
            description="Created by test_integration.py",
            category="test-equipment",
            tags=[f"integration-{tag}"],
        )

        output = client.create_resource_specification(spec_input)
        assert output.spec_hash, "Expected a non-empty spec_hash"
        assert output.spec.name == spec_input.name
        assert output.spec.category == "test-equipment"

        # Verify it's now in the full list
        all_specs = client.get_all_resource_specifications()
        names = [s.name for s in all_specs.specifications]
        assert spec_input.name in names

    def test_get_latest(self, live_check: None, client: HolochainGatewayClient):
        """Create a spec and retrieve it by hash."""
        tag = _uid()
        spec_input = ResourceSpecificationInput(
            name=f"Latest Test Spec {tag}",
            description="For get_latest test",
            category="test-equipment",
        )

        created = client.create_resource_specification(spec_input)
        retrieved = client.get_latest_resource_specification(created.spec_hash)

        assert retrieved.name == spec_input.name
        assert retrieved.description == spec_input.description

    def test_get_with_rules(self, live_check: None, client: HolochainGatewayClient):
        """Create a spec and retrieve it with governance rules."""
        tag = _uid()
        spec_input = ResourceSpecificationInput(
            name=f"Rules Test Spec {tag}",
            description="For get_with_rules test",
            category="test-equipment",
        )

        created = client.create_resource_specification(spec_input)
        result = client.get_resource_specification_with_rules(created.spec_hash)

        assert result.specification.name == spec_input.name
        assert isinstance(result.governance_rules, list)


# --- EconomicResource CRUD ---


class TestEconomicResource:
    def test_create_linked_to_spec(self, live_check: None, client: HolochainGatewayClient):
        """Create a spec, then a resource linked to it."""
        tag = _uid()

        # Create spec first
        spec_output = client.create_resource_specification(
            ResourceSpecificationInput(
                name=f"Resource Test Spec {tag}",
                description="Parent spec for resource test",
                category="test-equipment",
            )
        )

        # Create resource linked to the spec
        resource_input = EconomicResourceInput(
            spec_hash=spec_output.spec_hash,
            quantity=3.0,
            unit="unit",
        )
        resource_output = client.create_economic_resource(resource_input)

        assert resource_output.resource_hash, "Expected a non-empty resource_hash"
        assert resource_output.resource.quantity == 3.0
        assert resource_output.resource.unit == "unit"
        assert resource_output.resource.state == ResourceState.PENDING_VALIDATION

    def test_get_all_resources(self, live_check: None, client: HolochainGatewayClient):
        """Create a resource and verify it appears in the list."""
        tag = _uid()

        spec_output = client.create_resource_specification(
            ResourceSpecificationInput(
                name=f"GetAll Resource Spec {tag}",
                description="For get_all test",
                category="test-consumable",
            )
        )
        client.create_economic_resource(
            EconomicResourceInput(
                spec_hash=spec_output.spec_hash,
                quantity=5.0,
                unit="kg",
            )
        )

        all_resources = client.get_all_economic_resources()
        assert len(all_resources.resources) >= 1

    def test_get_latest_resource(self, live_check: None, client: HolochainGatewayClient):
        """Create a resource and retrieve it by hash."""
        tag = _uid()

        spec_output = client.create_resource_specification(
            ResourceSpecificationInput(
                name=f"Latest Resource Spec {tag}",
                description="For get_latest_resource test",
                category="test-equipment",
            )
        )
        created = client.create_economic_resource(
            EconomicResourceInput(
                spec_hash=spec_output.spec_hash,
                quantity=1.0,
                unit="unit",
            )
        )

        retrieved = client.get_latest_economic_resource(created.resource_hash)
        assert retrieved.quantity == 1.0
        assert retrieved.unit == "unit"


# --- State transitions ---


class TestResourceState:
    def test_update_state(self, live_check: None, client: HolochainGatewayClient):
        """Create a resource and transition its state."""
        tag = _uid()

        spec_output = client.create_resource_specification(
            ResourceSpecificationInput(
                name=f"State Test Spec {tag}",
                description="For state transition test",
                category="test-equipment",
            )
        )
        resource_output = client.create_economic_resource(
            EconomicResourceInput(
                spec_hash=spec_output.spec_hash,
                quantity=1.0,
                unit="unit",
            )
        )
        assert resource_output.resource.state == ResourceState.PENDING_VALIDATION

        # Transition to Active
        client.update_resource_state(
            UpdateResourceStateInput(
                resource_hash=resource_output.resource_hash,
                new_state=ResourceState.ACTIVE,
            )
        )

        updated = client.get_latest_economic_resource(resource_output.resource_hash)
        assert updated.state == ResourceState.ACTIVE


# --- Full sync pipeline ---


class TestSyncPipeline:
    def test_sync_inventory_live(self, live_check: None, client: HolochainGatewayClient, tmp_path):
        """Run the full sync pipeline against a live conductor."""
        bridge = NondominiumBridge(
            erp_client=MockERPClient(),
            gateway_client=client,
            state_path=tmp_path / "sync_state.json",
        )

        result = bridge.sync_inventory()

        assert result.specs_created == 4
        assert result.resources_created == 4
        assert result.skipped == 0
        assert result.errors == []

    def test_sync_idempotency_live(
        self, live_check: None, client: HolochainGatewayClient, tmp_path
    ):
        """Second sync with same state file should skip everything."""
        state_path = tmp_path / "sync_state.json"
        bridge = NondominiumBridge(
            erp_client=MockERPClient(),
            gateway_client=client,
            state_path=state_path,
        )

        result1 = bridge.sync_inventory()
        assert result1.specs_created == 4

        result2 = bridge.sync_inventory()
        assert result2.specs_created == 0
        assert result2.skipped == 4
        assert result2.errors == []


# --- Error handling ---


class TestErrorHandling:
    def test_bad_hash_raises(self, live_check: None, client: HolochainGatewayClient):
        """Requesting a non-existent hash should raise GatewayError."""
        with pytest.raises(GatewayError):
            client.get_latest_resource_specification("uhCkkInvalidHashThatDoesNotExist")
