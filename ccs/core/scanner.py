from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from app.http import rpc as generic_rpc, request_json
from app.db import connect
from ccs.services.solana_rpc import rpc as solana_rpc
from ccs.services.token_metadata import resolve_solana_token

def native_price(symbol: str) -> float:
    ids = {"ETH": "ethereum", "BNB": "binancecoin", "SOL": "solana"}
    asset_id = ids.get(symbol)
    if not asset_id:
        return 0.0
    try:
        data = request_json(
            f"https://api.coingecko.com/api/v3/simple/price?ids={asset_id}&vs_currencies=usd"
        )
        return float(data.get(asset_id, {}).get("usd", 0))
    except Exception:
        return 0.0

def score(usd_value: float, fee: float, liquidity: float) -> int:
    if usd_value <= 0:
        return 0
    net = usd_value - fee
    value_points = min(55, int(max(net, 0) * 8))
    liquidity_points = 25 if liquidity >= 100000 else 15 if liquidity >= 10000 else 5
    fee_points = 20 if fee <= usd_value * 0.1 else 10 if fee <= usd_value * 0.25 else 0
    return min(100, value_points + liquidity_points + fee_points)

def _asset(
    wallet, network, asset_type, contract, symbol, name, amount, raw, decimals,
    price, liquidity=0, change=0, token_account="", image_url="",
    market_cap=0, fdv=0, metadata_source="", metadata_sources=None, pair_url=""
):
    fee = {"ethereum": 0.50, "bnb": 0.03, "solana": 0.01}.get(network, 0.10)
    usd = amount * price
    return {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "wallet_id": wallet["id"],
        "network": network,
        "address": wallet["address"],
        "asset_type": asset_type,
        "contract": contract,
        "symbol": symbol,
        "name": name,
        "amount": amount,
        "raw_amount": str(raw),
        "decimals": decimals,
        "price_usd": price,
        "usd_value": usd,
        "estimated_fee_usd": fee,
        "net_value_usd": usd - fee,
        "recovery_score": score(usd, fee, liquidity),
        "liquidity_usd": liquidity,
        "price_change_24h": change,
        "market_cap_usd": market_cap,
        "fdv_usd": fdv,
        "image_url": image_url,
        "metadata_source": metadata_source,
        "metadata_sources": list(metadata_sources or []),
        "pair_url": pair_url,
        "token_account": token_account,
    }

def scan_wallet(wallet: dict, network_cfg: dict, config: dict | None = None) -> list[dict]:
    network = wallet["network"]
    rpc_url = network_cfg["rpc_url"]
    assets = []

    if network in {"ethereum", "bnb"}:
        raw_hex = generic_rpc(rpc_url, "eth_getBalance", [wallet["address"], "latest"])
        raw = int(raw_hex, 16)
        amount = raw / 10**18
        symbol = network_cfg["symbol"]
        assets.append(_asset(
            wallet, network, "NATIVE", "", symbol, symbol, amount, raw, 18, native_price(symbol),
            metadata_source="native"
        ))

    elif network == "solana":
        result = solana_rpc("getBalance", [wallet["address"], {"commitment": "confirmed"}], config)
        raw = int((result or {}).get("value", 0))
        amount = raw / 10**9
        assets.append(_asset(
            wallet, network, "NATIVE", "", "SOL", "Solana", amount, raw, 9, native_price("SOL"),
            metadata_source="native"
        ))

        tokens = solana_rpc("getTokenAccountsByOwner", [
            wallet["address"],
            {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},
            {"encoding": "jsonParsed"}
        ], config)

        max_tokens = int((config or {}).get("scanner", {}).get("max_spl_tokens_per_wallet", 100))
        for item in (tokens or {}).get("value", [])[:max(1, max_tokens)]:
            info = item["account"]["data"]["parsed"]["info"]
            mint = info["mint"]
            amount_info = info["tokenAmount"]
            amount = float(amount_info.get("uiAmount") or 0)
            if amount <= 0:
                continue
            raw = amount_info.get("amount", "0")
            decimals = int(amount_info.get("decimals", 0))

            metadata = resolve_solana_token(mint, config)
            assets.append(_asset(
                wallet=wallet,
                network=network,
                asset_type="SPL",
                contract=mint,
                symbol=str(metadata.get("symbol") or mint[:6]),
                name=str(metadata.get("name") or "Token SPL"),
                amount=amount,
                raw=raw,
                decimals=decimals,
                price=float(metadata.get("price_usd") or 0),
                liquidity=float(metadata.get("liquidity_usd") or 0),
                change=float(metadata.get("price_change_24h") or 0),
                token_account=item.get("pubkey", ""),
                image_url=str(metadata.get("image_url") or ""),
                market_cap=float(metadata.get("market_cap_usd") or 0),
                fdv=float(metadata.get("fdv_usd") or 0),
                metadata_source=str(metadata.get("metadata_source") or ""),
                metadata_sources=metadata.get("sources") or [],
                pair_url=str(metadata.get("pair_url") or ""),
            ))
    return assets

def save_assets(root: Path, assets: list[dict]) -> None:
    db = connect(root)
    for a in assets:
        db.execute("""
        INSERT INTO assets(
          checked_at,wallet_id,network,address,asset_type,contract,symbol,name,
          amount,raw_amount,decimals,price_usd,usd_value,estimated_fee_usd,
          net_value_usd,recovery_score
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            a["checked_at"], a["wallet_id"], a["network"], a["address"], a["asset_type"],
            a["contract"], a["symbol"], a["name"], a["amount"], a["raw_amount"],
            a["decimals"], a["price_usd"], a["usd_value"], a["estimated_fee_usd"],
            a["net_value_usd"], a["recovery_score"]
        ))
    db.commit()
    db.close()

def scan_all(root: Path, config: dict) -> tuple[list[dict], list[str]]:
    assets, errors = [], []
    networks = config.get("networks", {})
    for wallet in config.get("wallets", []):
        if not wallet.get("enabled"):
            continue
        try:
            assets.extend(scan_wallet(wallet, networks[wallet["network"]], config))
        except Exception as exc:
            errors.append(f"{wallet['id']}: {exc}")
    save_assets(root, assets)
    return assets, errors
