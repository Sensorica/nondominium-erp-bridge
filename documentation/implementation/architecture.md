# Architecture

> **Document Type**: Implementation Reference
> **Last Updated**: 2026-02-17
> **Related Documents**:
> - [Requirements](../requirements/erp_bridge_requirements.md)
> - [Technical Specifications](../specifications/erp_bridge_specifications.md)
> - [Module Reference](module-reference.md)

---

## 1. System Overview

The Nondominium-ERP Bridge is a Python application that syncs ERP inventory into Holochain's Nondominium app via the `hc-http-gw` HTTP gateway. Nondominium has three zomes, with `zome_person` as the foundational identity layer. The bridge currently covers `zome_resource` (inventory) and `zome_gouvernance` (commitments, events, PPRs), while `zome_person` (person profiles, roles, capabilities) is not yet bridged but is required for complete e2e workflows.

```
┌──────────────────┐     ┌──────────────────────────────────────────┐      ┌───────────────┐
│  ERP Source      │     │          Python Bridge (bridge/)         │      │  Holochain    │
│                  │     │                                          │      │  Conductor    │
│  MockERPClient   │────>│  Mapper → Pydantic Models → GatewayClient│─────>│               │
│  (erp_mock.py)   │     │    ↓ HTTP GET + base64url                │      │  Nondominium  │
│                  │     │                                          │      │  hApp         │
│  Odoo Addon      │     │  UseProcess → GatewayClient              │      │               │
│  (optional)      │     │    ↓ Commitment + Event + PPR            │      │ ┌───────────┐ │
│                  │     │                                          │      │ │zome_      │ │
└──────────────────┘     │  Discovery → GatewayClient               │      │ │person     │ │
                         │    ↓ Read-only DHT queries               │ ┌──> │ │(foundation│ │
                         │                                          │ │    │ │ not yet   │ │
                         │  hc-http-gw ─────────────────────────────│─┘    │ │ bridged)  │ │
                         └──────────────────────────────────────────┘      │ ├───────────┤ │
                                                                           │ │zome_      │ │
                                                                           │ │resource   │ │
                                                                           │ ├───────────┤ │
                                                                           │ │zome_      │ │
                                                                           │ │gouvernance│ │
                                                                           │ └───────────┘ │
                                                                           └───────────────┘
                                                                                  │
                                                                            DHT Network
                                                                                  │
                                                                            Other Organizations
```

### Four Pipelines (one planned)

1. **Person/Identity Pipeline** (Planned — foundational): `person` -> `gateway_client` -> hc-http-gw -> `zome_person` — will handle Person profile creation, role assignment, capability-based sharing, and cross-zome identity validation
2. **Sync Pipeline** (ERP -> Holochain): `erp_mock` -> `mapper` -> `models` -> `gateway_client` -> hc-http-gw -> `zome_resource`
3. **Discovery Pipeline** (Holochain -> Python): `gateway_client` -> hc-http-gw -> Holochain DHT -> `discovery` -> Python objects
4. **Governance Pipeline** (Use process): `use_process` -> `gateway_client` -> hc-http-gw -> `zome_gouvernance`

### Cross-Zome Dependencies

```
zome_person ⇄ zome_gouvernance
  │
  ├── zome_person → zome_gouvernance:
  │     validate_agent_identity (for AccountableAgent promotion)
  │     validate_specialized_role (for Transport/Repair/Storage roles)
  │     validate_agent_for_promotion (for role promotions)
  │
  └── zome_gouvernance → zome_person:
        validate_agent_private_data (for custody transfer validation)
        validate_agent_for_promotion (for agent capability checks)
```

These cross-zome calls mean some governance operations require a Person profile in `zome_person`.

---

## 2. Module Dependency Graph

```
bridge/
├── config.py              # No bridge dependencies (only stdlib + dotenv)
├── models.py              # No bridge dependencies (only pydantic)
├── erp_mock.py            # No bridge dependencies (only stdlib)
├── gateway_client.py      # Depends on: config, models
├── mapper.py              # Depends on: erp_mock, models
├── discovery.py           # Depends on: gateway_client, models
├── sync.py                # Depends on: erp_mock, gateway_client, mapper
└── use_process.py         # Depends on: gateway_client, models
```

Dependency direction (lower depends on upper):

```
        config.py    models.py    erp_mock.py
             \          |  \         /    \
              \         |   \       /      \
          gateway_client.py  mapper.py      \
             /   |   \                       \
   discovery.py  |  use_process.py            \
                 |                             |
              sync.py ←────────────────────────┘
```

The three leaf modules (`config`, `models`, `erp_mock`) have no internal dependencies. Higher-level modules compose them. The `use_process` module depends only on `gateway_client` and `models`.

---

## 3. Data Flow: Sync Pipeline

The sync pipeline (`sync.py` -> `NondominiumBridge.sync_inventory()`) processes each ERP product:

```
For each MockProduct with qty > 0:
  1. Check SyncState (JSON file) — skip if already synced
  2. product_to_resource_spec(product) → ResourceSpecificationInput
  3. gateway.create_resource_specification(input) → spec_hash
  4. product_to_economic_resource(product, spec_hash) → EconomicResourceInput
  5. gateway.create_economic_resource(input) → resource_hash
  6. Record (product_id → spec_hash, resource_hash) in SyncState
  7. On error at any step: log error, skip product, continue with next
```

**Idempotency**: `SyncState` persists a JSON file mapping `product_id` -> `{spec_hash, resource_hash}`. Products already in the file are skipped on subsequent runs.

**Error handling**: Per-item — a failure creating one product's spec or resource does not abort the entire sync. Errors are collected in `SyncResult.errors`.

---

## 4. Data Flow: Discovery Pipeline

The discovery module (`discovery.py` -> `ResourceDiscovery`) provides read-only access to the Nondominium DHT:

```
discover_by_category(category)
  → gateway.get_resource_specifications_by_category(category)
  → list[ResourceSpecification]

get_resources_for_spec(spec_hash)
  → gateway.get_resources_by_specification(spec_hash)
  → list[EconomicResource]

check_availability(spec_hash)
  → get_resources_for_spec(spec_hash)
  → count

discover_all()
  → Currently a stub (returns empty list)
  → Limitation: get_all_resource_specifications doesn't return hashes,
    so specs can't be correlated to resources
```

---

## 5. Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Frozen `GatewayConfig` dataclass** | Immutable after creation; prevents accidental mutation of connection settings |
| **Pydantic v2 models** | Field names must match Rust zome types exactly for JSON transcoding via hc-http-gw |
| **Base64url encoding (no padding)** | Required by hc-http-gw protocol (RFC 4648 URL-safe, `=` stripped) |
| **Mock ERP client** | Allows development/testing without live ERP infrastructure |
| **Per-item error handling** | One failed product shouldn't prevent syncing others |
| **JSON-file sync state** | Simple persistence for PoC; no database dependency |
| **`requests.Session`** | Connection pooling for multiple gateway calls |
| **Pure mapper functions** | No side effects — easy to test and reason about |
| **Separate discovery module** | Clean separation between write (sync) and read (discovery) paths |

---

## 6. Implementation Status

Mapping of requirements (from [erp_bridge_requirements.md](../requirements/erp_bridge_requirements.md)) to current implementation:

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| **FR-1** Read ERP Inventory | Partial | `erp_mock.py` provides mock data; Odoo addon provides PoC UI. Live ERPLibre XML-RPC not implemented. |
| **FR-2** Map to ResourceSpecification | Done | `mapper.product_to_resource_spec()` |
| **FR-3** Publish EconomicResource | Done | `mapper.product_to_economic_resource()` + `gateway_client.create_economic_resource()` |
| **FR-4** Discover Resources | Partial | `discovery.py` provides category-based and spec-based discovery; `discover_all()` is a stub |
| **FR-5** Initiate Use Process | Done | `use_process.py` orchestrates `propose_commitment` via `zome_gouvernance` |
| **FR-6** Record Events & PPRs | Done | `gateway_client.log_economic_event()` + `issue_participation_receipts()` via `zome_gouvernance` |

### Sync Pipeline (Issues #7, #8)

| Feature | Status |
|---------|--------|
| Full sync pipeline orchestration | Done (`sync.py`) |
| Idempotent sync with JSON state | Done (`SyncState`) |
| Per-item error handling | Done |
| `sync_inventory.py` script | Done |
| Cross-org discovery module | Done (`discovery.py`) |

### Governance Pipeline (Issue #9)

| Feature | Status |
|---------|--------|
| Governance models (`zome_gouvernance` types) | Done (`models.py` — 25 governance types) |
| Multi-zome gateway client | Done (`gateway_client.py` — 19 governance methods) |
| Use process orchestration | Done (`use_process.py`) |
| End-to-end demo script | Done (`scripts/demo_full_flow.py`) |

### Docker / Odoo Integration

| Feature | Status | Notes |
|---------|--------|-------|
| Docker Compose (Odoo 17 + PostgreSQL) | Done | `docker/docker-compose.yml` |
| Odoo `nondominium_connector` addon | Done | `docker/addons/nondominium_connector/` — two models (`nondominium.config`, `product.template` extension), settings page, product form button |
| Product sync from Odoo UI | Done | Creates ResourceSpecification + EconomicResource, records hashes on product |
| Addon calls hc-http-gw directly | Current state | Duplicates bridge protocol logic (base64url encoding, URL construction) |
| Refactor addon to call bridge REST API | Planned | Decision made: addon will call the Python bridge instead of hc-http-gw directly |
| Tested with live Holochain infrastructure | Not done | Addon not tested with running conductor + hc-http-gw |

---

## 7. Known Gaps

| Gap | Details | Impact |
|-----|---------|--------|
| **`zome_person` not bridged** | Foundational identity zome for person profiles, roles, and capabilities has no Python bridge module | Cannot create Person profiles, assign roles, or validate agent identity from Python. Custody transfers and promotions that require cross-zome validation with `zome_person` will fail without manual Person setup via hc-http-gw. |
| **`discover_all()` is a stub** | `get_all_resource_specifications` doesn't return hashes, so specs can't be correlated to resources | Cannot enumerate all resources with their specs |
| **Governance rules always empty** | `mapper.product_to_resource_spec()` sets `governance_rules=[]` | No access control on published resources |
| **No location mapping** | `product_to_economic_resource()` sets `current_location=None` | Resource locations not tracked |
| **Untyped gateway methods** | Several resource and governance methods return `Any` | No Pydantic validation on these responses |
| **PPR output uses `Any`** | `IssueParticipationReceiptsOutput.claims` and `DeriveReputationSummaryOutput.summary` use `Any` | Complex cryptographic types need tightening for production |
| **Timestamp format unverified** | Modeled as `int` (microseconds); may be `{secs, nanos}` struct from Holochain | Needs verification with a running instance |
| **No live ERP integration** | Mock client + Odoo addon; ERPLibre XML-RPC not implemented | Cannot sync real inventory via XML-RPC |
| **No bidirectional sync** | One-way ERP -> Nondominium only | Changes in Nondominium not reflected in ERP |
| **ActionHash format unverified** | Serialization format from hc-http-gw needs verification with a running instance | Hashes may need format adjustments |
| **Odoo addon not tested with live infrastructure** | Docker setup works but addon not tested with running Holochain conductor | End-to-end Odoo flow unverified |
| **Odoo addon bypasses bridge** | The `nondominium_connector` addon talks directly to hc-http-gw, duplicating protocol logic from `gateway_client.py` | Will be refactored to call the Python bridge REST API instead |

---

## 8. hc-http-gw Protocol

All communication with Holochain goes through HTTP GET requests:

```
GET {host}/{dna_hash}/{app_id}/{zome}/{fn_name}?payload={base64url_json}
```

Where `{zome}` is `zome_person`, `zome_resource`, or `zome_gouvernance` (the bridge currently uses the latter two only).

- **Payloads**: Base64url encoded (RFC 4648), no padding (`=` stripped), compact JSON (`separators=(",", ":")`)
- **No-arg functions**: Functions taking `()` (like `get_all_resource_specifications`) omit `?payload=` entirely
- **Default port**: 8888
- **GET-only**: No POST support
- **No signals**: Request-response only

See the [PoC spec](../specifications/poc/hc_http_gw_poc_spec.md) Section 3 for full protocol details and limitations.
