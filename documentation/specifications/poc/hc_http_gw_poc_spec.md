# hc-http-gw PoC Implementation Specification

> **Document Type**: PoC Implementation Guide
> **Version**: 1.1
> **Last Updated**: 2026-02-12
> **Related Documents**:
> - [Requirements](../../requirements/erp_bridge_requirements.md)
> - [Technical Specifications](../erp_bridge_specifications.md)
> - [Architecture (what IS built)](../../implementation/architecture.md)
> - [Module Reference](../../implementation/module-reference.md)
> - [Development Guide](../../implementation/development-guide.md)

> **Note**: This document is a **specification** — it describes the planned approach and design for the PoC. For documentation of what has actually been implemented, see the [Implementation docs](../../implementation/architecture.md). Code examples that previously appeared in this document have been replaced with cross-references to the implementation docs, which track the actual source code.

---

## 1. Overview and Goals

### 1.1 Purpose

This document provides step-by-step implementation details for the Proof of Concept (PoC) using the Holochain HTTP Gateway (`hc-http-gw`) to bridge ERPLibre with Nondominium.

### 1.2 PoC Goals

- **Speed to prototype**: Get a working demo in hours, not days
- **Simplicity**: Use familiar HTTP requests with Python's `requests` library
- **Zero custom bridge code**: Leverage pre-built `hc-http-gw`
- **Proof, not production**: Demonstrate feasibility without real-time signals

### 1.3 What hc-http-gw Provides

The [Holochain HTTP Gateway](https://github.com/holochain/hc-http-gw) exposes Holochain zome functions as REST endpoints, allowing traditional HTTP clients to interact with Holochain apps.

---

## 2. Prerequisites and Setup

### 2.1 Required Components

| Component | Version | Purpose |
|-----------|---------|---------|
| Nix | Latest | Dev shell providing Holochain toolchain |
| Holochain | 0.6.x (hdi 0.7.0 / hdk 0.6.0) | Distributed app framework |
| hc-http-gw | Latest | HTTP-to-WebSocket bridge |
| Nondominium hApp | Latest | ValueFlows-compliant resource app |
| Python | 3.10+ | Bridge scripts |
| uv | Latest | Python virtual environment and package management |

### 2.2 Environment Setup

See the [Development Guide](../../implementation/development-guide.md) for detailed setup instructions.

---

## 3. hc-http-gw Configuration

### 3.1 API Format

**Critical Understanding**: hc-http-gw is **GET-only** with a specific URL format:

```
GET http://{host}/{dna-hash}/{coordinator-id}/{zome}/{function}?payload={base64-encoded-json}
```

| Component | Description | Example |
|-----------|-------------|---------|
| `{host}` | Gateway host and port | `localhost:8888` |
| `{dna-hash}` | Holochain DNA hash | `uhC0k...` |
| `{coordinator-id}` | App/coordinator ID | `nondominium` |
| `{zome}` | Zome name | `zome_resource` |
| `{function}` | Zome function name | `create_resource_specification` |
| `payload` | Base64-encoded JSON input | `eyJuYW1lIjoi...` |

### 3.2 Environment Variables

```bash
# hc-http-gw configuration (set via environment when running hc-http-gw)
HC_GW_ALLOWED_FNS_nondominium=create_resource_specification,get_all_resource_specifications,...
# The full list of allowed functions (including zome_gouvernance functions) is in scripts/setup_conductor.sh
```

```bash
# Python bridge configuration (.env file)
HC_GW_URL=http://127.0.0.1:8888
HC_GW_TIMEOUT=30
HC_APP_ID=nondominium
HC_DNA_HASH=<discovered after installing the hApp>
```

### 3.3 Nix-Based Setup (PoC)

The bridge repo has its own `flake.nix` that provides the complete dev environment (holonix + Python 3.12 + uv). See the [Development Guide](../../implementation/development-guide.md) for full setup instructions.

> **Note**: Docker Compose may be used for future production deployments. See the [Technical Specifications](../erp_bridge_specifications.md) for the Docker configuration.

### 3.4 Known Limitations

| Limitation | Impact | Workaround |
|------------|--------|------------|
| **GET-only** | Cannot use POST for zome calls | Base64-encode payload in query string |
| **No signals** | Cannot receive push notifications | Implement periodic polling |
| **No webhooks** | ERP cannot be notified of changes | Manual refresh or scheduled sync |
| **URL length limits** | Large payloads may fail | Keep payloads small, use hashes |

---

## 4. ERPLibre Integration

### 4.1 ERPLibre API Connection (Aspirational)

> **Note**: This section describes the planned live ERPLibre integration. The current PoC uses a mock ERP client (`bridge/erp_mock.py`). See the [Module Reference](../../implementation/module-reference.md#5-erp_mockpy--mock-erp-client) for the mock implementation.

```python
import xmlrpc.client
import base64
import json
import requests

class ERPLibreClient:
    def __init__(self, url, db, username, password):
        self.url = url
        self.db = db
        self.username = username
        self.password = password

        # Authenticate
        common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
        self.uid = common.authenticate(db, username, password, {})
        self.models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

    def get_available_products(self):
        """Read products with available quantity."""
        return self.models.execute_kw(
            self.db, self.uid, self.password,
            'product.product', 'search_read',
            [[('qty_available', '>', 0)]],
            {'fields': ['name', 'default_code', 'qty_available', 'uom_id', 'categ_id']}
        )
```

### 4.2 Data Mapping

For the actual mapping implementation, see the [Module Reference — mapper.py](../../implementation/module-reference.md#4-mapperpy--erp-to-nondominium-mapping).

Key field name differences from REA/ValueFlows conventions:
- Uses `category` (NOT `default_unit`)
- Uses `spec_hash` (NOT `conforms_to`)
- Uses `current_location` (NOT `location`)

---

## 5. Implementation Steps

### 5.1 Phase 1: Environment Setup (Week 1)

See the [Development Guide](../../implementation/development-guide.md) for complete setup instructions covering:
- Nix dev environment
- Conductor and hc-http-gw startup
- DNA hash discovery
- Python environment and test data

The PoC uses a **mock ERP client** (`bridge/erp_mock.py`) with sample Sensorica fab-lab products instead of a live ERPLibre instance.

### 5.2 Phase 2: Bridge Development (Week 2)

The bridge is implemented across 7 Python modules. See the [Module Reference](../../implementation/module-reference.md) for the full API documentation of each module:

- **Gateway Client**: `bridge/gateway_client.py` — typed HTTP client wrapping all zome functions
- **Sync Pipeline**: `bridge/sync.py` — orchestrates ERP → Nondominium sync with idempotency

### 5.3 Phase 3: Cross-Organizational Discovery (Week 3)

**Resource Discovery**: Implemented in `bridge/discovery.py`. See the [Module Reference](../../implementation/module-reference.md#6-discoverypy--cross-org-resource-discovery) for the full API.

**Transfer Custody**: The `transfer_custody` function is bridged via `gateway_client.transfer_custody()`.

**Governance (Commitments, Events, PPRs)**: The governance zome (`zome_gouvernance`) provides `propose_commitment`, `log_economic_event`, and PPR generation. These are fully bridged via `bridge/gateway_client.py` (19 governance methods) and orchestrated by `bridge/use_process.py`. See the [Module Reference](../../implementation/module-reference.md#8-use_processpy--use-process-orchestration) for the full API.

### 5.4 Phase 4: Demo and Documentation (Week 4)

**Full Demo Script**: Implemented as `scripts/demo_full_flow.py`. The demo exercises the complete bridge flow in 5 steps:

1. **SYNC** — Publish ERP products as ResourceSpecifications and EconomicResources
2. **DISCOVER** — Find resources by category via the DHT
3. **COMMIT** — Propose a `VfAction.Use` commitment for a discovered resource
4. **EVENT** — Log the economic event with optional PPR generation
5. **VERIFY** — Query commitments, events, and validation receipts to confirm state

See the [Development Guide](../../implementation/development-guide.md#55-running-the-end-to-end-demo) for instructions on running the demo.

---

## 7. Testing and Validation

### 7.1 Unit Tests

The project includes 101 tests across 8 test files. See the [Development Guide](../../implementation/development-guide.md#3-running-tests) for test commands and the [Module Reference](../../implementation/module-reference.md#10-test-coverage-summary) for per-file coverage details.

### 7.2 Integration Test Checklist

| Test Case | Expected Result | Pass/Fail |
|-----------|-----------------|-----------|
| Python tests pass | `pytest -v` reports 101 passed | |
| hc-http-gw reachable | `curl http://localhost:8888/` returns response | |
| Create ResourceSpecification | Returns `CreateResourceSpecificationOutput` with `spec_hash` | |
| Create EconomicResource | Returns `CreateEconomicResourceOutput` with `resource_hash` | |
| Get all economic resources | Returns `GetAllEconomicResourcesOutput` with resources list | |
| Get all resource specifications | Returns `GetAllResourceSpecificationsOutput` | |
| Transfer custody | Returns `TransferCustodyOutput` with updated resource | |
| Update resource state | Returns updated resource with new state | |
| Propose commitment | Returns `ProposeCommitmentOutput` with `commitment_hash` | |
| Log economic event | Returns `LogEconomicEventOutput` with `event_hash` | |
| Get all commitments | Returns list of `Commitment` objects | |

### 7.3 Validation Procedures

```bash
# 1. Verify hc-http-gw is running (port 8888)
curl http://localhost:8888/

# 2. Test zome call (get all economic resources — no payload needed)
curl "http://localhost:8888/<DNA_HASH>/nondominium/zome_resource/get_all_economic_resources"

# 3. Run Python unit tests
pytest -v

# 4. Run a manual sync test (requires running conductor)
python -c "
from bridge.config import GatewayConfig
from bridge.gateway_client import HolochainGatewayClient
gw = HolochainGatewayClient(GatewayConfig.from_env())
print('Health check:', gw.health_check())
"
```

---

## 8. Known Limitations

### 8.1 hc-http-gw Limitations

| Limitation | Description | PoC Impact | Production Solution |
|------------|-------------|------------|---------------------|
| GET-only | No POST method support | Must base64-encode all payloads | Use Node.js bridge |
| No signals | Cannot receive push notifications | Must poll for updates | Implement webhooks |
| URL length | Very large payloads may exceed URL limits | Keep data small | Use Node.js bridge |
| Single DNA | One DNA hash per gateway instance | Must know DNA hash | Config management |

### 8.2 PoC-Specific Limitations

| Limitation | Reason | Future Enhancement |
|------------|--------|-------------------|
| Unidirectional sync | PoC scope | Implement bidirectional in production |
| Single ERP | ERPLibre focus | Add Dolibarr, ERPNext modules |
| Periodic polling | No real-time | Add signal/webhook support |
| Mock ERP + Odoo addon (PoC) | Live ERPLibre XML-RPC not implemented | Implement full XML-RPC client |
| PPR output types use `Any` | Complex cryptographic types | Tighten Pydantic models for production |
| Timestamp format unverified | May be `{secs, nanos}` struct | Verify with running Holochain instance |

### 8.3 Workarounds

**For large payloads:**
```python
# Instead of sending full product data, send just the hash
# and let Nondominium fetch details if needed
def publish_minimal(product):
    return {
        "name": product['name'][:50],  # Truncate
        "external_id": product['id']    # Reference for lookup
    }
```

**For polling updates:**
```python
import time

def poll_for_changes(bridge, interval_seconds=60):
    """Poll for new resources periodically."""
    last_count = 0
    while True:
        resources = bridge.discover_resources()
        if len(resources) > last_count:
            print(f"New resources detected: {len(resources) - last_count}")
            last_count = len(resources)
        time.sleep(interval_seconds)
```

---

## 9. Next Steps After PoC

### 9.1 Immediate Next Steps

1. **Document findings** from PoC implementation
2. **Record demo video** showing full flow
3. **Identify gaps** for production requirements
4. **Plan Node.js bridge** development

### 9.2 Production Migration Path

1. Deploy Node.js bridge alongside hc-http-gw
2. Update ERPLibre module to call new bridge
3. Implement webhook handler for signals
4. Add proper zome call signing
5. Deprecate hc-http-gw

### 9.3 Feature Additions

| Feature | Priority | Effort | Status |
|---------|----------|--------|--------|
| Bidirectional sync | High | Medium | Not started |
| Real-time signals | High | Medium | Not started |
| ERPLibre Odoo module | Medium | High | Partially done (PoC addon at `docker/addons/nondominium_connector/`) |
| Multi-ERP support | Medium | High | Not started |
| PPR dashboard | Low | Medium | Not started |

---

## 10. References

- [hc-http-gw GitHub](https://github.com/holochain/hc-http-gw)
- [hc-http-gw spec.md](https://github.com/holochain/hc-http-gw/blob/main/spec.md)
- [Holochain Client JS](https://github.com/holochain/holochain-client-js)
- [ERPLibre GitHub](https://github.com/ERPLibre/ERPLibre)
- [Nondominium Repository](https://github.com/Sensorica/nondominium)
