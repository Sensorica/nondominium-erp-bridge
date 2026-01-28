# Documentation Index

> **Nondominium-ERP Bridge Project Documentation**
> **Last Updated**: 2026-01-27

---

## Quick Navigation

| Document | Purpose | Audience |
|----------|---------|----------|
| [Requirements](requirements/erp_bridge_requirements.md) | High-level requirements, business goals, scope | Product Owners, Stakeholders |
| [Technical Specifications](specifications/erp_bridge_specifications.md) | Architecture, APIs, security, deployment | Developers, Architects |
| [PoC Implementation Guide](specifications/poc/hc_http_gw_poc_spec.md) | Step-by-step PoC setup and code | Developers |

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
- Phased approach (PoC → Production → Advanced)

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

PoC-specific implementation guide covering:
- hc-http-gw configuration and limitations
- ERPLibre integration code
- Step-by-step implementation phases
- Complete code examples
- Testing and validation procedures
- Known limitations and workarounds
- Next steps after PoC

---

## Document Relationships

```
┌─────────────────────────────────────────────────────────────────────┐
│                          DOCUMENTATION                              │
│                                                                     │
│  ┌─────────────────────┐                                            │
│  │    REQUIREMENTS     │ ◄── WHAT needs to be built and WHY         │
│  │  (High-Level Goals) │                                            │
│  └──────────┬──────────┘                                            │
│             │                                                       │
│             │ Informs                                                │
│             ▼                                                       │
│  ┌─────────────────────┐                                            │
│  │   SPECIFICATIONS    │ ◄── HOW it will be built technically       │
│  │ (Technical Details) │                                            │
│  └──────────┬──────────┘                                            │
│             │                                                       │
│             │ Implements                                             │
│             ▼                                                       │
│  ┌─────────────────────┐                                            │
│  │   POC SPEC          │ ◄── Immediate implementation details       │
│  │ (Implementation)    │                                            │
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
| **Protocol Bridge** | Reusable HTTP↔WebSocket adapter for Holochain |
| **ERP Module** | ERP-specific integration layer (data mapping, UI) |
| **hc-http-gw** | Holochain HTTP Gateway for PoC |
| **Organization Agent** | Holochain agent representing an organization (not individual users) |
| **PPR** | Private Participation Receipt - reputation tracking |

### Architecture Summary

```
ERP (ERPLibre) ←→ Protocol Bridge (hc-http-gw/Node.js) ←→ Holochain Conductor ←→ Nondominium DHT
```

### PoC vs Production

| Aspect | PoC | Production |
|--------|-----|------------|
| Protocol Bridge | hc-http-gw | Node.js |
| Sync Direction | ERP → Nondominium | Bidirectional |
| Real-time | Polling | Signals + Webhooks |
| ERP Support | ERPLibre only | Multi-ERP |

---

## Contributing

When updating documentation:

1. **Requirements changes** → Update `requirements/erp_bridge_requirements.md`
2. **Architecture changes** → Update `specifications/erp_bridge_specifications.md`
3. **Implementation changes** → Update `specifications/poc/hc_http_gw_poc_spec.md`
4. **Version updates** → Update this index

---

## Contact

- **Project**: [Nondominium ERP Bridge PoC](https://github.com/Sensorica/nondominium-erplibre-poc)
- **Nondominium**: [Sensorica/nondominium](https://github.com/Sensorica/nondominium)
- **ERPLibre**: [ERPLibre/ERPLibre](https://github.com/ERPLibre/ERPLibre)
