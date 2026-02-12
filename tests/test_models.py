"""Tests for Pydantic models: serialization, field names, enum values."""

from bridge.models import (
    CreateEconomicResourceOutput,
    CreateResourceSpecificationOutput,
    EconomicResourceInput,
    GetAllEconomicResourcesOutput,
    GetAllResourceSpecificationsOutput,
    GetResourceSpecWithRulesOutput,
    GovernanceRuleInput,
    ResourceSpecificationInput,
    ResourceState,
    TransferCustodyInput,
    TransferCustodyOutput,
    UpdateResourceStateInput,
)


class TestResourceState:
    def test_enum_values_match_rust(self):
        """Rust enum uses PascalCase variants."""
        assert ResourceState.PENDING_VALIDATION.value == "PendingValidation"
        assert ResourceState.ACTIVE.value == "Active"
        assert ResourceState.MAINTENANCE.value == "Maintenance"
        assert ResourceState.RETIRED.value == "Retired"
        assert ResourceState.RESERVED.value == "Reserved"


class TestResourceSpecificationInput:
    def test_serializes_with_correct_field_names(self):
        spec = ResourceSpecificationInput(
            name="Test Printer",
            description="A 3D printer",
            category="equipment",
            tags=["fab-lab"],
            governance_rules=[
                GovernanceRuleInput(
                    rule_type="access_requirement",
                    rule_data='{"requires_training": true}',
                )
            ],
        )
        data = spec.model_dump(mode="json")
        assert data["category"] == "equipment"
        assert data["tags"] == ["fab-lab"]
        assert data["governance_rules"][0]["rule_type"] == "access_requirement"
        assert data["image_url"] is None

    def test_round_trip_json(self):
        spec = ResourceSpecificationInput(
            name="Laser",
            description="CO2 laser",
            category="equipment",
        )
        json_str = spec.model_dump_json()
        restored = ResourceSpecificationInput.model_validate_json(json_str)
        assert restored == spec


class TestEconomicResourceInput:
    def test_uses_spec_hash_field(self):
        """Must use 'spec_hash' not 'conforms_to'."""
        resource = EconomicResourceInput(
            spec_hash="uhCkkSomeHash",
            quantity=2.0,
            unit="unit",
        )
        data = resource.model_dump(mode="json")
        assert "spec_hash" in data
        assert "conforms_to" not in data

    def test_optional_location(self):
        resource = EconomicResourceInput(
            spec_hash="uhCkkSomeHash",
            quantity=1.0,
            unit="kg",
            current_location="Lab A",
        )
        assert resource.current_location == "Lab A"


class TestOutputModels:
    def test_create_resource_spec_output(self):
        data = {
            "spec_hash": "uhCkkABC123",
            "spec": {
                "name": "Test",
                "description": "desc",
                "category": "equipment",
                "image_url": None,
                "tags": [],
                "is_active": True,
            },
            "governance_rule_hashes": ["uhCkkRule1"],
        }
        output = CreateResourceSpecificationOutput.model_validate(data)
        assert output.spec_hash == "uhCkkABC123"
        assert output.spec.category == "equipment"

    def test_create_economic_resource_output(self):
        data = {
            "resource_hash": "uhCkkRES123",
            "resource": {
                "quantity": 5.0,
                "unit": "unit",
                "custodian": "uhCAkAgent123",
                "current_location": None,
                "state": "PendingValidation",
            },
        }
        output = CreateEconomicResourceOutput.model_validate(data)
        assert output.resource.state == ResourceState.PENDING_VALIDATION

    def test_get_all_specs_output_empty(self):
        output = GetAllResourceSpecificationsOutput.model_validate({"specifications": []})
        assert output.specifications == []

    def test_get_all_resources_output(self):
        data = {
            "resources": [
                {
                    "quantity": 1.0,
                    "unit": "kg",
                    "custodian": "uhCAkAgent",
                    "current_location": "Lab",
                    "state": "Active",
                }
            ]
        }
        output = GetAllEconomicResourcesOutput.model_validate(data)
        assert len(output.resources) == 1
        assert output.resources[0].state == ResourceState.ACTIVE

    def test_transfer_custody_output(self):
        data = {
            "updated_resource_hash": "uhCkkNew",
            "updated_resource": {
                "quantity": 1.0,
                "unit": "unit",
                "custodian": "uhCAkNewAgent",
                "state": "Active",
            },
        }
        output = TransferCustodyOutput.model_validate(data)
        assert output.updated_resource.custodian == "uhCAkNewAgent"

    def test_get_spec_with_rules_output(self):
        data = {
            "specification": {
                "name": "Printer",
                "description": "3D printer",
                "category": "equipment",
                "tags": [],
                "is_active": True,
            },
            "governance_rules": [
                {
                    "rule_type": "access_requirement",
                    "rule_data": "{}",
                    "enforced_by": "admin",
                }
            ],
        }
        output = GetResourceSpecWithRulesOutput.model_validate(data)
        assert output.governance_rules[0].enforced_by == "admin"


class TestTransferCustodyInput:
    def test_serialization(self):
        inp = TransferCustodyInput(
            resource_hash="uhCkkRes",
            new_custodian="uhCAkNew",
            request_contact_info=True,
        )
        data = inp.model_dump(mode="json")
        assert data["resource_hash"] == "uhCkkRes"
        assert data["request_contact_info"] is True


class TestUpdateResourceStateInput:
    def test_state_enum_serialization(self):
        inp = UpdateResourceStateInput(
            resource_hash="uhCkkRes",
            new_state=ResourceState.ACTIVE,
        )
        data = inp.model_dump(mode="json")
        assert data["new_state"] == "Active"
