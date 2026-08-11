# CHANGELOG

## 7.0.0 — Windows Sprints 1, 2 e 3

Veja `CHANGELOG_V7.md`.

# CHANGELOG

## 6.0.1 — Phantom Link Fix

- Corrigido link interno da página: agora usa `APPROVAL_BRIDGE_PUBLIC_URL` em vez de `127.0.0.1`.
- Corrigido `scan_once.py` para usar somente `APPROVAL_BRIDGE_PUBLIC_URL`.
- Removido o `import()` dinâmico de `esm.sh`, que falhava no navegador interno da Phantom.
- Solana Web3 passa a ser carregado como script clássico com fallback de CDN.
- A página exibe o link exato usado para facilitar o diagnóstico.
- O launcher atualiza o `.env` e o ambiente do processo com a URL nova.

Propostas antigas no Telegram mantêm botões antigos. Depois de iniciar a nova versão, use **Reenviar cartão** ou **Reenviar pendentes**.
