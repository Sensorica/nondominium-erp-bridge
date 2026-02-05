"""Mock ERPLibre client with sample Sensorica products.

Simulates reading from an ERPLibre (Odoo) product.product model
so the bridge can be developed and tested without a live ERP instance.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MockProduct:
    """Mirrors key fields from ERPLibre product.product."""

    id: int
    name: str
    description: str
    category: str
    list_price: float
    qty_available: float
    uom_name: str
    image_url: str | None = None
    tags: list[str] | None = None


# Sample Sensorica fab-lab products
MOCK_PRODUCTS: list[MockProduct] = [
    MockProduct(
        id=1,
        name="Prusa MK4 3D Printer",
        description="FDM 3D printer for rapid prototyping, 250x210x220mm build volume",
        category="equipment",
        list_price=799.0,
        qty_available=2.0,
        uom_name="unit",
        tags=["3d-printing", "prototyping", "fab-lab"],
    ),
    MockProduct(
        id=2,
        name="40W CO2 Laser Cutter",
        description="40W CO2 laser for cutting and engraving wood, acrylic, and leather",
        category="equipment",
        list_price=1200.0,
        qty_available=1.0,
        uom_name="unit",
        tags=["laser-cutting", "fab-lab"],
    ),
    MockProduct(
        id=3,
        name="Arduino Mega 2560",
        description="ATmega2560-based microcontroller board for electronics prototyping",
        category="electronics",
        list_price=45.0,
        qty_available=10.0,
        uom_name="unit",
        tags=["electronics", "microcontroller", "prototyping"],
    ),
    MockProduct(
        id=4,
        name="PLA Filament 1kg - White",
        description="1.75mm PLA filament spool, 1kg, for FDM 3D printers",
        category="consumable",
        list_price=25.0,
        qty_available=8.0,
        uom_name="kg",
        tags=["3d-printing", "consumable"],
    ),
]


class MockERPClient:
    """Simulates reading products from ERPLibre."""

    def __init__(self) -> None:
        self._products = list(MOCK_PRODUCTS)

    def get_all_products(self) -> list[MockProduct]:
        return list(self._products)

    def get_available_products(self) -> list[MockProduct]:
        """Return products with qty > 0 (available for sharing)."""
        return [p for p in self._products if p.qty_available > 0]

    def get_product_by_id(self, product_id: int) -> MockProduct | None:
        for p in self._products:
            if p.id == product_id:
                return p
        return None
