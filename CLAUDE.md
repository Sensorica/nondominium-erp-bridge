# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Summary

Python bridge connecting ERP systems (currently mocked ERPLibre) to **Nondominium** (a Holochain app for peer-to-peer resource sharing) via **hc-http-gw**. This is a Proof of Concept — one-way sync, single org, mock ERP only.

## Development Setup

Requires Nix with flakes enabled. The `flake.nix` uses holonix `main-0.6` and provides holochain, hc, hc-http-gw, python312, and uv.

```bash
nix develop
uv venv .venv && source .venv/bin/activate
uv pip install -e ".[dev]"
```

## Commands

```bash
# Tests (101 total, no infrastructure needed)
pytest                                    # all tests
pytest tests/test_models.py               # Resource model serialization (13 tests)
pytest tests/test_gateway_client.py       # Resource HTTP client (13 tests)
pytest tests/test_mapper.py               # ERP→Nondominium mapping (8 tests)
pytest tests/test_discovery.py            # Cross-org discovery (8 tests)
pytest tests/test_sync.py                 # Sync pipeline + idempotency (11 tests)
pytest tests/test_governance_models.py    # Governance model serialization (25 tests)
pytest tests/test_governance_gateway.py   # Governance HTTP client (12 tests)
pytest tests/test_use_process.py          # Use process orchestration (6 tests)
pytest -k "test_name"                     # single test by name

# Linting & type checking
ruff check .                        # lint (E, F, I, W rules)
ruff format --check .               # format check
mypy bridge/                        # strict type checking

# Live infrastructure (requires running Holochain conductor + hc-http-gw)
bash scripts/setup_conductor.sh     # start conductor + gateway
python scripts/smoke_test.py        # integration test
python scripts/create_test_data.py  # populate from mock ERP
python scripts/sync_inventory.py    # run full sync pipeline
python scripts/demo_full_flow.py    # full demo: sync→discover→commit→event→verify

# Docker (Odoo/ERPLibre)
cd docker && docker compose up -d   # start Odoo 17 + PostgreSQL
python docker/init-data.py          # seed sample products
```

## Architecture

```
ERP (Mock) → Mapper → Pydantic Models → GatewayClient → hc-http-gw → Holochain
```

Eight modules in `bridge/`, each with a single responsibility:

- **config.py** — `GatewayConfig` frozen dataclass, loads from env vars (`HC_GW_URL`, `HC_GW_TIMEOUT`, `HC_APP_ID`, `HC_DNA_HASH`)
- **models.py** — Pydantic v2 models mapping 1:1 to Rust zome types. Covers both `zome_resource` (specs, resources, governance rules) and `zome_gouvernance` (commitments, events, claims, validation, PPR)
- **gateway_client.py** — `HolochainGatewayClient` wrapping `zome_resource` and `zome_gouvernance` coordinator functions as typed Python methods. Multi-zome support via `zome` parameter on `_call()`
- **mapper.py** — Pure functions converting `MockProduct` → `ResourceSpecificationInput` / `EconomicResourceInput`
- **erp_mock.py** — `MockERPClient` simulating ERPLibre's `product.product` model with 4 sample Sensorica fab-lab products
- **discovery.py** — `ResourceDiscovery` providing cross-org resource discovery via the Nondominium DHT (category-based search, spec-based lookup)
- **sync.py** — `NondominiumBridge` orchestrating the full sync pipeline with `SyncState` (JSON-file idempotency) and per-item error handling
- **use_process.py** — `UseProcess` orchestrating the Use lifecycle: propose commitment → log economic event (with optional PPR generation)

## hc-http-gw Protocol

All Holochain calls go through HTTP GET:
```
GET {host}/{dna_hash}/{app_id}/{zome}/{fn_name}?payload={base64url_json}
```

Two zomes are exposed: `zome_resource` (resource specs, economic resources, governance rules) and `zome_gouvernance` (commitments, events, claims, validation, PPR).

- Payloads: base64url (RFC 4648), **no padding** (`=` stripped), compact JSON (`separators=(",", ":")`)
- Functions taking `()` (like `get_all_resource_specifications`) omit `?payload=` entirely
- The DNA hash is discovered at runtime via `hc sandbox call list-apps` and set in `.env`

## Critical Naming Conventions

Pydantic field names **must match Rust zome field names exactly** (hc-http-gw uses JSON transcoding):

| This project uses | NOT the REA/ValueFlows name |
|---|---|
| `category` | ~~`default_unit`~~ |
| `spec_hash` | ~~`conforms_to`~~ |

`ResourceState` enum values are **PascalCase** strings: `"PendingValidation"`, `"Active"`, `"Maintenance"`, `"Retired"`, `"Reserved"`.

## Nondominium Rust Source Locations

When verifying or updating models, check these files in the `nondominium` sibling repo:

**zome_resource (resources & specs):**
- **Integrity types**: `dnas/nondominium/zomes/integrity/zome_resource/src/lib.rs`
- **ResourceSpecification coordinator**: `dnas/nondominium/zomes/coordinator/zome_resource/src/resource_specification.rs`
- **EconomicResource coordinator**: `dnas/nondominium/zomes/coordinator/zome_resource/src/economic_resource.rs`
- **GovernanceRule coordinator**: `dnas/nondominium/zomes/coordinator/zome_resource/src/governance_rule.rs`

**zome_gouvernance (commitments, events, PPR):**
- **Integrity types + VfAction enum**: `dnas/nondominium/zomes/integrity/zome_gouvernance/src/lib.rs`
- **PPR types (ParticipationClaimType, PerformanceMetrics)**: `dnas/nondominium/zomes/integrity/zome_gouvernance/src/ppr.rs`
- **Commitment coordinator**: `dnas/nondominium/zomes/coordinator/zome_gouvernance/src/commitment.rs`
- **EconomicEvent coordinator**: `dnas/nondominium/zomes/coordinator/zome_gouvernance/src/economic_event.rs`
- **PPR coordinator**: `dnas/nondominium/zomes/coordinator/zome_gouvernance/src/ppr.rs`
- **Validation coordinator**: `dnas/nondominium/zomes/coordinator/zome_gouvernance/src/validation.rs`

## Testing Patterns

- `pytest-httpserver` provides a real HTTP server for `test_gateway_client.py` — no mocking of `requests` internals
- Tests verify URL construction, base64url encoding correctness, payload omission for unit functions, and Pydantic round-trip serialization
- Model tests validate that serialized JSON field names match what Holochain expects

## Build System Notes

- Build backend is `setuptools.build_meta` (not legacy backend)
- Python >=3.10 required (uses `X | Y` union syntax)
- Ruff configured for line-length 100, mypy in strict mode
