"""Tests for governance Pydantic models: enums, serialization, field names."""

from bridge.models import (
    Claim,
    ClaimCommitmentOutput,
    Commitment,
    CreateResourceValidationOutput,
    CreateValidationReceiptOutput,
    DeriveReputationSummaryInput,
    DeriveReputationSummaryOutput,
    EconomicEvent,
    IssueParticipationReceiptsInput,
    IssueParticipationReceiptsOutput,
    LogEconomicEventInput,
    LogEconomicEventOutput,
    LogInitialTransferInput,
    LogInitialTransferOutput,
    ParticipationClaimType,
    PerformanceMetrics,
    ProposeCommitmentInput,
    ProposeCommitmentOutput,
    ReputationSummary,
    ResourceValidation,
    ValidationReceipt,
    VfAction,
)


class TestVfAction:
    def test_enum_values_match_rust(self):
        """Rust enum uses PascalCase variants."""
        assert VfAction.TRANSFER.value == "Transfer"
        assert VfAction.MOVE.value == "Move"
        assert VfAction.USE.value == "Use"
        assert VfAction.CONSUME.value == "Consume"
        assert VfAction.PRODUCE.value == "Produce"
        assert VfAction.WORK.value == "Work"
        assert VfAction.MODIFY.value == "Modify"
        assert VfAction.COMBINE.value == "Combine"
        assert VfAction.SEPARATE.value == "Separate"
        assert VfAction.RAISE.value == "Raise"
        assert VfAction.LOWER.value == "Lower"
        assert VfAction.CITE.value == "Cite"
        assert VfAction.ACCEPT.value == "Accept"
        assert VfAction.INITIAL_TRANSFER.value == "InitialTransfer"
        assert VfAction.ACCESS_FOR_USE.value == "AccessForUse"
        assert VfAction.TRANSFER_CUSTODY.value == "TransferCustody"

    def test_all_16_variants(self):
        assert len(VfAction) == 16

    def test_string_serialization(self):
        """VfAction is str enum — serializes as string in JSON."""
        assert str(VfAction.USE) == "VfAction.USE"
        assert VfAction.USE.value == "Use"


class TestParticipationClaimType:
    def test_enum_values_match_rust(self):
        assert ParticipationClaimType.RESOURCE_CREATION.value == "ResourceCreation"
        assert ParticipationClaimType.RESOURCE_VALIDATION.value == "ResourceValidation"
        assert ParticipationClaimType.CUSTODY_TRANSFER.value == "CustodyTransfer"
        assert ParticipationClaimType.CUSTODY_ACCEPTANCE.value == "CustodyAcceptance"
        assert (
            ParticipationClaimType.MAINTENANCE_COMMITMENT_ACCEPTED.value
            == "MaintenanceCommitmentAccepted"
        )
        assert (
            ParticipationClaimType.MAINTENANCE_FULFILLMENT_COMPLETED.value
            == "MaintenanceFulfillmentCompleted"
        )
        assert (
            ParticipationClaimType.STORAGE_COMMITMENT_ACCEPTED.value == "StorageCommitmentAccepted"
        )
        assert (
            ParticipationClaimType.STORAGE_FULFILLMENT_COMPLETED.value
            == "StorageFulfillmentCompleted"
        )
        assert (
            ParticipationClaimType.TRANSPORT_COMMITMENT_ACCEPTED.value
            == "TransportCommitmentAccepted"
        )
        assert (
            ParticipationClaimType.TRANSPORT_FULFILLMENT_COMPLETED.value
            == "TransportFulfillmentCompleted"
        )
        assert ParticipationClaimType.GOOD_FAITH_TRANSFER.value == "GoodFaithTransfer"
        assert (
            ParticipationClaimType.DISPUTE_RESOLUTION_PARTICIPATION.value
            == "DisputeResolutionParticipation"
        )
        assert ParticipationClaimType.VALIDATION_ACTIVITY.value == "ValidationActivity"
        assert ParticipationClaimType.RULE_COMPLIANCE.value == "RuleCompliance"
        assert ParticipationClaimType.END_OF_LIFE_DECLARATION.value == "EndOfLifeDeclaration"
        assert ParticipationClaimType.END_OF_LIFE_VALIDATION.value == "EndOfLifeValidation"

    def test_all_16_variants(self):
        assert len(ParticipationClaimType) == 16


class TestCommitment:
    def test_serialization_field_names(self):
        c = Commitment(
            action=VfAction.USE,
            provider="uhCAkProvider",
            receiver="uhCAkReceiver",
            due_date=1700000000000000,
            committed_at=1699000000000000,
        )
        data = c.model_dump(mode="json")
        assert data["action"] == "Use"
        assert data["provider"] == "uhCAkProvider"
        assert data["receiver"] == "uhCAkReceiver"
        assert data["resource_inventoried_as"] is None
        assert data["resource_conforms_to"] is None
        assert data["input_of"] is None

    def test_optional_fields(self):
        c = Commitment(
            action=VfAction.TRANSFER,
            provider="uhCAkAA",
            receiver="uhCAkBB",
            resource_inventoried_as="uhCkkRes",
            resource_conforms_to="uhCkkSpec",
            input_of="uhCkkProcess",
            due_date=1700000000000000,
            note="test note",
            committed_at=1699000000000000,
        )
        data = c.model_dump(mode="json")
        assert data["resource_inventoried_as"] == "uhCkkRes"
        assert data["note"] == "test note"

    def test_round_trip(self):
        c = Commitment(
            action=VfAction.USE,
            provider="uhCAkAA",
            receiver="uhCAkBB",
            due_date=1700000000000000,
            committed_at=1699000000000000,
        )
        json_str = c.model_dump_json()
        restored = Commitment.model_validate_json(json_str)
        assert restored == c


class TestEconomicEvent:
    def test_serialization_field_names(self):
        e = EconomicEvent(
            action=VfAction.USE,
            provider="uhCAkProvider",
            receiver="uhCAkReceiver",
            resource_inventoried_as="uhCkkRes",
            affects="uhCkkRes",
            resource_quantity=1.5,
            event_time=1700000000000000,
        )
        data = e.model_dump(mode="json")
        assert data["action"] == "Use"
        assert data["resource_inventoried_as"] == "uhCkkRes"
        assert data["affects"] == "uhCkkRes"
        assert data["resource_quantity"] == 1.5

    def test_optional_note(self):
        e = EconomicEvent(
            action=VfAction.PRODUCE,
            provider="uhCAkAA",
            receiver="uhCAkBB",
            resource_inventoried_as="uhCkkRes",
            affects="uhCkkRes",
            resource_quantity=10.0,
            event_time=1700000000000000,
            note="Production run",
        )
        assert e.note == "Production run"


class TestClaim:
    def test_serialization(self):
        c = Claim(
            fulfills="uhCkkCommitment",
            fulfilled_by="uhCkkEventAA",
            claimed_at=1700000000000000,
        )
        data = c.model_dump(mode="json")
        assert data["fulfills"] == "uhCkkCommitment"
        assert data["fulfilled_by"] == "uhCkkEventAA"
        assert data["note"] is None


class TestValidationReceipt:
    def test_serialization(self):
        v = ValidationReceipt(
            validator="uhCAkValidator",
            validated_item="uhCkkItem",
            validation_type="resource_approval",
            approved=True,
            validated_at=1700000000000000,
        )
        data = v.model_dump(mode="json")
        assert data["validator"] == "uhCAkValidator"
        assert data["approved"] is True
        assert data["notes"] is None


class TestResourceValidation:
    def test_serialization(self):
        rv = ResourceValidation(
            resource="uhCkkRes",
            validation_scheme="2-of-3",
            required_validators=3,
            current_validators=1,
            status="pending",
            created_at=1700000000000000,
            updated_at=1700000000000000,
        )
        data = rv.model_dump(mode="json")
        assert data["validation_scheme"] == "2-of-3"
        assert data["required_validators"] == 3
        assert data["status"] == "pending"


class TestPerformanceMetrics:
    def test_serialization(self):
        pm = PerformanceMetrics(
            timeliness=0.9,
            quality=0.85,
            reliability=0.95,
            communication=0.8,
            overall_satisfaction=0.88,
        )
        data = pm.model_dump(mode="json")
        assert data["timeliness"] == 0.9
        assert data["overall_satisfaction"] == 0.88
        assert data["notes"] is None


class TestReputationSummary:
    def test_serialization(self):
        rs = ReputationSummary(
            total_claims=25,
            average_performance=0.87,
            creation_claims=5,
            custody_claims=8,
            service_claims=7,
            governance_claims=3,
            end_of_life_claims=2,
            period_start=1690000000000000,
            period_end=1700000000000000,
            agent="uhCAkAgent",
            generated_at=1700000000000000,
        )
        data = rs.model_dump(mode="json")
        assert data["total_claims"] == 25
        assert data["creation_claims"] == 5
        assert data["agent"] == "uhCAkAgent"


class TestProposeCommitmentInput:
    def test_serialization(self):
        inp = ProposeCommitmentInput(
            action=VfAction.USE,
            resource_hash="uhCkkRes",
            provider="uhCAkProvider",
            due_date=1700000000000000,
            note="Use request",
        )
        data = inp.model_dump(mode="json")
        assert data["action"] == "Use"
        assert isinstance(data["resource_hash"], list)
        assert data["resource_spec_hash"] is None

    def test_minimal_fields(self):
        inp = ProposeCommitmentInput(
            action=VfAction.TRANSFER,
            provider="uhCAkAA",
            due_date=1700000000000000,
        )
        data = inp.model_dump(mode="json")
        assert data["resource_hash"] is None
        assert data["note"] is None


class TestLogEconomicEventInput:
    def test_serialization(self):
        inp = LogEconomicEventInput(
            action=VfAction.USE,
            provider="uhCAkProvider",
            receiver="uhCAkReceiver",
            resource_inventoried_as="uhCkkRes",
            resource_quantity=2.0,
            commitment_hash="uhCkkCommit",
            generate_pprs=True,
        )
        data = inp.model_dump(mode="json")
        assert data["action"] == "Use"
        assert data["resource_quantity"] == 2.0
        assert data["generate_pprs"] is True

    def test_optional_fields(self):
        inp = LogEconomicEventInput(
            action=VfAction.PRODUCE,
            provider="uhCAkAA",
            receiver="uhCAkBB",
            resource_inventoried_as="uhCkkRes",
            resource_quantity=10.0,
        )
        data = inp.model_dump(mode="json")
        assert data["commitment_hash"] is None
        assert data["generate_pprs"] is None


class TestLogInitialTransferInput:
    def test_serialization(self):
        inp = LogInitialTransferInput(
            resource_hash="uhCkkRes",
            receiver="uhCAkReceiver",
            quantity=5.0,
        )
        data = inp.model_dump(mode="json")
        assert isinstance(data["resource_hash"], list)
        assert data["quantity"] == 5.0


class TestIssueParticipationReceiptsInput:
    def test_serialization(self):
        metrics = PerformanceMetrics(
            timeliness=0.9,
            quality=0.85,
            reliability=0.95,
            communication=0.8,
            overall_satisfaction=0.88,
        )
        inp = IssueParticipationReceiptsInput(
            fulfills="uhCkkCommit",
            fulfilled_by="uhCkkEventAA",
            provider="uhCAkProvider",
            receiver="uhCAkReceiver",
            claim_types=[
                ParticipationClaimType.CUSTODY_TRANSFER,
                ParticipationClaimType.CUSTODY_ACCEPTANCE,
            ],
            provider_metrics=metrics,
            receiver_metrics=metrics,
        )
        data = inp.model_dump(mode="json")
        assert data["claim_types"] == ["CustodyTransfer", "CustodyAcceptance"]
        assert data["provider_metrics"]["timeliness"] == 0.9
        assert data["resource_hash"] is None


class TestDeriveReputationSummaryInput:
    def test_serialization(self):
        inp = DeriveReputationSummaryInput(
            period_start=1690000000000000,
            period_end=1700000000000000,
        )
        data = inp.model_dump(mode="json")
        assert data["claim_type_filter"] is None

    def test_with_filter(self):
        inp = DeriveReputationSummaryInput(
            period_start=1690000000000000,
            period_end=1700000000000000,
            claim_type_filter=[ParticipationClaimType.CUSTODY_TRANSFER],
        )
        data = inp.model_dump(mode="json")
        assert data["claim_type_filter"] == ["CustodyTransfer"]


class TestGovernanceOutputModels:
    def test_propose_commitment_output(self):
        data = {
            "commitment_hash": "uhCkkCommit",
            "commitment": {
                "action": "Use",
                "provider": "uhCAkAA",
                "receiver": "uhCAkBB",
                "resource_inventoried_as": "uhCkkRes",
                "resource_conforms_to": None,
                "input_of": None,
                "due_date": 1700000000000000,
                "note": None,
                "committed_at": 1699000000000000,
            },
        }
        output = ProposeCommitmentOutput.model_validate(data)
        assert output.commitment_hash == "uhCkkCommit"
        assert output.commitment.action == VfAction.USE

    def test_claim_commitment_output(self):
        data = {
            "claim_hash": "uhCkkClaim",
            "claim": {
                "fulfills": "uhCkkCommit",
                "fulfilled_by": "uhCkkEventAA",
                "claimed_at": 1700000000000000,
                "note": None,
            },
        }
        output = ClaimCommitmentOutput.model_validate(data)
        assert output.claim.fulfills == "uhCkkCommit"

    def test_log_economic_event_output(self):
        data = {
            "event_hash": "uhCkkEventAA",
            "event": {
                "action": "Use",
                "provider": "uhCAkAA",
                "receiver": "uhCAkBB",
                "resource_inventoried_as": "uhCkkRes",
                "affects": "uhCkkRes",
                "resource_quantity": 1.0,
                "event_time": 1700000000000000,
                "note": None,
            },
            "ppr_claims": None,
        }
        output = LogEconomicEventOutput.model_validate(data)
        assert output.event.action == VfAction.USE
        assert output.ppr_claims is None

    def test_log_initial_transfer_output(self):
        data = {
            "event_hash": "uhCkkEventAA",
            "event": {
                "action": "InitialTransfer",
                "provider": "uhCAkAA",
                "receiver": "uhCAkBB",
                "resource_inventoried_as": "uhCkkRes",
                "affects": "uhCkkRes",
                "resource_quantity": 5.0,
                "event_time": 1700000000000000,
            },
            "ppr_claims": None,
        }
        output = LogInitialTransferOutput.model_validate(data)
        assert output.event.action == VfAction.INITIAL_TRANSFER

    def test_create_validation_receipt_output(self):
        data = {
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
        output = CreateValidationReceiptOutput.model_validate(data)
        assert output.receipt.approved is True

    def test_create_resource_validation_output(self):
        data = {
            "validation_hash": "uhCkkValidation",
            "validation": {
                "resource": "uhCkkRes",
                "validation_scheme": "2-of-3",
                "required_validators": 3,
                "current_validators": 0,
                "status": "pending",
                "created_at": 1700000000000000,
                "updated_at": 1700000000000000,
            },
        }
        output = CreateResourceValidationOutput.model_validate(data)
        assert output.validation.required_validators == 3

    def test_issue_participation_receipts_output(self):
        data = {
            "provider_claim_hash": "uhCkkProvClaim",
            "receiver_claim_hash": "uhCkkRecvClaim",
            "provider_claim": {"some": "complex_data"},
            "receiver_claim": {"some": "complex_data"},
        }
        output = IssueParticipationReceiptsOutput.model_validate(data)
        assert output.provider_claim_hash == "uhCkkProvClaim"

    def test_derive_reputation_summary_output(self):
        data = {
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
        output = DeriveReputationSummaryOutput.model_validate(data)
        assert output.summary.total_claims == 10
        assert output.claims_included == 10
