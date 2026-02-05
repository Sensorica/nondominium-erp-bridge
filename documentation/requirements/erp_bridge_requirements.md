# ERP-Holochain Bridge Requirements

> **Document Type**: High-Level Requirements
> **Version**: 1.0
> **Last Updated**: 2026-02-05
> **Related Documents**:
> - [Technical Specifications](../specifications/erp_bridge_specifications.md)
> - [PoC Implementation Guide](../specifications/poc/hc_http_gw_poc_spec.md)

---

## 1. Executive Summary

This document defines the high-level requirements for bridging traditional Enterprise Resource Planning (ERP) systems with Nondominium's peer-to-peer resource-sharing infrastructure. The goal is to enable organizations using centralized ERP systems to participate in decentralized resource economies without abandoning their existing business infrastructure.

**Key Principle**: The bridge is designed as a **reusable, ERP-agnostic Protocol Bridge** that can serve multiple ERP systems (ERPLibre, Dolibarr, ERPNext, etc.), while ERP-specific integration logic resides in dedicated modules for each platform.

---

## 2. Problem Statement

### 2.1 The Challenge

Organizations currently manage their inventory, equipment, and resources using centralized ERP systems (e.g., Odoo, SAP, ERPNext). While these systems excel at internal management, they create **data silos** that prevent resource sharing across organizational boundaries.

**Current limitations:**

| Limitation | Impact |
|------------|--------|
| **No cross-organizational visibility** | Organization A cannot see if Organization B has idle equipment that could be borrowed |
| **Trust barriers** | Ad-hoc resource sharing requires manual coordination, legal contracts, and trust-building overhead |
| **Platform dependency** | Centralized marketplaces extract rent and control access |
| **Data sovereignty concerns** | Organizations are reluctant to upload sensitive inventory data to third-party platforms |

### 2.2 The Opportunity

Nondominium offers a **peer-to-peer, organization-agnostic** resource-sharing layer that can complement existing ERP systems:

- Resources can be **selectively published** from ERP inventory to Nondominium without migrating away from the ERP
- Organizations retain **full sovereignty** over their data and participation
- **Reputation tracking (PPR system)** replaces heavy legal contracts with cryptographic accountability
- **Emergent coordination** via stigmergy reduces the need for manual negotiation

---

## 3. Goals and Objectives

### 3.1 Primary Goals

1. **Enable Cross-Organizational Resource Discovery**: Allow organizations to discover available resources from other organizations through Nondominium's DHT network
2. **Preserve Data Sovereignty**: Organizations maintain full control over which resources they share and with whom
3. **Minimize Integration Overhead**: Provide a simple, non-invasive bridge that doesn't require modifications to ERP core code
4. **Support Multiple ERPs**: Design a reusable protocol bridge that works with any ERP system

### 3.2 Success Criteria

| Criterion | Measure |
|-----------|---------|
| **Integration simplicity** | Bridge deployable as separate service/container |
| **Non-invasiveness** | Zero modifications to ERP core code |
| **Cross-org discovery** | Resources from Org A visible to Org B within 1 minute of publication |
| **Data mapping accuracy** | 100% of ERP product data maps correctly to Nondominium format |
| **Accountability** | All resource transactions generate verifiable PPRs |

---

## 4. Agent Model Concept

### 4.1 Organization as Holochain Agent

In this architecture, the **organization is the Holochain agent**, not individual end-users. This differs from typical Holochain applications where each person runs their own node.

**Key distinctions:**

| Aspect | Individual Agents (Typical Holochain) | Organization Agents (ERP Bridge) |
|--------|---------------------------------------|----------------------------------|
| **Node operator** | End-user | Organization's IT infrastructure |
| **Identity** | Personal keypair | Organizational keypair |
| **End-user access** | Direct to conductor | Mediated via ERP |
| **Key management** | User responsibility | IT administration |
| **PPR accountability** | Individual reputation | Organizational reputation |

### 4.2 Benefits of Organization-Level Agents

1. **Organizational sovereignty**: The organization controls its participation in the network
2. **Existing authentication**: ERP handles employee authentication/authorization
3. **Single source of truth**: One agent key per organization, not hundreds
4. **Operational simplicity**: IT manages one node, not per-employee nodes
5. **PPR accountability**: Reputation tied to organization, matching business relationships

### 4.3 Trust Model

The end-user **delegates** their participation to the organization. The organization is the **accountable party** in the peer-to-peer network.

```
End-user (employee)
    │
    │ Trusts organization (employment relationship)
    ▼
Organization's ERP System
    │
    │ Authenticates & authorizes actions
    ▼
Organization's Holochain Agent
    │
    │ Cryptographically signs all DHT actions
    ▼
Nondominium Network
    │
    │ PPR tracks organizational reputation
    ▼
Other Organizations
```

---

## 5. Functional Requirements

### 5.1 PoC Functional Requirements

| ID | Requirement | Priority | Description |
|----|-------------|----------|-------------|
| **FR-1** | Read ERP Inventory | Must Have | Read inventory data from ERPLibre via its API |
| **FR-2** | Map to ResourceSpecification | Must Have | Map ERPLibre products to Nondominium `ResourceSpecification` entries |
| **FR-3** | Publish EconomicResource | Must Have | Publish selected inventory items as `EconomicResource` entries in Nondominium |
| **FR-4** | Discover Resources | Must Have | Query Nondominium for available resources from other organizations |
| **FR-5** | Initiate Use Process | Future | Initiate a `Use` process in Nondominium for a discovered resource *(requires `create_commitment` zome function — not yet implemented)* |
| **FR-6** | Record Events & PPRs | Future | Record the `EconomicEvent` and generate PPRs for both parties *(requires `record_economic_event` zome function — not yet implemented)* |

### 5.2 Production Functional Requirements (Future)

| ID | Requirement | Priority | Description |
|----|-------------|----------|-------------|
| **FR-7** | Bidirectional Sync | Should Have | Changes in Nondominium reflected back to ERP |
| **FR-8** | Real-time Signals | Should Have | Push notifications for resource requests |
| **FR-9** | Governance Rules | Could Have | Organizations set access rules via ERP UI |
| **FR-10** | PPR Dashboard | Could Have | Display reputation scores in ERP |
| **FR-11** | Multi-ERP Support | Should Have | Support for Dolibarr, ERPNext, etc. |

---

## 6. Non-Functional Requirements

### 6.1 PoC Non-Functional Requirements

| ID | Requirement | Description |
|----|-------------|-------------|
| **NFR-1** | Non-invasive Integration | The bridge should not require modifications to ERPLibre core code |
| **NFR-2** | Containerized Deployment | The bridge should be deployable as a separate service/container |
| **NFR-3** | Periodic Sync Acceptable | Real-time synchronization is not required (periodic sync is acceptable for PoC) |
| **NFR-4** | Unidirectional Sync (PoC) | ERP → Nondominium sync only (bidirectional is a future requirement) |

### 6.2 Production Non-Functional Requirements (Future)

| ID | Requirement | Description |
|----|-------------|-------------|
| **NFR-5** | Security | Agent keys never exposed; all signing server-side |
| **NFR-6** | Scalability | Support for 100+ concurrent organizations |
| **NFR-7** | Reliability | 99.9% uptime for bridge service |
| **NFR-8** | Performance | Resource discovery < 2 seconds |

---

## 7. Scope Boundaries

### 7.1 In Scope (PoC)

- ERPLibre inventory reading via XML-RPC API
- Product → ResourceSpecification mapping
- Stock → EconomicResource mapping
- Cross-organizational resource discovery
- Custody transfer between organizations
- HTTP Gateway (`hc-http-gw`) as protocol bridge

> **Note**: Use process initiation (FR-5) and PPR generation (FR-6) are **future scope** — the `create_commitment` and `record_economic_event` zome functions do not yet exist in the Nondominium codebase. The PoC demonstrates `transfer_custody` as the available cross-org action.

### 7.2 Out of Scope (PoC)

| Item | Reason |
|------|--------|
| Complex governance rules enforcement | Requires additional Nondominium features |
| Financial transactions or invoicing | Outside core resource-sharing scope |
| Multi-warehouse scenarios | Adds complexity beyond PoC needs |
| Full PPR reputation dashboard | UI enhancement for production |
| Multi-ERP support (Dolibarr, ERPNext) | PoC focuses on ERPLibre only |
| Real-time signals/webhooks | Requires Node.js bridge (production) |

---

## 8. Data Mapping Requirements

### 8.1 Core Mappings

| ERP Concept | Nondominium Concept | Notes |
|-------------|---------------------|-------|
| Product Template | `ResourceSpecification` | Defines what can be shared (uses `category`, `tags`, `image_url`, `is_active`) |
| Product Variant | `EconomicResource` | Specific instance available for sharing (uses `spec_hash`, `current_location`, `custodian`, `state`) |
| Stock Location | Resource `current_location` field | Where the resource is physically located |
| Available Quantity | `quantity` in `EconomicResource` | How much is available |
| Stock Move | `EconomicEvent` (Transfer, Use) | *Future — not yet implemented in Nondominium* |

### 8.2 ERPLibre-Specific Mappings

| ERPLibre Model | Purpose | Mapped To |
|----------------|---------|-----------|
| `product.product` | Individual products | `ResourceSpecification` + `EconomicResource` |
| `stock.quant` | Available quantities per location | `quantity` field |
| `stock.move` | Movement history and planned transfers | *Future: `EconomicEvent`* |
| `stock.warehouse` | Physical locations | `current_location` field |

---

## 9. PoC Demonstration Scenario

### 9.1 Objective

Demonstrate that inventory from two organizations running ERPLibre can be synchronized to Nondominium and made discoverable for sharing.

### 9.2 Scenario Flow

1. **Organization A** has a 3D printer listed in its ERPLibre inventory
2. **Organization B** has a laser cutter listed in its ERPLibre inventory
3. Both organizations **publish** their available equipment to Nondominium
4. Each organization can **discover** the other's equipment via Nondominium
5. Organization B requests **custody transfer** of Organization A's 3D printer via `transfer_custody`
6. *(Future)* The usage is **recorded** as an `EconomicEvent` in Nondominium — requires zome functions not yet implemented
7. *(Future)* The usage is **reflected back** to Organization A's ERPLibre as a "Loan" or "External Use" stock move

### 9.3 Acceptance Criteria

| Criterion | Verification Method |
|-----------|---------------------|
| Products correctly mapped | Compare ERP data with Nondominium entries |
| Cross-org discovery works | Org B can see Org A's resources |
| Custody transfer works | Org B can request custody of Org A's resource |
| *(Future)* Use process records event | Verify EconomicEvent in DHT |
| *(Future)* PPRs generated | Both parties have participation receipts |

---

## 10. Phased Approach

### 10.1 Phase 1: PoC (Current Focus)

**Goal**: Rapid prototyping using `hc-http-gw`

- **Timeline**: 4 weeks
- **Protocol Bridge**: hc-http-gw (pre-built HTTP gateway)
- **Sync**: Unidirectional (ERP → Nondominium)
- **Real-time**: No (periodic polling)
- **ERP**: ERPLibre only

### 10.2 Phase 2: Production Bridge

**Goal**: Full-featured production deployment

- **Protocol Bridge**: Node.js with `@holochain/client`
- **Sync**: Bidirectional
- **Real-time**: Yes (signals + webhooks)
- **ERP**: ERPLibre + Dolibarr + ERPNext

### 10.3 Phase 3: Advanced Features

**Goal**: Enhanced capabilities

- ML-powered PPR scoring
- AI resource matching
- Predictive analytics
- Native Python client (if ML/AI becomes central)

---

## 11. Glossary

| Term | Definition |
|------|------------|
| **DHT** | Distributed Hash Table - the peer-to-peer data storage layer in Holochain |
| **EconomicEvent** | A ValueFlows concept representing an observed economic action |
| **EconomicResource** | A ValueFlows concept representing a specific instance of a resource |
| **hc-http-gw** | Holochain HTTP Gateway - exposes zome functions as REST endpoints |
| **PPR** | Private Participation Receipt - cryptographic proof of economic participation |
| **ResourceSpecification** | A ValueFlows concept defining the characteristics of a type of resource |
| **Zome** | A Holochain module containing application logic |

---

## 12. References

- [ValueFlows Ontology](https://www.valueflows.org/)
- [Holochain Documentation](https://developer.holochain.org/)
- [ERPLibre GitHub](https://github.com/ERPLibre/ERPLibre)
- [Odoo API Documentation](https://www.odoo.com/documentation/16.0/developer/reference/external_api.html)
