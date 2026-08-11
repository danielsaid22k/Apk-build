from __future__ import annotations

from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
import json


class HttpError(RuntimeError):
    def __init__(self, message: str, *, status: int | None = None, body: str = ""):
        super().__init__(message)
        self.status = status
        self.body = body


def _decode_json(raw: bytes) -> dict:
    text = raw.decode("utf-8", errors="replace")
    try:
        return json.loads(text)
    except ValueError as exc:
        raise HttpError(f"Resposta JSON inválida: {text[:500]}", body=text) from exc


def request_json(
    url: str,
    method: str = "GET",
    payload: dict | None = None,
    timeout: int = 30,
    *,
    form_encoded: bool = False,
) -> dict:
    if payload is None:
        data = None
        content_type = "application/json"
    elif form_encoded:
        normalized = {}
        for key, value in payload.items():
            if isinstance(value, (dict, list)):
                normalized[key] = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
            else:
                normalized[key] = str(value)
        data = urlencode(normalized).encode("utf-8")
        content_type = "application/x-www-form-urlencoded; charset=utf-8"
    else:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        content_type = "application/json; charset=utf-8"

    request = Request(
        url,
        method=method,
        data=data,
        headers={
            "User-Agent": "CryptoCertifiedSwitch/7.0.0",
            "Content-Type": content_type,
            "Accept": "application/json",
        },
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            return _decode_json(response.read())
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        description = body
        try:
            parsed = json.loads(body)
            description = str(parsed.get("description") or parsed)
        except ValueError:
            pass
        raise HttpError(
            f"HTTP {exc.code}: {description}",
            status=exc.code,
            body=body,
        ) from exc
    except URLError as exc:
        raise HttpError(f"Falha de rede: {exc.reason}") from exc


def rpc(url: str, method: str, params: list) -> object:
    result = request_json(url, "POST", {
        "jsonrpc": "2.0", "id": 1, "method": method, "params": params
    })
    if "error" in result:
        raise HttpError(str(result["error"]))
    return result.get("result")


def telegram_api(token: str, method: str, payload: dict) -> dict:
    token = token.strip()
    if not token:
        raise HttpError("Token do Telegram vazio.")
    return request_json(
        f"https://api.telegram.org/bot{token}/{method}",
        "POST",
        payload,
        form_encoded=True,
    )
