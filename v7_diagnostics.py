#!/usr/bin/env python3
from pathlib import Path
import json
import os

from app.env import load
from app.runtime import ensure_directories
from ccs.services.solana_rpc import configured_endpoints, redact_url, status, validate
from ccs.storage.json_cache import JsonCache

ROOT = Path(__file__).resolve().parent
ensure_directories(ROOT)
load(ROOT / ".env", override=True)

def main() -> int:
    config = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    print("CCS v7.0.0 — diagnóstico Sprints 1, 2 e 3")
    print("Arquitetura: OK (ccs.core / ccs.services / ccs.storage)")
    cache = JsonCache(
        ROOT / "data" / "token_metadata_cache.json",
        int(os.getenv("TOKEN_METADATA_CACHE_TTL_SECONDS", "21600")),
    )
    removed = cache.purge_expired()
    print(f"Cache de metadados: OK (expirados removidos={removed})")

    endpoints = configured_endpoints(config)
    print(f"RPCs Solana configuradas: {len(endpoints)}")
    for endpoint in endpoints:
        print(" -", redact_url(endpoint))

    solana_enabled = any(
        w.get("enabled") and w.get("network") == "solana"
        for w in config.get("wallets", [])
    )
    if endpoints:
        ok, detail = validate(config)
        print("RPC Solana:", "OK" if ok else "FALHOU", detail)
        if solana_enabled and not ok:
            return 2
    elif solana_enabled:
        print("RPC Solana: FALHOU — Solana habilitada sem RPC.")
        return 2
    else:
        print("RPC Solana: não configurada (Solana desabilitada).")

    last = status()
    if last:
        print("Último status RPC:", last.get("ok"), last.get("endpoint"))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
