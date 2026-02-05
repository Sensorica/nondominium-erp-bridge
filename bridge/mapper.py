"""Maps ERP products to Nondominium input types.

Uses the actual field names from the Nondominium zome coordinator:
- ResourceSpecificationInput uses `category` (not `default_unit`)
- EconomicResourceInput uses `spec_hash` (not `conforms_to`)
"""

from __future__ import annotations

from bridge.erp_mock import MockProduct
from bridge.models import EconomicResourceInput, ResourceSpecificationInput


def product_to_resource_spec(product: MockProduct) -> ResourceSpecificationInput:
    """Map an ERP product to a Nondominium ResourceSpecificationInput."""
    return ResourceSpecificationInput(
        name=product.name,
        description=product.description,
        category=product.category,
        image_url=product.image_url,
        tags=product.tags or [],
        governance_rules=[],
    )


def product_to_economic_resource(
    product: MockProduct,
    spec_hash: str,
) -> EconomicResourceInput:
    """Map an ERP product to a Nondominium EconomicResourceInput.

    Args:
        product: The ERP product to map.
        spec_hash: The ActionHash of the ResourceSpecification created for this product.
    """
    return EconomicResourceInput(
        spec_hash=spec_hash,
        quantity=product.qty_available,
        unit=product.uom_name,
        current_location=None,
    )
