# hc-http-gw PoC Implementation Specification

> **Document Type**: PoC Implementation Guide
> **Version**: 1.0
> **Last Updated**: 2026-02-05
> **Related Documents**:
> - [Requirements](../../requirements/erp_bridge_requirements.md)
> - [Technical Specifications](../erp_bridge_specifications.md)

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

```bash
# Clone the bridge repository
git clone https://github.com/Sensorica/nondominium-erp-bridge.git
cd nondominium-erp-bridge

# Enter the Nix dev shell (provides holochain, hc, hc-http-gw, Python 3.12, uv)
nix develop

# Create .env from example
cp .env.example .env
# Edit .env to set HC_DNA_HASH after running the conductor (see Section 5.1)

# Set up Python environment
uv venv .venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

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
# The full list of allowed functions is in scripts/setup_conductor.sh
```

```bash
# Python bridge configuration (.env file)
HC_GW_URL=http://127.0.0.1:8888
HC_GW_TIMEOUT=30
HC_APP_ID=nondominium
HC_DNA_HASH=<discovered after installing the hApp>
```

### 3.3 Nix-Based Setup (PoC)

The bridge repo has its own `flake.nix` that provides the complete dev environment (holonix + Python 3.12 + uv):

```bash
# 1. Enter the Nix dev shell (provides holochain, hc, hc-http-gw, python, uv)
nix develop

# 2. Build the hApp (if not already built)
cd ../nondominium && npm run build:happ && cd -

# 3. Run the automated setup script
bash scripts/setup_conductor.sh
# This starts a sandbox conductor + hc-http-gw on port 8888

# 4. In another terminal, discover the DNA hash
hc sandbox call list-apps --directories .local/sandbox

# 5. Set the DNA hash in .env
echo "HC_DNA_HASH=uhC0k..." >> .env
```

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

### 4.1 ERPLibre API Connection

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

```python
# bridge/mapper.py (actual implementation)
from bridge.models import ResourceSpecificationInput, EconomicResourceInput

def product_to_resource_spec(product):
    """Map an ERP product to a Nondominium ResourceSpecificationInput."""
    return ResourceSpecificationInput(
        name=product['name'],
        description=product.get('description', f"SKU: {product.get('default_code', 'N/A')}"),
        category=product.get('category', 'general'),  # NOTE: `category`, not `default_unit`
        image_url=product.get('image_url'),
        tags=product.get('tags', []),
        governance_rules=[],
    )

def product_to_economic_resource(product, spec_hash):
    """Map an ERP product to a Nondominium EconomicResourceInput."""
    return EconomicResourceInput(
        spec_hash=spec_hash,       # NOTE: `spec_hash`, not `conforms_to`
        quantity=product['qty_available'],
        unit=product.get('uom_name', 'unit'),
        current_location=None,     # NOTE: `current_location`, not `location`
    )
```

---

## 5. Implementation Steps

### 5.1 Phase 1: Environment Setup (Week 1)

**Step 1.1: Set Up Nix Dev Environment**

```bash
# Enter the bridge Nix dev shell (provides holochain, hc, hc-http-gw, Python 3.12, uv)
nix develop

# Build the Nondominium hApp (if not already built)
cd ../nondominium && npm run build:happ && cd -
```

**Step 1.2: Start Holochain Conductor and hc-http-gw**

```bash
# Run the setup script
bash scripts/setup_conductor.sh

# This script:
#   1. Checks prerequisites (holochain, hc, nondominium.happ)
#   2. Creates a sandbox conductor
#   3. Starts hc-http-gw on port 8888 with allowed functions
```

**Step 1.3: Discover DNA Hash and Configure**

```bash
# In another terminal, discover the DNA hash
hc sandbox call list-apps --directories .local/sandbox

# Copy .env.example and set the DNA hash
cp .env.example .env
# Edit .env: HC_DNA_HASH=uhC0k...
```

**Step 1.4: Set Up Python Environment and Test Data**

```bash
# Set up Python with uv
uv venv .venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# Run tests to verify setup
pytest -v
```

The PoC uses a **mock ERP client** (`bridge/erp_mock.py`) with sample Sensorica fab-lab products instead of a live ERPLibre instance. This allows development and testing without ERP infrastructure.

### 5.2 Phase 2: Bridge Development (Week 2)

**Step 2.1: Gateway Client**

The actual implementation (`bridge/gateway_client.py`) uses Pydantic models and base64url encoding:

```python
# bridge/gateway_client.py (simplified excerpt)
import base64
import json
import requests

class HolochainGatewayClient:
    ZOME = "zome_resource"

    def __init__(self, config):
        self.config = config  # GatewayConfig with url, dna_hash, app_id, timeout
        self._session = requests.Session()

    @staticmethod
    def _encode_payload(data):
        """Base64url-encode a JSON payload (RFC 4648, no padding)."""
        json_bytes = json.dumps(data, separators=(",", ":")).encode()
        return base64.urlsafe_b64encode(json_bytes).rstrip(b"=").decode()

    def _call(self, fn_name, payload=None):
        """Call a zome function via hc-http-gw and return parsed JSON."""
        url = f"{self.config.url}/{self.config.dna_hash}/{self.config.app_id}/{self.ZOME}/{fn_name}"
        params = {}
        if payload is not None:
            params["payload"] = self._encode_payload(payload)
        resp = self._session.get(url, params=params, timeout=self.config.timeout)
        resp.raise_for_status()
        return resp.json()

    # Typed methods return Pydantic models:
    def create_resource_specification(self, input_data):
        data = self._call("create_resource_specification", input_data.model_dump(mode="json"))
        return CreateResourceSpecificationOutput.model_validate(data)

    def get_all_economic_resources(self):
        data = self._call("get_all_economic_resources")  # No payload for () functions
        return GetAllEconomicResourcesOutput.model_validate(data)

    def transfer_custody(self, input_data):
        data = self._call("transfer_custody", input_data.model_dump(mode="json"))
        return TransferCustodyOutput.model_validate(data)
    # ... see bridge/gateway_client.py for full implementation
```

**Step 2.2: Sync Script**

```python
# Example sync script using the bridge modules
from bridge.config import GatewayConfig
from bridge.erp_mock import MockERPClient
from bridge.gateway_client import HolochainGatewayClient
from bridge.mapper import product_to_resource_spec, product_to_economic_resource

def sync_inventory():
    """Sync ERP inventory to Nondominium."""

    # Initialize clients
    erp = MockERPClient()  # Replace with ERPLibreClient for real ERP
    gw = HolochainGatewayClient(GatewayConfig.from_env())

    # Get available products
    products = erp.get_available_products()
    print(f"Found {len(products)} products to sync")

    for product in products:
        # Create ResourceSpecification (uses `category`, not `default_unit`)
        spec_input = product_to_resource_spec(product)
        result = gw.create_resource_specification(spec_input)
        spec_hash = result.spec_hash
        print(f"Created spec: {spec_hash}")

        # Create EconomicResource (uses `spec_hash`, not `conforms_to`)
        resource_input = product_to_economic_resource(product, spec_hash)
        resource_result = gw.create_economic_resource(resource_input)
        print(f"Created resource: {resource_result.resource_hash}")

if __name__ == '__main__':
    sync_inventory()
```

### 5.3 Phase 3: Cross-Organizational Discovery (Week 3)

**Step 3.1: Resource Discovery**

```python
# Example: discovering resources from the network
from bridge.config import GatewayConfig
from bridge.gateway_client import HolochainGatewayClient

def discover_resources():
    """Discover resources from other organizations."""

    gw = HolochainGatewayClient(GatewayConfig.from_env())

    result = gw.get_all_economic_resources()  # NOTE: `get_all_economic_resources`, not `get_all_resources`

    print("\n=== Available Resources ===\n")
    for resource in result.resources:
        print(f"  Quantity: {resource.quantity} {resource.unit}")
        print(f"  Location: {resource.current_location or 'Unknown'}")  # NOTE: `current_location`
        print(f"  Custodian: {resource.custodian}")
        print(f"  State: {resource.state.value}")
        print()

if __name__ == '__main__':
    discover_resources()
```

**Step 3.2: Transfer Custody**

The current Nondominium codebase supports `transfer_custody` as the available cross-organization action. `create_commitment` and `record_economic_event` are **not yet implemented** in the zome.

```python
# Example: transferring custody of a resource to another agent
from bridge.config import GatewayConfig
from bridge.gateway_client import HolochainGatewayClient
from bridge.models import TransferCustodyInput

def transfer_resource(resource_hash, new_custodian_pubkey):
    """Transfer custody of a resource to another organization."""

    gw = HolochainGatewayClient(GatewayConfig.from_env())

    input_data = TransferCustodyInput(
        resource_hash=resource_hash,
        new_custodian=new_custodian_pubkey,
    )

    result = gw.transfer_custody(input_data)
    print(f"Custody transferred: {result.updated_resource_hash}")
    return result
```

### 5.4 Phase 4: Demo and Documentation (Week 4)

**Step 4.1: Full Demo Script**

```python
# demo/full_demo.py
"""
ERP-Holochain Bridge PoC Demonstration

This script demonstrates the available flow:
1. Organization A publishes resources from ERP (mock)
2. Organization B discovers resources via Nondominium
3. Organization B requests custody transfer of a resource

Note: Steps for create_commitment and record_economic_event are
future scope — these zome functions do not yet exist in Nondominium.
"""

from bridge.config import GatewayConfig
from bridge.erp_mock import MockERPClient
from bridge.gateway_client import HolochainGatewayClient
from bridge.mapper import product_to_resource_spec, product_to_economic_resource

def demo():
    print("=" * 60)
    print("ERP-Holochain Bridge PoC Demo")
    print("=" * 60)

    # Setup clients
    erp = MockERPClient()
    gw = HolochainGatewayClient(GatewayConfig.from_env())

    # Step 1: Publish resources from mock ERP
    print("\n[Step 1] Publishing resources from mock ERP...")
    products = erp.get_available_products()
    for product in products:
        spec_input = product_to_resource_spec(product)
        spec_result = gw.create_resource_specification(spec_input)
        resource_input = product_to_economic_resource(product, spec_result.spec_hash)
        gw.create_economic_resource(resource_input)
        print(f"  Published: {product.name}")

    # Step 2: Discover resources
    print("\n[Step 2] Discovering resources from Nondominium...")
    result = gw.get_all_economic_resources()
    for r in result.resources:
        print(f"  Found: {r.quantity} {r.unit} (state: {r.state.value})")

    # Step 3: Transfer custody (the available cross-org action)
    print("\n[Step 3] Custody transfer available via transfer_custody()...")
    print("  (Requires a second agent's public key — see bridge/models.py TransferCustodyInput)")

    # Future steps (not yet implemented in Nondominium):
    # Step 4: create_commitment — request to use a resource
    # Step 5: record_economic_event — record usage with PPRs

    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)

if __name__ == '__main__':
    demo()
```

---

## 6. Code Examples

### 6.1 Actual Bridge Architecture

The PoC bridge is split across multiple modules in the `bridge/` package:

```
bridge/
├── __init__.py
├── config.py          # GatewayConfig loaded from .env
├── models.py          # Pydantic v2 models matching Rust zome types
├── gateway_client.py  # Typed HTTP client for hc-http-gw
├── mapper.py          # ERP product → Nondominium input mapping
└── erp_mock.py        # Mock ERP client with sample products
```

**Key models (`bridge/models.py`):**

```python
from pydantic import BaseModel, Field
from enum import Enum

class ResourceState(str, Enum):
    PENDING_VALIDATION = "PendingValidation"
    ACTIVE = "Active"
    MAINTENANCE = "Maintenance"
    RETIRED = "Retired"
    RESERVED = "Reserved"

class ResourceSpecification(BaseModel):
    name: str
    description: str
    category: str                          # NOT `default_unit`
    image_url: str | None = None
    tags: list[str] = Field(default_factory=list)
    is_active: bool = True

class EconomicResource(BaseModel):
    quantity: float
    unit: str
    custodian: str                         # AgentPubKey as base64 string
    current_location: str | None = None    # NOT `location`
    state: ResourceState = ResourceState.PENDING_VALIDATION

class ResourceSpecificationInput(BaseModel):
    name: str
    description: str
    category: str                          # NOT `default_unit`
    image_url: str | None = None
    tags: list[str] = Field(default_factory=list)
    governance_rules: list[GovernanceRuleInput] = Field(default_factory=list)

class EconomicResourceInput(BaseModel):
    spec_hash: str                         # NOT `conforms_to`
    quantity: float
    unit: str
    current_location: str | None = None    # NOT `location`

class TransferCustodyInput(BaseModel):
    resource_hash: str
    new_custodian: str                     # AgentPubKey
    request_contact_info: bool | None = None
```

**Encoding (`bridge/gateway_client.py`):**

```python
@staticmethod
def _encode_payload(data):
    """Base64url-encode a JSON payload (RFC 4648, no padding)."""
    json_bytes = json.dumps(data, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(json_bytes).rstrip(b"=").decode()
    # NOTE: urlsafe_b64encode (not b64encode), with padding stripped
```

See `bridge/gateway_client.py` for the complete typed client with all zome function wrappers.

### 6.2 Example: Simple Web Interface (Future)

```python
# web/app.py (example — not part of current PoC scaffolding)
"""
Simple Flask web interface for the PoC demo.
"""

from flask import Flask, render_template, jsonify
from bridge.config import GatewayConfig
from bridge.erp_mock import MockERPClient
from bridge.gateway_client import HolochainGatewayClient
from bridge.mapper import product_to_resource_spec, product_to_economic_resource

app = Flask(__name__)

erp = MockERPClient()
gw = HolochainGatewayClient(GatewayConfig.from_env())

@app.route('/api/local-products')
def local_products():
    """Get products from mock ERP."""
    products = erp.get_available_products()
    return jsonify([{"name": p.name, "qty": p.qty_available} for p in products])

@app.route('/api/network-resources')
def network_resources():
    """Get resources from Nondominium network."""
    result = gw.get_all_economic_resources()
    return jsonify([r.model_dump() for r in result.resources])

if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

---

## 7. Testing and Validation

### 7.1 Unit Tests

The PoC includes 34 unit tests covering models, gateway client, and mapper:

```bash
# Run all tests
pytest -v

# Run specific test modules
pytest tests/test_models.py -v      # Pydantic model validation
pytest tests/test_gateway.py -v     # Gateway client (mocked HTTP)
pytest tests/test_mapper.py -v      # ERP → Nondominium mapping
```

Example test (from `tests/test_mapper.py`):

```python
from bridge.erp_mock import MOCK_PRODUCTS
from bridge.mapper import product_to_resource_spec, product_to_economic_resource

def test_product_to_resource_spec():
    product = MOCK_PRODUCTS[0]
    spec = product_to_resource_spec(product)
    assert spec.name == product.name
    assert spec.category == product.category   # `category`, not `default_unit`
    assert spec.tags == product.tags

def test_product_to_economic_resource():
    product = MOCK_PRODUCTS[0]
    resource = product_to_economic_resource(product, "uhCkk_test_hash")
    assert resource.spec_hash == "uhCkk_test_hash"  # `spec_hash`, not `conforms_to`
    assert resource.quantity == product.qty_available
```

### 7.2 Integration Test Checklist

| Test Case | Expected Result | Pass/Fail |
|-----------|-----------------|-----------|
| Python tests pass | `pytest -v` reports 34 passed | |
| hc-http-gw reachable | `curl http://localhost:8888/` returns response | |
| Create ResourceSpecification | Returns `CreateResourceSpecificationOutput` with `spec_hash` | |
| Create EconomicResource | Returns `CreateEconomicResourceOutput` with `resource_hash` | |
| Get all economic resources | Returns `GetAllEconomicResourcesOutput` with resources list | |
| Get all resource specifications | Returns `GetAllResourceSpecificationsOutput` | |
| Transfer custody | Returns `TransferCustodyOutput` with updated resource | |
| Update resource state | Returns updated resource with new state | |

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
| No UI integration | PoC uses scripts | Build Odoo module UI |
| Periodic polling | No real-time | Add signal/webhook support |

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

| Feature | Priority | Effort |
|---------|----------|--------|
| Bidirectional sync | High | Medium |
| Real-time signals | High | Medium |
| ERPLibre Odoo module | Medium | High |
| Multi-ERP support | Medium | High |
| PPR dashboard | Low | Medium |

---

## 10. References

- [hc-http-gw GitHub](https://github.com/holochain/hc-http-gw)
- [hc-http-gw spec.md](https://github.com/holochain/hc-http-gw/blob/main/spec.md)
- [Holochain Client JS](https://github.com/holochain/holochain-client-js)
- [ERPLibre GitHub](https://github.com/ERPLibre/ERPLibre)
- [Nondominium Repository](https://github.com/Sensorica/nondominium)
