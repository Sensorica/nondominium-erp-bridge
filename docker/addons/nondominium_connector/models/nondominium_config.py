import base64
import json
import logging

import requests
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class NondominiumConfig(models.Model):
    _name = "nondominium.config"
    _description = "Nondominium Gateway Configuration"

    name = fields.Char(default="Default", required=True)
    hc_gw_url = fields.Char(
        string="Gateway URL",
        default="http://127.0.0.1:8888",
        required=True,
        help="hc-http-gw base URL (e.g., http://127.0.0.1:8888)",
    )
    hc_dna_hash = fields.Char(
        string="DNA Hash",
        required=True,
        help="Nondominium DNA hash (from hc sandbox call list-apps)",
    )
    hc_app_id = fields.Char(
        string="App ID",
        default="nondominium",
        required=True,
    )
    active = fields.Boolean(default=True)

    @api.model
    def get_config(self):
        """Return the active configuration record."""
        config = self.search([("active", "=", True)], limit=1)
        if not config:
            raise ValueError(
                "No active Nondominium configuration found. Go to Settings → Nondominium."
            )
        return config

    def _build_url(self, zome, fn_name):
        """Build hc-http-gw URL for a zome function call."""
        return f"{self.hc_gw_url}/{self.hc_dna_hash}/{self.hc_app_id}/{zome}/{fn_name}"

    @staticmethod
    def _encode_payload(data):
        """Base64url-encode a JSON payload (RFC 4648, no padding)."""
        json_bytes = json.dumps(data, separators=(",", ":")).encode()
        return base64.urlsafe_b64encode(json_bytes).rstrip(b"=").decode()

    def call_zome(self, zome, fn_name, payload=None, timeout=30):
        """Call a Nondominium zome function via hc-http-gw.

        Args:
            zome: Zome name (e.g., "zome_resource")
            fn_name: Function name (e.g., "create_resource_specification")
            payload: Python dict/list to encode, or None for () functions
            timeout: HTTP timeout in seconds

        Returns:
            Parsed JSON response.

        Raises:
            requests.RequestException on HTTP errors.
        """
        url = self._build_url(zome, fn_name)
        params = {}
        if payload is not None:
            params["payload"] = self._encode_payload(payload)

        _logger.info("Nondominium call: %s/%s", zome, fn_name)
        resp = requests.get(url, params=params, timeout=timeout)
        resp.raise_for_status()
        return resp.json()

    def action_test_connection(self):
        """Test the gateway connection (button action)."""
        self.ensure_one()
        try:
            self.call_zome("zome_resource", "get_all_resource_specifications")
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Connection Successful",
                    "message": "Successfully connected to Nondominium gateway.",
                    "type": "success",
                    "sticky": False,
                },
            }
        except Exception as e:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Connection Failed",
                    "message": str(e),
                    "type": "danger",
                    "sticky": True,
                },
            }
