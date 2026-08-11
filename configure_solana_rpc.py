#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import getpass
import os

from app.env import load
from app.solana_rpc import validate

ROOT = Path(__file__).resolve().parent
ENV = ROOT / ".env"


def parse_env() -> tuple[list[str], dict[str, str]]:
    lines = ENV.read_text(encoding="utf-8-sig").splitlines() if ENV.exists() else []
    values: dict[str, str] = {}
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key, value = stripped.split("=", 1)
            values[key.strip()] = value.strip()
    return lines, values


def save_values(updates: dict[str, str]) -> None:
    lines, _ = parse_env()
    remaining = dict(updates)
    output: list[str] = []
    for line in lines:
        key = line.split("=", 1)[0].strip() if "=" in line else ""
        if key in remaining:
            output.append(f"{key}={remaining.pop(key)}")
        else:
            output.append(line)
    if remaining:
        if output and output[-1].strip():
            output.append("")
        output.append("# Solana RPC")
        for key, value in remaining.items():
            output.append(f"{key}={value}")
    ENV.write_text("\n".join(output).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    if not ENV.exists() and (ROOT / ".env.example").exists():
        ENV.write_text((ROOT / ".env.example").read_text(encoding="utf-8"), encoding="utf-8")

    print("=" * 62)
    print(" CCS v6.1.1 — CONFIGURAR RPC SOLANA")
    print("=" * 62)
    print("1 - Helius (recomendado)")
    print("2 - URL RPC personalizada")
    option = input("Escolha [1]: ").strip() or "1"

    updates = {
        "SOLANA_RPC_TIMEOUT_SECONDS": "20",
        "SOLANA_RPC_VALIDATE_ON_START": "true",
    }
    if option == "1":
        key = getpass.getpass("Cole sua Helius API key (não será exibida): ").strip()
        if not key:
            print("API key vazia. Configuração cancelada.")
            return 1
        updates.update({
            "HELIUS_API_KEY": key,
            "SOLANA_RPC_URL": "",
        })
        beta = input("Ativar Helius beta como fallback? [s/N]: ").strip().lower()
        updates["SOLANA_RPC_ENABLE_HELIUS_BETA_FALLBACK"] = "true" if beta in {"s", "sim", "y", "yes"} else "false"
    elif option == "2":
        url = input("URL RPC principal completa: ").strip()
        if not url.startswith("https://"):
            print("A URL deve começar com https://")
            return 1
        updates.update({"SOLANA_RPC_URL": url, "HELIUS_API_KEY": ""})
    else:
        print("Opção inválida.")
        return 1

    fallback = input("URL RPC de fallback (Enter para nenhuma): ").strip()
    if fallback and not fallback.startswith("https://"):
        print("A URL de fallback deve começar com https://")
        return 1
    updates["SOLANA_RPC_FALLBACK_URL"] = fallback
    save_values(updates)

    # Recarrega as novas variáveis no processo para validar.
    load(ENV, override=True)
    ok, detail = validate()
    if ok:
        print(f"RPC validada com sucesso: {detail}")
        print("A chave ficou salva somente no arquivo .env local.")
        return 0
    print(f"A configuração foi salva, mas a validação falhou: {detail}")
    print("Revise a chave, a rede e as restrições da API no painel do provedor.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
