"""Tests for governance gateway methods using pytest-httpserver mock."""

import pytest
from pytest_httpserver import HTTPServer

from bridge.config import GatewayConfig
from bridge.gateway_client import HolochainGatewayClient
from bridge.models import (
    CreateValidationReceiptInput,
    LogEconomicEventInput,
    LogInitialTransferInput,
    ProposeCommitmentInput,
    VfAction,
)

DNA_HASH = "uhC0kTestDnaHash"
APP_ID = "nondominium"
ZOME_GOV = "zome_gouvernance"


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


def _gov_path(fn_name: str) -> str:
    return f"/{DNA_HASH}/{APP_ID}/{ZOME_GOV}/{fn_name}"


class TestGovernanceURLConstruction:
    def test_base_url_governance_zome(self, client: HolochainGatewayClient, config: GatewayConfig):
        expected = f"{config.url}/{DNA_HASH}/{APP_ID}/{ZOME_GOV}"
        assert client._base_url(zome=ZOME_GOV) == expected

    def test_base_url_default_is_resource(
        self, client: HolochainGatewayClient, config: GatewayConfig
    ):
        """Default zome should remain zome_resource for backward compat."""
        expected = f"{config.url}/{DNA_HASH}/{APP_ID}/zome_resource"
        assert client._base_url() == expected


class TestProposeCommitment:
    def test_success(self, httpserver: HTTPServer, client: HolochainGatewayClient):
        response_data = {
            "commitment_hash": "uhCkkCommit123",
            "commitment": {
                "action": "Use",
                "provider": "uhCAkProvider",
                "receiver": "uhCAkReceiver",
                "resource_inventoried_as": "uhCkkRes",
                "resource_conforms_to": None,
                "input_of": None,
                "due_date": 1700000000000000,
                "note": "Use request",
                "committed_at": 1699000000000000,
            },
        }
        httpserver.expect_request(
            _gov_path("propose_commitment"),
        ).respond_with_json(response_data)

        result = client.propose_commitment(
            ProposeCommitmentInput(
                action=VfAction.USE,
                resource_hash="uhCkkRes",
                provider="uhCAkProvider",
                due_date=1700000000000000,
                note="Use request",
            )
        )
        assert result.commitment_hash == "uhCkkCommit123"
        assert result.commitment.action == VfAction.USE


class TestGetAllCommitments:
    def test_returns_list(self, httpserver: HTTPServer, client: HolochainGatewayClient):
        response_data = [
            {
                "action": "Use",
                "provider": "uhCAkA",
                "receiver": "uhCAkB",
                "resource_inventoried_as": None,
                "resource_conforms_to": None,
                "input_of": None,
                "due_date": 1700000000000000,
                "note": None,
                "committed_at": 1699000000000000,
            }
        ]
        httpserver.expect_request(
            _gov_path("get_all_commitments"),
        ).respond_with_json(response_data)

        result = client.get_all_commitments()
        assert len(result) == 1
        assert result[0].action == VfAction.USE

    def test_no_payload_param(self, httpserver: HTTPServer, client: HolochainGatewayClient):
        """get_all_commitments takes () — no ?payload= param."""
        httpserver.expect_request(
            _gov_path("get_all_commitments"),
        ).respond_with_json([])

        client.get_all_commitments()

        log = httpserver.log
        assert len(log) == 1
        request_url = log[0][0].url
        assert "payload" not in request_url


class TestLogEconomicEvent:
    def test_success(self, httpserver: HTTPServer, client: HolochainGatewayClient):
        response_data = {
            "event_hash": "uhCkkEvent123",
            "event": {
                "action": "Use",
                "provider": "uhCAkProvider",
                "receiver": "uhCAkReceiver",
                "resource_inventoried_as": "uhCkkRes",
                "affects": "uhCkkRes",
                "resource_quantity": 1.5,
                "event_time": 1700000000000000,
                "note": None,
            },
            "ppr_claims": None,
        }
        httpserver.expect_request(
            _gov_path("log_economic_event"),
        ).respond_with_json(response_data)

        result = client.log_economic_event(
            LogEconomicEventInput(
                action=VfAction.USE,
                provider="uhCAkProvider",
                receiver="uhCAkReceiver",
                resource_inventoried_as="uhCkkRes",
                resource_quantity=1.5,
                generate_pprs=True,
            )
        )
        assert result.event_hash == "uhCkkEvent123"
        assert result.event.resource_quantity == 1.5

    def test_payload_encoding(self, httpserver: HTTPServer, client: HolochainGatewayClient):
        """Verify the governance payload is base64url-encoded correctly."""
        httpserver.expect_request(
            _gov_path("log_economic_event"),
        ).respond_with_json(
            {
                "event_hash": "uhCkkEE",
                "event": {
                    "action": "Use",
                    "provider": "uhCAkAA",
                    "receiver": "uhCAkBB",
                    "resource_inventoried_as": "uhCkkRR",
                    "affects": "uhCkkRR",
                    "resource_quantity": 1.0,
                    "event_time": 1700000000000000,
                },
                "ppr_claims": None,
            }
        )

        client.log_economic_event(
            LogEconomicEventInput(
                action=VfAction.USE,
                provider="uhCAkAA",
                receiver="uhCAkBB",
                resource_inventoried_as="uhCkkRR",
                resource_quantity=1.0,
            )
        )

        log = httpserver.log
        assert len(log) == 1
        request_url = log[0][0].url
        assert "payload=" in request_url


class TestLogInitialTransfer:
    def test_success(self, httpserver: HTTPServer, client: HolochainGatewayClient):
        response_data = {
            "event_hash": "uhCkkEvent456",
            "event": {
                "action": "InitialTransfer",
                "provider": "uhCAkCreator",
                "receiver": "uhCAkReceiver",
                "resource_inventoried_as": "uhCkkRes",
                "affects": "uhCkkRes",
                "resource_quantity": 5.0,
                "event_time": 1700000000000000,
            },
            "ppr_claims": None,
        }
        httpserver.expect_request(
            _gov_path("log_initial_transfer"),
        ).respond_with_json(response_data)

        result = client.log_initial_transfer(
            LogInitialTransferInput(
                resource_hash="uhCkkRes",
                receiver="uhCAkReceiver",
                quantity=5.0,
            )
        )
        assert result.event_hash == "uhCkkEvent456"
        assert result.event.action == VfAction.INITIAL_TRANSFER


class TestCreateValidationReceipt:
    def test_success(self, httpserver: HTTPServer, client: HolochainGatewayClient):
        response_data = {
            "receipt_hash": "uhCkkReceipt",
            "receipt": {
                "validator": "uhCAkValidator",
                "validated_item": "uhCkkItem",
                "validation_type": "resource_approval",
                "approved": True,
                "notes": None,
                "validated_at": 1700000000000000,
            },
        }
        httpserver.expect_request(
            _gov_path("create_validation_receipt"),
        ).respond_with_json(response_data)

        result = client.create_validation_receipt(
            CreateValidationReceiptInput(
                validated_item="uhCkkItem",
                validation_type="resource_approval",
                approved=True,
            )
        )
        assert result.receipt_hash == "uhCkkReceipt"
        assert result.receipt.approved is True


class TestGetAllValidationReceipts:
    def test_returns_list(self, httpserver: HTTPServer, client: HolochainGatewayClient):
        response_data = [
            {
                "validator": "uhCAkV",
                "validated_item": "uhCkkI",
                "validation_type": "resource_approval",
                "approved": True,
                "notes": None,
                "validated_at": 1700000000000000,
            }
        ]
        httpserver.expect_request(
            _gov_path("get_all_validation_receipts"),
        ).respond_with_json(response_data)

        result = client.get_all_validation_receipts()
        assert len(result) == 1
        assert result[0].approved is True


class TestDeriveReputationSummary:
    def test_success(self, httpserver: HTTPServer, client: HolochainGatewayClient):
        from bridge.models import DeriveReputationSummaryInput

        response_data = {
            "summary": {
                "total_claims": 10,
                "average_performance": 0.85,
                "creation_claims": 2,
                "custody_claims": 3,
                "service_claims": 2,
                "governance_claims": 2,
                "end_of_life_claims": 1,
                "period_start": 1690000000000000,
                "period_end": 1700000000000000,
                "agent": "uhCAkAgent",
                "generated_at": 1700000000000000,
            },
            "claims_included": 10,
        }
        httpserver.expect_request(
            _gov_path("derive_reputation_summary"),
        ).respond_with_json(response_data)

        result = client.derive_reputation_summary(
            DeriveReputationSummaryInput(
                period_start=1690000000000000,
                period_end=1700000000000000,
            )
        )
        assert result.summary.total_claims == 10
        assert result.claims_included == 10
