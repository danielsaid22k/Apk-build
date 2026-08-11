# v6.1.1 — Helius RPC, proxy e fallback

- RPC Solana configurável pelo `.env`.
- Suporte direto à Helius por `HELIUS_API_KEY`.
- Proxy RPC no Approval Bridge: a chave não é entregue ao navegador da Phantom.
- Fallback opcional e Helius Gatekeeper beta opcional.
- Validação `getHealth` + `getLatestBlockhash` antes de iniciar.
- Logs em `logs/solana_rpc.log`, sempre com credenciais mascaradas.
- Scanner Solana e montagem SPL usam a mesma camada de RPC.
- Migração passa a mesclar `.env` e carteiras sem apagar recursos novos.
- Adicionados `CONFIGURE_SOLANA_RPC.bat` e `OPEN_ENV.bat`.
