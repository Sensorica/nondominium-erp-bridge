"""Pydantic v2 models matching the Nondominium zome_resource Rust types.

These models map 1:1 to the Holochain zome types defined in:
- integrity/zome_resource/src/lib.rs (data types)
- coordinator/zome_resource/src/resource_specification.rs (input/output types)
- coordinator/zome_resource/src/economic_resource.rs (input/output types)
- coordinator/zome_resource/src/governance_rule.rs (input/output types)
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

# --- Integrity types (stored on-chain) ---


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


# --- Coordinator input types ---


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


# --- Coordinator output types ---


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
