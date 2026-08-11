from __future__ import annotations

from pathlib import Path
from ccs.core.paths import runtime_root
import os

from app.http import request_json
from ccs.core.logging import log
from ccs.storage.json_cache import JsonCache
from ccs.services.solana_rpc import rpc as solana_rpc

ROOT = runtime_root()

def _ttl() -> int:
    try:
        return max(300, int(os.getenv("TOKEN_METADATA_CACHE_TTL_SECONDS", "21600")))
    except ValueError:
        return 21600

def _cache() -> JsonCache:
    return JsonCache(ROOT / "data" / "token_metadata_cache.json", _ttl())

def _default(mint: str) -> dict:
    return {
        "name": "Token SPL",
        "symbol": mint[:6] if mint else "TOKEN",
        "image_url": "",
        "description": "",
        "metadata_source": "fallback",
    }

def _helius_metadata(mint: str, config: dict | None = None) -> dict:
    # Helius DAS getAsset. This may not be enabled for every endpoint/account;
    # failure is intentionally non-fatal.
    result = solana_rpc("getAsset", {"id": mint}, config)
    if not isinstance(result, dict):
        return {}
    content = result.get("content") or {}
    metadata = content.get("metadata") or {}
    links = content.get("links") or {}
    files = content.get("files") or []
    image_url = str(links.get("image") or "")
    if not image_url and files and isinstance(files[0], dict):
        image_url = str(files[0].get("uri") or "")
    token_info = result.get("token_info") or {}
    return {
        "name": str(metadata.get("name") or "").strip(),
        "symbol": str(metadata.get("symbol") or token_info.get("symbol") or "").strip(),
        "image_url": image_url.strip(),
        "description": str(metadata.get("description") or "").strip(),
        "metadata_source": "helius",
    }

def _dex_market(mint: str) -> dict:
    data = request_json(f"https://api.dexscreener.com/latest/dex/tokens/{mint}")
    pairs = [p for p in data.get("pairs", []) if p.get("chainId") == "solana"]
    if not pairs:
        return {}
    pair = max(pairs, key=lambda p: float((p.get("liquidity") or {}).get("usd") or 0))
    base = pair.get("baseToken") or {}
    info = pair.get("info") or {}
    image_url = str(info.get("imageUrl") or "")
    return {
        "name": str(base.get("name") or "").strip(),
        "symbol": str(base.get("symbol") or "").strip(),
        "image_url": image_url.strip(),
        "price_usd": float(pair.get("priceUsd") or 0),
        "liquidity_usd": float((pair.get("liquidity") or {}).get("usd") or 0),
        "price_change_24h": float((pair.get("priceChange") or {}).get("h24") or 0),
        "market_cap_usd": float(pair.get("marketCap") or 0),
        "fdv_usd": float(pair.get("fdv") or 0),
        "pair_url": str(pair.get("url") or ""),
        "market_source": "dexscreener",
    }

def resolve_solana_token(mint: str, config: dict | None = None, force: bool = False) -> dict:
    mint = str(mint or "").strip()
    if not mint:
        return _default("")

    cache = _cache()
    if not force:
        cached = cache.get(f"solana:{mint}")
        if cached:
            cached["cache_hit"] = True
            return cached

    result = _default(mint)
    sources = []

    try:
        helius = _helius_metadata(mint, config)
        if helius:
            for key, value in helius.items():
                if value:
                    result[key] = value
            sources.append("helius")
    except Exception as exc:
        log(ROOT, "metadata", "WARN", f"Helius metadata falhou mint={mint}: {exc}")

    try:
        market = _dex_market(mint)
        if market:
            for key, value in market.items():
                if value not in ("", None):
                    result[key] = value
            sources.append("dexscreener")
    except Exception as exc:
        log(ROOT, "metadata", "WARN", f"DexScreener falhou mint={mint}: {exc}")

    result.setdefault("price_usd", 0.0)
    result.setdefault("liquidity_usd", 0.0)
    result.setdefault("price_change_24h", 0.0)
    result.setdefault("market_cap_usd", 0.0)
    result.setdefault("fdv_usd", 0.0)
    result.setdefault("pair_url", "")
    result["sources"] = sources or ["fallback"]
    result["cache_hit"] = False
    cache.set(f"solana:{mint}", result)
    log(ROOT, "metadata", "INFO", f"mint={mint} fontes={','.join(result['sources'])}")
    return result
