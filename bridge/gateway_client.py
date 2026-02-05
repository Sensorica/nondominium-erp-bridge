"""Typed Python client for Nondominium via hc-http-gw.

hc-http-gw exposes Holochain zome functions as HTTP GET endpoints:
    GET {host}/{dna_hash}/{zome}/{fn}?payload={base64url_json}

Payloads are base64url-encoded JSON (RFC 4648 URL-safe, no padding).
Functions that take `()` omit the `?payload=` parameter entirely.
"""

from __future__ import annotations

import base64
import json
from typing import Any

import requests

from bridge.config import GatewayConfig
from bridge.models import (
    CreateEconomicResourceOutput,
    CreateResourceSpecificationOutput,
    EconomicResource,
    EconomicResourceInput,
    GetAllEconomicResourcesOutput,
    GetAllResourceSpecificationsOutput,
    GetResourceSpecWithRulesOutput,
    ResourceSpecification,
    ResourceSpecificationInput,
    TransferCustodyInput,
    TransferCustodyOutput,
    UpdateResourceStateInput,
)


class GatewayError(Exception):
    """Error communicating with hc-http-gw."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        self.status_code = status_code
        super().__init__(message)


class HolochainGatewayClient:
    """Typed client wrapping hc-http-gw for the zome_resource coordinator."""

    ZOME = "zome_resource"

    def __init__(self, config: GatewayConfig) -> None:
        self.config = config
        self._session = requests.Session()

    # --- URL / encoding helpers ---

    def _base_url(self) -> str:
        return f"{self.config.url}/{self.config.dna_hash}/{self.config.app_id}/{self.ZOME}"

    @staticmethod
    def _encode_payload(data: Any) -> str:
        """Base64url-encode a JSON payload (no padding)."""
        json_bytes = json.dumps(data, separators=(",", ":")).encode()
        return base64.urlsafe_b64encode(json_bytes).rstrip(b"=").decode()

    def _call(self, fn_name: str, payload: Any | None = None) -> Any:
        """Call a zome function via hc-http-gw and return parsed JSON."""
        url = f"{self._base_url()}/{fn_name}"
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
        data = self._call("get_latest_resource_specification", action_hash)
        return ResourceSpecification.model_validate(data)

    def get_resource_specification_with_rules(
        self, spec_hash: str
    ) -> GetResourceSpecWithRulesOutput:
        data = self._call("get_resource_specification_with_rules", spec_hash)
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
        data = self._call("get_latest_economic_resource", action_hash)
        return EconomicResource.model_validate(data)

    def get_resources_by_specification(self, spec_hash: str) -> Any:
        return self._call("get_resources_by_specification", spec_hash)

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
