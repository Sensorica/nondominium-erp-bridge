"""Pydantic v2 models matching the Nondominium Holochain zome types.

These models map 1:1 to the Holochain zome types defined in:
- integrity/zome_resource/src/lib.rs (resource data types)
- coordinator/zome_resource/src/resource_specification.rs (input/output types)
- coordinator/zome_resource/src/economic_resource.rs (input/output types)
- coordinator/zome_resource/src/governance_rule.rs (input/output types)
- integrity/zome_gouvernance/src/lib.rs (governance data types)
- integrity/zome_gouvernance/src/ppr.rs (PPR types)
- coordinator/zome_gouvernance/src/commitment.rs (commitment input/output)
- coordinator/zome_gouvernance/src/economic_event.rs (event input/output)
- coordinator/zome_gouvernance/src/ppr.rs (PPR input/output)
- coordinator/zome_gouvernance/src/validation.rs (validation input/output)
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

# ============================================================
# zome_resource — Integrity types (stored on-chain)
# ============================================================


class ResourceState(str, Enum):
    """Maps to zome_resource_integrity::ResourceState."""

    PENDING_VALIDATION = "PendingValidation"
    ACTIVE = "Active"
    MAINTENANCE = "Maintenance"
    RETIRED = "Retired"
    RESERVED = "Reserved"


class ResourceSpecification(BaseModel):
    """Maps to zome_resource_integrity::ResourceSpecification."""

    name: str
    description: str
    category: str
    image_url: str | None = None
    tags: list[str] = Field(default_factory=list)
    is_active: bool = True


class GovernanceRule(BaseModel):
    """Maps to zome_resource_integrity::GovernanceRule."""

    rule_type: str
    rule_data: str
    enforced_by: str | None = None


class EconomicResource(BaseModel):
    """Maps to zome_resource_integrity::EconomicResource."""

    quantity: float
    unit: str
    custodian: str  # AgentPubKey serialized as base64 string
    current_location: str | None = None
    state: ResourceState = ResourceState.PENDING_VALIDATION


# --- zome_resource coordinator input types ---


class GovernanceRuleInput(BaseModel):
    """Maps to coordinator::GovernanceRuleInput."""

    rule_type: str
    rule_data: str
    enforced_by: str | None = None


class ResourceSpecificationInput(BaseModel):
    """Maps to coordinator::ResourceSpecificationInput."""

    name: str
    description: str
    category: str
    image_url: str | None = None
    tags: list[str] = Field(default_factory=list)
    governance_rules: list[GovernanceRuleInput] = Field(default_factory=list)


class EconomicResourceInput(BaseModel):
    """Maps to coordinator::EconomicResourceInput."""

    spec_hash: str  # ActionHash serialized by hc-http-gw
    quantity: float
    unit: str
    current_location: str | None = None


class TransferCustodyInput(BaseModel):
    """Maps to coordinator::TransferCustodyInput."""

    resource_hash: str  # ActionHash
    new_custodian: str  # AgentPubKey
    request_contact_info: bool | None = None


class UpdateResourceStateInput(BaseModel):
    """Maps to coordinator::UpdateResourceStateInput."""

    resource_hash: str  # ActionHash
    new_state: ResourceState


# --- zome_resource coordinator output types ---


class CreateResourceSpecificationOutput(BaseModel):
    """Maps to coordinator::CreateResourceSpecificationOutput."""

    spec_hash: str  # ActionHash
    spec: ResourceSpecification
    governance_rule_hashes: list[str] = Field(default_factory=list)


class GetAllResourceSpecificationsOutput(BaseModel):
    """Maps to coordinator::GetAllResourceSpecificationsOutput."""

    specifications: list[ResourceSpecification] = Field(default_factory=list)


class GetResourceSpecWithRulesOutput(BaseModel):
    """Maps to coordinator::GetResourceSpecWithRulesOutput."""

    specification: ResourceSpecification
    governance_rules: list[GovernanceRule] = Field(default_factory=list)


class CreateEconomicResourceOutput(BaseModel):
    """Maps to coordinator::CreateEconomicResourceOutput."""

    resource_hash: str  # ActionHash
    resource: EconomicResource


class GetAllEconomicResourcesOutput(BaseModel):
    """Maps to coordinator::GetAllEconomicResourcesOutput."""

    resources: list[EconomicResource] = Field(default_factory=list)


class TransferCustodyOutput(BaseModel):
    """Maps to coordinator::TransferCustodyOutput."""

    updated_resource_hash: str  # ActionHash
    updated_resource: EconomicResource


# ============================================================
# zome_gouvernance — Enums
# ============================================================


class VfAction(str, Enum):
    """Maps to zome_gouvernance_integrity::VfAction.

    ValueFlows action types used in commitments and economic events.
    """

    TRANSFER = "Transfer"
    MOVE = "Move"
    USE = "Use"
    CONSUME = "Consume"
    PRODUCE = "Produce"
    WORK = "Work"
    MODIFY = "Modify"
    COMBINE = "Combine"
    SEPARATE = "Separate"
    RAISE = "Raise"
    LOWER = "Lower"
    CITE = "Cite"
    ACCEPT = "Accept"
    INITIAL_TRANSFER = "InitialTransfer"
    ACCESS_FOR_USE = "AccessForUse"
    TRANSFER_CUSTODY = "TransferCustody"


class ParticipationClaimType(str, Enum):
    """Maps to zome_gouvernance_integrity::ParticipationClaimType.

    Types of participation claims for Private Participation Receipts (PPR).
    """

    # Genesis Role - Network Entry
    RESOURCE_CREATION = "ResourceCreation"
    RESOURCE_VALIDATION = "ResourceValidation"

    # Core Usage Role - Custodianship
    CUSTODY_TRANSFER = "CustodyTransfer"
    CUSTODY_ACCEPTANCE = "CustodyAcceptance"

    # Intermediate Roles - Specialized Services
    MAINTENANCE_COMMITMENT_ACCEPTED = "MaintenanceCommitmentAccepted"
    MAINTENANCE_FULFILLMENT_COMPLETED = "MaintenanceFulfillmentCompleted"
    STORAGE_COMMITMENT_ACCEPTED = "StorageCommitmentAccepted"
    STORAGE_FULFILLMENT_COMPLETED = "StorageFulfillmentCompleted"
    TRANSPORT_COMMITMENT_ACCEPTED = "TransportCommitmentAccepted"
    TRANSPORT_FULFILLMENT_COMPLETED = "TransportFulfillmentCompleted"
    GOOD_FAITH_TRANSFER = "GoodFaithTransfer"

    # Network Governance
    DISPUTE_RESOLUTION_PARTICIPATION = "DisputeResolutionParticipation"
    VALIDATION_ACTIVITY = "ValidationActivity"
    RULE_COMPLIANCE = "RuleCompliance"

    # Resource End-of-Life Management
    END_OF_LIFE_DECLARATION = "EndOfLifeDeclaration"
    END_OF_LIFE_VALIDATION = "EndOfLifeValidation"


# ============================================================
# zome_gouvernance — Integrity types (stored on-chain)
# ============================================================


class Commitment(BaseModel):
    """Maps to zome_gouvernance_integrity::Commitment."""

    action: VfAction
    provider: str  # AgentPubKey
    receiver: str  # AgentPubKey
    resource_inventoried_as: str | None = None  # ActionHash
    resource_conforms_to: str | None = None  # ActionHash
    input_of: str | None = None  # ActionHash
    due_date: int  # Holochain Timestamp (microseconds since epoch)
    note: str | None = None
    committed_at: int  # Holochain Timestamp


class EconomicEvent(BaseModel):
    """Maps to zome_gouvernance_integrity::EconomicEvent."""

    action: VfAction
    provider: str  # AgentPubKey
    receiver: str  # AgentPubKey
    resource_inventoried_as: str  # ActionHash
    affects: str  # ActionHash
    resource_quantity: float
    event_time: int  # Holochain Timestamp
    note: str | None = None


class Claim(BaseModel):
    """Maps to zome_gouvernance_integrity::Claim."""

    fulfills: str  # ActionHash — link to Commitment
    fulfilled_by: str  # ActionHash — link to EconomicEvent
    claimed_at: int  # Holochain Timestamp
    note: str | None = None


class ValidationReceipt(BaseModel):
    """Maps to zome_gouvernance_integrity::ValidationReceipt."""

    validator: str  # AgentPubKey
    validated_item: str  # ActionHash
    validation_type: str
    approved: bool
    notes: str | None = None
    validated_at: int  # Holochain Timestamp


class ResourceValidation(BaseModel):
    """Maps to zome_gouvernance_integrity::ResourceValidation."""

    resource: str  # ActionHash
    validation_scheme: str
    required_validators: int
    current_validators: int
    status: str  # "pending", "approved", "rejected"
    created_at: int  # Holochain Timestamp
    updated_at: int  # Holochain Timestamp


class PerformanceMetrics(BaseModel):
    """Maps to zome_gouvernance_integrity::PerformanceMetrics.

    All scores are 0.0 to 1.0.
    """

    timeliness: float
    quality: float
    reliability: float
    communication: float
    overall_satisfaction: float
    notes: str | None = None


class ReputationSummary(BaseModel):
    """Maps to zome_gouvernance_integrity::ReputationSummary."""

    total_claims: int
    average_performance: float
    creation_claims: int
    custody_claims: int
    service_claims: int
    governance_claims: int
    end_of_life_claims: int
    period_start: int  # Holochain Timestamp
    period_end: int  # Holochain Timestamp
    agent: str  # AgentPubKey
    generated_at: int  # Holochain Timestamp


# ============================================================
# zome_gouvernance — Coordinator input types
# ============================================================


class ProposeCommitmentInput(BaseModel):
    """Maps to coordinator::ProposeCommitmentInput."""

    action: VfAction
    resource_hash: str | None = None  # ActionHash
    resource_spec_hash: str | None = None  # ActionHash
    provider: str  # AgentPubKey
    due_date: int  # Holochain Timestamp
    note: str | None = None


class ClaimCommitmentInput(BaseModel):
    """Maps to coordinator::ClaimCommitmentInput."""

    commitment_hash: str  # ActionHash
    fulfillment_note: str | None = None


class LogEconomicEventInput(BaseModel):
    """Maps to coordinator::LogEconomicEventInput."""

    action: VfAction
    provider: str  # AgentPubKey
    receiver: str  # AgentPubKey
    resource_inventoried_as: str  # ActionHash
    resource_quantity: float
    note: str | None = None
    commitment_hash: str | None = None  # ActionHash
    generate_pprs: bool | None = None


class LogInitialTransferInput(BaseModel):
    """Maps to coordinator::LogInitialTransferInput."""

    resource_hash: str  # ActionHash
    receiver: str  # AgentPubKey
    quantity: float


class CreateValidationReceiptInput(BaseModel):
    """Maps to coordinator::CreateValidationReceiptInput."""

    validated_item: str  # ActionHash
    validation_type: str
    approved: bool
    notes: str | None = None


class CreateResourceValidationInput(BaseModel):
    """Maps to coordinator::CreateResourceValidationInput."""

    resource: str  # ActionHash
    validation_scheme: str
    required_validators: int


class IssueParticipationReceiptsInput(BaseModel):
    """Maps to coordinator::IssueParticipationReceiptsInput."""

    fulfills: str  # ActionHash — Commitment
    fulfilled_by: str  # ActionHash — EconomicEvent
    provider: str  # AgentPubKey
    receiver: str  # AgentPubKey
    claim_types: list[ParticipationClaimType]
    provider_metrics: PerformanceMetrics
    receiver_metrics: PerformanceMetrics
    resource_hash: str | None = None  # ActionHash
    notes: str | None = None


class DeriveReputationSummaryInput(BaseModel):
    """Maps to coordinator::DeriveReputationSummaryInput."""

    period_start: int  # Holochain Timestamp
    period_end: int  # Holochain Timestamp
    claim_type_filter: list[ParticipationClaimType] | None = None


# ============================================================
# zome_gouvernance — Coordinator output types
# ============================================================


class ProposeCommitmentOutput(BaseModel):
    """Maps to coordinator::ProposeCommitmentOutput."""

    commitment_hash: str  # ActionHash
    commitment: Commitment


class ClaimCommitmentOutput(BaseModel):
    """Maps to coordinator::ClaimCommitmentOutput."""

    claim_hash: str  # ActionHash
    claim: Claim


class LogEconomicEventOutput(BaseModel):
    """Maps to coordinator::LogEconomicEventOutput."""

    event_hash: str  # ActionHash
    event: EconomicEvent
    ppr_claims: Any | None = None  # IssueParticipationReceiptsOutput (complex nested type)


class LogInitialTransferOutput(BaseModel):
    """Maps to coordinator::LogInitialTransferOutput."""

    event_hash: str  # ActionHash
    event: EconomicEvent
    ppr_claims: Any | None = None


class CreateValidationReceiptOutput(BaseModel):
    """Maps to coordinator::CreateValidationReceiptOutput."""

    receipt_hash: str  # ActionHash
    receipt: ValidationReceipt


class CreateResourceValidationOutput(BaseModel):
    """Maps to coordinator::CreateResourceValidationOutput."""

    validation_hash: str  # ActionHash
    validation: ResourceValidation


class IssueParticipationReceiptsOutput(BaseModel):
    """Maps to coordinator::IssueParticipationReceiptsOutput.

    Note: provider_claim and receiver_claim contain PrivateParticipationClaim
    with CryptographicSignature (raw bytes). Typed as Any for PoC.
    """

    provider_claim_hash: str  # ActionHash
    receiver_claim_hash: str  # ActionHash
    provider_claim: Any = None  # PrivateParticipationClaim
    receiver_claim: Any = None  # PrivateParticipationClaim


class DeriveReputationSummaryOutput(BaseModel):
    """Maps to coordinator::DeriveReputationSummaryOutput."""

    summary: ReputationSummary
    claims_included: int
