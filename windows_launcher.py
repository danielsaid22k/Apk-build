#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import os
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
import urllib.request

ROOT = Path(__file__).resolve().parent
ENV_PATH = ROOT / ".env"
TOOLS = ROOT / "tools"
LOGS = ROOT / "logs"
CLOUDFLARED = TOOLS / "cloudflared.exe"
TUNNEL_LOG = LOGS / "cloudflared.log"

URL_PATTERN = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com", re.I)

def ensure_dirs() -> None:
    for relative in (
        "data", "logs", "backups", "tools",
        "proposals/pending", "proposals/submitted",
        "proposals/completed", "proposals/rejected", "proposals/failed",
    ):
        (ROOT / relative).mkdir(parents=True, exist_ok=True)

def load_env() -> dict[str, str]:
    values: dict[str, str] = {}
    if not ENV_PATH.exists():
        return values
    for raw in ENV_PATH.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values

def save_env_value(key: str, value: str) -> None:
    lines = ENV_PATH.read_text(encoding="utf-8") .splitlines() if ENV_PATH.exists() else []
    output: list[str] = []
    found = False
    for line in lines:
        if line.startswith(key + "="):
            output.append(f"{key}={value}")
            found = True
        else:
            output.append(line)
    if not found:
        output.append(f"{key}={value}")
    ENV_PATH.write_text("\n".join(output).rstrip() + "\n", encoding="utf-8")

def bridge_online() -> bool:
    try:
        with urllib.request.urlopen("http://127.0.0.1:8765/health", timeout=1) as response:
            return response.status == 200
    except Exception:
        return False

def wait_for_tunnel(process: subprocess.Popen[str], timeout: int = 45) -> str:
    deadline = time.time() + timeout
    lines: list[str] = []
    while time.time() < deadline:
        if process.poll() is not None:
            break
        line = process.stdout.readline() if process.stdout else ""
        if line:
            lines.append(line)
            with TUNNEL_LOG.open("a", encoding="utf-8") as log:
                log.write(line)
            match = URL_PATTERN.search(line)
            if match:
                return match.group(0).rstrip("/")
        else:
            time.sleep(0.1)
    tail = "".join(lines[-20:])
    raise RuntimeError(
        "O Cloudflare Tunnel não gerou uma URL HTTPS.\n"
        f"Veja: {TUNNEL_LOG}\n{tail}"
    )

def terminate(process: subprocess.Popen | None) -> None:
    if not process or process.poll() is not None:
        return
    try:
        process.terminate()
        process.wait(timeout=5)
    except Exception:
        try:
            process.kill()
        except Exception:
            pass

def main() -> int:
    ensure_dirs()
    if not ENV_PATH.exists():
        shutil_source = ROOT / ".env.example"
        if shutil_source.exists():
            ENV_PATH.write_text(shutil_source.read_text(encoding="utf-8"), encoding="utf-8")
        else:
            ENV_PATH.write_text("", encoding="utf-8")

    if not CLOUDFLARED.exists():
        print("ERRO: tools\\cloudflared.exe não encontrado.")
        print("Execute primeiro: INSTALL_WINDOWS.bat")
        return 1

    env_values = load_env()
    if not env_values.get("TELEGRAM_BOT_TOKEN") or not env_values.get("TELEGRAM_CHAT_ID"):
        print("Telegram ainda não configurado.")
        print("Execute: CONFIGURE_TELEGRAM.bat")
        return 1

    TUNNEL_LOG.write_text("", encoding="utf-8")
    tunnel_cmd = [
        str(CLOUDFLARED),
        "tunnel",
        "--no-autoupdate",
        "--url",
        "http://127.0.0.1:8765",
    ]

    print("Iniciando Cloudflare Quick Tunnel...")
    tunnel = subprocess.Popen(
        tunnel_cmd,
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
    )

    app: subprocess.Popen | None = None
    try:
        public_url = wait_for_tunnel(tunnel)
        save_env_value("APPROVAL_BRIDGE_PUBLIC_URL", public_url)
        os.environ["APPROVAL_BRIDGE_PUBLIC_URL"] = public_url
        print(f"URL pública configurada: {public_url}")
        print("Iniciando Bridge, Telegram, scanner e backups...")

        app = subprocess.Popen(
            [sys.executable, "-u", "run_all.py"],
            cwd=ROOT,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        )

        print("")
        print("CCS v6.1.1 Windows está em execução.")
        print("Não feche esta janela.")
        print("Pressione CTRL+C para encerrar tudo com segurança.")
        print("")

        while app.poll() is None and tunnel.poll() is None:
            time.sleep(1)

        if app.poll() is not None:
            print(f"O aplicativo encerrou com código {app.returncode}.")
        if tunnel.poll() is not None:
            print(f"O túnel encerrou com código {tunnel.returncode}.")
        return app.returncode or tunnel.returncode or 0

    except KeyboardInterrupt:
        print("\nEncerrando...")
        return 0
    except Exception as exc:
        print(f"ERRO: {exc}")
        return 1
    finally:
        terminate(app)
        terminate(tunnel)

if __name__ == "__main__":
    raise SystemExit(main())
