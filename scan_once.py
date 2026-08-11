
#!/usr/bin/env python3
from pathlib import Path
from ccs.core.paths import runtime_root
import json
import os

from app.runtime import ensure_directories
from app.env import load
from app.scanner import scan_all
from app.proposals import create
from app.telegram import send, proposal_card, proposal_buttons

ROOT=runtime_root()
ensure_directories(ROOT)
load(ROOT/".env", override=True)

def main():
    config=json.loads((ROOT/"config.json").read_text(encoding="utf-8"))
    assets,errors=scan_all(ROOT,config)
    proposals=[]
    for asset in assets:
        proposal=create(ROOT,config,asset)
        if proposal:
            proposals.append(proposal)
            base=os.getenv("APPROVAL_BRIDGE_PUBLIC_URL", "").strip().rstrip("/")
            if not base:
                print("AVISO: APPROVAL_BRIDGE_PUBLIC_URL ausente; proposta enviada sem botão externo seguro.")
            send(ROOT,proposal_card(proposal),proposal_buttons(proposal,base))
    print(f"Coleta concluída | ativos={len(assets)} | propostas={len(proposals)} | falhas={len(errors)}")
    for error in errors:print("FALHA:",error)
    if os.getenv("TELEGRAM_COLLECTION_RECEIPT","true").lower() in {"true","1","yes","sim"}:
        send(ROOT,
             "🧾 <b>RECIBO DE COLETA</b>\n"
             f"Ativos: <b>{len(assets)}</b>\nPropostas: <b>{len(proposals)}</b>\nFalhas: <b>{len(errors)}</b>")
    return 0 if not errors else 2

if __name__=="__main__":
    raise SystemExit(main())
