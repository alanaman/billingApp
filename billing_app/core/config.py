"""Configuration loading for the BillingApp."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from .paths import resource_path
from .state import log_msg

DEFAULT_CONFIG = {"invoice_prefix": "A"}


def load_config() -> Dict[str, Any]:
    config_path = Path(resource_path("config.json"))
    if not config_path.exists():
        log_msg(f"Config file not found at {config_path}, using defaults.")
        return DEFAULT_CONFIG.copy()

    try:
        with config_path.open("r", encoding="utf-8") as fh:
            loaded = json.load(fh)
        merged = {**DEFAULT_CONFIG, **loaded}
        return merged
    except Exception as exc:  # pylint: disable=broad-except
        log_msg(f"Failed to load config.json: {exc}. Using defaults.")
        return DEFAULT_CONFIG.copy()
