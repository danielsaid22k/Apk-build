#!/usr/bin/env python3
from pathlib import Path
from ccs.core.paths import runtime_root
import html
import json
import os
import time

from app.runtime import ensure_directories
from app.env import load
from app.http import telegram_api
from app.telegram import (
    send, dashboard, dashboard_buttons, proposal_card,
    proposal_buttons, short_address,
)
from app.proposals import pending, find, move
from app.backup import create
from app.bridge_url import validate_public_https, check_health

ROOT = runtime_root()
ensure_directories(ROOT)
load(ROOT / ".env", override=True)

def answer(token: str, callback_id: str, text: str):
    try:
        telegram_api(token, "answerCallbackQuery", {
            "callback_query_id": callback_id,
            "text": text[:180],
        })
    except Exception:
        pass

def wallet_summary(config: dict) -> str:
    destinations = config.get("destination_wallets", {})
    lines = ["👛 <b>CARTEIRAS CONFIGURADAS</b>", "━━━━━━━━━━━━━━━━━━━━"]
    for wallet in config.get("wallets", []):
        network = str(wallet.get("network", ""))
        destination = destinations.get(network, {})
        origin_status = "✅" if wallet.get("enabled") else "⛔"
        destination_status = "✅" if destination.get("enabled") else "⛔"
        lines.extend([
            f"<b>{network.upper()}</b>",
            f"{origin_status} Origem {html.escape(str(wallet.get('wallet', '')))}: "
            f"<code>{html.escape(short_address(wallet.get('address', 'VAZIA')))}</code>",
            f"{destination_status} Destino Trust: "
            f"<code>{html.escape(short_address(destination.get('address', 'VAZIA')))}</code>",
            "",
        ])
    lines.append("🔐 Chaves privadas e seed phrases não são armazenadas.")
    return "\n".join(lines)

def statistics(root: Path) -> str:
    folders = ("pending", "submitted", "completed", "rejected", "failed")
    counts = {}
    for folder in folders:
        directory = root / "proposals" / folder
        counts[folder] = len(list(directory.glob("*.json"))) if directory.exists() else 0
    return (
        "📊 <b>ESTATÍSTICAS DE PROPOSTAS</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"⏳ Pendentes: <b>{counts['pending']}</b>\n"
        f"📤 Enviadas à rede: <b>{counts['submitted']}</b>\n"
        f"✅ Concluídas: <b>{counts['completed']}</b>\n"
        f"🚫 Rejeitadas: <b>{counts['rejected']}</b>\n"
        f"❌ Falhas: <b>{counts['failed']}</b>"
    )

def public_bridge_url() -> str:
    return os.getenv("APPROVAL_BRIDGE_PUBLIC_URL", "").strip().rstrip("/")

def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    authorized_chat = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if not token or not authorized_chat:
        print("Telegram não configurado.")
        return 1

    config = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    offset = 0

    while True:
        try:
            result = telegram_api(token, "getUpdates", {
                "offset": offset,
                "timeout": 20,
                "allowed_updates": ["callback_query"],
            })
            for update in result.get("result", []):
                offset = max(offset, int(update["update_id"]) + 1)
                callback = update.get("callback_query") or {}
                callback_id = str(callback.get("id", ""))
                data = str(callback.get("data", ""))
                actual_chat = str(
                    (((callback.get("message") or {}).get("chat") or {}).get("id", ""))
                )
                if actual_chat != authorized_chat:
                    answer(token, callback_id, "Acesso não autorizado.")
                    continue

                answer(token, callback_id, "Comando recebido.")

                if data == "panel":
                    send(ROOT, dashboard(ROOT, config), dashboard_buttons())

                elif data == "proposals":
                    items = pending(ROOT)
                    if not items:
                        send(ROOT, "📑 <b>PROPOSTAS</b>\nNenhuma proposta pendente.",
                             dashboard_buttons())
                    else:
                        for proposal in items[:10]:
                            send(ROOT, proposal_card(proposal),
                                 proposal_buttons(proposal, public_bridge_url()))

                elif data == "wallets":
                    send(ROOT, wallet_summary(config), dashboard_buttons())

                elif data == "stats":
                    send(ROOT, statistics(ROOT), dashboard_buttons())

                elif data == "resend_pending":
                    items = pending(ROOT)
                    if not items:
                        send(ROOT, "📨 Não existem propostas pendentes para reenviar.")
                    else:
                        for proposal in items[:10]:
                            send(ROOT, proposal_card(proposal),
                                 proposal_buttons(proposal, public_bridge_url()))
                        send(ROOT, f"📨 <b>{len(items[:10])}</b> proposta(s) reenviada(s).")

                elif data == "bridge_status":
                    public_url = public_bridge_url()
                    valid, reason = validate_public_https(public_url)
                    if not valid:
                        send(
                            ROOT,
                            "🌐 <b>BRIDGE HTTPS NÃO CONFIGURADO</b>\n"
                            f"{html.escape(reason)}\n\n"
                            "No Termux, execute:\n"
                            "<code>sh configure_public_bridge.sh</code>",
                            dashboard_buttons(),
                        )
                    else:
                        online, detail = check_health(public_url)
                        icon = "✅" if online else "❌"
                        send(
                            ROOT,
                            "🌐 <b>STATUS DO BRIDGE HTTPS</b>\n"
                            f"{icon} {html.escape(detail)}\n"
                            f"<code>{html.escape(public_url)}</code>",
                            dashboard_buttons(),
                        )

                elif data == "bridge_help":
                    send(
                        ROOT,
                        "⚠️ <b>URL HTTPS NECESSÁRIA</b>\n"
                        "Os aplicativos de carteira não conseguem acessar "
                        "<code>127.0.0.1</code> por um botão do Telegram.\n\n"
                        "Configure um domínio ou túnel HTTPS que encaminhe para "
                        "<code>127.0.0.1:8765</code> e execute:\n"
                        "<code>sh configure_public_bridge.sh</code>\n\n"
                        "O botão de confirmação só será liberado com uma URL "
                        "pública HTTPS válida.",
                        dashboard_buttons(),
                    )

                elif data == "backup":
                    path = create(ROOT)
                    send(ROOT,
                         "💾 <b>BACKUP CONCLUÍDO</b>\n"
                         f"<code>{html.escape(str(path.relative_to(ROOT)))}</code>",
                         dashboard_buttons())

                elif data == "diagnostic":
                    send(ROOT,
                         "🩺 <b>DIAGNÓSTICO PROFISSIONAL</b>\n"
                         "━━━━━━━━━━━━━━━━━━━━\n"
                         "✅ Telegram conectado\n"
                         "✅ Menu interativo ativo\n"
                         "✅ Approval Bridge configurado\n"
                         "✅ Backup disponível\n"
                         "✅ Confirmação manual obrigatória\n"
                         "⛔ Assinatura automática desativada\n"
                         "⛔ Débito automático desativado",
                         dashboard_buttons())

                elif data == "help":
                    send(ROOT,
                         "ℹ️ <b>FLUXO SEGURO</b>\n"
                         "1. O scanner cria uma proposta.\n"
                         "2. Você revisa rede, quantidade, origem e destino.\n"
                         "3. O botão abre a carteira de origem.\n"
                         "4. A carteira mostra a transação completa.\n"
                         "5. Somente sua confirmação envia a transação.\n\n"
                         "⚠️ Nunca informe seed phrase ou chave privada.",
                         dashboard_buttons())

                elif data.startswith("status:"):
                    pid = data.split(":", 1)[1]
                    found = find(ROOT, pid)
                    if not found:
                        send(ROOT, "❓ Proposta não encontrada.")
                    else:
                        proposal, folder = found
                        tx_hash = proposal.get("tx_hash", "")
                        message = (
                            "📌 <b>STATUS DA PROPOSTA</b>\n"
                            f"Status: <b>{html.escape(str(proposal.get('status')))}</b>\n"
                            f"Pasta: <code>{html.escape(folder)}</code>"
                        )
                        if tx_hash:
                            message += f"\nHash: <code>{html.escape(str(tx_hash))}</code>"
                        send(ROOT, message, dashboard_buttons())

                elif data.startswith("resend:"):
                    pid = data.split(":", 1)[1]
                    found = find(ROOT, pid)
                    if not found:
                        send(ROOT, "❓ Proposta não encontrada.")
                    else:
                        proposal, _ = found
                        send(ROOT, proposal_card(proposal),
                             proposal_buttons(proposal, public_bridge_url()))

                elif data.startswith("reject:"):
                    pid = data.split(":", 1)[1]
                    try:
                        move(ROOT, pid, "rejected", "REJECTED_BY_USER")
                        send(ROOT,
                             "🚫 <b>PROPOSTA REJEITADA</b>\n"
                             f"ID: <code>{html.escape(pid)}</code>",
                             dashboard_buttons())
                    except Exception as exc:
                        send(ROOT, f"Erro ao rejeitar: {html.escape(str(exc))}")

        except KeyboardInterrupt:
            return 0
        except Exception as exc:
            print("Telegram:", exc, flush=True)
            time.sleep(5)

if __name__ == "__main__":
    raise SystemExit(main())
