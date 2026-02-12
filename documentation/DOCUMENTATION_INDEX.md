# Documentation Index

> **Nondominium-ERP Bridge Project Documentation**
> **Last Updated**: 2026-02-12

---

## Quick Navigation

| Document | Purpose | Audience |
|----------|---------|----------|
| [Requirements](requirements/erp_bridge_requirements.md) | High-level requirements, business goals, scope | Product Owners, Stakeholders |
| [Technical Specifications](specifications/erp_bridge_specifications.md) | Architecture, APIs, security, deployment | Developers, Architects |
| [PoC Implementation Guide](specifications/poc/hc_http_gw_poc_spec.md) | PoC specification and implementation plan | Developers |
| [Architecture](implementation/architecture.md) | Actual system architecture, data flows, status | Developers |
| [Module Reference](implementation/module-reference.md) | Per-module API documentation | Developers |
| [Development Guide](implementation/development-guide.md) | Setup, testing, extending | Developers |

---

## Document Overview

### Requirements

**[erp_bridge_requirements.md](requirements/erp_bridge_requirements.md)**

High-level requirements document covering:
- Problem statement and opportunity
- Goals and success criteria
- Agent model concept (Organization as Holochain Agent)
- Functional requirements (FR-1 to FR-6)
- Non-functional requirements (NFR-1 to NFR-4)
- Scope boundaries and PoC scenario
- Data mapping requirements
- Phased approach (PoC -> Production -> Advanced)

### Technical Specifications

**[erp_bridge_specifications.md](specifications/erp_bridge_specifications.md)**

Detailed technical specifications covering:
- Two-layer architecture (Protocol Bridge + ERP Module)
- Component design and responsibilities
- Protocol bridge options comparison (hc-http-gw vs Node.js vs Python)
- Data models and mappings
- API specifications
- Security architecture
- Deployment topology
- Multi-ERP support matrix
- Migration path from PoC to production

### PoC Implementation

**[hc_http_gw_poc_spec.md](specifications/poc/hc_http_gw_poc_spec.md)**

PoC-specific specification and implementation guide covering:
- hc-http-gw configuration and limitations
- ERPLibre integration plan (aspirational)
- Step-by-step implementation phases
- Testing and validation procedures
- Known limitations and workarounds
- Next steps after PoC

### Implementation Documentation

**[architecture.md](implementation/architecture.md)**

What is actually built — the living record of the current implementation:
- System overview and pipeline diagrams (3 pipelines: sync, discovery, governance)
- Module dependency graph (8 modules)
- Sync, discovery, and governance data flows
- Key design decisions
- Implementation status (FR-1 to FR-6 mapping)
- Known gaps

**[module-reference.md](implementation/module-reference.md)**

Per-module API reference for developers:
- All 8 bridge modules with classes, methods, and types
- 5 scripts with descriptions (including end-to-end demo)
- Test coverage summary (101 tests across 8 files)

**[development-guide.md](implementation/development-guide.md)**

Practical guide for developers:
- Prerequisites and environment setup
- Running tests (101 tests, no infrastructure needed)
- Linting and type checking
- Running with live infrastructure
- Docker / Odoo development
- Running the end-to-end demo
- Extending the bridge (adding zome functions, ERP sources, model fields, Odoo addon)

---

## Document Relationships

```
┌─────────────────────────────────────────────────────────────────────┐
│                          DOCUMENTATION                              │
│                                                                     │
│  ┌─────────────────────┐                                            │
│  │    REQUIREMENTS     │ <── WHAT needs to be built and WHY         │
│  │  (High-Level Goals) │                                            │
│  └──────────┬──────────┘                                            │
│             │                                                       │
│             │ Informs                                               │
│             v                                                       │
│  ┌─────────────────────┐                                            │
│  │   SPECIFICATIONS    │ <── HOW it will be built technically       │
│  │ (Technical Details) │                                            │
│  └──────────┬──────────┘                                            │
│             │                                                       │
│             │ Guides                                                │
│             v                                                       │
│  ┌─────────────────────┐                                            │
│  │   POC SPEC          │ <── Planned approach and phases            │
│  │ (Specification)     │                                            │
│  └──────────┬──────────┘                                            │
│             │                                                       │
│             │ Realized as                                            │
│             v                                                       │
│  ┌─────────────────────┐                                            │
│  │  IMPLEMENTATION     │ <── WHAT IS actually built                 │
│  │ (Living Reference)  │     architecture, modules, dev guide       │
│  └─────────────────────┘                                            │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2026-01-27 | Initial documentation structure | - |
| - | - | Separated requirements from specifications | - |
| - | - | Created dedicated PoC implementation guide | - |
| 1.1 | 2026-02-05 | Corrected field names, zome functions, port, environment setup, and code examples to match actual Nondominium codebase and PoC scaffolding | - |
| 1.2 | 2026-02-12 | Added implementation documentation layer (architecture, module reference, development guide). Trimmed PoC spec to remove code duplicating bridge/ modules. Updated all cross-references and counts. | - |
| 1.3 | 2026-02-12 | Added governance bridge (`zome_gouvernance` models + gateway methods + `use_process` module). Added Docker/Odoo setup and `nondominium_connector` addon. Added end-to-end demo script. Updated all implementation docs to reflect 8 modules and 101 tests. | - |

---

## Archives

Historical documents preserved for reference:

| Document | Original Date | Reason for Archiving |
|----------|---------------|----------------------|
| [erp_holochain_bridge_v1.md](archives/erp_holochain_bridge_v1.md) | 2026-01-27 | Restructured into separate requirements and specifications |

---

## Quick Reference

### Key Concepts

| Term | Definition |
|------|------------|
| **Protocol Bridge** | Reusable HTTP->WebSocket adapter for Holochain |
| **ERP Module** | ERP-specific integration layer (data mapping, UI) |
| **hc-http-gw** | Holochain HTTP Gateway for PoC |
| **Organization Agent** | Holochain agent representing an organization (not individual users) |
| **PPR** | Private Participation Receipt - reputation tracking |

### Architecture Summary

```
ERP (Mock/Odoo) -> Python Bridge -> hc-http-gw -> Holochain Conductor -> Nondominium DHT
                                                                          ├── zome_resource
                                                                          └── zome_gouvernance
```

### PoC vs Production

| Aspect | PoC | Production |
|--------|-----|------------|
| Protocol Bridge | hc-http-gw (via Python client) | Node.js |
| Dev Environment | Nix dev shell | Docker / Nix |
| Sync Direction | ERP -> Nondominium | Bidirectional |
| Real-time | Polling | Signals + Webhooks |
| ERP Source | Mock ERP client + Odoo addon (PoC) | Multi-ERP (ERPLibre, etc.) |

---

## Contributing

When updating documentation:

1. **Requirements changes** -> Update `requirements/erp_bridge_requirements.md`
2. **Architecture changes** -> Update `specifications/erp_bridge_specifications.md`
3. **PoC specification changes** -> Update `specifications/poc/hc_http_gw_poc_spec.md`
4. **Implementation changes** -> Update docs in `implementation/` (architecture, module-reference, development-guide)
5. **Version updates** -> Update this index

---

## Contact

- **Project**: [Nondominium ERP Bridge PoC](https://github.com/Sensorica/nondominium-erplibre-poc)
- **Nondominium**: [Sensorica/nondominium](https://github.com/Sensorica/nondominium)
- **ERPLibre**: [ERPLibre/ERPLibre](https://github.com/ERPLibre/ERPLibre)
