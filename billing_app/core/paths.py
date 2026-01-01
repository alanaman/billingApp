"""Path helpers for locating packaged resources and writable data files."""
from __future__ import annotations

import os
import sys
from pathlib import Path


def app_root() -> Path:
    """Return the root directory for the application (source or frozen)."""
    try:
        base = Path(sys._MEIPASS)  # type: ignore[attr-defined]
    except Exception:
        # In dev, start from the project root (one level above the package)
        base = Path(__file__).resolve().parent.parent.parent
    return base


def resource_path(relative_path: str) -> str:
    """Resolve a resource path that works in dev and in PyInstaller builds."""
    base = app_root()
    candidate = base / relative_path
    if candidate.exists():
        return str(candidate)

    # Fallback: some resources (like database/) live alongside the package during dev
    alt = base / "billing_app" / relative_path
    return str(alt)


def ensure_dir(path: Path) -> Path:
    """Create the directory if it does not exist and return the path."""
    path.mkdir(parents=True, exist_ok=True)
    return path
