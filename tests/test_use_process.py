"""Tests for UseProcess orchestration."""

import pytest
from pytest_httpserver import HTTPServer

from bridge.config import GatewayConfig
from bridge.gateway_client import GatewayError, HolochainGatewayClient
from bridge.models import VfAction
from bridge.use_process import UseProcess, UseProcessResult

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


@pytest.fixture()
def use_process(client: HolochainGatewayClient) -> UseProcess:
    return UseProcess(client)


def _gov_path(fn_name: str) -> str:
    return f"/{DNA_HASH}/{APP_ID}/{ZOME_GOV}/{fn_name}"


COMMITMENT_RESPONSE = {
    "commitment_hash": "uhCkkCommit",
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

EVENT_RESPONSE = {
    "event_hash": "uhCkkEvent",
    "event": {
        "action": "Use",
        "provider": "uhCAkProvider",
        "receiver": "uhCAkReceiver",
        "resource_inventoried_as": "uhCkkRes",
        "affects": "uhCkkRes",
        "resource_quantity": 1.0,
        "event_time": 1700000000000000,
        "note": None,
    },
    "ppr_claims": None,
}


class TestRequestUse:
    def test_creates_use_commitment(self, httpserver: HTTPServer, use_process: UseProcess):
        httpserver.expect_request(
            _gov_path("propose_commitment"),
        ).respond_with_json(COMMITMENT_RESPONSE)

        result = use_process.request_use(
            resource_hash="uhCkkRes",
            provider="uhCAkProvider",
            due_date=1700000000000000,
            note="Use request",
        )
        assert result.commitment_hash == "uhCkkCommit"
        assert result.commitment.action == VfAction.USE


class TestRecordUseEvent:
    def test_logs_use_event(self, httpserver: HTTPServer, use_process: UseProcess):
        httpserver.expect_request(
            _gov_path("log_economic_event"),
        ).respond_with_json(EVENT_RESPONSE)

        result = use_process.record_use_event(
            resource_hash="uhCkkRes",
            provider="uhCAkProvider",
            receiver="uhCAkReceiver",
            quantity=1.0,
            commitment_hash="uhCkkCommit",
        )
        assert result.event_hash == "uhCkkEvent"
        assert result.event.action == VfAction.USE
        assert result.event.resource_quantity == 1.0


class TestExecuteUseProcess:
    def test_full_flow(self, httpserver: HTTPServer, use_process: UseProcess):
        httpserver.expect_request(
            _gov_path("propose_commitment"),
        ).respond_with_json(COMMITMENT_RESPONSE)
        httpserver.expect_request(
            _gov_path("log_economic_event"),
        ).respond_with_json(EVENT_RESPONSE)

        result = use_process.execute_use_process(
            resource_hash="uhCkkRes",
            provider="uhCAkProvider",
            receiver="uhCAkReceiver",
            quantity=1.0,
            due_date=1700000000000000,
        )
        assert isinstance(result, UseProcessResult)
        assert result.commitment.commitment_hash == "uhCkkCommit"
        assert result.event.event_hash == "uhCkkEvent"

    def test_commitment_failure_stops_process(
        self, httpserver: HTTPServer, use_process: UseProcess
    ):
        httpserver.expect_request(
            _gov_path("propose_commitment"),
        ).respond_with_data("Internal Server Error", status=500)

        with pytest.raises(GatewayError):
            use_process.execute_use_process(
                resource_hash="uhCkkRes",
                provider="uhCAkProvider",
                receiver="uhCAkReceiver",
                quantity=1.0,
                due_date=1700000000000000,
            )

    def test_event_failure_after_commitment(self, httpserver: HTTPServer, use_process: UseProcess):
        """If commitment succeeds but event fails, GatewayError is raised."""
        httpserver.expect_request(
            _gov_path("propose_commitment"),
        ).respond_with_json(COMMITMENT_RESPONSE)
        httpserver.expect_request(
            _gov_path("log_economic_event"),
        ).respond_with_data("Internal Server Error", status=500)

        with pytest.raises(GatewayError):
            use_process.execute_use_process(
                resource_hash="uhCkkRes",
                provider="uhCAkProvider",
                receiver="uhCAkReceiver",
                quantity=1.0,
                due_date=1700000000000000,
            )

    def test_with_notes(self, httpserver: HTTPServer, use_process: UseProcess):
        httpserver.expect_request(
            _gov_path("propose_commitment"),
        ).respond_with_json(COMMITMENT_RESPONSE)
        httpserver.expect_request(
            _gov_path("log_economic_event"),
        ).respond_with_json(EVENT_RESPONSE)

        result = use_process.execute_use_process(
            resource_hash="uhCkkRes",
            provider="uhCAkProvider",
            receiver="uhCAkReceiver",
            quantity=1.0,
            due_date=1700000000000000,
            commitment_note="Reservation for workshop",
            event_note="Used during workshop",
        )
        assert isinstance(result, UseProcessResult)
