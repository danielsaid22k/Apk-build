
#!/usr/bin/env python3
from pathlib import Path
from ccs.core.paths import runtime_root
import json
import os
import socket

from app.env import load
from app.wallets import validate
from app.runtime import ensure_directories
from app.bridge_url import validate_public_https
from app.solana_rpc import validate as validate_solana_rpc

ROOT=runtime_root()
load(ROOT/".env", override=True)

def main():
    ensure_directories(ROOT)
    config=json.loads((ROOT/"config.json").read_text(encoding="utf-8"))
    print("="*60)
    print(" Health Check — Crypto Certified Switch v6.1.1 SPL + Helius RPC")
    print("="*60)
    errors=validate(config)
    if os.getenv("ENABLE_TELEGRAM","true").lower() in {"true","1","yes","sim"}:
        if not os.getenv("TELEGRAM_BOT_TOKEN",""):errors.append("TELEGRAM_BOT_TOKEN ausente.")
        if not os.getenv("TELEGRAM_CHAT_ID",""):errors.append("TELEGRAM_CHAT_ID ausente.")
    enabled=sum(1 for w in config["wallets"] if w.get("enabled"))
    print(f"Carteiras de origem habilitadas: {enabled}")
    if errors:
        for error in errors:print("ERRO:",error)
        print("Health check reprovado.")
        return 1
    print("Origens e destinos válidos e diferentes.")
    solana_enabled=any(w.get("enabled") and w.get("network")=="solana" for w in config.get("wallets",[]))
    rpc_ok,rpc_detail=validate_solana_rpc(config)
    if rpc_ok:
        print(f"RPC Solana: OK ({rpc_detail})")
    elif solana_enabled:
        print(f"ERRO: RPC Solana indisponível: {rpc_detail}")
        return 1
    else:
        print(f"Aviso: RPC Solana não configurada: {rpc_detail}")
    public_url = os.getenv("APPROVAL_BRIDGE_PUBLIC_URL", "")
    valid_public, public_reason = validate_public_https(public_url)
    if valid_public:
        print("Bridge público HTTPS configurado.")
    else:
        print(f"Aviso: botões de carteira bloqueados — {public_reason}")
    print("Health check concluído com sucesso.")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
