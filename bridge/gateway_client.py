"""Typed Python client for Nondominium via hc-http-gw.

hc-http-gw exposes Holochain zome functions as HTTP GET endpoints:
    GET {host}/{dna_hash}/{app_id}/{zome}/{fn}?payload={base64_json}

Payloads are standard base64-encoded JSON (with padding).
Functions that take `()` omit the `?payload=` parameter entirely.

Hash values (ActionHash, AgentPubKey) are byte arrays in the JSON payload
due to hc-http-gw v0.3.x msgpack-to-JSON transcoding.
"""

from __future__ import annotations

import base64
import json
from typing import Any

import requests

from bridge.config import GatewayConfig
from bridge.models import (
    ClaimCommitmentInput,
    ClaimCommitmentOutput,
    Commitment,
    CreateEconomicResourceOutput,
    CreateResourceSpecificationOutput,
    CreateResourceValidationInput,
    CreateResourceValidationOutput,
    CreateValidationReceiptInput,
    CreateValidationReceiptOutput,
    DeriveReputationSummaryInput,
    DeriveReputationSummaryOutput,
    EconomicResource,
    EconomicResourceInput,
    GetAllEconomicResourcesOutput,
    GetAllResourceSpecificationsOutput,
    GetResourceSpecWithRulesOutput,
    IssueParticipationReceiptsInput,
    IssueParticipationReceiptsOutput,
    LogEconomicEventInput,
    LogEconomicEventOutput,
    LogInitialTransferInput,
    LogInitialTransferOutput,
    ProposeCommitmentInput,
    ProposeCommitmentOutput,
    ResourceSpecification,
    ResourceSpecificationInput,
    TransferCustodyInput,
    TransferCustodyOutput,
    UpdateResourceStateInput,
    ValidationReceipt,
    hash_to_bytes,
)


class GatewayError(Exception):
    """Error communicating with hc-http-gw."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        self.status_code = status_code
        super().__init__(message)


class HolochainGatewayClient:
    """Typed client wrapping hc-http-gw for Nondominium zome coordinators."""

    ZOME_RESOURCE = "zome_resource"
    ZOME_GOUVERNANCE = "zome_gouvernance"

    def __init__(self, config: GatewayConfig) -> None:
        self.config = config
        self._session = requests.Session()

    # --- URL / encoding helpers ---

    def _base_url(self, zome: str = "zome_resource") -> str:
        return f"{self.config.url}/{self.config.dna_hash}/{self.config.app_id}/{zome}"

    @staticmethod
    def _encode_payload(data: Any) -> str:
        """Base64-encode a JSON payload for hc-http-gw.

        hc-http-gw v0.3.x expects standard base64 with padding.
        """
        json_bytes = json.dumps(data, separators=(",", ":")).encode()
        return base64.b64encode(json_bytes).decode()

    def _call(self, fn_name: str, payload: Any | None = None, zome: str = "zome_resource") -> Any:
        """Call a zome function via hc-http-gw and return parsed JSON."""
        url = f"{self._base_url(zome)}/{fn_name}"
        params: dict[str, str] = {}
        if payload is not None:
            params["payload"] = self._encode_payload(payload)

        try:
            resp = self._session.get(url, params=params, timeout=self.config.timeout)
        except requests.RequestException as exc:
            raise GatewayError(f"HTTP request failed: {exc}") from exc

        if resp.status_code != 200:
            raise GatewayError(
                f"Gateway returned {resp.status_code}: {resp.text}",
                status_code=resp.status_code,
            )

        return resp.json()

    # --- ResourceSpecification functions ---

    def create_resource_specification(
        self, input_data: ResourceSpecificationInput
    ) -> CreateResourceSpecificationOutput:
        data = self._call(
            "create_resource_specification",
            input_data.model_dump(mode="json"),
        )
        return CreateResourceSpecificationOutput.model_validate(data)

    def get_all_resource_specifications(self) -> GetAllResourceSpecificationsOutput:
        data = self._call("get_all_resource_specifications")
        return GetAllResourceSpecificationsOutput.model_validate(data)

    def get_latest_resource_specification(self, action_hash: str) -> ResourceSpecification:
        data = self._call("get_latest_resource_specification", hash_to_bytes(action_hash))
        return ResourceSpecification.model_validate(data)

    def get_resource_specification_with_rules(
        self, spec_hash: str
    ) -> GetResourceSpecWithRulesOutput:
        data = self._call("get_resource_specification_with_rules", hash_to_bytes(spec_hash))
        return GetResourceSpecWithRulesOutput.model_validate(data)

    def get_resource_specifications_by_category(self, category: str) -> Any:
        return self._call("get_resource_specifications_by_category", category)

    def get_my_resource_specifications(self) -> Any:
        return self._call("get_my_resource_specifications")

    # --- EconomicResource functions ---

    def create_economic_resource(
        self, input_data: EconomicResourceInput
    ) -> CreateEconomicResourceOutput:
        data = self._call(
            "create_economic_resource",
            input_data.model_dump(mode="json"),
        )
        return CreateEconomicResourceOutput.model_validate(data)

    def get_all_economic_resources(self) -> GetAllEconomicResourcesOutput:
        data = self._call("get_all_economic_resources")
        return GetAllEconomicResourcesOutput.model_validate(data)

    def get_latest_economic_resource(self, action_hash: str) -> EconomicResource:
        data = self._call("get_latest_economic_resource", hash_to_bytes(action_hash))
        return EconomicResource.model_validate(data)

    def get_resources_by_specification(self, spec_hash: str) -> Any:
        return self._call("get_resources_by_specification", hash_to_bytes(spec_hash))

    def get_my_economic_resources(self) -> Any:
        return self._call("get_my_economic_resources")

    # --- Custody & state functions ---

    def transfer_custody(self, input_data: TransferCustodyInput) -> TransferCustodyOutput:
        data = self._call("transfer_custody", input_data.model_dump(mode="json"))
        return TransferCustodyOutput.model_validate(data)

    def update_resource_state(self, input_data: UpdateResourceStateInput) -> Any:
        return self._call("update_resource_state", input_data.model_dump(mode="json"))

    # --- Health check ---

    def health_check(self) -> bool:
        """Check if the gateway is reachable by attempting a read operation."""
        try:
            self.get_all_resource_specifications()
            return True
        except GatewayError:
            return False

    # --- Commitment functions (zome_gouvernance) ---

    def propose_commitment(self, input_data: ProposeCommitmentInput) -> ProposeCommitmentOutput:
        data = self._call(
            "propose_commitment",
            input_data.model_dump(mode="json"),
            zome=self.ZOME_GOUVERNANCE,
        )
        return ProposeCommitmentOutput.model_validate(data)

    def get_all_commitments(self) -> list[Commitment]:
        data = self._call("get_all_commitments", zome=self.ZOME_GOUVERNANCE)
        return [Commitment.model_validate(c) for c in data]

    def get_commitments_for_agent(self, agent_pub_key: str) -> list[Commitment]:
        data = self._call(
            "get_commitments_for_agent", hash_to_bytes(agent_pub_key), zome=self.ZOME_GOUVERNANCE
        )
        return [Commitment.model_validate(c) for c in data]

    def claim_commitment(self, input_data: ClaimCommitmentInput) -> ClaimCommitmentOutput:
        data = self._call(
            "claim_commitment",
            input_data.model_dump(mode="json"),
            zome=self.ZOME_GOUVERNANCE,
        )
        return ClaimCommitmentOutput.model_validate(data)

    def get_all_claims(self) -> Any:
        return self._call("get_all_claims", zome=self.ZOME_GOUVERNANCE)

    def get_claims_for_commitment(self, commitment_hash: str) -> Any:
        return self._call(
            "get_claims_for_commitment", hash_to_bytes(commitment_hash), zome=self.ZOME_GOUVERNANCE
        )

    # --- EconomicEvent functions (zome_gouvernance) ---

    def log_economic_event(self, input_data: LogEconomicEventInput) -> LogEconomicEventOutput:
        data = self._call(
            "log_economic_event",
            input_data.model_dump(mode="json"),
            zome=self.ZOME_GOUVERNANCE,
        )
        return LogEconomicEventOutput.model_validate(data)

    def log_initial_transfer(self, input_data: LogInitialTransferInput) -> LogInitialTransferOutput:
        data = self._call(
            "log_initial_transfer",
            input_data.model_dump(mode="json"),
            zome=self.ZOME_GOUVERNANCE,
        )
        return LogInitialTransferOutput.model_validate(data)

    def get_all_economic_events(self) -> Any:
        return self._call("get_all_economic_events", zome=self.ZOME_GOUVERNANCE)

    def get_events_for_resource(self, resource_hash: str) -> Any:
        return self._call(
            "get_events_for_resource", hash_to_bytes(resource_hash), zome=self.ZOME_GOUVERNANCE
        )

    def get_events_for_agent(self, agent_pub_key: str) -> Any:
        return self._call(
            "get_events_for_agent", hash_to_bytes(agent_pub_key), zome=self.ZOME_GOUVERNANCE
        )

    # --- Validation functions (zome_gouvernance) ---

    def create_validation_receipt(
        self, input_data: CreateValidationReceiptInput
    ) -> CreateValidationReceiptOutput:
        data = self._call(
            "create_validation_receipt",
            input_data.model_dump(mode="json"),
            zome=self.ZOME_GOUVERNANCE,
        )
        return CreateValidationReceiptOutput.model_validate(data)

    def get_validation_history(self, item_hash: str) -> list[ValidationReceipt]:
        data = self._call(
            "get_validation_history", hash_to_bytes(item_hash), zome=self.ZOME_GOUVERNANCE
        )
        return [ValidationReceipt.model_validate(r) for r in data]

    def get_all_validation_receipts(self) -> list[ValidationReceipt]:
        data = self._call("get_all_validation_receipts", zome=self.ZOME_GOUVERNANCE)
        return [ValidationReceipt.model_validate(r) for r in data]

    def create_resource_validation(
        self, input_data: CreateResourceValidationInput
    ) -> CreateResourceValidationOutput:
        data = self._call(
            "create_resource_validation",
            input_data.model_dump(mode="json"),
            zome=self.ZOME_GOUVERNANCE,
        )
        return CreateResourceValidationOutput.model_validate(data)

    def check_validation_status(self, validation_hash: str) -> Any:
        return self._call(
            "check_validation_status",
            hash_to_bytes(validation_hash),
            zome=self.ZOME_GOUVERNANCE,
        )

    # --- PPR functions (zome_gouvernance) ---

    def issue_participation_receipts(
        self, input_data: IssueParticipationReceiptsInput
    ) -> IssueParticipationReceiptsOutput:
        data = self._call(
            "issue_participation_receipts",
            input_data.model_dump(mode="json"),
            zome=self.ZOME_GOUVERNANCE,
        )
        return IssueParticipationReceiptsOutput.model_validate(data)

    def get_my_participation_claims(self) -> Any:
        return self._call("get_my_participation_claims", zome=self.ZOME_GOUVERNANCE)

    def derive_reputation_summary(
        self, input_data: DeriveReputationSummaryInput
    ) -> DeriveReputationSummaryOutput:
        data = self._call(
            "derive_reputation_summary",
            input_data.model_dump(mode="json"),
            zome=self.ZOME_GOUVERNANCE,
        )
        return DeriveReputationSummaryOutput.model_validate(data)
