from urllib.parse import urlparse
import json
import urllib.request
import urllib.error

LOCAL_HOSTS = {"127.0.0.1", "localhost", "0.0.0.0", "::1"}

def normalize(value: str) -> str:
    return str(value or "").strip().rstrip("/")

def validate_public_https(value: str):
    value = normalize(value)
    if not value:
        return False, "APPROVAL_BRIDGE_PUBLIC_URL não configurada."
    parsed = urlparse(value)
    if parsed.scheme.lower() != "https":
        return False, "A URL pública precisa começar com https://"
    host = (parsed.hostname or "").lower()
    if not host:
        return False, "A URL pública não possui domínio válido."
    if host in LOCAL_HOSTS or host.endswith(".localhost"):
        return False, "Endereços locais não funcionam nos botões do Telegram."
    if parsed.username or parsed.password:
        return False, "A URL pública não pode conter usuário ou senha."
    return True, ""

def health_url(value: str) -> str:
    return f"{normalize(value)}/health"

def check_health(value: str, timeout: int = 5):
    valid, reason = validate_public_https(value)
    if not valid:
        return False, reason
    request = urllib.request.Request(
        health_url(value),
        headers={"User-Agent": "CryptoCertifiedSwitch/5.5.1"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
            if response.status != 200:
                return False, f"Bridge respondeu HTTP {response.status}."
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                return False, "O endpoint /health não retornou JSON."
            if payload.get("ok") is True:
                return True, "Bridge HTTPS online."
            return False, f"Resposta de health inválida: {payload}"
    except urllib.error.HTTPError as exc:
        return False, f"Bridge respondeu HTTP {exc.code}."
    except urllib.error.URLError as exc:
        return False, f"Bridge inacessível: {exc.reason}"
    except Exception as exc:
        return False, f"Falha ao verificar bridge: {exc}"
