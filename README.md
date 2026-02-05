# Nondominium-ERP Bridge PoC

> Bridge traditional ERP systems with Nondominium's peer-to-peer resource-sharing infrastructure

## Overview

This project demonstrates how organizations using centralized ERP systems can participate in decentralized resource economies through Nondominium without abandoning their existing business infrastructure.

**Key Features:**
- Selective resource publishing from ERP inventory to Nondominium
- Cross-organizational resource discovery
- Organization-level Holochain agents (not individual users)
- Typed Python client for hc-http-gw

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    ERPLibre     │     │  Python Bridge  │     │    Holochain    │
│   (Inventory)   │────>│  (hc-http-gw)   │────>│  (Nondominium)  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
     XML-RPC              HTTP GET + base64url       DHT
```

## Quick Start

### Prerequisites

- **Nix** with flakes enabled
- Built `nondominium.happ` (see [Nondominium repo](https://github.com/Sensorica/nondominium))

### Install

```bash
# Enter the Nix dev shell (provides holochain, hc, hc-http-gw, Python 3.12, uv)
nix develop

# Create virtual environment and install Python deps
uv venv .venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

### Run Tests (no infra needed)

```bash
pytest
```

### Run with Live Infrastructure

```bash
# 1. Enter the Nix dev shell (if not already in it)
nix develop

# 2. Build the Nondominium hApp (if not done)
cd ../nondominium && npm run build:happ && cd -

# 3. Start conductor + gateway
bash scripts/setup_conductor.sh

# 4. Discover the DNA hash and set it in .env
cp .env.example .env
# Edit .env and set HC_DNA_HASH from the sandbox output

# 5. Run smoke test
python scripts/smoke_test.py

# 6. Create test data from mock ERP products
python scripts/create_test_data.py
```

## Project Structure

```
nondominium-erp-bridge/
├── flake.nix                           # Nix dev shell (holonix + Python + uv)
├── .env.example                        # Environment variable template
├── pyproject.toml                      # Python project config (PEP 621)
├── bridge/
│   ├── __init__.py
│   ├── config.py                       # GatewayConfig from env vars
│   ├── gateway_client.py               # Typed hc-http-gw client (core)
│   ├── models.py                       # Pydantic models matching Rust types
│   ├── mapper.py                       # ERP product → Nondominium mapping
│   └── erp_mock.py                     # Mock ERPLibre client
├── scripts/
│   ├── setup_conductor.sh              # Nix-based conductor + gateway setup
│   ├── smoke_test.py                   # Integration test (needs infra)
│   └── create_test_data.py             # Populate Nondominium from mock ERP
├── tests/
│   ├── test_models.py                  # Pydantic serialization tests
│   ├── test_gateway_client.py          # Client tests (mocked HTTP)
│   └── test_mapper.py                  # Mapping correctness tests
└── documentation/                      # Design docs and specs
```

## How hc-http-gw Works

The bridge communicates with Holochain via [hc-http-gw](https://github.com/holochain/hc-http-gw), which exposes zome functions as HTTP GET endpoints:

```
GET {host}/{dna_hash}/{app_id}/{zome}/{fn}?payload={base64url_json}
```

- Payloads are **base64url-encoded JSON** (RFC 4648, no padding)
- Functions taking `()` omit the `?payload=` parameter
- Responses are JSON-transcoded Holochain data

## Current Limitations

- **Mock ERP only**: Uses `erp_mock.py` instead of live ERPLibre XML-RPC
- **No bidirectional sync**: One-way ERP → Nondominium only
- **ActionHash format**: Serialization format from hc-http-gw needs verification with a running instance
- **Single organization**: No multi-tenant support yet

## Documentation

| Document | Description |
|----------|-------------|
| [Documentation Index](documentation/DOCUMENTATION_INDEX.md) | Navigation hub for all documentation |
| [Requirements](documentation/requirements/erp_bridge_requirements.md) | High-level requirements and business goals |
| [Technical Specifications](documentation/specifications/erp_bridge_specifications.md) | Architecture and API details |
| [PoC Implementation Guide](documentation/specifications/poc/hc_http_gw_poc_spec.md) | Step-by-step implementation |

## Related Projects

- [Nondominium](https://github.com/Sensorica/nondominium) - Holochain app (hdi 0.7.0 / hdk 0.6.0)
- [ERPLibre](https://github.com/ERPLibre/ERPLibre) - Open-source Odoo fork
- [hc-http-gw](https://github.com/holochain/hc-http-gw) - Holochain HTTP Gateway
- [ValueFlows](https://www.valueflows.org/) - Economic coordination ontology

## Contributing

Contributions welcome! Please read the documentation before submitting PRs.

## License

[License to be determined]
