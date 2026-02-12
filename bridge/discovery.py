"""Cross-org resource discovery via the Nondominium DHT.

Resources synced by one org become discoverable by others. This module
wraps the gateway's read-only search/filter methods into a higher-level
discovery API.
"""

from __future__ import annotations

from dataclasses import dataclass

from bridge.gateway_client import HolochainGatewayClient
from bridge.models import EconomicResource, ResourceSpecification


@dataclass
class DiscoveredResource:
    """A resource joined with its specification for display."""

    spec_hash: str
    spec: ResourceSpecification
    resource_hash: str
    resource: EconomicResource


class ResourceDiscovery:
    """High-level discovery API over the Nondominium DHT."""

    def __init__(self, gateway_client: HolochainGatewayClient) -> None:
        self.gateway = gateway_client

    def discover_all(self) -> list[DiscoveredResource]:
        """Get all specs and resources, correlate them into DiscoveredResource objects.

        Note: The gateway returns resources without their spec_hash in the
        EconomicResource struct (it's in the link, not the entry). So we
        use get_resources_by_specification to correlate spec→resources.
        """
        specs_output = self.gateway.get_all_resource_specifications()
        discovered: list[DiscoveredResource] = []

        for spec in specs_output.specifications:
            # We need the spec hash to query linked resources.
            # get_all_resource_specifications returns specs but not hashes.
            # For PoC, we use category-based discovery instead.
            pass

        # PoC limitation: get_all_resource_specifications doesn't return hashes,
        # so we can't correlate specs to resources. Full implementation would
        # need a zome function that returns (hash, spec) pairs.
        return discovered

    def discover_by_category(self, category: str) -> list[ResourceSpecification]:
        """Find all resource specifications in a given category.

        Uses the zome's get_resource_specifications_by_category function.
        """
        data = self.gateway.get_resource_specifications_by_category(category)
        # The zome returns a list of ResourceSpecification records
        if isinstance(data, list):
            return [ResourceSpecification.model_validate(item) for item in data]
        return []

    def get_resources_for_spec(self, spec_hash: str) -> list[EconomicResource]:
        """Get all economic resources linked to a specification.

        Useful for checking availability of a particular type of resource.
        """
        data = self.gateway.get_resources_by_specification(spec_hash)
        if isinstance(data, list):
            return [EconomicResource.model_validate(item) for item in data]
        return []

    def check_availability(self, spec_hash: str) -> int:
        """Count how many resources exist for a given specification."""
        resources = self.get_resources_for_spec(spec_hash)
        return len(resources)
