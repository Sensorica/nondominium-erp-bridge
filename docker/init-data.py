#!/usr/bin/env python3
"""Seed Odoo with sample products matching the mock ERP data.

Usage:
    1. Start Odoo: docker compose up -d
    2. Create a database via http://localhost:8069 (name: "nondominium-poc", install Inventory)
    3. Run: python init-data.py

Requires: pip install OdooRPC  (or use xmlrpc.client directly)
"""

import xmlrpc.client

# Connection settings
URL = "http://localhost:8069"
DB = "nondominium-poc"
USERNAME = "admin"
PASSWORD = "admin"

# Products matching bridge/erp_mock.py MOCK_PRODUCTS
PRODUCTS = [
    {
        "name": "Prusa i3 MK3S+ 3D Printer",
        "default_code": "FAB-3DP-001",
        "type": "product",
        "categ_name": "equipment",
        "description": (
            "Open-source FDM 3D printer with auto bed leveling, "
            "filament sensor, and power panic recovery. "
            "Build volume: 250x210x210mm."
        ),
        "list_price": 799.0,
        "standard_price": 600.0,
        "qty_available": 2.0,
    },
    {
        "name": "K40 CO2 Laser Cutter",
        "default_code": "FAB-LAS-001",
        "type": "product",
        "categ_name": "equipment",
        "description": (
            "40W CO2 laser engraver/cutter suitable for wood, acrylic, "
            "leather, and paper. Work area: 300x200mm."
        ),
        "list_price": 450.0,
        "standard_price": 300.0,
        "qty_available": 1.0,
    },
    {
        "name": "Arduino Mega 2560 Rev3",
        "default_code": "FAB-MCU-001",
        "type": "product",
        "categ_name": "components",
        "description": (
            "ATmega2560 microcontroller board with 54 digital I/O pins, "
            "16 analog inputs, and 256KB flash memory."
        ),
        "list_price": 38.0,
        "standard_price": 20.0,
        "qty_available": 15.0,
    },
    {
        "name": "PLA Filament 1.75mm (1kg)",
        "default_code": "FAB-FIL-001",
        "type": "product",
        "categ_name": "consumable",
        "description": (
            "Standard PLA filament for FDM 3D printing. "
            "1.75mm diameter, 1kg spool, various colors available."
        ),
        "list_price": 25.0,
        "standard_price": 15.0,
        "qty_available": 20.0,
    },
]


def main() -> None:
    # Authenticate
    common = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/common")
    uid = common.authenticate(DB, USERNAME, PASSWORD, {})
    if not uid:
        print("ERROR: Authentication failed. Check DB name and credentials.")
        return
    print(f"Authenticated as uid={uid}")

    models = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object")

    def execute(model: str, method: str, *args: object, **kwargs: object) -> object:
        return models.execute_kw(DB, uid, PASSWORD, model, method, list(args), kwargs)

    # Get or create product categories
    category_cache: dict[str, int] = {}
    for product in PRODUCTS:
        categ_name = product["categ_name"]
        if categ_name not in category_cache:
            ids = execute("product.category", "search", [("name", "=", categ_name)])
            if ids:
                category_cache[categ_name] = ids[0]
            else:
                cat_id = execute("product.category", "create", {"name": categ_name})
                category_cache[categ_name] = cat_id
                print(f"  Created category: {categ_name} (id={cat_id})")

    # Create products
    for product in PRODUCTS:
        existing = execute(
            "product.template",
            "search",
            [("default_code", "=", product["default_code"])],
        )
        if existing:
            print(f"  SKIP (exists): {product['name']}")
            continue

        vals = {
            "name": product["name"],
            "default_code": product["default_code"],
            "type": product["type"],
            "categ_id": category_cache[product["categ_name"]],
            "description": product["description"],
            "list_price": product["list_price"],
            "standard_price": product["standard_price"],
        }
        prod_id = execute("product.template", "create", vals)
        print(f"  Created: {product['name']} (id={prod_id})")

    print("\nDone! Products created in Odoo.")
    print("View them at: http://localhost:8069/web#action=stock.product_template_action_product")


if __name__ == "__main__":
    main()
