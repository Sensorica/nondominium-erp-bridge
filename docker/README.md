# Odoo/ERPLibre Docker Setup

Docker Compose configuration for running Odoo 17.0 with PostgreSQL for Nondominium bridge development.

## Quick Start

```bash
cd docker/

# Start services
docker compose up -d

# Wait for Odoo to initialize (~30 seconds)
# Then open http://localhost:8069 in your browser
```

## First-Time Setup

1. **Create database**: At http://localhost:8069, fill in:
   - Database Name: `nondominium-poc`
   - Email: `admin`
   - Password: `admin`
   - Check "Demo data" (optional)
   - Click "Create Database"

2. **Install Inventory module**: Go to Apps → search "Inventory" → Install

3. **Seed sample products**:
   ```bash
   pip install OdooRPC  # or just use xmlrpc.client (no extra dep needed)
   python init-data.py
   ```

4. **Verify**: Go to Inventory → Products — you should see 4 Sensorica fab-lab products.

## Services

| Service | Port | Description |
|---------|------|-------------|
| `odoo` | 8069 | Odoo 17.0 web interface |
| `db` | (internal) | PostgreSQL 15 database |

## Custom Addons

The `addons/` directory is mounted at `/mnt/extra-addons` inside the Odoo container. Place Odoo modules here (e.g., `nondominium_connector/`) and they'll be available for installation.

After adding a new module:
1. Restart Odoo: `docker compose restart odoo`
2. Go to Apps → Update Apps List
3. Search for your module and install it

### `nondominium_connector` Addon

An Odoo 17 module that extends `product.template` with Nondominium sync capabilities. It provides a PoC UI for publishing Odoo products to the Nondominium DHT.

**Module structure:**

```
nondominium_connector/
├── __manifest__.py                  # Odoo module manifest (depends: product, stock)
├── models/
│   ├── nondominium_config.py        # nondominium.config model (gateway settings)
│   └── product_sync.py              # product.template extension (sync fields + button)
├── views/
│   ├── nondominium_config_views.xml # Settings form, tree, and menu item
│   └── product_views.xml            # Product form button, "Nondominium" tab, list column
└── security/
    └── ir.model.access.csv          # ACL: users read-only, stock managers full access
```

**Two models:**

- **`nondominium.config`** — Stores gateway connection settings (URL, DNA hash, app ID). Provides `call_zome()` for making hc-http-gw requests and a "Test Connection" button.
- **`product.template` (inherited)** — Adds sync fields (`nondominium_spec_hash`, `nondominium_resource_hash`, `nondominium_synced`, `nondominium_sync_date`) and a "Sync to Nondominium" button.

**Sync flow:**

1. Creates a `ResourceSpecification` (from product name, description, category)
2. Creates an `EconomicResource` (linked to the spec, with quantity and unit)
3. Records the returned hashes and sync timestamp on the Odoo product record
4. Handles partial failures (spec created but resource failed) with user notifications

**UI elements:**

- **Settings page**: Inventory → Configuration → Nondominium — configure gateway URL, DNA hash, app ID; "Test Connection" button
- **Product form**: "Sync to Nondominium" button in header; "Nondominium" tab showing sync status, last sync date, spec hash, resource hash
- **Product list**: Optional "ND Synced" column

**Permissions:**

| Group | Config Read | Config Write | Config Create | Config Delete |
|-------|------------|-------------|--------------|--------------|
| All users (`base.group_user`) | Yes | No | No | No |
| Stock managers (`stock.group_stock_manager`) | Yes | Yes | Yes | Yes |

**Current limitation — direct hc-http-gw calls:**

The addon currently talks directly to hc-http-gw, duplicating the base64url encoding and URL construction logic already provided by the Python bridge (`bridge/gateway_client.py`). The architectural decision has been made to refactor the addon to call the Python bridge's REST API instead, which will:

- Eliminate protocol duplication between the addon and the bridge
- Let the bridge own all Holochain communication logic
- Make the addon simpler (just HTTP POST to the bridge)
- Enable the addon to benefit from bridge features (Pydantic validation, error handling, sync state)

## Management

```bash
# View logs
docker compose logs -f odoo

# Stop services
docker compose down

# Stop and remove data
docker compose down -v

# Restart Odoo (e.g., after adding addon)
docker compose restart odoo
```
