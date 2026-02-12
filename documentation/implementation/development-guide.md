# Development Guide

> **Document Type**: Implementation Reference
> **Last Updated**: 2026-02-12
> **Related Documents**:
> - [Architecture](architecture.md)
> - [Module Reference](module-reference.md)

---

## 1. Prerequisites

- **Nix** with flakes enabled (`experimental-features = nix-command flakes` in `~/.config/nix/nix.conf`)
- **nondominium.happ** built from the [Nondominium repo](https://github.com/Sensorica/nondominium) (needed for live infrastructure only, not for tests)

---

## 2. Environment Setup

```bash
# Enter the Nix dev shell (provides holochain, hc, hc-http-gw, Python 3.12, uv)
nix develop

# Create Python virtual environment and install dependencies
uv venv .venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

The `flake.nix` uses holonix `main-0.6` and provides:
- Holochain conductor (hdi 0.7.0 / hdk 0.6.0)
- `hc` CLI tool
- `hc-http-gw` HTTP gateway
- Python 3.12
- `uv` package manager

---

## 3. Running Tests

All 101 tests run without any infrastructure (no Holochain conductor or hc-http-gw needed).

```bash
# All tests
pytest

# With verbose output
pytest -v

# Individual test files
pytest tests/test_models.py               # 13 tests — Resource model serialization
pytest tests/test_gateway_client.py       # 13 tests — Resource HTTP client (mocked server)
pytest tests/test_mapper.py               # 8 tests  — ERP→Nondominium mapping
pytest tests/test_discovery.py            # 8 tests  — Cross-org resource discovery
pytest tests/test_sync.py                 # 11 tests — Sync pipeline + idempotency
pytest tests/test_governance_models.py    # 31 tests — Governance model serialization
pytest tests/test_governance_gateway.py   # 11 tests — Governance gateway methods
pytest tests/test_use_process.py          # 6 tests  — Use process orchestration

# Single test by name
pytest -k "test_name"
```

Gateway, discovery, sync, and governance tests use `pytest-httpserver` which starts a real local HTTP server — no mocking of `requests` internals.

---

## 4. Linting and Type Checking

```bash
# Lint (E, F, I, W rules)
ruff check .

# Format check
ruff format --check .

# Auto-fix lint issues
ruff check --fix .

# Auto-format
ruff format .

# Strict type checking
mypy bridge/
```

Configuration is in `pyproject.toml`:
- Ruff: line-length 100
- Mypy: strict mode

---

## 5. Running with Live Infrastructure

### 5.1 Start Conductor and Gateway

```bash
# 1. Enter the Nix dev shell (if not already)
nix develop

# 2. Build the Nondominium hApp (if not already built)
cd ../nondominium && npm run build:happ && cd -

# 3. Start conductor + hc-http-gw on port 8888
bash scripts/setup_conductor.sh
```

### 5.2 Discover DNA Hash

In a separate terminal:

```bash
# Discover the DNA hash
hc sandbox call list-apps --directories .local/sandbox

# Copy .env.example and set the DNA hash
cp .env.example .env
# Edit .env: HC_DNA_HASH=uhC0k...
```

### 5.3 Run Scripts

```bash
# Integration smoke test (creates a spec and reads it back)
python scripts/smoke_test.py

# Populate Nondominium from mock ERP products
python scripts/create_test_data.py

# Run the full sync pipeline (with idempotency)
python scripts/sync_inventory.py

# Run the full end-to-end demo (sync → discover → commit → event → verify)
python scripts/demo_full_flow.py
```

### 5.4 Docker / Odoo Development

An Odoo 17 + PostgreSQL environment is provided via Docker Compose for developing and testing the `nondominium_connector` addon.

```bash
# Start Odoo and PostgreSQL
cd docker && docker compose up -d

# Seed sample products
python docker/init-data.py

# Access Odoo at http://localhost:8069 (admin/admin)
```

See `docker/README.md` for full instructions on the Odoo setup, addon installation, and configuration.

The `nondominium_connector` addon is located at `docker/addons/nondominium_connector/` and provides:
- Settings page for Holochain gateway configuration
- "Sync to Nondominium" button on product forms
- Sync status tracking per product

### 5.5 Running the End-to-End Demo

The demo script (`scripts/demo_full_flow.py`) exercises the complete bridge flow. It requires a running Holochain conductor + hc-http-gw and `HC_DNA_HASH` set in `.env`.

```bash
python scripts/demo_full_flow.py
```

The demo executes 5 steps:
1. **SYNC** — Publishes ERP products as ResourceSpecifications and EconomicResources
2. **DISCOVER** — Finds resources by category via the DHT
3. **COMMIT** — Proposes a `VfAction.Use` commitment for a discovered resource
4. **EVENT** — Logs the economic event with optional PPR generation
5. **VERIFY** — Queries commitments, events, and validation receipts to confirm state

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HC_GW_URL` | `http://127.0.0.1:8888` | hc-http-gw URL |
| `HC_GW_TIMEOUT` | `30` | Request timeout (seconds) |
| `HC_APP_ID` | `nondominium` | Holochain app ID |
| `HC_DNA_HASH` | (none) | DNA hash from `hc sandbox call list-apps` |

---

## 6. Extending the Bridge

### Adding a New Zome Function Wrapper

1. Check the zome function signature in the [Nondominium source](https://github.com/Sensorica/nondominium) (see [Architecture](architecture.md) for file locations)

2. If needed, add input/output Pydantic models to `bridge/models.py`:
   ```python
   class NewFunctionInput(BaseModel):
       field_name: str  # Must match Rust field name exactly
   ```

3. Add the method to `bridge/gateway_client.py`:
   ```python
   def new_function(self, input_data: NewFunctionInput) -> NewFunctionOutput:
       data = self._call("new_function", input_data.model_dump(mode="json"))
       return NewFunctionOutput.model_validate(data)
   ```

   For governance zome functions, pass the `zome` parameter:
   ```python
   def new_governance_function(self, input_data: NewInput) -> NewOutput:
       data = self._call("new_function", input_data.model_dump(mode="json"),
                         zome=self.ZOME_GOUVERNANCE)
       return NewOutput.model_validate(data)
   ```

4. Add the function name to `HC_GW_ALLOWED_FNS_nondominium` in `scripts/setup_conductor.sh`

5. Add tests in `tests/test_gateway_client.py` (resource zome) or `tests/test_governance_gateway.py` (governance zome) using `pytest-httpserver`

### Adding a New ERP Source

1. Create a new module (e.g., `bridge/erp_erplibre.py`) implementing the same interface as `MockERPClient`:
   ```python
   class ERPLibreClient:
       def get_all_products(self) -> list[MockProduct]: ...
       def get_available_products(self) -> list[MockProduct]: ...
       def get_product_by_id(self, product_id: int) -> MockProduct | None: ...
   ```

2. Use the same `MockProduct` dataclass (or create a protocol/interface) so existing mappers work unchanged

3. Update `NondominiumBridge` usage in scripts to accept the new client

### Developing the Odoo Addon

The PoC Odoo addon is at `docker/addons/nondominium_connector/`. To develop:

1. Start Docker: `cd docker && docker compose up -d`
2. Edit addon files (models, views, controllers)
3. Restart Odoo: `docker compose restart odoo`
4. Upgrade the module in Odoo: Apps → Nondominium Connector → Upgrade

### Adding New Model Fields

When Nondominium zome types change:

1. Check the Rust source in `nondominium/dnas/nondominium/zomes/`:
   - **Resource integrity types**: `integrity/zome_resource/src/lib.rs`
   - **Resource coordinator types**: `coordinator/zome_resource/src/resource_specification.rs`, `economic_resource.rs`, `governance_rule.rs`
   - **Governance integrity types**: `integrity/zome_gouvernance/src/lib.rs`, `ppr.rs`
   - **Governance coordinator types**: `coordinator/zome_gouvernance/src/commitment.rs`, `economic_event.rs`, `ppr.rs`, `validation.rs`

2. Update the corresponding Pydantic model in `bridge/models.py` — field names **must match exactly**

3. Update mappers in `bridge/mapper.py` if the new fields should be populated from ERP data

4. Update tests to cover the new fields

---

## 7. Build System

- Build backend: `setuptools.build_meta` (not legacy backend)
- Python: >=3.10 (uses `X | Y` union syntax)
- Package management: `uv` (via Nix)
- Dependencies declared in `pyproject.toml` under `[project.dependencies]` and `[project.optional-dependencies.dev]`

For machine-oriented quick reference, see [CLAUDE.md](../../CLAUDE.md) in the project root.
