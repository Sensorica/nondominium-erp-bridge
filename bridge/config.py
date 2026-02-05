"""Configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class GatewayConfig:
    """Connection settings for hc-http-gw."""

    url: str = "http://127.0.0.1:8888"
    timeout: int = 30
    app_id: str = "nondominium"
    dna_hash: str = ""

    @classmethod
    def from_env(cls, dotenv_path: str | None = None) -> GatewayConfig:
        """Load config from environment variables (.env file supported)."""
        load_dotenv(dotenv_path)
        return cls(
            url=os.getenv("HC_GW_URL", "http://127.0.0.1:8888").rstrip("/"),
            timeout=int(os.getenv("HC_GW_TIMEOUT", "30")),
            app_id=os.getenv("HC_APP_ID", "nondominium"),
            dna_hash=os.getenv("HC_DNA_HASH", ""),
        )
