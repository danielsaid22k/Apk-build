CRYPTO CERTIFIED SWITCH v7.0.0 — WINDOWS 10/11
================================================

FORMA MAIS RÁPIDA

1. Extraia o ZIP para uma pasta simples, por exemplo:
   C:\CCS_Windows

2. Clique duas vezes em:
   INSTALL_WINDOWS.bat

3. Depois execute:
   CONFIGURE_TELEGRAM.bat
   CONFIGURE_WALLETS.bat
   TEST_WINDOWS.bat

4. Para iniciar tudo:
   START_WINDOWS.bat

O START_WINDOWS.bat:

- inicia um Cloudflare Quick Tunnel;
- obtém uma URL HTTPS trycloudflare.com;
- grava automaticamente a URL no arquivo .env;
- inicia o Approval Bridge na porta 8765;
- inicia o Telegram Control;
- inicia o scanner e os backups.

Não feche a janela enquanto estiver usando o sistema.
A URL do Quick Tunnel muda quando o programa é reiniciado, mas o launcher
atualiza o .env automaticamente.

SEGURANÇA

- Use somente endereços públicos.
- Nunca informe seed phrase ou chave privada.
- Origem e destino não podem ser iguais.
- O programa não realiza assinatura automática.
- A confirmação final continua dentro da Phantom ou Binance Web3.

ARQUIVOS PRINCIPAIS

INSTALL_WINDOWS.bat       instala Python/venv/cloudflared
START_WINDOWS.bat         inicia tudo com um clique
CONFIGURE_TELEGRAM.bat    configura bot e Chat ID
CONFIGURE_WALLETS.bat     configura origens e destinos
TEST_WINDOWS.bat          executa verificações
START_BRIDGE_ONLY.bat     inicia apenas o Bridge
BACKUP_NOW.bat            cria backup imediato
RESTORE_LATEST.bat        restaura o backup mais recente
WALLET_STATUS.bat         mostra as carteiras configuradas
