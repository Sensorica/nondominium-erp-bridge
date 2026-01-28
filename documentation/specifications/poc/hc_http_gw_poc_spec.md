# hc-http-gw PoC Implementation Specification

> **Document Type**: PoC Implementation Guide
> **Version**: 1.0
> **Last Updated**: 2026-01-27
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
| Docker | Latest | Container runtime |
| Docker Compose | Latest | Multi-container orchestration |
| ERPLibre | Latest | ERP system |
| Holochain | 0.4.x | Distributed app framework |
| hc-http-gw | Latest | HTTP-to-WebSocket bridge |
| Nondominium hApp | Latest | ValueFlows-compliant resource app |
| Python | 3.10+ | Bridge scripts |

### 2.2 Environment Setup

```bash
# Clone the PoC repository
git clone https://github.com/Sensorica/nondominium-erplibre-poc.git
cd nondominium-erplibre-poc

# Create environment file
cat > .env << EOF
ERPLIBRE_DB=erplibre_db
ERPLIBRE_USER=admin
ERPLIBRE_PASSWORD=admin
HC_GW_PORT=8090
HC_ADMIN_PORT=4444
HC_APP_PORT=8888
EOF
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
| `{host}` | Gateway host and port | `localhost:8090` |
| `{dna-hash}` | Holochain DNA hash | `uhC0k...` |
| `{coordinator-id}` | App/coordinator ID | `nondominium` |
| `{zome}` | Zome name | `zome_resource` |
| `{function}` | Zome function name | `create_resource_specification` |
| `payload` | Base64-encoded JSON input | `eyJuYW1lIjoi...` |

### 3.2 Environment Variables

```bash
# hc-http-gw configuration
HC_GW_ADMIN_WS_URL=ws://holochain:4444       # Admin WebSocket URL
HC_GW_ALLOWED_APP_IDS=nondominium            # Allowed app IDs (comma-separated)
HC_GW_PORT=8090                               # Gateway listening port
HC_GW_LOG_LEVEL=info                          # Logging level
```

### 3.3 Docker Compose for hc-http-gw

```yaml
services:
  hc-http-gw:
    image: holochain/hc-http-gw:latest
    ports:
      - "8090:8090"
    environment:
      - HC_GW_ADMIN_WS_URL=ws://holochain:4444
      - HC_GW_ALLOWED_APP_IDS=nondominium
      - HC_GW_PORT=8090
    networks:
      - internal
    depends_on:
      - holochain

  holochain:
    image: holochain/holochain:latest
    volumes:
      - ./happ:/happ
      - ./keys:/keys
    networks:
      - internal

networks:
  internal:
    internal: true
```

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
class NondominiumMapper:
    @staticmethod
    def product_to_resource_spec(product):
        """Map ERPLibre product to Nondominium ResourceSpecification."""
        return {
            "name": product['name'],
            "description": f"SKU: {product.get('default_code', 'N/A')}",
            "default_unit": product['uom_id'][1] if product.get('uom_id') else "unit",
            "governance_rules": []
        }

    @staticmethod
    def product_to_economic_resource(product, spec_hash):
        """Map ERPLibre product to Nondominium EconomicResource."""
        return {
            "conforms_to": spec_hash,
            "quantity": product['qty_available'],
            "unit": product['uom_id'][1] if product.get('uom_id') else "unit",
            "location": "warehouse"  # Could map from stock.warehouse
        }
```

---

## 5. Implementation Steps

### 5.1 Phase 1: Environment Setup (Week 1)

**Step 1.1: Deploy ERPLibre**

```bash
# Start ERPLibre with Docker
docker-compose -f docker-compose.erplibre.yml up -d

# Wait for initialization
sleep 30

# Create test database
docker exec erplibre odoo -d erplibre_db -i base --stop-after-init
```

**Step 1.2: Deploy Holochain and Nondominium**

```bash
# Start Holochain conductor
docker-compose -f docker-compose.holochain.yml up -d

# Install Nondominium hApp
docker exec holochain hc app install ./happ/nondominium.happ
```

**Step 1.3: Deploy hc-http-gw**

```bash
# Start the HTTP gateway
docker-compose -f docker-compose.gateway.yml up -d

# Verify gateway is running
curl http://localhost:8090/health
```

**Step 1.4: Create Test Data**

```python
# scripts/create_test_data.py
from erp_client import ERPLibreClient

erp = ERPLibreClient(
    url='http://localhost:8069',
    db='erplibre_db',
    username='admin',
    password='admin'
)

# Create Organization A products
org_a_products = [
    {'name': '3D Printer - Prusa MK4', 'default_code': 'PRUSA-MK4', 'qty_available': 1},
    {'name': 'Laser Cutter - 40W', 'default_code': 'LASER-40W', 'qty_available': 1},
    {'name': 'CNC Router', 'default_code': 'CNC-R01', 'qty_available': 2},
]

for product in org_a_products:
    erp.create_product(product)
```

### 5.2 Phase 2: Bridge Development (Week 2)

**Step 2.1: Gateway Client**

```python
# bridge/gateway_client.py
import requests
import base64
import json

class HcHttpGwClient:
    def __init__(self, gw_url, dna_hash, app_id="nondominium"):
        self.gw_url = gw_url
        self.dna_hash = dna_hash
        self.app_id = app_id

    def call_zome(self, zome, function, payload=None):
        """Call a zome function via hc-http-gw."""
        url = f"{self.gw_url}/{self.dna_hash}/{self.app_id}/{zome}/{function}"

        if payload:
            payload_b64 = base64.b64encode(
                json.dumps(payload).encode()
            ).decode()
            url += f"?payload={payload_b64}"

        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    def create_resource_specification(self, spec_input):
        """Create a ResourceSpecification."""
        return self.call_zome(
            "zome_resource",
            "create_resource_specification",
            spec_input
        )

    def create_economic_resource(self, resource_input):
        """Create an EconomicResource."""
        return self.call_zome(
            "zome_resource",
            "create_economic_resource",
            resource_input
        )

    def get_all_resources(self):
        """Get all available resources."""
        return self.call_zome(
            "zome_resource",
            "get_all_resources"
        )
```

**Step 2.2: Sync Script**

```python
# bridge/sync_erp_to_nondominium.py
from erp_client import ERPLibreClient
from gateway_client import HcHttpGwClient
from mapper import NondominiumMapper

def sync_inventory():
    """Sync ERPLibre inventory to Nondominium."""

    # Initialize clients
    erp = ERPLibreClient(
        url='http://localhost:8069',
        db='erplibre_db',
        username='admin',
        password='admin'
    )

    gw = HcHttpGwClient(
        gw_url='http://localhost:8090',
        dna_hash='uhC0k...'  # Your DNA hash
    )

    # Get available products
    products = erp.get_available_products()
    print(f"Found {len(products)} products to sync")

    for product in products:
        # Create ResourceSpecification
        spec_input = NondominiumMapper.product_to_resource_spec(product)
        spec_hash = gw.create_resource_specification(spec_input)
        print(f"Created spec: {spec_hash}")

        # Create EconomicResource
        resource_input = NondominiumMapper.product_to_economic_resource(
            product, spec_hash
        )
        resource_hash = gw.create_economic_resource(resource_input)
        print(f"Created resource: {resource_hash}")

if __name__ == '__main__':
    sync_inventory()
```

### 5.3 Phase 3: Cross-Organizational Discovery (Week 3)

**Step 3.1: Resource Discovery**

```python
# bridge/discover_resources.py
from gateway_client import HcHttpGwClient

def discover_resources():
    """Discover resources from other organizations."""

    gw = HcHttpGwClient(
        gw_url='http://localhost:8090',
        dna_hash='uhC0k...'
    )

    resources = gw.get_all_resources()

    print("\n=== Available Resources ===\n")
    for resource in resources:
        print(f"Resource: {resource.get('conforms_to', 'Unknown')}")
        print(f"  Quantity: {resource.get('quantity', 0)} {resource.get('unit', 'units')}")
        print(f"  Location: {resource.get('location', 'Unknown')}")
        print(f"  Hash: {resource.get('hash', 'N/A')}")
        print()

if __name__ == '__main__':
    discover_resources()
```

**Step 3.2: Request Use Process**

```python
# bridge/request_resource.py
from gateway_client import HcHttpGwClient

def request_resource_use(resource_hash, quantity, duration_hours):
    """Request to use a discovered resource."""

    gw = HcHttpGwClient(
        gw_url='http://localhost:8090',
        dna_hash='uhC0k...'
    )

    # Create a commitment (request)
    commitment_input = {
        "resource_hash": resource_hash,
        "requested_quantity": quantity,
        "duration_hours": duration_hours,
        "purpose": "Research project",
        "action_type": "use"
    }

    commitment_hash = gw.call_zome(
        "zome_resource",
        "create_commitment",
        commitment_input
    )

    print(f"Created use request: {commitment_hash}")
    return commitment_hash
```

### 5.4 Phase 4: Demo and Documentation (Week 4)

**Step 4.1: Full Demo Script**

```python
# demo/full_demo.py
"""
ERP-Holochain Bridge PoC Demonstration

This script demonstrates the full flow:
1. Organization A publishes resources from ERPLibre
2. Organization B discovers resources via Nondominium
3. Organization B requests to use Organization A's 3D printer
4. The use event is recorded with PPRs
"""

from bridge.erp_client import ERPLibreClient
from bridge.gateway_client import HcHttpGwClient
from bridge.mapper import NondominiumMapper

def demo():
    print("=" * 60)
    print("ERP-Holochain Bridge PoC Demo")
    print("=" * 60)

    # Setup clients
    erp_a = ERPLibreClient('http://org-a:8069', 'db_a', 'admin', 'admin')
    erp_b = ERPLibreClient('http://org-b:8069', 'db_b', 'admin', 'admin')
    gw = HcHttpGwClient('http://localhost:8090', 'uhC0k...')

    # Step 1: Org A publishes resources
    print("\n[Step 1] Organization A publishing resources...")
    products_a = erp_a.get_available_products()
    for product in products_a:
        spec = NondominiumMapper.product_to_resource_spec(product)
        spec_hash = gw.create_resource_specification(spec)
        resource = NondominiumMapper.product_to_economic_resource(product, spec_hash)
        gw.create_economic_resource(resource)
        print(f"  Published: {product['name']}")

    # Step 2: Org B discovers resources
    print("\n[Step 2] Organization B discovering resources...")
    resources = gw.get_all_resources()
    for r in resources:
        print(f"  Found: {r['quantity']} x {r.get('conforms_to', 'Unknown')}")

    # Step 3: Org B requests 3D printer
    print("\n[Step 3] Organization B requesting 3D printer...")
    printer = next(r for r in resources if '3D Printer' in str(r))
    commitment = gw.call_zome('zome_resource', 'create_commitment', {
        'resource_hash': printer['hash'],
        'requested_quantity': 1,
        'duration_hours': 24,
        'purpose': 'Prototype fabrication'
    })
    print(f"  Request created: {commitment}")

    # Step 4: Record usage event
    print("\n[Step 4] Recording usage event...")
    event = gw.call_zome('zome_resource', 'record_economic_event', {
        'commitment_hash': commitment,
        'action': 'use',
        'resource_quantity': 1
    })
    print(f"  Event recorded: {event}")

    print("\n" + "=" * 60)
    print("Demo complete! PPRs generated for both organizations.")
    print("=" * 60)

if __name__ == '__main__':
    demo()
```

---

## 6. Code Examples

### 6.1 Complete Bridge Client

```python
# bridge/nondominium_bridge.py
"""
Complete Nondominium Bridge Client for ERPLibre PoC
"""

import xmlrpc.client
import requests
import base64
import json
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

@dataclass
class ResourceSpec:
    name: str
    description: str
    default_unit: str
    governance_rules: List[str]

@dataclass
class EconomicResource:
    conforms_to: str
    quantity: float
    unit: str
    location: str

class NondominiumBridge:
    """Bridge between ERPLibre and Nondominium via hc-http-gw."""

    def __init__(
        self,
        erp_url: str,
        erp_db: str,
        erp_user: str,
        erp_password: str,
        gateway_url: str,
        dna_hash: str
    ):
        # ERPLibre connection
        self.erp_url = erp_url
        self.erp_db = erp_db
        common = xmlrpc.client.ServerProxy(f'{erp_url}/xmlrpc/2/common')
        self.erp_uid = common.authenticate(erp_db, erp_user, erp_password, {})
        self.erp_models = xmlrpc.client.ServerProxy(f'{erp_url}/xmlrpc/2/object')

        # Gateway connection
        self.gateway_url = gateway_url
        self.dna_hash = dna_hash
        self.app_id = "nondominium"

    def _call_erp(self, model: str, method: str, args: List, kwargs: Dict = None) -> Any:
        """Call ERPLibre model method."""
        return self.erp_models.execute_kw(
            self.erp_db, self.erp_uid, self.erp_password,
            model, method, args, kwargs or {}
        )

    def _call_zome(self, zome: str, fn: str, payload: Optional[Dict] = None) -> Any:
        """Call Holochain zome function via gateway."""
        url = f"{self.gateway_url}/{self.dna_hash}/{self.app_id}/{zome}/{fn}"

        if payload:
            payload_b64 = base64.b64encode(json.dumps(payload).encode()).decode()
            url += f"?payload={payload_b64}"

        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json()

    def get_shareable_products(self) -> List[Dict]:
        """Get products available for sharing."""
        return self._call_erp(
            'product.product', 'search_read',
            [[('qty_available', '>', 0)]],
            {'fields': ['name', 'default_code', 'qty_available', 'uom_id', 'categ_id']}
        )

    def publish_resource(self, product: Dict) -> str:
        """Publish an ERPLibre product to Nondominium."""
        # Create ResourceSpecification
        spec_input = {
            "name": product['name'],
            "description": f"SKU: {product.get('default_code', 'N/A')}",
            "default_unit": product['uom_id'][1] if product.get('uom_id') else "unit",
            "governance_rules": []
        }
        spec_hash = self._call_zome("zome_resource", "create_resource_specification", spec_input)

        # Create EconomicResource
        resource_input = {
            "conforms_to": spec_hash,
            "quantity": product['qty_available'],
            "unit": product['uom_id'][1] if product.get('uom_id') else "unit",
            "location": "warehouse"
        }
        resource_hash = self._call_zome("zome_resource", "create_economic_resource", resource_input)

        return resource_hash

    def discover_resources(self) -> List[Dict]:
        """Discover available resources from other organizations."""
        return self._call_zome("zome_resource", "get_all_resources")

    def request_use(self, resource_hash: str, quantity: float, hours: int, purpose: str) -> str:
        """Request to use a resource."""
        commitment_input = {
            "resource_hash": resource_hash,
            "requested_quantity": quantity,
            "duration_hours": hours,
            "purpose": purpose,
            "action_type": "use"
        }
        return self._call_zome("zome_resource", "create_commitment", commitment_input)

    def sync_all(self) -> Dict[str, int]:
        """Sync all shareable products to Nondominium."""
        products = self.get_shareable_products()
        synced = 0

        for product in products:
            try:
                self.publish_resource(product)
                synced += 1
            except Exception as e:
                print(f"Failed to sync {product['name']}: {e}")

        return {"total": len(products), "synced": synced}
```

### 6.2 Simple Web Interface

```python
# web/app.py
"""
Simple Flask web interface for the PoC demo.
"""

from flask import Flask, render_template, jsonify
from bridge.nondominium_bridge import NondominiumBridge

app = Flask(__name__)

bridge = NondominiumBridge(
    erp_url='http://localhost:8069',
    erp_db='erplibre_db',
    erp_user='admin',
    erp_password='admin',
    gateway_url='http://localhost:8090',
    dna_hash='uhC0k...'  # Replace with actual DNA hash
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/local-products')
def local_products():
    """Get products from local ERPLibre."""
    products = bridge.get_shareable_products()
    return jsonify(products)

@app.route('/api/network-resources')
def network_resources():
    """Get resources from Nondominium network."""
    resources = bridge.discover_resources()
    return jsonify(resources)

@app.route('/api/sync', methods=['POST'])
def sync():
    """Sync local products to Nondominium."""
    result = bridge.sync_all()
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

---

## 7. Testing and Validation

### 7.1 Unit Tests

```python
# tests/test_bridge.py
import pytest
from bridge.nondominium_bridge import NondominiumBridge

@pytest.fixture
def bridge():
    return NondominiumBridge(
        erp_url='http://localhost:8069',
        erp_db='test_db',
        erp_user='admin',
        erp_password='admin',
        gateway_url='http://localhost:8090',
        dna_hash='uhC0k...'
    )

def test_get_products(bridge):
    products = bridge.get_shareable_products()
    assert isinstance(products, list)

def test_discover_resources(bridge):
    resources = bridge.discover_resources()
    assert isinstance(resources, list)

def test_publish_resource(bridge):
    product = {
        'name': 'Test Product',
        'default_code': 'TEST-001',
        'qty_available': 1,
        'uom_id': [1, 'Unit']
    }
    resource_hash = bridge.publish_resource(product)
    assert resource_hash is not None
    assert len(resource_hash) > 0
```

### 7.2 Integration Test Checklist

| Test Case | Expected Result | Pass/Fail |
|-----------|-----------------|-----------|
| ERPLibre API connection | Authenticated successfully | |
| Read products with quantity > 0 | Returns product list | |
| hc-http-gw health check | Returns 200 OK | |
| Create ResourceSpecification | Returns ActionHash | |
| Create EconomicResource | Returns ActionHash | |
| Get all resources | Returns resource list | |
| Create commitment | Returns commitment hash | |
| Record economic event | Returns event hash | |

### 7.3 Validation Procedures

```bash
# 1. Verify ERPLibre is running
curl http://localhost:8069/web/database/selector

# 2. Verify hc-http-gw is running
curl http://localhost:8090/health

# 3. Test zome call (get all resources)
curl "http://localhost:8090/uhC0k.../nondominium/zome_resource/get_all_resources"

# 4. Run sync script
python bridge/sync_erp_to_nondominium.py

# 5. Verify resources in Nondominium
python bridge/discover_resources.py
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
