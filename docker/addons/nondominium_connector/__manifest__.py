{
    "name": "Nondominium Connector",
    "version": "17.0.0.1.0",
    "category": "Inventory",
    "summary": "Sync products to Nondominium (Holochain) via hc-http-gw",
    "description": """
        Connects Odoo products to the Nondominium peer-to-peer resource
        sharing network via the hc-http-gw HTTP gateway.

        Features:
        - Configure Nondominium gateway connection in Settings
        - "Sync to Nondominium" button on product form
        - Track sync status and Nondominium hashes per product
    """,
    "author": "Sensorica",
    "license": "LGPL-3",
    "depends": ["product", "stock"],
    "data": [
        "security/ir.model.access.csv",
        "views/nondominium_config_views.xml",
        "views/product_views.xml",
    ],
    "installable": True,
    "application": False,
}
