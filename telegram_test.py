#!/usr/bin/env python3
from pathlib import Path
from ccs.core.paths import runtime_root
import json
import os

from app.env import load, parse
from app.runtime import ensure_directories
from app.telegram import send, dashboard, dashboard_buttons, last_error
from app.http import telegram_api, HttpError

ROOT = runtime_root()
ensure_directories(ROOT)
file_values = load(ROOT / ".env", override=True)


def masked(value: str) -> str:
    if len(value) < 10:
        return "***"
    return f"{value[:5]}…{value[-4:]}"


def main() -> int:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()

    print("Diagnóstico Telegram v7.0.0")
    print(f"- .env: {'OK' if (ROOT / '.env').exists() else 'AUSENTE'}")
    print(f"- Token carregado do arquivo: {masked(token) if token else 'AUSENTE'}")
    print(f"- Chat ID carregado do arquivo: {repr(chat_id) if chat_id else 'AUSENTE'}")

    if not token or not chat_id:
        print("Execute: sh configure_telegram.sh")
        return 1

    try:
        me = telegram_api(token, "getMe", {})
        username = (me.get("result") or {}).get("username", "sem_username")
        print(f"- Bot API: OK (@{username})")
    except HttpError as exc:
        print(f"- Bot API: FALHA — {exc}")
        return 1

    config = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    ok = send(ROOT, dashboard(ROOT, config), dashboard_buttons())
    if ok:
        print("Telegram OK. Menu profissional enviado.")
        return 0

    print(f"Falha ao enviar: {last_error(ROOT) or 'erro não informado'}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
