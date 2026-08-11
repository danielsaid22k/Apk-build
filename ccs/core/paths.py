from __future__ import annotations
from pathlib import Path
import os

def package_root() -> Path:
    return Path(__file__).resolve().parents[2]

def runtime_root() -> Path:
    value = os.getenv("CCS_RUNTIME_ROOT", "").strip()
    return Path(value).expanduser().resolve() if value else package_root()
