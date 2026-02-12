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
