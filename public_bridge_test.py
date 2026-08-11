#!/usr/bin/env python3
from pathlib import Path
import os

from app.env import load
from app.bridge_url import validate_public_https, check_health

ROOT = Path(__file__).resolve().parent
load(ROOT / ".env", override=True)
url = os.getenv("APPROVAL_BRIDGE_PUBLIC_URL", "").strip()

valid, reason = validate_public_https(url)
print(f"URL: {url or 'AUSENTE'}")
if not valid:
    print(f"FALHA: {reason}")
    raise SystemExit(1)

online, detail = check_health(url)
print(detail)
raise SystemExit(0 if online else 1)
