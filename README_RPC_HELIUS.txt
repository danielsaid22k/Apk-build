CRYPTO CERTIFIED SWITCH v6.1.1 — HELIUS RPC + FALLBACK
=======================================================

CONFIGURAÇÃO RECOMENDADA

1. Execute INSTALL_WINDOWS.bat
2. Execute MIGRAR_DADOS_ANTIGOS.bat, se necessário
3. Execute CONFIGURE_SOLANA_RPC.bat
4. Escolha Helius e cole sua API key
5. Execute TEST_WINDOWS.bat
6. Execute START_WINDOWS.bat

A API key fica somente no arquivo .env do computador.
A página aberta na Phantom chama /api/solana-rpc no seu próprio Bridge;
o Bridge consulta a Helius no servidor. Assim, a chave não aparece no HTML
nem no JavaScript entregue ao celular.

ABRIR O .ENV

- Clique em OPEN_ENV.bat
- Ou, no CMD dentro da pasta do projeto, execute: notepad .env

VARIÁVEIS

HELIUS_API_KEY=                 chave do painel Helius
SOLANA_RPC_URL=                URL principal personalizada (opcional)
SOLANA_RPC_FALLBACK_URL=       fallback HTTPS opcional
SOLANA_RPC_ENABLE_HELIUS_BETA_FALLBACK=false
SOLANA_RPC_TIMEOUT_SECONDS=20
SOLANA_RPC_VALIDATE_ON_START=true

LOG

logs\solana_rpc.log

As chaves são mascaradas como *** nos logs.

BACKUP

Execute BACKUP_NOW.bat. O backup inclui .env, portanto contém o token do
Telegram e, quando configurada, a API key da Helius. Guarde a pasta backups
em local privado e não envie o .env para terceiros.
