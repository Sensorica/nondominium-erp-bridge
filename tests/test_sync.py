"""Tests for the inventory sync pipeline."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pytest_httpserver import HTTPServer

from bridge.config import GatewayConfig
from bridge.erp_mock import MockERPClient
from bridge.gateway_client import HolochainGatewayClient
from bridge.sync import NondominiumBridge, SyncResult, SyncState

DNA_HASH = "uhC0kTestDnaHash"
APP_ID = "nondominium"
ZOME = "zome_resource"


def _zome_path(fn_name: str) -> str:
    return f"/{DNA_HASH}/{APP_ID}/{ZOME}/{fn_name}"


# --- Fixtures ---


@pytest.fixture()
def config(httpserver: HTTPServer) -> GatewayConfig:
    return GatewayConfig(
        url=httpserver.url_for("").rstrip("/"),
        timeout=5,
        app_id=APP_ID,
        dna_hash=DNA_HASH,
    )


@pytest.fixture()
def client(config: GatewayConfig) -> HolochainGatewayClient:
    return HolochainGatewayClient(config)


@pytest.fixture()
def state_path(tmp_path: Path) -> Path:
    return tmp_path / "sync_state.json"


@pytest.fixture()
def bridge(client: HolochainGatewayClient, state_path: Path) -> NondominiumBridge:
    return NondominiumBridge(
        erp_client=MockERPClient(),
        gateway_client=client,
        state_path=state_path,
    )


def _fake_action_hash(seed: int) -> list[int]:
    """Create a fake ActionHash byte array (mimics hc-http-gw v0.3.x response format).

    Real ActionHash is 39 bytes; we use shorter fakes since only round-trip matters.
    """
    return [132, 41, 36, seed, 0, 0]


def _fake_agent_hash() -> list[int]:
    """Fake AgentPubKey byte array."""
    return [132, 32, 36, 99, 0, 0]


def _mock_spec_response(product_id: int, name: str, category: str) -> dict:
    return {
        "spec_hash": _fake_action_hash(product_id),
        "spec": {
            "name": name,
            "description": "test",
            "category": category,
            "image_url": None,
            "tags": [],
            "is_active": True,
        },
        "governance_rule_hashes": [],
    }


def _mock_resource_response(product_id: int) -> dict:
    return {
        "resource_hash": _fake_action_hash(product_id + 100),
        "resource": {
            "quantity": 1.0,
            "unit": "unit",
            "custodian": _fake_agent_hash(),
            "state": "PendingValidation",
        },
    }


def _register_product_handlers(httpserver: HTTPServer, product_id: int, name: str, cat: str):
    """Register spec+resource creation handlers for one product."""
    httpserver.expect_ordered_request(
        _zome_path("create_resource_specification"),
    ).respond_with_json(_mock_spec_response(product_id, name, cat))
    httpserver.expect_ordered_request(
        _zome_path("create_economic_resource"),
    ).respond_with_json(_mock_resource_response(product_id))


# --- SyncState tests ---


class TestSyncState:
    def test_empty_state(self, state_path: Path):
        state = SyncState(state_path)
        assert not state.is_synced(1)
        assert state.get_entry(1) is None

    def test_record_and_retrieve(self, state_path: Path):
        state = SyncState(state_path)
        state.record(1, "specABC", "resXYZ")
        assert state.is_synced(1)
        assert state.get_entry(1) == {"spec_hash": "specABC", "resource_hash": "resXYZ"}

    def test_persistence(self, state_path: Path):
        state = SyncState(state_path)
        state.record(42, "specHash", "resHash")
        state.save()

        # Load from same path
        state2 = SyncState(state_path)
        assert state2.is_synced(42)
        assert state2.get_entry(42) == {"spec_hash": "specHash", "resource_hash": "resHash"}

    def test_save_creates_file(self, state_path: Path):
        state = SyncState(state_path)
        state.save()
        assert state_path.exists()
        assert json.loads(state_path.read_text()) == {}


# --- SyncResult tests ---


class TestSyncResult:
    def test_defaults(self):
        r = SyncResult()
        assert r.specs_created == 0
        assert r.resources_created == 0
        assert r.skipped == 0
        assert r.errors == []

    def test_total_processed(self):
        r = SyncResult(specs_created=2, skipped=1, errors=["e1"])
        assert r.total_processed == 4  # 2 + 1 + 1


# --- Full sync pipeline tests ---


class TestSyncPipeline:
    def test_full_sync(self, httpserver: HTTPServer, bridge: NondominiumBridge):
        """All 4 mock products should be synced."""
        products = bridge.erp.get_available_products()
        for p in products:
            _register_product_handlers(httpserver, p.id, p.name, p.category)

        result = bridge.sync_inventory()

        assert result.specs_created == 4
        assert result.resources_created == 4
        assert result.skipped == 0
        assert result.errors == []

    def test_idempotency(self, httpserver: HTTPServer, bridge: NondominiumBridge):
        """Second sync should skip all products."""
        products = bridge.erp.get_available_products()

        # First sync
        for p in products:
            _register_product_handlers(httpserver, p.id, p.name, p.category)
        result1 = bridge.sync_inventory()
        assert result1.specs_created == 4

        # Second sync — no new handlers needed, everything should be skipped
        result2 = bridge.sync_inventory()
        assert result2.specs_created == 0
        assert result2.resources_created == 0
        assert result2.skipped == 4
        assert result2.errors == []

    def test_state_persisted_across_instances(
        self,
        httpserver: HTTPServer,
        bridge: NondominiumBridge,
        client: HolochainGatewayClient,
        state_path: Path,
    ):
        """State file survives bridge re-instantiation."""
        products = bridge.erp.get_available_products()
        for p in products:
            _register_product_handlers(httpserver, p.id, p.name, p.category)
        bridge.sync_inventory()

        # Create a new bridge instance using same state path
        bridge2 = NondominiumBridge(
            erp_client=MockERPClient(),
            gateway_client=client,
            state_path=state_path,
        )
        result = bridge2.sync_inventory()
        assert result.skipped == 4
        assert result.specs_created == 0

    def test_partial_failure_spec(self, httpserver: HTTPServer, bridge: NondominiumBridge):
        """If spec creation fails, product is skipped with error; others continue."""
        products = bridge.erp.get_available_products()

        # First product: spec fails
        httpserver.expect_ordered_request(
            _zome_path("create_resource_specification"),
        ).respond_with_data("Internal Server Error", status=500)

        # Remaining products: succeed
        for p in products[1:]:
            _register_product_handlers(httpserver, p.id, p.name, p.category)

        result = bridge.sync_inventory()

        assert result.specs_created == 3
        assert result.resources_created == 3
        assert len(result.errors) == 1
        assert "spec creation failed" in result.errors[0]

    def test_partial_failure_resource(self, httpserver: HTTPServer, bridge: NondominiumBridge):
        """If resource creation fails after spec, error recorded; others continue."""
        products = bridge.erp.get_available_products()

        # First product: spec ok, resource fails
        httpserver.expect_ordered_request(
            _zome_path("create_resource_specification"),
        ).respond_with_json(_mock_spec_response(products[0].id, products[0].name, "equipment"))
        httpserver.expect_ordered_request(
            _zome_path("create_economic_resource"),
        ).respond_with_data("Error", status=500)

        # Remaining products: succeed
        for p in products[1:]:
            _register_product_handlers(httpserver, p.id, p.name, p.category)

        result = bridge.sync_inventory()

        assert result.specs_created == 4  # spec succeeded for all 4
        assert result.resources_created == 3  # resource failed for first
        assert len(result.errors) == 1
        assert "resource creation failed" in result.errors[0]
