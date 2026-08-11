#!/usr/bin/env python3
from pathlib import Path
import os
import re

from app.env import load
from app.bridge_url import validate_public_https, check_health

ROOT = Path(__file__).resolve().parent
ENV_PATH = ROOT / ".env"
load(ENV_PATH, override=True)

def save_value(key: str, value: str) -> None:
    text = ENV_PATH.read_text(encoding="utf-8") if ENV_PATH.exists() else ""
    pattern = rf"^{re.escape(key)}=.*$"
    replacement = f"{key}={value}"
    if re.search(pattern, text, flags=re.MULTILINE):
        text = re.sub(pattern, replacement, text, flags=re.MULTILINE)
    else:
        if text and not text.endswith("\n"):
            text += "\n"
        text += replacement + "\n"
    ENV_PATH.write_text(text, encoding="utf-8")

def main() -> int:
    current = os.getenv("APPROVAL_BRIDGE_PUBLIC_URL", "").strip()
    prompt = "URL pública HTTPS"
    if current:
        prompt += f" [{current}]"
    value = input(prompt + ": ").strip() or current

    valid, reason = validate_public_https(value)
    if not valid:
        print(f"URL rejeitada: {reason}")
        return 1

    print("Verificando endpoint /health...")
    online, detail = check_health(value)
    print(detail)
    if not online:
        confirm = input("Salvar mesmo assim? [s/N]: ").strip().lower()
        if confirm not in {"s", "sim", "y", "yes"}:
            print("Nada foi alterado.")
            return 1

    save_value("APPROVAL_BRIDGE_PUBLIC_URL", value.rstrip("/"))
    print(".env atualizado.")
    print("No Telegram, toque em 'Status do Bridge HTTPS'.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
