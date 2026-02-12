import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    nondominium_spec_hash = fields.Char(
        string="Spec Hash",
        readonly=True,
        copy=False,
        help="Nondominium ResourceSpecification ActionHash",
    )
    nondominium_resource_hash = fields.Char(
        string="Resource Hash",
        readonly=True,
        copy=False,
        help="Nondominium EconomicResource ActionHash",
    )
    nondominium_synced = fields.Boolean(
        string="Synced",
        readonly=True,
        copy=False,
        default=False,
    )
    nondominium_sync_date = fields.Datetime(
        string="Last Sync",
        readonly=True,
        copy=False,
    )

    def _get_product_category_name(self):
        """Map Odoo product category to Nondominium category string."""
        if self.categ_id:
            return self.categ_id.name.lower()
        return "uncategorized"

    def action_sync_to_nondominium(self):
        """Sync this product to Nondominium as ResourceSpecification + EconomicResource."""
        self.ensure_one()
        config = self.env["nondominium.config"].get_config()

        # Step 1: Create ResourceSpecification
        spec_input = {
            "name": self.name or "",
            "description": self.description or self.name or "",
            "category": self._get_product_category_name(),
            "image_url": None,
            "tags": [],
            "governance_rules": [],
        }

        try:
            spec_result = config.call_zome(
                "zome_resource", "create_resource_specification", spec_input
            )
            spec_hash = spec_result.get("spec_hash", "")
            _logger.info("Created ResourceSpecification: %s for %s", spec_hash, self.name)
        except Exception as e:
            _logger.error("Failed to create ResourceSpecification for %s: %s", self.name, e)
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Sync Failed",
                    "message": f"ResourceSpecification creation failed: {e}",
                    "type": "danger",
                    "sticky": True,
                },
            }

        # Step 2: Create EconomicResource
        resource_input = {
            "spec_hash": spec_hash,
            "quantity": self.qty_available if hasattr(self, "qty_available") else 1.0,
            "unit": self.uom_id.name if self.uom_id else "unit",
            "current_location": None,
        }

        try:
            resource_result = config.call_zome(
                "zome_resource", "create_economic_resource", resource_input
            )
            resource_hash = resource_result.get("resource_hash", "")
            _logger.info("Created EconomicResource: %s for %s", resource_hash, self.name)
        except Exception as e:
            _logger.error("Failed to create EconomicResource for %s: %s", self.name, e)
            # Still record the spec hash even if resource creation failed
            self.write(
                {
                    "nondominium_spec_hash": spec_hash,
                    "nondominium_synced": False,
                    "nondominium_sync_date": fields.Datetime.now(),
                }
            )
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Partial Sync",
                    "message": f"Spec created but resource failed: {e}",
                    "type": "warning",
                    "sticky": True,
                },
            }

        # Step 3: Record sync status
        self.write(
            {
                "nondominium_spec_hash": spec_hash,
                "nondominium_resource_hash": resource_hash,
                "nondominium_synced": True,
                "nondominium_sync_date": fields.Datetime.now(),
            }
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Sync Successful",
                "message": (
                    f"Product synced to Nondominium.\n"
                    f"Spec: {spec_hash[:16]}...\n"
                    f"Resource: {resource_hash[:16]}..."
                ),
                "type": "success",
                "sticky": False,
            },
        }
