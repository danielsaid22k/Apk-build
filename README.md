# Crypto Certified Switch v6.1.2 — ATA automática

Consulte `README_ATA.txt` e `CHANGELOG_ATA.md` para esta atualização.

# Crypto Certified Switch v5.5.1 — HTTPS Bridge Guard

## Instalar

```sh
cd ~/storage/downloads
unzip Crypto_Certified_Switch_v5_5_1_HTTPS_BRIDGE_GUARD.zip
mv Crypto_Certified_Switch_v5_5_1_HTTPS_BRIDGE_GUARD ~/
cd ~/Crypto_Certified_Switch_v5_5_1_HTTPS_BRIDGE_GUARD
sh install_termux.sh
```

## Configuração normal

```sh
sh configure_telegram.sh
sh configure_wallets.sh
```

## Configurar o Bridge público

Disponibilize o serviço local `127.0.0.1:8765` em um domínio ou túnel HTTPS
sob seu controle. Depois execute:

```sh
sh configure_public_bridge.sh
```

Teste:

```sh
sh public_bridge_test.sh
```

Links locais ou sem HTTPS são bloqueados automaticamente.

## Testar e iniciar

```sh
sh test_termux.sh
sh telegram_test_termux.sh
sh run_with_wakelock.sh
```

A confirmação final continua dentro da carteira de origem. O programa não cria
hospedagem, domínio ou túnel e não realiza assinatura automática.
