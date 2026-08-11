
import re

def valid_evm(value: str) -> bool:
    return bool(re.fullmatch(r"0x[a-fA-F0-9]{40}", value or ""))

def valid_solana(value: str) -> bool:
    return bool(re.fullmatch(r"[1-9A-HJ-NP-Za-km-z]{32,44}", value or ""))

def same(network: str, left: str, right: str) -> bool:
    if not left or not right:
        return False
    if network in {"ethereum", "bnb"}:
        return left.strip().lower() == right.strip().lower()
    return left.strip() == right.strip()

def validate(config: dict) -> list[str]:
    errors = []
    destinations = config.get("destination_wallets", {})
    enabled = 0
    for wallet in config.get("wallets", []):
        if not wallet.get("enabled"):
            continue
        enabled += 1
        network = str(wallet.get("network", ""))
        origin = str(wallet.get("address", ""))
        validator = valid_solana if network == "solana" else valid_evm
        if not validator(origin):
            errors.append(f"{network}: origem inválida.")
        destination = destinations.get(network, {})
        if not destination.get("enabled"):
            errors.append(f"{network}: destino Trust Wallet desativado.")
            continue
        target = str(destination.get("address", ""))
        if not validator(target):
            errors.append(f"{network}: destino Trust Wallet inválido.")
        if same(network, origin, target):
            errors.append(f"{network}: origem e destino não podem ser iguais.")
    if enabled == 0:
        errors.append("Nenhuma carteira de origem habilitada.")
    return errors
