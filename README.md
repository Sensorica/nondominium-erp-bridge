# Nondominium-ERP Bridge PoC

> Bridge traditional ERP systems with Nondominium's peer-to-peer resource-sharing infrastructure

## Overview

This project demonstrates how organizations using centralized ERP systems can participate in decentralized resource economies through Nondominium without abandoning their existing business infrastructure.

**Key Features:**
- Selective resource publishing from ERP inventory to Nondominium
- Cross-organizational resource discovery
- Organization-level Holochain agents (not individual users)
- Cryptographic accountability via PPR (Private Participation Receipts)

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    ERPLibre     │     │ Protocol Bridge │     │    Holochain    │
│   (Inventory)   │────▶│  (hc-http-gw)   │────▶│  (Nondominium)  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                              HTTP                  WebSocket
```

## Documentation

| Document | Description |
|----------|-------------|
| [Documentation Index](documentation/DOCUMENTATION_INDEX.md) | Navigation hub for all documentation |
| [Requirements](documentation/requirements/erp_bridge_requirements.md) | High-level requirements and business goals |
| [Technical Specifications](documentation/specifications/erp_bridge_specifications.md) | Architecture and API details |
| [PoC Implementation Guide](documentation/specifications/poc/hc_http_gw_poc_spec.md) | Step-by-step implementation |

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.10+
- Holochain 0.4.x
- ERPLibre (Odoo-based)

### Setup

```bash
# Clone the repository
git clone https://github.com/Sensorica/nondominium-erplibre-poc.git
cd nondominium-erplibre-poc

# Start services
docker-compose up -d

# Run the sync script
python bridge/sync_erp_to_nondominium.py
```

## Project Structure

```
nondominium-erplibre-poc/
├── README.md                           # This file
├── docker-compose.yml                  # Container orchestration
├── documentation/
│   ├── DOCUMENTATION_INDEX.md          # Documentation navigation
│   ├── requirements/
│   │   └── erp_bridge_requirements.md  # High-level requirements
│   ├── specifications/
│   │   ├── erp_bridge_specifications.md # Technical specs
│   │   └── poc/
│   │       └── hc_http_gw_poc_spec.md  # PoC implementation guide
│   └── archives/
│       └── erp_holochain_bridge_v1.md  # Original document (archived)
├── bridge/                             # Python bridge scripts
│   ├── erp_client.py                   # ERPLibre API client
│   ├── gateway_client.py               # hc-http-gw client
│   └── sync_erp_to_nondominium.py      # Main sync script
└── demo/                               # Demo scripts and web UI
```

## PoC Scope

### In Scope
- ERPLibre inventory reading via XML-RPC API
- Product → ResourceSpecification mapping
- Cross-organizational resource discovery
- Basic Use process initiation
- PPR generation

### Out of Scope (PoC)
- Complex governance rules
- Financial transactions
- Multi-ERP support (Dolibarr, ERPNext)
- Real-time signals/webhooks
- Full UI integration

## Phased Approach

| Phase | Protocol Bridge | Features |
|-------|-----------------|----------|
| **PoC** (Current) | hc-http-gw | Unidirectional sync, polling |
| **Production** | Node.js | Bidirectional, signals, webhooks |
| **Advanced** | Python client | ML/AI integration |

## Related Projects

- [Nondominium](https://github.com/Sensorica/nondominium) - ValueFlows-compliant Holochain app
- [ERPLibre](https://github.com/ERPLibre/ERPLibre) - Open-source Odoo fork
- [hc-http-gw](https://github.com/holochain/hc-http-gw) - Holochain HTTP Gateway
- [ValueFlows](https://www.valueflows.org/) - Economic coordination ontology

## Contributing

Contributions welcome! Please read the documentation before submitting PRs.

## License

[License to be determined]
