#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import os

from app.backup import create
from app.env import load, parse
from app.http import telegram_api, HttpError

ROOT = Path(__file__).resolve().parent
ENV = ROOT / ".env"


def save_values(updates: dict[str, str]) -> None:
    lines = ENV.read_text(encoding="utf-8-sig").splitlines() if ENV.exists() else []
    result: list[str] = []
    seen: set[str] = set()

    for line in lines:
        if "=" in line and not line.lstrip().startswith("#"):
            key = line.split("=", 1)[0].strip()
            if key in updates:
                result.append(f"{key}={updates[key]}")
                seen.add(key)
                continue
        result.append(line)

    for key, value in updates.items():
        if key not in seen:
            result.append(f"{key}={value}")

    ENV.write_text("\n".join(result).rstrip() + "\n", encoding="utf-8")


def detect_chat_id(token: str) -> str:
    result = telegram_api(token, "getUpdates", {"limit": 100, "timeout": 0})
    messages = [
        item.get("message") or item.get("edited_message")
        for item in result.get("result", [])
    ]
    messages = [m for m in messages if isinstance(m, dict) and isinstance(m.get("chat"), dict)]
    private = [m for m in messages if m["chat"].get("type") == "private"]
    selected = (private or messages)
    if not selected:
        return ""
    return str(selected[-1]["chat"]["id"])


def main() -> int:
    backup = create(ROOT)
    print(f"Backup criado: {backup.relative_to(ROOT)}")

    existing = parse(ENV)
    token = input("Token do bot Telegram: ").strip() or existing.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        print("Token obrigatório.")
        return 1

    try:
        result = telegram_api(token, "getMe", {})
        username = (result.get("result") or {}).get("username", "sem_username")
        print(f"Bot validado: @{username}")
        detected = detect_chat_id(token)
    except HttpError as exc:
        print(f"Falha ao validar o bot: {exc}")
        return 1

    prompt = f"Chat ID autorizado [{detected}]: " if detected else "Chat ID autorizado: "
    chat_id = input(prompt).strip() or detected or existing.get("TELEGRAM_CHAT_ID", "")
    if not chat_id or not chat_id.lstrip("-").isdigit():
        print("Chat ID inválido.")
        return 1

    # Testa exatamente as credenciais que serão gravadas.
    try:
        telegram_api(token, "sendMessage", {
            "chat_id": chat_id,
            "text": "✅ Telegram CCS conectado e configuração validada.",
        })
    except HttpError as exc:
        print(f"Falha no envio de validação: {exc}")
        print("Envie /start ao bot e execute o configurador novamente.")
        return 1

    save_values({
        "ENABLE_TELEGRAM": "true",
        "TELEGRAM_BOT_TOKEN": token,
        "TELEGRAM_CHAT_ID": chat_id,
        "TELEGRAM_HEARTBEAT_SECONDS": "60",
        "TELEGRAM_RETRY_ATTEMPTS": "3",
        "TELEGRAM_RETRY_DELAY_SECONDS": "3",
        "TELEGRAM_COLLECTION_RECEIPT": "true",
    })

    # Atualiza o processo atual também, substituindo exports antigos.
    load(ENV, override=True)
    print(".env salvo e validado com sucesso.")
    print("Agora execute: sh telegram_test_termux.sh")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
