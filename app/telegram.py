from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
import html
import json
import os
import time

from .http import telegram_api
from .proposals import pending
from .bridge_url import validate_public_https

def _state_path(root: Path) -> Path:
    return root / "data" / "telegram_delivery.json"

def _state(root: Path):
    default = {"sent": 0, "failed": 0, "last_success": "", "last_error": ""}
    try:
        loaded = json.loads(_state_path(root).read_text(encoding="utf-8"))
        return {**default, **loaded} if isinstance(loaded, dict) else default
    except Exception:
        return default

def _save(root: Path, state):
    _state_path(root).parent.mkdir(parents=True, exist_ok=True)
    _state_path(root).write_text(
        json.dumps(state, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

def send(root: Path, text: str, buttons=None) -> bool:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    state = _state(root)

    if not token or not chat_id:
        state["failed"] = int(state.get("failed", 0)) + 1
        state["last_error"] = "Token ou Chat ID ausente no .env"
        _save(root, state)
        return False

    attempts = max(1, int(os.getenv("TELEGRAM_RETRY_ATTEMPTS", "3")))
    delay = max(1, int(os.getenv("TELEGRAM_RETRY_DELAY_SECONDS", "3")))
    error = ""

    for attempt in range(attempts):
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        if buttons:
            payload["reply_markup"] = {"inline_keyboard": buttons}

        try:
            result = telegram_api(token, "sendMessage", payload)
            if result.get("ok"):
                state["sent"] = int(state.get("sent", 0)) + 1
                state["last_success"] = datetime.now(timezone.utc).isoformat()
                state["last_error"] = ""
                _save(root, state)
                return True
            error = str(result)
        except Exception as exc:
            error = str(exc)

        if attempt + 1 < attempts:
            time.sleep(delay)

    state["failed"] = int(state.get("failed", 0)) + 1
    state["last_error"] = error
    _save(root, state)
    return False

def short_address(value: str) -> str:
    value = str(value or "")
    return value if len(value) <= 18 else f"{value[:9]}…{value[-7:]}"

def wallet_label(network: str) -> str:
    return "Phantom" if network in {"ethereum", "solana"} else "Binance Web3"

def dashboard(root: Path, config: dict):
    delivery = _state(root)
    proposals = pending(root)
    enabled_wallets = sum(1 for item in config.get("wallets", []) if item.get("enabled"))
    heartbeat = os.getenv("TELEGRAM_HEARTBEAT_SECONDS", "60")
    return (
        "💠 <b>CRYPTO CERTIFIED SWITCH</b>\n"
        "<b>Professional Control Center · v7.0.0</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🟢 <b>Sistema:</b> operacional\n"
        "🌉 <b>Approval Bridge:</b> disponível\n"
        "📡 <b>Telegram:</b> conectado\n"
        f"💓 <b>Heartbeat:</b> {html.escape(heartbeat)} segundos\n"
        f"👛 <b>Origens habilitadas:</b> {enabled_wallets}\n"
        f"📑 <b>Propostas pendentes:</b> {len(proposals)}\n"
        f"📨 <b>Mensagens entregues:</b> {delivery.get('sent', 0)}\n"
        f"⚠️ <b>Falhas registradas:</b> {delivery.get('failed', 0)}\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🔐 <b>Modo protegido:</b> nenhuma assinatura ou débito automático.\n"
        "A confirmação final acontece dentro da carteira de origem."
    )

def dashboard_buttons():
    return [
        [{"text": "📑 Propostas", "callback_data": "proposals"},
         {"text": "🔄 Atualizar", "callback_data": "panel"}],
        [{"text": "👛 Carteiras", "callback_data": "wallets"},
         {"text": "📊 Estatísticas", "callback_data": "stats"}],
        [{"text": "📨 Reenviar pendentes", "callback_data": "resend_pending"}],
        [{"text": "🌐 Status do Bridge HTTPS", "callback_data": "bridge_status"}],
        [{"text": "💾 Criar backup", "callback_data": "backup"},
         {"text": "🩺 Diagnóstico", "callback_data": "diagnostic"}],
        [{"text": "ℹ️ Segurança e ajuda", "callback_data": "help"}],
    ]

def _money(value) -> str:
    try:
        return f"{float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "0,00"

def proposal_card(proposal: dict):
    asset = proposal["asset"]
    destination = proposal["destination"]
    network = str(asset["network"])
    wallet = wallet_label(network)
    status = html.escape(str(proposal.get("status", "PENDENTE")))
    symbol = html.escape(str(asset.get("symbol") or "TOKEN"))
    name = html.escape(str(asset.get("name") or "Token"))
    contract = str(asset.get("contract") or "")
    metadata_sources = ", ".join(asset.get("metadata_sources") or []) or str(asset.get("metadata_source") or "local")
    lines = [
        "💎 <b>PROPOSTA PRONTA PARA REVISÃO</b>",
        "━━━━━━━━━━━━━━━━━━━━",
        f"🪙 <b>Token:</b> {name} ({symbol})",
        f"🌐 <b>Rede:</b> {network.upper()}",
        f"👛 <b>Carteira de origem:</b> {wallet}",
        f"💰 <b>Quantidade:</b> <code>{float(asset.get('amount',0)):.8f}</code>",
        f"💵 <b>Valor estimado:</b> US$ {_money(asset.get('usd_value',0))}",
        f"⛽ <b>Taxa estimada:</b> US$ {_money(asset.get('estimated_fee_usd',0))}",
        f"📈 <b>Valor líquido:</b> US$ {_money(asset.get('net_value_usd',0))}",
        f"⭐ <b>Score:</b> {int(asset.get('recovery_score',0))}/100",
    ]
    if asset.get("asset_type") == "SPL":
        lines.extend([
            f"🏷️ <b>Mint:</b> <code>{html.escape(short_address(contract))}</code>",
            f"🔢 <b>Decimais:</b> {int(asset.get('decimals',0))}",
            f"💧 <b>Liquidez:</b> US$ {_money(asset.get('liquidity_usd',0))}",
            f"🏦 <b>Market Cap:</b> US$ {_money(asset.get('market_cap_usd',0))}",
            f"📊 <b>24h:</b> {float(asset.get('price_change_24h',0)):.2f}%",
            f"🔎 <b>Dados:</b> {html.escape(metadata_sources)}",
        ])
        image_url = str(asset.get("image_url") or "").strip()
        if image_url.startswith("https://"):
            lines.append(f'🖼️ <b>Ícone:</b> <a href="{html.escape(image_url, quote=True)}">visualizar</a>')
    lines.extend([
        f"🔐 <b>Origem:</b> <code>{html.escape(short_address(asset.get('address','')))}</code>",
        f"🛡️ <b>Destino:</b> <code>{html.escape(short_address(destination.get('address','')))}</code>",
        f"📌 <b>Status:</b> {status}",
        f"🆔 <code>{html.escape(str(proposal['proposal_id']))}</code>",
        "━━━━━━━━━━━━━━━━━━━━",
        "⚠️ Revise token, quantidade, rede e destino. A assinatura continua exclusivamente na carteira.",
    ])
    return "\n".join(lines)


def approval_url(proposal: dict, public_url: str) -> str:
    valid, reason = validate_public_https(public_url)
    if not valid:
        raise ValueError(reason)
    return f"{public_url.rstrip('/')}/proposal/{proposal['proposal_id']}"

def wallet_open_url(proposal: dict, public_url: str) -> str:
    review_url = approval_url(proposal, public_url)
    network = proposal["asset"]["network"]
    if network in {"solana", "ethereum"}:
        encoded = quote(review_url, safe="")
        return f"https://phantom.app/ul/browse/{encoded}?ref={encoded}"
    return review_url

def proposal_buttons(proposal: dict, public_url: str):
    pid = proposal["proposal_id"]
    wallet = wallet_label(proposal["asset"]["network"])
    valid, _ = validate_public_https(public_url)

    if not valid:
        return [
            [{"text": "⚠️ Configurar Bridge HTTPS", "callback_data": "bridge_help"}],
            [
                {"text": "📌 Ver status", "callback_data": f"status:{pid}"},
                {"text": "📤 Reenviar cartão", "callback_data": f"resend:{pid}"},
            ],
            [
                {"text": "🚫 Rejeitar", "callback_data": f"reject:{pid}"},
                {"text": "🏠 Menu", "callback_data": "panel"},
            ],
        ]

    return [
        [{"text": "🔎 Revisar proposta", "url": approval_url(proposal, public_url)}],
        [{
            "text": f"🔐 Abrir {wallet} para confirmar",
            "url": wallet_open_url(proposal, public_url),
        }],
        [
            {"text": "📌 Ver status", "callback_data": f"status:{pid}"},
            {"text": "📤 Reenviar cartão", "callback_data": f"resend:{pid}"},
        ],
        [
            {"text": "🚫 Rejeitar", "callback_data": f"reject:{pid}"},
            {"text": "🏠 Menu", "callback_data": "panel"},
        ],
    ]
def last_error(root: Path) -> str:
    return str(_state(root).get("last_error", ""))
