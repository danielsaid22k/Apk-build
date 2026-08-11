CRYPTO CERTIFIED SWITCH v7.0.0 — WINDOWS
SPRINTS 1, 2 E 3
============================================================

SPRINT 1 — ARQUITETURA
- Novo pacote ccs.core para lógica central.
- Novo pacote ccs.services para integrações.
- Novo pacote ccs.storage para persistência/cache.
- Pasta app permanece como camada de compatibilidade com a v6.
- Nenhuma mudança no formato dos backups, propostas ou carteiras.

SPRINT 2 — SCANNER INTELIGENTE
- Tokens SPL enriquecidos com nome, símbolo e ícone quando disponíveis.
- Helius DAS é consultada para metadados.
- DexScreener complementa preço, liquidez, market cap, FDV e variação 24h.
- Cache persistente em data\token_metadata_cache.json.
- Falha de metadados não bloqueia o scanner: o mint continua utilizável.
- Telegram exibe informações enriquecidas da proposta.

SPRINT 3 — RPC
- Camada RPC Solana consolidada em ccs.services.solana_rpc.
- Helius, URL principal, fallback e compatibilidade com RPC legada.
- Endpoint saudável passa a ser preferido.
- Cooldown temporário para endpoints com falha.
- Logs com chaves mascaradas.
- Status mais recente em data\solana_rpc_status.json.
- Proxy interno da página da Phantom permanece sem expor HELIUS_API_KEY.

INSTALAÇÃO
1. INSTALL_WINDOWS.bat
2. MIGRAR_DADOS_ANTIGOS.bat (se necessário)
3. CONFIGURE_SOLANA_RPC.bat
4. CONFIGURE_TELEGRAM.bat / CONFIGURE_WALLETS.bat se ainda não configurados
5. V7_TESTS.bat
6. V7_DIAGNOSTICS.bat
7. START_WINDOWS.bat

BACKUP
Antes de migrar dados: BACKUP_NOW.bat

SEGURANÇA
A v7 mantém assinatura manual na carteira e não armazena seed phrase/chave privada.
