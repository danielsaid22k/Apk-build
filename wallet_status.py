
#!/usr/bin/env python3
from pathlib import Path
from ccs.core.paths import runtime_root
import json

from app.wallets import validate

ROOT = runtime_root()
config = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))

origins = {w["network"]: w for w in config.get("wallets", [])}
destinations = config.get("destination_wallets", {})

print("CONTAS CONFIGURADAS")
print("=" * 60)
for network in ("ethereum", "bnb", "solana"):
    origin = origins.get(network, {})
    destination = destinations.get(network, {})
    print(f"{network.upper()}")
    print(f"  Origem:  {origin.get('wallet','')} | {origin.get('address','') or 'VAZIA'} | enabled={origin.get('enabled',False)}")
    print(f"  Destino: {destination.get('wallet','')} | {destination.get('address','') or 'VAZIA'} | enabled={destination.get('enabled',False)}")

errors = validate(config)
print("")
if errors:
    print("ERROS:")
    for error in errors:
        print(f"- {error}")
    raise SystemExit(1)

print("Origens e destinos válidos e diferentes.")
