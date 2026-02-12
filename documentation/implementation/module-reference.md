# Module Reference

> **Document Type**: Implementation Reference
> **Last Updated**: 2026-02-12
> **Related Documents**:
> - [Architecture](architecture.md)
> - [Development Guide](development-guide.md)

---

## 1. `config.py` — Gateway Configuration

**Purpose**: Immutable connection settings for hc-http-gw, loaded from environment variables.

### Classes

**`GatewayConfig`** (frozen dataclass)

| Field | Type | Default | Env Var |
|-------|------|---------|---------|
| `url` | `str` | `"http://127.0.0.1:8888"` | `HC_GW_URL` |
| `timeout` | `int` | `30` | `HC_GW_TIMEOUT` |
| `app_id` | `str` | `"nondominium"` | `HC_APP_ID` |
| `dna_hash` | `str` | `""` | `HC_DNA_HASH` |

**`GatewayConfig.from_env(dotenv_path=None)`** — Class method. Loads from `.env` file (via `python-dotenv`) and environment variables. Strips trailing `/` from URL.

### Dependencies

- `os`, `dataclasses` (stdlib)
- `dotenv` (python-dotenv)

### Tests

No dedicated test file. Tested indirectly via `test_gateway_client.py`.

---

## 2. `models.py` — Pydantic v2 Models

**Purpose**: Python types matching the Nondominium Rust zome types exactly. Field names are critical — hc-http-gw uses JSON transcoding. Covers both `zome_resource` and `zome_gouvernance` types.

### Resource Integrity Types (on-chain data)

| Model | Rust Source | Key Fields |
|-------|------------|------------|
| `ResourceState` | `zome_resource_integrity::ResourceState` | Enum: `PendingValidation`, `Active`, `Maintenance`, `Retired`, `Reserved` |
| `ResourceSpecification` | `zome_resource_integrity::ResourceSpecification` | `name`, `description`, `category`, `image_url`, `tags`, `is_active` |
| `GovernanceRule` | `zome_resource_integrity::GovernanceRule` | `rule_type`, `rule_data`, `enforced_by` |
| `EconomicResource` | `zome_resource_integrity::EconomicResource` | `quantity`, `unit`, `custodian`, `current_location`, `state` |

### Resource Coordinator Input Types

| Model | Key Fields | Notes |
|-------|------------|-------|
| `GovernanceRuleInput` | `rule_type`, `rule_data`, `enforced_by` | |
| `ResourceSpecificationInput` | `name`, `description`, `category`, `image_url`, `tags`, `governance_rules` | Uses `category` (NOT `default_unit`) |
| `EconomicResourceInput` | `spec_hash`, `quantity`, `unit`, `current_location` | Uses `spec_hash` (NOT `conforms_to`) |
| `TransferCustodyInput` | `resource_hash`, `new_custodian`, `request_contact_info` | |
| `UpdateResourceStateInput` | `resource_hash`, `new_state` | |

### Resource Coordinator Output Types

| Model | Key Fields |
|-------|------------|
| `CreateResourceSpecificationOutput` | `spec_hash`, `spec`, `governance_rule_hashes` |
| `GetAllResourceSpecificationsOutput` | `specifications` |
| `GetResourceSpecWithRulesOutput` | `specification`, `governance_rules` |
| `CreateEconomicResourceOutput` | `resource_hash`, `resource` |
| `GetAllEconomicResourcesOutput` | `resources` |
| `TransferCustodyOutput` | `updated_resource_hash`, `updated_resource` |

### Governance Enums

| Model | Variants | Notes |
|-------|----------|-------|
| `VfAction` | 16 PascalCase variants: `Transfer`, `Move`, `Use`, `Consume`, `Produce`, `Work`, `Modify`, `Combine`, `Separate`, `Raise`, `Lower`, `Cite`, `Accept`, `InitialTransfer`, `AccessForUse`, `TransferCustody` | ValueFlows action types |
| `ParticipationClaimType` | 16 PascalCase variants: `ResourceCreation`, `ResourceValidation`, `CustodyTransfer`, `CustodyAcceptance`, `MaintenanceCommitmentAccepted`, `MaintenanceFulfillmentCompleted`, `StorageCommitmentAccepted`, `StorageFulfillmentCompleted`, `TransportCommitmentAccepted`, `TransportFulfillmentCompleted`, `GoodFaithTransfer`, `DisputeResolutionParticipation`, `ValidationActivity`, `RuleCompliance`, `EndOfLifeDeclaration`, `EndOfLifeValidation` | PPR claim types |

### Governance Integrity Types

| Model | Rust Source | Key Fields |
|-------|------------|------------|
| `Commitment` | `zome_gouvernance_integrity` | `provider`, `receiver`, `resource_inventoried_as`, `resource_conforms_to`, `input_of`, `due_date`, `note`, `committed_at` |
| `EconomicEvent` | `zome_gouvernance_integrity` | `action`, `provider`, `receiver`, `resource_inventoried_as`, `affects`, `resource_quantity`, `event_time`, `note` |
| `Claim` | `zome_gouvernance_integrity` | `fulfills`, `fulfilled_by`, `claimed_at`, `note` |
| `ValidationReceipt` | `zome_gouvernance_integrity` | `validator`, `validated_item`, `validation_type`, `approved`, `notes`, `validated_at` |
| `ResourceValidation` | `zome_gouvernance_integrity` | `resource`, `validation_scheme`, `required_validators`, `current_validators`, `status`, `created_at`, `updated_at` |
| `PerformanceMetrics` | `zome_gouvernance_integrity::ppr` | `timeliness`, `quality`, `reliability`, `communication`, `overall_satisfaction`, `notes` |
| `ReputationSummary` | `zome_gouvernance_integrity::ppr` | `total_claims`, `average_performance`, `creation_claims`, `custody_claims`, `service_claims`, `governance_claims`, `end_of_life_claims`, `period_start`, `period_end`, `agent`, `generated_at` |

### Governance Coordinator Input Types

| Model | Key Fields | Notes |
|-------|------------|-------|
| `ProposeCommitmentInput` | `provider`, `receiver`, `resource_inventoried_as`, `resource_conforms_to`, `input_of`, `due_date`, `note` | |
| `ClaimCommitmentInput` | `commitment_hash`, `note` | |
| `LogEconomicEventInput` | `action`, `provider`, `receiver`, `resource_inventoried_as`, `affects`, `resource_quantity`, `commitment_hash`, `generate_pprs`, `note` | |
| `LogInitialTransferInput` | `resource_hash`, `provider`, `receiver`, `note` | |
| `CreateValidationReceiptInput` | `validated_item`, `validation_type`, `approved`, `notes` | |
| `CreateResourceValidationInput` | `resource`, `validation_scheme`, `required_validators` | |
| `IssueParticipationReceiptsInput` | `event_hash`, `claim_type`, `performance_metrics` | |
| `DeriveReputationSummaryInput` | `agent`, `period_start`, `period_end` | |

### Governance Coordinator Output Types

| Model | Key Fields | Notes |
|-------|------------|-------|
| `ProposeCommitmentOutput` | `commitment_hash`, `commitment` | |
| `ClaimCommitmentOutput` | `claim_hash`, `claim` | |
| `LogEconomicEventOutput` | `event_hash`, `event` | |
| `LogInitialTransferOutput` | `event_hash`, `event` | |
| `CreateValidationReceiptOutput` | `receipt_hash`, `receipt` | |
| `CreateResourceValidationOutput` | `validation_hash`, `validation` | |
| `IssueParticipationReceiptsOutput` | `claims` | Uses `Any` for PoC (complex `PrivateParticipationClaim` serialization) |
| `DeriveReputationSummaryOutput` | `summary` | Uses `Any` for PoC |

**Total**: 40 types (1 resource enum + 4 resource integrity + 5 resource input + 6 resource output + 2 governance enums + 7 governance integrity + 8 governance input + 8 governance output)

### Critical Field Names

| This project uses | NOT the REA/ValueFlows name |
|---|---|
| `category` | ~~`default_unit`~~ |
| `spec_hash` | ~~`conforms_to`~~ |
| `current_location` | ~~`location`~~ |

`ResourceState` enum values are **PascalCase** strings, not UPPER_CASE. `VfAction` and `ParticipationClaimType` also use PascalCase.

Timestamp fields (e.g., `due_date`, `committed_at`, `event_time`) are modeled as `int` (microseconds since epoch). The exact serialization format from Holochain needs live verification.

### Dependencies

- `enum`, `typing` (stdlib)
- `pydantic`

### Tests

- `tests/test_models.py` — 13 tests covering resource model serialization round-trips, field name validation, enum values, and optional field handling.
- `tests/test_governance_models.py` — 31 tests covering governance enums, integrity types, input/output serialization, and field name correctness.

---

## 3. `gateway_client.py` — Holochain Gateway Client

**Purpose**: Typed Python client wrapping all `zome_resource` and `zome_gouvernance` coordinator functions as HTTP calls via hc-http-gw.

### Constants

- `ZOME_RESOURCE = "zome_resource"` — Default zome for resource operations
- `ZOME_GOUVERNANCE = "zome_gouvernance"` — Zome for governance operations (commitments, events, PPR)

### Classes

**`GatewayError(Exception)`** — Raised on HTTP errors. Has `status_code: int | None` attribute.

**`HolochainGatewayClient`**

Constructor: `__init__(self, config: GatewayConfig)`

### Internal Helpers

- `_base_url(zome: str = "zome_resource")` — Constructs `{url}/{dna_hash}/{app_id}/{zome}`
- `_encode_payload(data)` — Static. Base64url encodes JSON (no padding)
- `_call(fn_name, payload=None, zome: str = "zome_resource")` — Calls zome function, returns parsed JSON. The `zome` parameter enables multi-zome support.

### Resource Methods (`zome_resource`)

**Typed Methods (return Pydantic models)**

| Method | Input | Return Type | Zome Function |
|--------|-------|-------------|---------------|
| `create_resource_specification` | `ResourceSpecificationInput` | `CreateResourceSpecificationOutput` | `create_resource_specification` |
| `get_all_resource_specifications` | (none) | `GetAllResourceSpecificationsOutput` | `get_all_resource_specifications` |
| `get_latest_resource_specification` | `str` (ActionHash) | `ResourceSpecification` | `get_latest_resource_specification` |
| `get_resource_specification_with_rules` | `str` (ActionHash) | `GetResourceSpecWithRulesOutput` | `get_resource_specification_with_rules` |
| `create_economic_resource` | `EconomicResourceInput` | `CreateEconomicResourceOutput` | `create_economic_resource` |
| `get_all_economic_resources` | (none) | `GetAllEconomicResourcesOutput` | `get_all_economic_resources` |
| `get_latest_economic_resource` | `str` (ActionHash) | `EconomicResource` | `get_latest_economic_resource` |
| `transfer_custody` | `TransferCustodyInput` | `TransferCustodyOutput` | `transfer_custody` |
| `health_check` | (none) | `bool` | (calls `get_all_resource_specifications`) |

**Untyped Methods (return `Any`)**

| Method | Input | Zome Function |
|--------|-------|---------------|
| `get_resource_specifications_by_category` | `str` | `get_resource_specifications_by_category` |
| `get_my_resource_specifications` | (none) | `get_my_resource_specifications` |
| `get_resources_by_specification` | `str` | `get_resources_by_specification` |
| `get_my_economic_resources` | (none) | `get_my_economic_resources` |
| `update_resource_state` | `UpdateResourceStateInput` | `update_resource_state` |

### Governance Methods (`zome_gouvernance`)

All governance methods call `_call()` with `zome=self.ZOME_GOUVERNANCE`.

**Commitment Functions**

| Method | Input | Return Type | Zome Function |
|--------|-------|-------------|---------------|
| `propose_commitment` | `ProposeCommitmentInput` | `ProposeCommitmentOutput` | `propose_commitment` |
| `get_all_commitments` | (none) | `list[Commitment]` | `get_all_commitments` |
| `get_commitments_for_agent` | `str` (agent pubkey) | `list[Commitment]` | `get_commitments_for_agent` |
| `claim_commitment` | `ClaimCommitmentInput` | `ClaimCommitmentOutput` | `claim_commitment` |
| `get_claims_for_commitment` | `str` (commitment hash) | `Any` | `get_claims_for_commitment` |

**EconomicEvent Functions**

| Method | Input | Return Type | Zome Function |
|--------|-------|-------------|---------------|
| `log_economic_event` | `LogEconomicEventInput` | `LogEconomicEventOutput` | `log_economic_event` |
| `log_initial_transfer` | `LogInitialTransferInput` | `LogInitialTransferOutput` | `log_initial_transfer` |
| `get_all_economic_events` | (none) | `Any` | `get_all_economic_events` |
| `get_events_for_resource` | `str` (resource hash) | `Any` | `get_events_for_resource` |
| `get_events_for_agent` | `str` (agent pubkey) | `Any` | `get_events_for_agent` |

**Validation Functions**

| Method | Input | Return Type | Zome Function |
|--------|-------|-------------|---------------|
| `create_validation_receipt` | `CreateValidationReceiptInput` | `CreateValidationReceiptOutput` | `create_validation_receipt` |
| `get_validation_history` | `str` (item hash) | `list[ValidationReceipt]` | `get_validation_history` |
| `get_all_validation_receipts` | (none) | `list[ValidationReceipt]` | `get_all_validation_receipts` |
| `create_resource_validation` | `CreateResourceValidationInput` | `CreateResourceValidationOutput` | `create_resource_validation` |
| `check_validation_status` | `str` (validation hash) | `Any` | `check_validation_status` |
| `get_all_claims` | (none) | `Any` | `get_all_claims` |

**PPR Functions**

| Method | Input | Return Type | Zome Function |
|--------|-------|-------------|---------------|
| `issue_participation_receipts` | `IssueParticipationReceiptsInput` | `IssueParticipationReceiptsOutput` | `issue_participation_receipts` |
| `get_my_participation_claims` | (none) | `Any` | `get_my_participation_claims` |
| `derive_reputation_summary` | `DeriveReputationSummaryInput` | `DeriveReputationSummaryOutput` | `derive_reputation_summary` |

### Dependencies

- `base64`, `json` (stdlib)
- `requests`
- `bridge.config`, `bridge.models`

### Tests

- `tests/test_gateway_client.py` — 13 tests using `pytest-httpserver` (real HTTP server, no mocking of `requests` internals). Tests URL construction, base64url encoding, payload omission, error handling for resource methods.
- `tests/test_governance_gateway.py` — 11 tests using `pytest-httpserver`. Tests governance URL construction, multi-zome routing, payload encoding for governance methods.

---

## 4. `mapper.py` — ERP-to-Nondominium Mapping

**Purpose**: Pure functions converting ERP product data to Nondominium input types.

### Functions

**`product_to_resource_spec(product: MockProduct) -> ResourceSpecificationInput`**

Maps:
| MockProduct field | ResourceSpecificationInput field |
|---|---|
| `name` | `name` |
| `description` | `description` |
| `category` | `category` |
| `image_url` | `image_url` |
| `tags` | `tags` (defaults to `[]`) |
| — | `governance_rules` (always `[]`) |

**`product_to_economic_resource(product: MockProduct, spec_hash: str) -> EconomicResourceInput`**

Maps:
| Source | EconomicResourceInput field |
|---|---|
| `spec_hash` argument | `spec_hash` |
| `product.qty_available` | `quantity` |
| `product.uom_name` | `unit` |
| — | `current_location` (always `None`) |

### Dependencies

- `bridge.erp_mock` (MockProduct)
- `bridge.models` (EconomicResourceInput, ResourceSpecificationInput)

### Tests

`tests/test_mapper.py` — 8 tests covering field mapping correctness, tag handling, optional fields, and all 4 sample products.

---

## 5. `erp_mock.py` — Mock ERP Client

**Purpose**: Simulates reading from an ERPLibre `product.product` model with sample Sensorica fab-lab products.

### Types

**`MockProduct`** (dataclass)

| Field | Type | Description |
|-------|------|-------------|
| `id` | `int` | Product ID |
| `name` | `str` | Product name |
| `description` | `str` | Product description |
| `category` | `str` | Product category |
| `list_price` | `float` | List price |
| `qty_available` | `float` | Available quantity |
| `uom_name` | `str` | Unit of measure |
| `image_url` | `str \| None` | Image URL (optional) |
| `tags` | `list[str] \| None` | Tags (optional) |

### Sample Data (`MOCK_PRODUCTS`)

| ID | Name | Category | Qty | UoM |
|----|------|----------|-----|-----|
| 1 | Prusa MK4 3D Printer | equipment | 2.0 | unit |
| 2 | 40W CO2 Laser Cutter | equipment | 1.0 | unit |
| 3 | Arduino Mega 2560 | electronics | 10.0 | unit |
| 4 | PLA Filament 1kg - White | consumable | 8.0 | kg |

### Classes

**`MockERPClient`**

| Method | Return Type | Description |
|--------|-------------|-------------|
| `get_all_products()` | `list[MockProduct]` | All 4 products |
| `get_available_products()` | `list[MockProduct]` | Products with `qty_available > 0` |
| `get_product_by_id(product_id)` | `MockProduct \| None` | Lookup by ID |

### Dependencies

- `dataclasses` (stdlib)

### Tests

Tested indirectly via `test_mapper.py` and `test_sync.py`.

---

## 6. `discovery.py` — Cross-Org Resource Discovery

**Purpose**: High-level read-only API for discovering resources from the Nondominium DHT.

### Types

**`DiscoveredResource`** (dataclass)

| Field | Type | Description |
|-------|------|-------------|
| `spec_hash` | `str` | ActionHash of the specification |
| `spec` | `ResourceSpecification` | The specification data |
| `resource_hash` | `str` | ActionHash of the resource |
| `resource` | `EconomicResource` | The resource data |

### Classes

**`ResourceDiscovery`**

Constructor: `__init__(self, gateway_client: HolochainGatewayClient)`

| Method | Return Type | Description |
|--------|-------------|-------------|
| `discover_all()` | `list[DiscoveredResource]` | **Stub** — returns empty list (see known gaps in [architecture.md](architecture.md)) |
| `discover_by_category(category)` | `list[ResourceSpecification]` | Find specs by category |
| `get_resources_for_spec(spec_hash)` | `list[EconomicResource]` | Get resources linked to a spec |
| `check_availability(spec_hash)` | `int` | Count resources for a spec |

### Dependencies

- `bridge.gateway_client` (HolochainGatewayClient)
- `bridge.models` (EconomicResource, ResourceSpecification)

### Tests

`tests/test_discovery.py` — 8 tests using `pytest-httpserver` for mocked gateway responses.

---

## 7. `sync.py` — Inventory Sync Pipeline

**Purpose**: Orchestrates the full sync flow: ERP products -> Nondominium resources, with idempotency and per-item error handling.

### Types

**`SyncResult`** (dataclass)

| Field | Type | Description |
|-------|------|-------------|
| `specs_created` | `int` | Number of specs created this run |
| `resources_created` | `int` | Number of resources created this run |
| `skipped` | `int` | Number of already-synced products skipped |
| `errors` | `list[str]` | Error messages for failed products |
| `total_processed` | `int` | Property: `specs_created + skipped + len(errors)` |

**`SyncState`**

Persists sync state to a JSON file for idempotency.

| Method | Description |
|--------|-------------|
| `__init__(path: Path)` | Load existing state from file |
| `save()` | Write state to file |
| `is_synced(product_id: int)` | Check if product was already synced |
| `record(product_id, spec_hash, resource_hash)` | Record a successful sync |
| `get_entry(product_id: int)` | Get sync record for a product |
| `as_dict()` | Get full state as dict |

### Classes

**`NondominiumBridge`**

Constructor: `__init__(self, erp_client: MockERPClient, gateway_client: HolochainGatewayClient, state_path: Path | None = None)`

| Method | Return Type | Description |
|--------|-------------|-------------|
| `sync_inventory()` | `SyncResult` | Sync all available products (main entry point) |

### Dependencies

- `json`, `logging`, `pathlib` (stdlib)
- `bridge.erp_mock` (MockERPClient, MockProduct)
- `bridge.gateway_client` (GatewayError, HolochainGatewayClient)
- `bridge.mapper` (product_to_economic_resource, product_to_resource_spec)

### Tests

`tests/test_sync.py` — 11 tests using `pytest-httpserver`. Tests full sync flow, idempotency, skip behavior, partial failures, and state persistence.

---

## 8. `use_process.py` — Use Process Orchestration

**Purpose**: High-level business flow composing commitment + event into a Use lifecycle. Orchestrates proposing a commitment, logging an economic event, and optionally generating PPRs.

### Types

**`UseProcessResult`** (dataclass)

| Field | Type | Description |
|-------|------|-------------|
| `commitment` | `ProposeCommitmentOutput` | The proposed commitment result |
| `event` | `LogEconomicEventOutput` | The logged economic event result |

### Classes

**`UseProcess`**

Constructor: `__init__(self, client: HolochainGatewayClient)`

| Method | Input | Return Type | Description |
|--------|-------|-------------|-------------|
| `request_use(resource_hash, provider, due_date, note=None)` | `str`, `str`, `int`, `str \| None` | `ProposeCommitmentOutput` | Proposes a `VfAction.Use` commitment for a resource |
| `record_use_event(resource_hash, provider, receiver, quantity, commitment_hash=None, generate_pprs=True, note=None)` | `str`, `str`, `str`, `float`, `str \| None`, `bool`, `str \| None` | `LogEconomicEventOutput` | Logs a `VfAction.Use` economic event with optional PPR generation |
| `execute_use_process(resource_hash, provider, receiver, quantity, due_date, generate_pprs=True, commitment_note=None, event_note=None)` | multiple | `UseProcessResult` | Full orchestration: `request_use()` → `record_use_event()`. Raises `GatewayError` on failure. |

### Dependencies

- `dataclasses`, `logging` (stdlib)
- `bridge.gateway_client` (HolochainGatewayClient, GatewayError)
- `bridge.models` (ProposeCommitmentInput, ProposeCommitmentOutput, LogEconomicEventInput, LogEconomicEventOutput, VfAction)

### Tests

`tests/test_use_process.py` — 6 tests covering full use process orchestration, individual steps, error handling, and optional parameters.

---

## 9. Scripts

### `scripts/setup_conductor.sh`

Starts a Holochain sandbox conductor and hc-http-gw. Checks for prerequisites (holochain, hc, nondominium.happ).

### `scripts/smoke_test.py`

Integration test that creates a resource specification and reads it back. Requires running conductor + gateway.

### `scripts/create_test_data.py`

Populates Nondominium from mock ERP products. Requires running conductor + gateway.

### `scripts/sync_inventory.py`

Runs the full sync pipeline using `NondominiumBridge`. Requires `HC_DNA_HASH` in `.env` and running infrastructure. Reports results to stdout.

### `scripts/demo_full_flow.py`

End-to-end demonstration of the complete bridge flow. Requires running conductor + hc-http-gw. Executes 5 steps:

1. **SYNC** — Publish ERP products as ResourceSpecifications and EconomicResources
2. **DISCOVER** — Find resources by category via the DHT
3. **COMMIT** — Propose a `VfAction.Use` commitment for a discovered resource
4. **EVENT** — Log the economic event with optional PPR generation
5. **VERIFY** — Query commitments, events, and validation receipts to confirm state

---

## 10. Test Coverage Summary

| Test File | Tests | Covers |
|-----------|-------|--------|
| `tests/test_models.py` | 13 | Resource model serialization, field names, enums, optional fields |
| `tests/test_gateway_client.py` | 13 | Resource URL construction, base64url encoding, payload omission, errors |
| `tests/test_mapper.py` | 8 | Field mapping, tags, optionals, all sample products |
| `tests/test_discovery.py` | 8 | Category discovery, spec-based lookup, availability, empty results |
| `tests/test_sync.py` | 11 | Full sync, idempotency, skip, partial failures, state persistence |
| `tests/test_governance_models.py` | 31 | Governance enums, integrity types, input/output serialization, field names |
| `tests/test_governance_gateway.py` | 11 | Governance URL construction, multi-zome routing, payload encoding |
| `tests/test_use_process.py` | 6 | Use process orchestration, individual steps, error handling |
| **Total** | **101** | |

All tests run without infrastructure (no Holochain/hc-http-gw needed). Gateway tests use `pytest-httpserver` for real HTTP server mocking.
