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

**Purpose**: Python types matching the Nondominium `zome_resource` Rust types exactly. Field names are critical — hc-http-gw uses JSON transcoding.

### Integrity Types (on-chain data)

| Model | Rust Source | Key Fields |
|-------|------------|------------|
| `ResourceState` | `zome_resource_integrity::ResourceState` | Enum: `PendingValidation`, `Active`, `Maintenance`, `Retired`, `Reserved` |
| `ResourceSpecification` | `zome_resource_integrity::ResourceSpecification` | `name`, `description`, `category`, `image_url`, `tags`, `is_active` |
| `GovernanceRule` | `zome_resource_integrity::GovernanceRule` | `rule_type`, `rule_data`, `enforced_by` |
| `EconomicResource` | `zome_resource_integrity::EconomicResource` | `quantity`, `unit`, `custodian`, `current_location`, `state` |

### Coordinator Input Types

| Model | Key Fields | Notes |
|-------|------------|-------|
| `GovernanceRuleInput` | `rule_type`, `rule_data`, `enforced_by` | |
| `ResourceSpecificationInput` | `name`, `description`, `category`, `image_url`, `tags`, `governance_rules` | Uses `category` (NOT `default_unit`) |
| `EconomicResourceInput` | `spec_hash`, `quantity`, `unit`, `current_location` | Uses `spec_hash` (NOT `conforms_to`) |
| `TransferCustodyInput` | `resource_hash`, `new_custodian`, `request_contact_info` | |
| `UpdateResourceStateInput` | `resource_hash`, `new_state` | |

### Coordinator Output Types

| Model | Key Fields |
|-------|------------|
| `CreateResourceSpecificationOutput` | `spec_hash`, `spec`, `governance_rule_hashes` |
| `GetAllResourceSpecificationsOutput` | `specifications` |
| `GetResourceSpecWithRulesOutput` | `specification`, `governance_rules` |
| `CreateEconomicResourceOutput` | `resource_hash`, `resource` |
| `GetAllEconomicResourcesOutput` | `resources` |
| `TransferCustodyOutput` | `updated_resource_hash`, `updated_resource` |

**Total**: 15 types (4 integrity + 5 input + 6 output)

### Critical Field Names

| This project uses | NOT the REA/ValueFlows name |
|---|---|
| `category` | ~~`default_unit`~~ |
| `spec_hash` | ~~`conforms_to`~~ |
| `current_location` | ~~`location`~~ |

`ResourceState` enum values are **PascalCase** strings, not UPPER_CASE.

### Dependencies

- `enum` (stdlib)
- `pydantic`

### Tests

`tests/test_models.py` — 13 tests covering serialization round-trips, field name validation, enum values, and optional field handling.

---

## 3. `gateway_client.py` — Holochain Gateway Client

**Purpose**: Typed Python client wrapping all `zome_resource` coordinator functions as HTTP calls via hc-http-gw.

### Classes

**`GatewayError(Exception)`** — Raised on HTTP errors. Has `status_code: int | None` attribute.

**`HolochainGatewayClient`**

Constructor: `__init__(self, config: GatewayConfig)`

### Typed Methods (return Pydantic models)

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

### Untyped Methods (return `Any`)

| Method | Input | Zome Function |
|--------|-------|---------------|
| `get_resource_specifications_by_category` | `str` | `get_resource_specifications_by_category` |
| `get_my_resource_specifications` | (none) | `get_my_resource_specifications` |
| `get_resources_by_specification` | `str` | `get_resources_by_specification` |
| `get_my_economic_resources` | (none) | `get_my_economic_resources` |
| `update_resource_state` | `UpdateResourceStateInput` | `update_resource_state` |

### Internal Helpers

- `_base_url()` — Constructs `{url}/{dna_hash}/{app_id}/zome_resource`
- `_encode_payload(data)` — Static. Base64url encodes JSON (no padding)
- `_call(fn_name, payload=None)` — Calls zome function, returns parsed JSON

### Dependencies

- `base64`, `json` (stdlib)
- `requests`
- `bridge.config`, `bridge.models`

### Tests

`tests/test_gateway_client.py` — 13 tests using `pytest-httpserver` (real HTTP server, no mocking of `requests` internals). Tests URL construction, base64url encoding, payload omission, error handling.

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

## 8. Scripts

### `scripts/setup_conductor.sh`

Starts a Holochain sandbox conductor and hc-http-gw. Checks for prerequisites (holochain, hc, nondominium.happ).

### `scripts/smoke_test.py`

Integration test that creates a resource specification and reads it back. Requires running conductor + gateway.

### `scripts/create_test_data.py`

Populates Nondominium from mock ERP products. Requires running conductor + gateway.

### `scripts/sync_inventory.py`

Runs the full sync pipeline using `NondominiumBridge`. Requires `HC_DNA_HASH` in `.env` and running infrastructure. Reports results to stdout.

---

## 9. Test Coverage Summary

| Test File | Tests | Covers |
|-----------|-------|--------|
| `tests/test_models.py` | 13 | Pydantic serialization, field names, enums, optional fields |
| `tests/test_gateway_client.py` | 13 | URL construction, base64url encoding, payload omission, errors |
| `tests/test_mapper.py` | 8 | Field mapping, tags, optionals, all sample products |
| `tests/test_discovery.py` | 8 | Category discovery, spec-based lookup, availability, empty results |
| `tests/test_sync.py` | 11 | Full sync, idempotency, skip, partial failures, state persistence |
| **Total** | **53** | |

All tests run without infrastructure (no Holochain/hc-http-gw needed). Gateway tests use `pytest-httpserver` for real HTTP server mocking.
