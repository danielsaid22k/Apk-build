from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from ccs.core.paths import runtime_root
from threading import Lock
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
import json
import os
import time

from app.http import HttpError, request_json

ROOT = runtime_root()
LOG_PATH = ROOT / "logs" / "solana_rpc.log"
STATUS_PATH = ROOT / "data" / "solana_rpc_status.json"
_LOCK = Lock()
_PREFERRED: str | None = None
_FAILURES: dict[str, dict] = {}

_RETRYABLE_HTTP = {401, 403, 408, 409, 425, 429, 500, 502, 503, 504}
_RETRYABLE_RPC_CODES = {-32005, -32004, -32002, -32603}

def _bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "sim", "on"}

def _int(name: str, default: int, minimum: int, maximum: int) -> int:
    try:
        return max(minimum, min(maximum, int(os.getenv(name, str(default)))))
    except ValueError:
        return default

def _timeout() -> int:
    return _int("SOLANA_RPC_TIMEOUT_SECONDS", 20, 3, 120)

def _cooldown() -> int:
    return _int("SOLANA_RPC_FAILURE_COOLDOWN_SECONDS", 30, 5, 600)

def _helius_url(host: str = "mainnet.helius-rpc.com") -> str:
    key = os.getenv("HELIUS_API_KEY", "").strip()
    return f"https://{host}/?api-key={key}" if key else ""

def redact_url(url: str) -> str:
    if not url:
        return "<não configurado>"
    parts = urlsplit(url)
    safe_query = []
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        lowered = key.lower().replace("_", "-")
        if lowered in {"api-key", "apikey", "key", "token"}:
            value = "***"
        safe_query.append((key, value))
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(safe_query), parts.fragment))

def _log(level: str, message: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    line = f"{datetime.now(timezone.utc).isoformat()} [{level}] {message}"
    with _LOCK:
        with LOG_PATH.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
    print(f"Solana RPC [{level}]: {message}", flush=True)

def _save_status(method: str, endpoint: str, ok: bool, detail: str = "") -> None:
    STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "method": method,
        "endpoint": redact_url(endpoint),
        "ok": bool(ok),
        "detail": detail[:500],
    }
    STATUS_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def configured_endpoints(config: dict | None = None) -> list[str]:
    endpoints: list[str] = []
    explicit = os.getenv("SOLANA_RPC_URL", "").strip()
    helius = _helius_url()
    legacy = ""
    if config:
        legacy = str(config.get("networks", {}).get("solana", {}).get("rpc_url", "")).strip()
    fallback = os.getenv("SOLANA_RPC_FALLBACK_URL", "").strip()
    beta = _helius_url("beta.helius-rpc.com") if _bool("SOLANA_RPC_ENABLE_HELIUS_BETA_FALLBACK", False) else ""

    # Prefer user configuration and Helius. Legacy public RPC is compatibility fallback.
    for endpoint in (explicit, helius, fallback, beta, legacy):
        if endpoint and endpoint not in endpoints:
            endpoints.append(endpoint)
    return endpoints

def _available(endpoint: str) -> bool:
    failure = _FAILURES.get(endpoint)
    if not failure:
        return True
    return time.time() >= float(failure.get("retry_after", 0) or 0)

def _mark_failure(endpoint: str, reason: str) -> None:
    current = _FAILURES.setdefault(endpoint, {"count": 0})
    current["count"] = int(current.get("count", 0)) + 1
    current["last_error"] = reason[:300]
    current["retry_after"] = time.time() + _cooldown()

def _mark_success(endpoint: str) -> None:
    _FAILURES.pop(endpoint, None)

def ordered_endpoints(config: dict | None = None) -> list[str]:
    endpoints = configured_endpoints(config)
    if _PREFERRED and _PREFERRED in endpoints:
        endpoints.remove(_PREFERRED)
        endpoints.insert(0, _PREFERRED)
    available = [e for e in endpoints if _available(e)]
    cooling = [e for e in endpoints if e not in available]
    # Never deadlock: cooled-down endpoints are retried after healthy candidates.
    return available + cooling

def request_payload(payload: dict, config: dict | None = None) -> dict:
    global _PREFERRED
    endpoints = ordered_endpoints(config)
    if not endpoints:
        raise HttpError("RPC Solana não configurada. Execute CONFIGURE_SOLANA_RPC.bat.")

    method = str(payload.get("method", "<sem método>"))
    last_error: Exception | None = None

    for index, endpoint in enumerate(endpoints, start=1):
        safe = redact_url(endpoint)
        _log("INFO", f"método={method} tentativa={index}/{len(endpoints)} endpoint={safe}")
        try:
            response = request_json(endpoint, "POST", payload, timeout=_timeout())
            rpc_error = response.get("error") if isinstance(response, dict) else None
            if rpc_error:
                code = rpc_error.get("code") if isinstance(rpc_error, dict) else None
                message = rpc_error.get("message") if isinstance(rpc_error, dict) else str(rpc_error)
                detail = f"RPC {code}: {message}"
                if code in _RETRYABLE_RPC_CODES and index < len(endpoints):
                    _mark_failure(endpoint, detail)
                    _save_status(method, endpoint, False, detail)
                    _log("WARN", f"endpoint={safe} {detail}; usando fallback")
                    last_error = HttpError(detail)
                    continue
                _save_status(method, endpoint, False, detail)
                _log("ERROR", f"endpoint={safe} {detail}")
                return response

            _PREFERRED = endpoint
            _mark_success(endpoint)
            _save_status(method, endpoint, True, "ok")
            _log("OK", f"método={method} endpoint={safe}")
            return response

        except HttpError as exc:
            last_error = exc
            status = exc.status
            retryable = status in _RETRYABLE_HTTP or status is None
            detail = f"HTTP={status or 'rede'} erro={exc}"
            _save_status(method, endpoint, False, detail)
            _log("WARN" if retryable else "ERROR", f"endpoint={safe} {detail}")
            if retryable:
                _mark_failure(endpoint, detail)
            if retryable and index < len(endpoints):
                continue
            raise
        except Exception as exc:
            last_error = exc
            detail = str(exc)
            _mark_failure(endpoint, detail)
            _save_status(method, endpoint, False, detail)
            _log("WARN", f"endpoint={safe} erro={detail}")
            if index < len(endpoints):
                continue
            raise HttpError(f"Todas as RPCs Solana falharam: {detail}") from exc

    raise HttpError(f"Todas as RPCs Solana falharam: {last_error}")

def rpc(method: str, params=None, config: dict | None = None):
    if params is None:
        params = []
    response = request_payload({
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params,
    }, config)
    if "error" in response:
        raise HttpError(str(response["error"]))
    return response.get("result")

def validate(config: dict | None = None) -> tuple[bool, str]:
    endpoints = configured_endpoints(config)
    if not endpoints:
        return False, "nenhum endpoint configurado"
    try:
        health = rpc("getHealth", [], config)
        if health not in {"ok", None}:
            _log("WARN", f"getHealth retornou {health!r}")
        blockhash = rpc("getLatestBlockhash", [{"commitment": "confirmed"}], config)
        if not isinstance(blockhash, dict) or not (blockhash.get("value") or {}).get("blockhash"):
            return False, "getLatestBlockhash retornou resposta inesperada"
        return True, redact_url(_PREFERRED or endpoints[0])
    except Exception as exc:
        return False, str(exc)

def status() -> dict:
    try:
        result = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
        return result if isinstance(result, dict) else {}
    except Exception:
        return {}
