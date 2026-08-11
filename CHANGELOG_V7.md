# Crypto Certified Switch v7.0.0

## Sprint 1 — Arquitetura
- Separação em `ccs.core`, `ccs.services` e `ccs.storage`.
- Camada `app` mantida para compatibilidade com código e backups v6.
- Logger e cache centralizados.

## Sprint 2 — Scanner inteligente
- Metadados SPL via Helius DAS com fallback.
- Dados de mercado via DexScreener.
- Cache persistente com TTL.
- Telegram mostra nome, símbolo, mint, decimais, liquidez, market cap, 24h e fonte.

## Sprint 3 — RPC
- RPC Solana centralizada.
- Helius / principal / fallback / compatibilidade.
- Preferência dinâmica do endpoint saudável.
- Cooldown de endpoints que falham.
- Logs com segredos mascarados e status persistente.

## Compatibilidade
- Mantidos Cloudflare, Telegram, Helius, Phantom, SPL/ATA, backup, restauração e migração.
