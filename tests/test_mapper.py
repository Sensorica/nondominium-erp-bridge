"""Tests for ERP product → Nondominium mapping."""

from bridge.erp_mock import MockProduct
from bridge.mapper import product_to_economic_resource, product_to_resource_spec

SAMPLE_PRODUCT = MockProduct(
    id=1,
    name="Prusa MK4",
    description="FDM 3D printer",
    category="equipment",
    list_price=799.0,
    qty_available=2.0,
    uom_name="unit",
    image_url="https://example.com/prusa.jpg",
    tags=["3d-printing", "fab-lab"],
)


class TestProductToResourceSpec:
    def test_maps_basic_fields(self):
        spec = product_to_resource_spec(SAMPLE_PRODUCT)
        assert spec.name == "Prusa MK4"
        assert spec.description == "FDM 3D printer"
        assert spec.category == "equipment"
        assert spec.image_url == "https://example.com/prusa.jpg"

    def test_maps_tags(self):
        spec = product_to_resource_spec(SAMPLE_PRODUCT)
        assert spec.tags == ["3d-printing", "fab-lab"]

    def test_empty_governance_rules(self):
        spec = product_to_resource_spec(SAMPLE_PRODUCT)
        assert spec.governance_rules == []

    def test_handles_none_tags(self):
        product = MockProduct(
            id=99,
            name="No Tags",
            description="Product without tags",
            category="other",
            list_price=10.0,
            qty_available=1.0,
            uom_name="unit",
            tags=None,
        )
        spec = product_to_resource_spec(product)
        assert spec.tags == []


class TestProductToEconomicResource:
    def test_maps_quantity_and_unit(self):
        resource = product_to_economic_resource(SAMPLE_PRODUCT, "uhCkkSpecHash")
        assert resource.quantity == 2.0
        assert resource.unit == "unit"

    def test_uses_spec_hash(self):
        resource = product_to_economic_resource(SAMPLE_PRODUCT, "uhCkkSpecHash")
        assert resource.spec_hash == "uhCkkSpecHash"

    def test_location_is_none(self):
        resource = product_to_economic_resource(SAMPLE_PRODUCT, "uhCkkSpecHash")
        assert resource.current_location is None

    def test_serialized_field_names(self):
        resource = product_to_economic_resource(SAMPLE_PRODUCT, "uhCkkHash")
        data = resource.model_dump(mode="json")
        assert "spec_hash" in data
        assert "conforms_to" not in data
