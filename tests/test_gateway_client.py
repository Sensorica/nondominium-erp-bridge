"""Tests for HolochainGatewayClient using pytest-httpserver mock."""

import base64
import json

import pytest
from pytest_httpserver import HTTPServer

from bridge.config import GatewayConfig
from bridge.gateway_client import GatewayError, HolochainGatewayClient
from bridge.models import (
    EconomicResourceInput,
    ResourceSpecificationInput,
    ResourceState,
)

DNA_HASH = "uhC0kTestDnaHash"
APP_ID = "nondominium"
ZOME = "zome_resource"


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


def _zome_path(fn_name: str) -> str:
    return f"/{DNA_HASH}/{APP_ID}/{ZOME}/{fn_name}"


class TestURLConstruction:
    def test_base_url(self, client: HolochainGatewayClient, config: GatewayConfig):
        expected = f"{config.url}/{DNA_HASH}/{APP_ID}/{ZOME}"
        assert client._base_url() == expected


class TestBase64Encoding:
    def test_encode_dict(self):
        payload = {"name": "test", "value": 42}
        encoded = HolochainGatewayClient._encode_payload(payload)
        decoded = json.loads(base64.b64decode(encoded))
        assert decoded == payload

    def test_encode_string(self):
        payload = "uhCkkSomeHash"
        encoded = HolochainGatewayClient._encode_payload(payload)
        decoded = json.loads(base64.b64decode(encoded))
        assert decoded == payload

    def test_standard_base64_with_padding(self):
        """hc-http-gw v0.3.x requires standard base64 with = padding."""
        # Use a payload whose JSON is not a multiple of 3 bytes
        encoded = HolochainGatewayClient._encode_payload({"k": "v"})
        # Standard base64 pads to multiple of 4
        assert len(encoded) % 4 == 0

    def test_compact_json(self):
        """Payload should use compact JSON (no spaces)."""
        payload = {"name": "test", "value": 42}
        encoded = HolochainGatewayClient._encode_payload(payload)
        decoded_str = base64.b64decode(encoded).decode()
        assert " " not in decoded_str


class TestNullPayload:
    def test_no_payload_param_for_unit_functions(
        self, httpserver: HTTPServer, client: HolochainGatewayClient
    ):
        """Functions taking () should NOT send ?payload= parameter."""
        httpserver.expect_request(
            _zome_path("get_all_resource_specifications"),
        ).respond_with_json({"specifications": []})

        client.get_all_resource_specifications()

        # Verify the request was made without payload param
        log = httpserver.log
        assert len(log) == 1
        request_url = log[0][0].url
        assert "payload" not in request_url


class TestCreateResourceSpecification:
    def test_success(self, httpserver: HTTPServer, client: HolochainGatewayClient):
        response_data = {
            "spec_hash": "uhCkkABC",
            "spec": {
                "name": "Printer",
                "description": "3D printer",
                "category": "equipment",
                "image_url": None,
                "tags": ["fab-lab"],
                "is_active": True,
            },
            "governance_rule_hashes": [],
        }
        httpserver.expect_request(
            _zome_path("create_resource_specification"),
        ).respond_with_json(response_data)

        result = client.create_resource_specification(
            ResourceSpecificationInput(
                name="Printer",
                description="3D printer",
                category="equipment",
                tags=["fab-lab"],
            )
        )
        assert result.spec_hash == "uhCkkABC"
        assert result.spec.category == "equipment"


class TestGetAllResourceSpecifications:
    def test_returns_specs(self, httpserver: HTTPServer, client: HolochainGatewayClient):
        httpserver.expect_request(
            _zome_path("get_all_resource_specifications"),
        ).respond_with_json(
            {
                "specifications": [
                    {
                        "name": "Laser",
                        "description": "CO2 laser",
                        "category": "equipment",
                        "tags": [],
                        "is_active": True,
                    }
                ]
            }
        )

        result = client.get_all_resource_specifications()
        assert len(result.specifications) == 1
        assert result.specifications[0].name == "Laser"


class TestCreateEconomicResource:
    def test_success(self, httpserver: HTTPServer, client: HolochainGatewayClient):
        httpserver.expect_request(
            _zome_path("create_economic_resource"),
        ).respond_with_json(
            {
                "resource_hash": "uhCkkRES",
                "resource": {
                    "quantity": 2.0,
                    "unit": "unit",
                    "custodian": "uhCAkAgent",
                    "state": "PendingValidation",
                },
            }
        )

        result = client.create_economic_resource(
            EconomicResourceInput(
                spec_hash="uhCkkSpec",
                quantity=2.0,
                unit="unit",
            )
        )
        assert result.resource_hash == "uhCkkRES"
        assert result.resource.state == ResourceState.PENDING_VALIDATION


class TestErrorHandling:
    def test_http_error_raises_gateway_error(
        self, httpserver: HTTPServer, client: HolochainGatewayClient
    ):
        httpserver.expect_request(
            _zome_path("get_all_resource_specifications"),
        ).respond_with_data("Internal Server Error", status=500)

        with pytest.raises(GatewayError) as exc_info:
            client.get_all_resource_specifications()
        assert exc_info.value.status_code == 500

    def test_connection_error_raises_gateway_error(self):
        config = GatewayConfig(
            url="http://127.0.0.1:1",  # unlikely to be open
            timeout=1,
            app_id=APP_ID,
            dna_hash=DNA_HASH,
        )
        client = HolochainGatewayClient(config)
        with pytest.raises(GatewayError):
            client.get_all_resource_specifications()


class TestHealthCheck:
    def test_healthy(self, httpserver: HTTPServer, client: HolochainGatewayClient):
        httpserver.expect_request(
            _zome_path("get_all_resource_specifications"),
        ).respond_with_json({"specifications": []})

        assert client.health_check() is True

    def test_unhealthy(self, httpserver: HTTPServer, client: HolochainGatewayClient):
        httpserver.expect_request(
            _zome_path("get_all_resource_specifications"),
        ).respond_with_data("Error", status=500)

        assert client.health_check() is False
