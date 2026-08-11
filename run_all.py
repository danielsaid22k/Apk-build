
#!/usr/bin/env python3
from pathlib import Path
from ccs.core.paths import runtime_root
import json
import os
import signal
import subprocess
import sys
import threading
import time

from app.runtime import ensure_directories
from app.env import load
from app.backup import create
from app.telegram import send,dashboard,dashboard_buttons
from approval_server import Handler
from app.solana_rpc import validate as validate_solana_rpc
from http.server import ThreadingHTTPServer

ROOT=runtime_root()
ensure_directories(ROOT)
load(ROOT/".env", override=True)
running=True

def stop(*_):
    global running
    running=False

def bridge(config):
    host=os.getenv("APPROVAL_BRIDGE_HOST",config["approval_bridge"]["host"])
    port=int(os.getenv("APPROVAL_BRIDGE_PORT",str(config["approval_bridge"]["port"])))
    server=ThreadingHTTPServer((host,port),Handler);server.timeout=1
    print(f"🌉 Bridge ativo em http://{host}:{port}",flush=True)
    while running:server.handle_request()
    server.server_close()

def heartbeat(config):
    while running:
        seconds=max(60,int(os.getenv("TELEGRAM_HEARTBEAT_SECONDS","60")))
        for _ in range(seconds):
            if not running:return
            time.sleep(1)
        send(ROOT,
             "💓 <b>SINAL DE VIDA CCS v7.0.0</b>\n"
             "🟢 Coletor online\n🟢 Telegram online\n🟢 Bridge online\n"
             "Nenhuma proposta é necessária para este aviso.",
             dashboard_buttons())

def auto_backup():
    while running:
        keep=max(1,int(os.getenv("AUTO_BACKUP_KEEP","20")))
        path=create(ROOT,keep);print(f"💾 Backup: {path.relative_to(ROOT)}",flush=True)
        seconds=max(300,int(os.getenv("AUTO_BACKUP_INTERVAL_SECONDS","3600")))
        for _ in range(seconds):
            if not running:return
            time.sleep(1)

def main():
    signal.signal(signal.SIGINT,stop)
    config=json.loads((ROOT/"config.json").read_text(encoding="utf-8"))
    solana_enabled=any(w.get("enabled") and w.get("network")=="solana" for w in config.get("wallets",[]))
    if os.getenv("SOLANA_RPC_VALIDATE_ON_START","true").strip().lower() in {"1","true","yes","sim","on"}:
        ok,detail=validate_solana_rpc(config)
        if ok:
            print(f"✅ RPC Solana validada: {detail}",flush=True)
        elif solana_enabled:
            print(f"❌ RPC Solana inválida: {detail}",flush=True)
            print("Execute CONFIGURE_SOLANA_RPC.bat antes de iniciar.",flush=True)
            return 2
        else:
            print(f"⚠️ RPC Solana não validada: {detail}",flush=True)
    threading.Thread(target=bridge,args=(config,),daemon=True).start()
    threading.Thread(target=heartbeat,args=(config,),daemon=True).start()
    threading.Thread(target=auto_backup,daemon=True).start()
    subprocess.Popen([sys.executable,"-u","telegram_control.py"],cwd=ROOT)
    send(ROOT,"🚀 <b>CCS v7.0.0 INICIADO</b>\nStable Bridge ativo.",dashboard_buttons())
    interval=max(30,int(os.getenv("POLL_INTERVAL_SECONDS","100")))
    while running:
        subprocess.run([sys.executable,"-u","scan_once.py"],cwd=ROOT)
        for _ in range(interval):
            if not running:break
            time.sleep(1)
    print("Encerrado com segurança.")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
