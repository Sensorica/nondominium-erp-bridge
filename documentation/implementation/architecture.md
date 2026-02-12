# Architecture

> **Document Type**: Implementation Reference
> **Last Updated**: 2026-02-12
> **Related Documents**:
> - [Requirements](../requirements/erp_bridge_requirements.md)
> - [Technical Specifications](../specifications/erp_bridge_specifications.md)
> - [Module Reference](module-reference.md)

---

## 1. System Overview

The Nondominium-ERP Bridge is a Python application that syncs ERP inventory into Holochain's Nondominium app via the `hc-http-gw` HTTP gateway. It currently uses a mock ERP client; live ERPLibre integration is planned.

```
┌─────────────────┐     ┌──────────────────────────────────────────┐      ┌───────────────┐
│   Mock ERP      │     │          Python Bridge (bridge/)         │      │  Holochain    │
│   (erp_mock.py) │────>│                                          │─────>│ Conductor     │
│                 │     │  MockERPClient                           │      │               │
│  4 sample       │     │    ↓                                     │      │ Nondominium   │
│  products       │     │  Mapper (product_to_resource_spec/...)   │      │ hApp          │
│                 │     │    ↓                                     │      │               │
│                 │     │  Pydantic Models (models.py)             │      │ zome_resource │
│                 │     │    ↓                                     │      │               │
│                 │     │  GatewayClient (gateway_client.py)       │      │               │
│                 │     │    ↓ HTTP GET + base64url                │      │               │
│                 │     │  hc-http-gw ─────────────────────────────│─────>│               │
└─────────────────┘     └──────────────────────────────────────────┘      └───────────────┘
                                                                                  │
                                                                            DHT Network
                                                                                  │
                                                                            Other Organizations
```

### Two Pipelines

1. **Sync Pipeline** (ERP -> Holochain): `erp_mock` -> `mapper` -> `models` -> `gateway_client` -> hc-http-gw -> Holochain
2. **Discovery Pipeline** (Holochain -> Python): `gateway_client` -> hc-http-gw -> Holochain DHT -> `discovery` -> Python objects

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
└── sync.py                # Depends on: erp_mock, gateway_client, mapper
```

Dependency direction (lower depends on upper):

```
        config.py    models.py    erp_mock.py
             \          |  \         /    \
              \         |   \       /      \
          gateway_client.py  mapper.py      \
               /     \                       \
        discovery.py  sync.py ←───────────────┘
```

The three leaf modules (`config`, `models`, `erp_mock`) have no internal dependencies. Higher-level modules compose them.

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
| **FR-1** Read ERP Inventory | Partial | `erp_mock.py` provides mock data; live ERPLibre XML-RPC not implemented |
| **FR-2** Map to ResourceSpecification | Done | `mapper.product_to_resource_spec()` |
| **FR-3** Publish EconomicResource | Done | `mapper.product_to_economic_resource()` + `gateway_client.create_economic_resource()` |
| **FR-4** Discover Resources | Partial | `discovery.py` provides category-based and spec-based discovery; `discover_all()` is a stub |
| **FR-5** Initiate Use Process | Not started | Requires `create_commitment` zome function (not in Nondominium yet) |
| **FR-6** Record Events & PPRs | Not started | Requires `record_economic_event` zome function (not in Nondominium yet) |

### Sync Pipeline (Issues #7, #8)

| Feature | Status |
|---------|--------|
| Full sync pipeline orchestration | Done (`sync.py`) |
| Idempotent sync with JSON state | Done (`SyncState`) |
| Per-item error handling | Done |
| `sync_inventory.py` script | Done |
| Cross-org discovery module | Done (`discovery.py`) |

---

## 7. Known Gaps

| Gap | Details | Impact |
|-----|---------|--------|
| **`discover_all()` is a stub** | `get_all_resource_specifications` doesn't return hashes, so specs can't be correlated to resources | Cannot enumerate all resources with their specs |
| **Governance rules always empty** | `mapper.product_to_resource_spec()` sets `governance_rules=[]` | No access control on published resources |
| **No location mapping** | `product_to_economic_resource()` sets `current_location=None` | Resource locations not tracked |
| **5 untyped gateway methods** | `get_resource_specifications_by_category`, `get_my_resource_specifications`, `get_resources_by_specification`, `get_my_economic_resources`, `update_resource_state` return `Any` | No Pydantic validation on these responses |
| **No live ERP integration** | Mock client only; ERPLibre XML-RPC not implemented | Cannot sync real inventory |
| **No bidirectional sync** | One-way ERP -> Nondominium only | Changes in Nondominium not reflected in ERP |
| **ActionHash format unverified** | Serialization format from hc-http-gw needs verification with a running instance | Hashes may need format adjustments |

---

## 8. hc-http-gw Protocol

All communication with Holochain goes through HTTP GET requests:

```
GET {host}/{dna_hash}/{app_id}/zome_resource/{fn_name}?payload={base64url_json}
```

- **Payloads**: Base64url encoded (RFC 4648), no padding (`=` stripped), compact JSON (`separators=(",", ":")`)
- **No-arg functions**: Functions taking `()` (like `get_all_resource_specifications`) omit `?payload=` entirely
- **Default port**: 8888
- **GET-only**: No POST support
- **No signals**: Request-response only

See the [PoC spec](../specifications/poc/hc_http_gw_poc_spec.md) Section 3 for full protocol details and limitations.
