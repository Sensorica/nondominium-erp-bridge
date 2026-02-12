"""Tests for the cross-org resource discovery module."""

from __future__ import annotations

import pytest
from pytest_httpserver import HTTPServer

from bridge.config import GatewayConfig
from bridge.discovery import ResourceDiscovery
from bridge.gateway_client import HolochainGatewayClient

DNA_HASH = "uhC0kTestDnaHash"
APP_ID = "nondominium"
ZOME = "zome_resource"


def _zome_path(fn_name: str) -> str:
    return f"/{DNA_HASH}/{APP_ID}/{ZOME}/{fn_name}"


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
def discovery(client: HolochainGatewayClient) -> ResourceDiscovery:
    return ResourceDiscovery(client)


SAMPLE_SPEC = {
    "name": "Prusa MK4",
    "description": "3D printer",
    "category": "equipment",
    "image_url": None,
    "tags": ["fab-lab"],
    "is_active": True,
}

SAMPLE_RESOURCE = {
    "quantity": 2.0,
    "unit": "unit",
    "custodian": "uhCAkAgent",
    "current_location": None,
    "state": "Active",
}


class TestDiscoverByCategory:
    def test_returns_specs(self, httpserver: HTTPServer, discovery: ResourceDiscovery):
        httpserver.expect_request(
            _zome_path("get_resource_specifications_by_category"),
        ).respond_with_json([SAMPLE_SPEC])

        specs = discovery.discover_by_category("equipment")
        assert len(specs) == 1
        assert specs[0].name == "Prusa MK4"
        assert specs[0].category == "equipment"

    def test_empty_category(self, httpserver: HTTPServer, discovery: ResourceDiscovery):
        httpserver.expect_request(
            _zome_path("get_resource_specifications_by_category"),
        ).respond_with_json([])

        specs = discovery.discover_by_category("nonexistent")
        assert specs == []

    def test_multiple_specs(self, httpserver: HTTPServer, discovery: ResourceDiscovery):
        spec2 = {**SAMPLE_SPEC, "name": "Laser Cutter", "description": "CO2 laser"}
        httpserver.expect_request(
            _zome_path("get_resource_specifications_by_category"),
        ).respond_with_json([SAMPLE_SPEC, spec2])

        specs = discovery.discover_by_category("equipment")
        assert len(specs) == 2
        assert specs[1].name == "Laser Cutter"


class TestGetResourcesForSpec:
    def test_returns_resources(self, httpserver: HTTPServer, discovery: ResourceDiscovery):
        httpserver.expect_request(
            _zome_path("get_resources_by_specification"),
        ).respond_with_json([SAMPLE_RESOURCE])

        resources = discovery.get_resources_for_spec("uhCkkSpecHash")
        assert len(resources) == 1
        assert resources[0].quantity == 2.0
        assert resources[0].unit == "unit"

    def test_no_resources(self, httpserver: HTTPServer, discovery: ResourceDiscovery):
        httpserver.expect_request(
            _zome_path("get_resources_by_specification"),
        ).respond_with_json([])

        resources = discovery.get_resources_for_spec("uhCkkEmptySpecAA")
        assert resources == []


class TestCheckAvailability:
    def test_count(self, httpserver: HTTPServer, discovery: ResourceDiscovery):
        httpserver.expect_request(
            _zome_path("get_resources_by_specification"),
        ).respond_with_json([SAMPLE_RESOURCE, SAMPLE_RESOURCE])

        count = discovery.check_availability("uhCkkSpecHash")
        assert count == 2

    def test_zero_availability(self, httpserver: HTTPServer, discovery: ResourceDiscovery):
        httpserver.expect_request(
            _zome_path("get_resources_by_specification"),
        ).respond_with_json([])

        count = discovery.check_availability("uhCkkEmptySpecAA")
        assert count == 0


class TestDiscoverAll:
    def test_returns_empty_for_poc(self, httpserver: HTTPServer, discovery: ResourceDiscovery):
        """PoC discover_all returns empty — full correlation needs spec hashes from links."""
        httpserver.expect_request(
            _zome_path("get_all_resource_specifications"),
        ).respond_with_json({"specifications": [SAMPLE_SPEC]})

        result = discovery.discover_all()
        assert result == []  # PoC limitation: no spec-hash correlation
