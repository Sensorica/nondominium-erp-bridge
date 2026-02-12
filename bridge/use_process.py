"""Use Process orchestration for Nondominium governance workflow.

Implements the "Use" lifecycle:
  1. propose_commitment (VfAction.USE) — request to use a resource
  2. log_economic_event (VfAction.USE) — record actual usage, optionally generate PPRs
"""

from __future__ import annotations

from dataclasses import dataclass

from bridge.gateway_client import HolochainGatewayClient
from bridge.models import (
    LogEconomicEventInput,
    LogEconomicEventOutput,
    ProposeCommitmentInput,
    ProposeCommitmentOutput,
    VfAction,
)


@dataclass
class UseProcessResult:
    """Result of a complete Use process (commit + event)."""

    commitment: ProposeCommitmentOutput
    event: LogEconomicEventOutput


class UseProcess:
    """Orchestrates the Use process flow via the governance zome."""

    def __init__(self, client: HolochainGatewayClient) -> None:
        self.client = client

    def request_use(
        self,
        resource_hash: str,
        provider: str,
        due_date: int,
        note: str | None = None,
    ) -> ProposeCommitmentOutput:
        """Step 1: Propose a Use commitment for a resource.

        Args:
            resource_hash: ActionHash of the EconomicResource to use.
            provider: AgentPubKey of the resource custodian/provider.
            due_date: Holochain Timestamp (microseconds since epoch).
            note: Optional note describing the intended use.

        Returns:
            ProposeCommitmentOutput with commitment_hash and commitment.
        """
        input_data = ProposeCommitmentInput(
            action=VfAction.USE,
            resource_hash=resource_hash,
            provider=provider,
            due_date=due_date,
            note=note,
        )
        return self.client.propose_commitment(input_data)

    def record_use_event(
        self,
        resource_hash: str,
        provider: str,
        receiver: str,
        quantity: float,
        commitment_hash: str | None = None,
        generate_pprs: bool = True,
        note: str | None = None,
    ) -> LogEconomicEventOutput:
        """Step 2: Record a Use economic event.

        Args:
            resource_hash: ActionHash of the resource being used.
            provider: AgentPubKey of the provider.
            receiver: AgentPubKey of the receiver/user.
            quantity: Amount of resource used.
            commitment_hash: Optional link to the commitment being fulfilled.
            generate_pprs: Whether to auto-generate PPR claims (default True).
            note: Optional note about the usage.

        Returns:
            LogEconomicEventOutput with event_hash, event, and optional ppr_claims.
        """
        input_data = LogEconomicEventInput(
            action=VfAction.USE,
            provider=provider,
            receiver=receiver,
            resource_inventoried_as=resource_hash,
            resource_quantity=quantity,
            note=note,
            commitment_hash=commitment_hash,
            generate_pprs=generate_pprs,
        )
        return self.client.log_economic_event(input_data)

    def execute_use_process(
        self,
        resource_hash: str,
        provider: str,
        receiver: str,
        quantity: float,
        due_date: int,
        generate_pprs: bool = True,
        commitment_note: str | None = None,
        event_note: str | None = None,
    ) -> UseProcessResult:
        """Execute the full Use process: propose commitment then log event.

        Args:
            resource_hash: ActionHash of the resource to use.
            provider: AgentPubKey of the resource provider.
            receiver: AgentPubKey of the resource user.
            quantity: Amount of resource to use.
            due_date: Holochain Timestamp for commitment due date.
            generate_pprs: Whether to auto-generate PPR claims.
            commitment_note: Optional note for the commitment.
            event_note: Optional note for the economic event.

        Returns:
            UseProcessResult containing both commitment and event outputs.

        Raises:
            GatewayError: If any gateway call fails.
        """
        commitment = self.request_use(
            resource_hash=resource_hash,
            provider=provider,
            due_date=due_date,
            note=commitment_note,
        )

        event = self.record_use_event(
            resource_hash=resource_hash,
            provider=provider,
            receiver=receiver,
            quantity=quantity,
            commitment_hash=commitment.commitment_hash,
            generate_pprs=generate_pprs,
            note=event_note,
        )

        return UseProcessResult(commitment=commitment, event=event)
