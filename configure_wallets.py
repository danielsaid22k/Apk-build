
#!/usr/bin/env python3
from pathlib import Path
import json

from app.runtime import ensure_directories
from app.backup import create
from app.wallets import valid_evm, valid_solana, same

ROOT=Path(__file__).resolve().parent
ensure_directories(ROOT)
CONFIG=ROOT/"config.json"

def get(prompt,validator):
    while True:
        value=input(prompt+": ").strip()
        if validator(value):return value
        print("Endereço inválido. Digite novamente.")

def main():
    backup=create(ROOT)
    print(f"Backup criado: {backup.relative_to(ROOT)}")
    config=json.loads(CONFIG.read_text(encoding="utf-8"))
    print("Use somente endereços públicos. Nunca informe seed/chave privada.")
    origin_eth=get("Phantom Ethereum — origem",valid_evm)
    origin_bnb=get("Binance Web3 BNB — origem",valid_evm)
    origin_sol=get("Phantom Solana — origem",valid_solana)
    while True:
        dest_eth=get("Trust Wallet Ethereum — destino",valid_evm)
        if not same("ethereum",origin_eth,dest_eth):break
        print("Origem e destino Ethereum não podem ser iguais.")
    while True:
        dest_bnb=get("Trust Wallet BNB — destino",valid_evm)
        if not same("bnb",origin_bnb,dest_bnb):break
        print("Origem e destino BNB não podem ser iguais.")
    while True:
        dest_sol=get("Trust Wallet Solana — destino",valid_solana)
        if not same("solana",origin_sol,dest_sol):break
        print("Origem e destino Solana não podem ser iguais.")
    origins={"ethereum":origin_eth,"bnb":origin_bnb,"solana":origin_sol}
    for wallet in config["wallets"]:
        wallet["address"]=origins[wallet["network"]];wallet["enabled"]=True
    destinations={"ethereum":dest_eth,"bnb":dest_bnb,"solana":dest_sol}
    for network,address in destinations.items():
        config["destination_wallets"][network].update({"address":address,"enabled":True,"wallet":"trust_wallet"})
    CONFIG.write_text(json.dumps(config,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("Configuração salva e validada.")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
