# ERP-Holochain Bridge Technical Specifications

> **Document Type**: Technical Specifications
> **Version**: 1.0
> **Last Updated**: 2026-02-12
> **Related Documents**:
> - [Requirements](../requirements/erp_bridge_requirements.md)
> - [PoC Specification](poc/hc_http_gw_poc_spec.md)
> - [Implementation Architecture](../implementation/architecture.md)
> - [Module Reference](../implementation/module-reference.md)

---

## 1. Architecture Overview

### 1.1 Two-Layer Architecture

The bridge architecture separates concerns into two distinct layers:

1. **Protocol Bridge** (Reusable): A thin, ERP-agnostic adapter that translates HTTP to Holochain's WebSocket protocol
2. **ERP Module** (Per-ERP): Contains business logic, data mapping, and UI integration specific to each ERP

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ERP-SPECIFIC MODULES (BFF-like Layer)               │
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
│  │ ERPLibre Module │  │ Dolibarr Module │  │ ERPNext Module  │              │
│  │ (Python/Odoo)   │  │ (PHP)           │  │ (Python/Frappe) │              │
│  │                 │  │                 │  │                 │              │
│  │ • UI views      │  │ • UI views      │  │ • UI views      │              │
│  │ • Data mapping  │  │ • Data mapping  │  │ • Data mapping  │              │
│  │ • BFF logic     │  │ • BFF logic     │  │ • BFF logic     │              │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘              │
│           │                    │                    │                       │
│           │ HTTP/JSON          │ HTTP/JSON          │ HTTP/JSON             │
│           │                    │                    │                       │
└───────────┼────────────────────┼────────────────────┼───────────────────────┘
            │                    │                    │
            └────────────────────┼────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     SHARED PROTOCOL BRIDGE                                  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    Generic REST API                                 │    │
│  │                                                                     │    │
│  │  PoC (hc-http-gw):                                                  │    │
│  │  GET /[dna]/[app]/[zome]/[fn]?payload={base64}                      │    │
│  │                                                                     │    │
│  │  Production (Node.js):                                              │    │
│  │  POST /api/v1/zome/:zome/:fn    → Call any zome function            │    │
│  │  GET  /api/v1/resources         → List resources                    │    │
│  │  POST /api/v1/webhooks          → Register signal callbacks         │    │
│  │                                                                     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                 │
                                 │ WebSocket
                                 ▼
                    ┌───────────────────────┐
                    │ Holochain Conductor   │
                    │ (Nondominium hApp)    │
                    └───────────────────────┘
```

### 1.2 Layer Responsibilities

| Layer | Responsibility | Changes When... |
|-------|---------------|-----------------|
| **ERP Module** | Business logic, data aggregation, UI | ERP-specific needs change |
| **Protocol Bridge** | HTTP ↔ WebSocket translation, signing | Holochain API changes |

### 1.3 Benefits of Separation

- **Reusability**: One bridge serves multiple ERPs
- **Separation of concerns**: Protocol complexity isolated from business logic
- **Independent evolution**: Bridge and modules can be updated independently
- **Testing**: Each layer can be tested in isolation

---

## 2. Component Design

### 2.1 ERP Module as BFF-like Layer

The ERP module acts as a **Backend for Frontend (BFF)** pattern within the ERP's architecture:

```
┌─────────────────────────────────────────────────────────────────┐
│                     ERP MODULE (per ERP)                        │
│                                                                 │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ 1. DATA AGGREGATION                                        │ │
│  │    Combine ERP inventory data with Nondominium resources   │ │
│  │    Join local stock with cross-org availability            │ │
│  │    Merge PPR reputation with supplier/customer records     │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ 2. DATA MAPPING                                            │ │
│  │    ERP Product → Nondominium ResourceSpecification         │ │
│  │    ERP Stock   → Nondominium EconomicResource              │ │
│  │    ERP Order   → Nondominium Commitment                    │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ 3. UI INTEGRATION                                          │ │
│  │    "Share Resource" button in inventory view               │ │
│  │    "Discover Resources" menu item                          │ │
│  │    "Request Resource" workflow                             │ │
│  │    PPR reputation dashboard                                │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ 4. WEBHOOK HANDLER (Production only)                       │ │
│  │    Receive signals from bridge                             │ │
│  │    Update ERP records accordingly                          │ │
│  │    Notify users of resource requests                       │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 ERPLibre Module Structure

The production ERPLibre module structure (aspirational):

```
nondominium_bridge/
├── __manifest__.py           # Odoo module manifest
├── models/
│   ├── nondominium_resource.py    # Transient model for cross-org resources
│   ├── nondominium_commitment.py  # Commitment tracking
│   └── res_partner_ppr.py         # PPR reputation on partners
├── controllers/
│   └── webhook_controller.py      # Receive Holochain signals
├── views/
│   ├── shareable_resources.xml    # Cross-org resource discovery
│   ├── resource_requests.xml      # Commitment management UI
│   └── ppr_dashboard.xml          # Reputation dashboard
├── wizards/
│   └── publish_resource_wizard.py # "Share to Nondominium" workflow
└── static/
    └── src/js/
        └── nondominium_widgets.js # Real-time update widgets
```

> **Note**: A PoC Odoo addon exists at `docker/addons/nondominium_connector/` with an actual `__manifest__.py`, models (`res_config_settings.py`, `product_template.py`), and views (`res_config_settings_views.xml`, `product_template_views.xml`). It demonstrates product-to-Nondominium sync from the Odoo UI.

---

## 3. Protocol Bridge Options

### 3.1 Option Comparison Matrix

| Criterion | hc-http-gw (PoC) | Node.js Bridge (Production) | Python Client (Future) |
|-----------|------------------|------------------------------|------------------------|
| **Ease of Implementation** | ⭐⭐⭐⭐⭐ High | ⭐⭐⭐⭐ Medium-High | ⭐⭐ Low |
| **Signal Support** | ❌ No | ✅ Yes | ✅ Yes (if implemented) |
| **Maintenance Burden** | ⭐⭐⭐⭐⭐ Very Low | ⭐⭐⭐⭐ Low | ⭐⭐ High |
| **Multi-ERP Reusability** | ✅ Yes | ✅ Yes | ⚠️ Python ERPs only |
| **Real-time Capability** | ❌ No | ✅ Yes | ✅ Yes |
| **Zome Call Signing** | ⚠️ Limited | ✅ Full support | ✅ Full (if implemented) |
| **ML/AI Integration** | ❌ No | ❌ No | ✅ Native |
| **Production Readiness** | ⭐⭐⭐ Good | ⭐⭐⭐⭐⭐ Excellent | ⭐⭐ Experimental |

### 3.2 Option 1: hc-http-gw (PoC)

**Best For**: Proof of concept and rapid prototyping

See [PoC Implementation Guide](poc/hc_http_gw_poc_spec.md) for details.

### 3.3 Option 2: Node.js Protocol Bridge (Production)

**Architecture:**
```
ERP Module (Python/PHP) <--HTTP/JSON--> Node.js Bridge <--WebSocket--> Holochain Conductor
```

**Key Features:**
- Full `@holochain/client` feature access
- Signal subscription and webhook forwarding
- Caching, batching, rate limiting capabilities
- Multi-ERP support via generic REST API

**Example Implementation:**
```javascript
// bridge/src/server.ts
import { AppWebsocket } from '@holochain/client';
import express from 'express';

const app = express();
const webhooks = new Map();  // URL -> event types

// Initialize Holochain connection
const appWs = await AppWebsocket.connect({
  url: 'ws://localhost:8888',
  token: process.env.HOLOCHAIN_TOKEN
});

// Generic zome call endpoint - works for ANY ERP
app.post('/api/v1/zome/:zome/:fn', async (req, res) => {
  const { zome, fn } = req.params;
  const result = await appWs.callZome({
    zome_name: zome,
    fn_name: fn,
    payload: req.body
  });
  res.json(result);
});

// Webhook registration for signals
app.post('/api/v1/webhooks', async (req, res) => {
  const { url, events } = req.body;
  webhooks.set(url, events);
  res.json({ status: 'registered' });
});

// Subscribe to Holochain signals and forward to webhooks
appWs.on('signal', async (signal) => {
  for (const [url, events] of webhooks) {
    if (events.includes(signal.type)) {
      await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(signal)
      });
    }
  }
});

app.listen(3000);
```

### 3.4 Option 3: Python Client (Future)

**Best For**: ML/AI-heavy use cases when Python ecosystem integration becomes critical

**Use Cases Enabled:**
- ML-Powered PPR Scoring
- AI Resource Matching (LangChain agents)
- Predictive Analytics
- Federated Learning
- Jupyter Notebooks for DHT data exploration
- Airflow/Prefect data pipelines

---

## 4. Data Models and Mappings

### 4.1 Core Data Mappings

| ERP Concept | Nondominium Concept | Notes |
|-------------|---------------------|-------|
| Product Template | `ResourceSpecification` | Defines what can be shared (`category`, `tags`, `image_url`, `is_active`) |
| Product Variant | `EconomicResource` | Specific instance (`spec_hash`, `current_location`, `custodian`, `state`) |
| Stock Location | Resource `current_location` field | Where the resource is physically located |
| Available Quantity | `quantity` in `EconomicResource` | How much is available |
| Resource State | `ResourceState` enum | `PendingValidation`, `Active`, `Maintenance`, `Retired`, `Reserved` |
| Stock Move | `EconomicEvent` (Transfer, Use) | Mapped via `log_economic_event` in `zome_gouvernance` |

### 4.2 ERPLibre Model Mappings

| ERPLibre Model | Fields Used | Maps To |
|----------------|-------------|---------|
| `product.product` | `name`, `default_code`, `description`, `categ_id` | `ResourceSpecification` (name, description, `category`) |
| `stock.quant` | `product_id`, `quantity`, `location_id` | `EconomicResource.quantity` |
| `product.uom` | `name` | `EconomicResource.unit` |
| `stock.warehouse` | `name`, `code` | `EconomicResource.current_location` |

> **Note**: The Nondominium `ResourceSpecification` uses `category` (not `default_unit`) and `EconomicResourceInput` uses `spec_hash` (not `conforms_to`). See `bridge/models.py` for the exact Pydantic models.

### 4.3 Nondominium Zome Functions

Complete function list from the `zome_resource` coordinator (Holochain 0.6.x, hdi 0.7.0 / hdk 0.6.0):

**ResourceSpecification functions:**

| Function | Input | Output | Description |
|----------|-------|--------|-------------|
| `create_resource_specification` | `ResourceSpecificationInput` | `CreateResourceSpecificationOutput` | Create a resource type with optional governance rules |
| `get_all_resource_specifications` | None | `GetAllResourceSpecificationsOutput` | List all resource specifications |
| `get_latest_resource_specification` | `ActionHash` | `ResourceSpecification` | Get a specific spec by hash |
| `get_resource_specification_with_rules` | `ActionHash` | `GetResourceSpecWithRulesOutput` | Get spec with its governance rules |
| `get_resource_specifications_by_category` | `String` | `Vec<ResourceSpecification>` | Filter specs by category |
| `get_my_resource_specifications` | None | `Vec<ResourceSpecification>` | Get specs created by current agent |
| `update_resource_specification` | update input | updated spec | Update an existing spec |

**EconomicResource functions:**

| Function | Input | Output | Description |
|----------|-------|--------|-------------|
| `create_economic_resource` | `EconomicResourceInput` | `CreateEconomicResourceOutput` | Create a resource instance linked to a spec via `spec_hash` |
| `get_all_economic_resources` | None | `GetAllEconomicResourcesOutput` | List all economic resources |
| `get_latest_economic_resource` | `ActionHash` | `EconomicResource` | Get a specific resource by hash |
| `get_resources_by_specification` | `ActionHash` | `Vec<EconomicResource>` | Get resources for a given spec |
| `get_my_economic_resources` | None | `Vec<EconomicResource>` | Get resources created by current agent |
| `update_economic_resource` | update input | updated resource | Update an existing resource |

**Custody & State functions:**

| Function | Input | Output | Description |
|----------|-------|--------|-------------|
| `transfer_custody` | `TransferCustodyInput` | `TransferCustodyOutput` | Transfer resource custody to another agent |
| `update_resource_state` | `UpdateResourceStateInput` | updated resource | Change resource state (Active, Retired, etc.) |

**GovernanceRule functions:**

| Function | Input | Output | Description |
|----------|-------|--------|-------------|
| `create_governance_rule` | `GovernanceRuleInput` | `ActionHash` | Create a governance rule |
| `get_all_governance_rules` | None | `Vec<GovernanceRule>` | List all governance rules |
| `get_latest_governance_rule` | `ActionHash` | `GovernanceRule` | Get a specific rule by hash |
| `update_governance_rule` | update input | updated rule | Update an existing rule |

**Governance Functions (`zome_gouvernance`):**

*Commitment functions:*

| Function | Input | Output | Description |
|----------|-------|--------|-------------|
| `propose_commitment` | `ProposeCommitmentInput` | `ProposeCommitmentOutput` | Propose a resource use commitment |
| `get_all_commitments` | None | `Vec<Commitment>` | List all commitments |
| `get_commitments_for_agent` | `AgentPubKey` | `Vec<Commitment>` | Get commitments for a specific agent |
| `claim_commitment` | `ClaimCommitmentInput` | `ClaimCommitmentOutput` | Claim fulfillment of a commitment |

*EconomicEvent functions:*

| Function | Input | Output | Description |
|----------|-------|--------|-------------|
| `log_economic_event` | `LogEconomicEventInput` | `LogEconomicEventOutput` | Log an economic event (Use, Transfer, etc.) |
| `log_initial_transfer` | `LogInitialTransferInput` | `LogInitialTransferOutput` | Log an initial transfer of a resource |
| `get_all_economic_events` | None | `Vec<EconomicEvent>` | List all economic events |
| `get_events_for_resource` | `ActionHash` | `Vec<EconomicEvent>` | Get events for a specific resource |

*Validation functions:*

| Function | Input | Output | Description |
|----------|-------|--------|-------------|
| `create_validation_receipt` | `CreateValidationReceiptInput` | `CreateValidationReceiptOutput` | Create a validation receipt |
| `get_validation_history` | `ActionHash` | `Vec<ValidationReceipt>` | Get validation history for an item |
| `get_all_validation_receipts` | None | `Vec<ValidationReceipt>` | List all validation receipts |
| `create_resource_validation` | `CreateResourceValidationInput` | `CreateResourceValidationOutput` | Create a resource validation process |
| `check_validation_status` | `ActionHash` | validation status | Check status of a validation process |

*PPR functions:*

| Function | Input | Output | Description |
|----------|-------|--------|-------------|
| `issue_participation_receipts` | `IssueParticipationReceiptsInput` | `IssueParticipationReceiptsOutput` | Issue PPR claims for an economic event |
| `get_my_participation_claims` | None | `Vec<PrivateParticipationClaim>` | Get current agent's PPR claims |
| `derive_reputation_summary` | `DeriveReputationSummaryInput` | `DeriveReputationSummaryOutput` | Derive reputation summary for an agent |

---

## 5. API Specifications

### 5.1 hc-http-gw API (PoC)

**URL Format:**
```
GET http://{host}/{dna-hash}/{app-id}/{zome}/{function}?payload={base64url-encoded-json}
```

**Important Details:**
- **GET-only**: No POST support
- **Base64url payload**: Input must be URL-safe base64-encoded (RFC 4648, no padding) in query string
- **No signals**: Request-response only, no push notifications
- **No-arg functions**: Functions taking `()` omit the `?payload=` parameter entirely
- **Default port**: 8888

**Example:**
```bash
# Create ResourceSpecification (note: base64url encoding, no padding)
PAYLOAD=$(echo -n '{"name":"3D Printer","description":"Available for sharing","category":"equipment","tags":[]}' | base64 -w0 | tr '+/' '-_' | tr -d '=')
curl "http://localhost:8888/uhC0k.../nondominium/zome_resource/create_resource_specification?payload=${PAYLOAD}"

# Get all economic resources (no payload needed)
curl "http://localhost:8888/uhC0k.../nondominium/zome_resource/get_all_economic_resources"
```

### 5.2 Node.js Bridge API (Production)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/zome/:zome/:fn` | POST | Call any zome function |
| `/api/v1/resources` | GET | List all available resources |
| `/api/v1/resources/:hash` | GET | Get specific resource |
| `/api/v1/commitments` | POST | Create commitment |
| `/api/v1/events` | GET | List economic events |
| `/api/v1/webhooks` | POST | Register signal callbacks |

### 5.3 ERPLibre API (XML-RPC)

**Authentication:**
```python
import xmlrpc.client

url = 'http://localhost:8069'
db = 'erplibre_db'
username = 'admin'
password = 'admin'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
```

**Reading Products:**
```python
products = models.execute_kw(db, uid, password,
    'product.product', 'search_read',
    [[('qty_available', '>', 0)]],
    {'fields': ['name', 'default_code', 'qty_available', 'uom_id']}
)
```

---

## 6. Security Specifications

### 6.1 Security Architecture

The Protocol Bridge runs **server-side only**. It must never be exposed to end-users directly.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           PUBLIC INTERNET                               │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ HTTPS (public)
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           SERVER-SIDE (Private Network)                 │
│                                                                         │
│   ┌─────────────┐      ┌─────────────────┐      ┌──────────────────┐    │
│   │ ERP System  │ HTTP │ Protocol Bridge │  WS  │ Holochain        │    │
│   │ (Python/PHP)│─────▶│                 │─────▶│ Conductor        │    │
│   └─────────────┘      └─────────────────┘      └──────────────────┘    │
│         │                      │                         │              │
│   Public:8069      localhost:3000/8888         localhost:8888         │
│         │                      │                         │              │
│   ┌─────▼─────┐                │                  ┌──────▼───────┐      │
│   │ Database  │                │                  │ Agent Keys   │      │
│   │           │                │                  │ (Protected)  │      │
│   └───────────┘                │                  └──────────────┘      │
│                                │                                        │
└────────────────────────────────┼────────────────────────────────────────┘
                                 │
                         🔒 NEVER EXPOSED
```

### 6.2 Security Requirements

| Concern | Risk if Violated | Mitigation |
|---------|------------------|------------|
| **Agent Private Keys** | Identity theft, impersonation | Keys stay on server, never transmitted |
| **Conductor WebSocket** | Unauthorized zome calls | Localhost only, firewalled |
| **Capability Tokens** | Unauthorized actions | Generated and used server-side |
| **Zome Call Signing** | Forged transactions | Signing happens in bridge |

---

## 7. Deployment Architecture

### 7.1 Option A: Bridge Per Organization (Recommended)

Each organization runs its own full stack:

```
┌─────────────────────────┐     ┌─────────────────────────┐
│ Org A Server            │     │ Org B Server            │
│ ┌─────────────────────┐ │     │ ┌─────────────────────┐ │
│ │ ERPLibre + Module   │ │     │ │ Dolibarr + Module   │ │
│ ├─────────────────────┤ │     │ ├─────────────────────┤ │
│ │ Protocol Bridge     │ │     │ │ Protocol Bridge     │ │
│ ├─────────────────────┤ │     │ ├─────────────────────┤ │
│ │ Holochain Node      │ │     │ │ Holochain Node      │ │
│ │ (Org A Agent)       │ │     │ │ (Org B Agent)       │ │
│ └─────────────────────┘ │     │ └─────────────────────┘ │
└───────────┬─────────────┘     └───────────┬─────────────┘
            │                               │
            └───────────────────────────────┘
                        DHT Network
```

### 7.2 PoC Development Environment (Nix)

The bridge repo has its own `flake.nix` providing the complete dev environment (holonix + Python 3.12 + uv). See `scripts/setup_conductor.sh` for the automated setup.

```bash
# Enter the bridge Nix dev shell (provides holochain, hc, hc-http-gw, python, uv)
nix develop

# Build the hApp (if not already built)
cd ../nondominium && npm run build:happ && cd -

# Run the setup script (starts conductor + hc-http-gw on port 8888)
bash scripts/setup_conductor.sh
```

### 7.3 Docker Compose Configuration (Future Production)

> **Note**: This Docker configuration is for future production deployment. The PoC uses Nix as described above.

```yaml
services:
  erplibre:
    image: erplibre/erplibre:latest
    ports:
      - "8069:8069"  # Public: ERPLibre web UI
    networks:
      - internal
    depends_on:
      - protocol-bridge

  protocol-bridge:
    build: ./bridge
    # NO public ports - internal only
    networks:
      - internal
    environment:
      - HOLOCHAIN_URL=ws://holochain:8888
    depends_on:
      - holochain

  holochain:
    image: holochain/holochain:latest
    # NO public ports - internal only
    networks:
      - internal
    volumes:
      - ./agent-keys:/keys  # Protected volume
      - ./happ:/happ

networks:
  internal:
    internal: true  # No external access
```

### 7.4 Option B: Shared Bridge Service (Managed)

For organizations preferring managed infrastructure:

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ ERPLibre    │     │ Dolibarr    │     │ ERPNext     │
│ Org A       │     │ Org B       │     │ Org C       │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │
                  ┌────────▼────────┐
                  │ Managed Bridge  │  ← Multi-tenant
                  │ Service         │     API key per org
                  └────────┬────────┘
                           │
             ┌─────────────┼─────────────┐
             │             │             │
      ┌──────▼──────┐ ┌────▼─────┐ ┌──────▼──────┐
      │ Org A Node  │ │Org B Node│ │ Org C Node  │
      └─────────────┘ └──────────┘ └─────────────┘
```

---

## 8. Multi-ERP Support

### 8.1 Compatible ERP Systems

| ERP | Language | Module Type | Integration Effort |
|-----|----------|-------------|-------------------|
| **ERPLibre/Odoo** | Python | Odoo Module | Medium |
| **Dolibarr** | PHP | Dolibarr Module | Medium |
| **ERPNext** | Python/JS | Frappe App | Medium |
| **Tryton** | Python | Tryton Module | Medium |
| **Metasfresh** | Java | Plugin | Higher |
| **Apache OFBiz** | Java | Component | Higher |
| **Custom ERP** | Any | HTTP client | Low |

### 8.2 Reusability Matrix

| Component | Reusable? | Notes |
|-----------|-----------|-------|
| **Protocol Bridge** | ✅ 100% | Generic HTTP↔WebSocket adapter |
| **Zome Function API** | ✅ 100% | Same Nondominium API for all |
| **Signal/Webhook System** | ✅ 100% | Any HTTP endpoint can receive |
| **Data Mapping** | ❌ ERP-specific | Each ERP has different data models |
| **UI Integration** | ❌ ERP-specific | Each ERP has different frontend |
| **Business Logic** | ❌ ERP-specific | BFF layer per ERP |

---

## 9. Migration Path: PoC to Production

### 9.1 Migration Steps

1. **Deploy Node.js bridge alongside hc-http-gw**
2. **Update ERPLibre module to call bridge instead of gateway**
3. **Implement webhook handler for Holochain signals**
4. **Add proper zome call signing and capability management**
5. **Deprecate hc-http-gw once bridge is stable**

### 9.2 Feature Comparison

| Feature | PoC (hc-http-gw) | Production (Node.js) |
|---------|------------------|----------------------|
| Sync direction | ERP → Nondominium | Bidirectional |
| Real-time updates | Polling | Signals + Webhooks |
| ERP support | ERPLibre only | Multi-ERP |
| Signing | Pre-authorized | Full capability management |
| Caching | None | Configurable |

---

## 10. References

- [Holochain HTTP Gateway](https://github.com/holochain/hc-http-gw)
- [Holochain Client JS](https://github.com/holochain/holochain-client-js)
- [Odoo API Documentation](https://www.odoo.com/documentation/16.0/developer/reference/external_api.html)
- [ValueFlows Ontology](https://www.valueflows.org/)
- [Nondominium Repository](https://github.com/Sensorica/nondominium)
