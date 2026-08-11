CRYPTO CERTIFIED SWITCH v7.1 — ANDROID/APK

Esta pasta foi adaptada a partir do V7 Windows fornecido pelo usuário.

O APK possui uma central de configuração para:
- Helius API Key
- Solana RPC e fallback
- Ethereum RPC
- BNB Chain RPC
- Telegram Bot Token
- Telegram Chat ID
- URL pública HTTPS do Approval Bridge
- Carteiras de origem Ethereum, BNB e Solana
- Carteiras de destino Ethereum, BNB e Solana
- Ativar/desativar cada carteira

SEGURANÇA
- Não solicita seed phrase.
- Não solicita chave privada.
- Mantém automatic_signing=false e automatic_debit=false.
- A confirmação final continua na carteira de origem.
- .env/config.json de Android ficam no armazenamento privado do app.

GERAR APK (Linux/WSL recomendado)
1. Instalar Python, Java JDK, git, zip/unzip e dependências do Buildozer.
2. python3 -m pip install --user buildozer cython
3. Na pasta do projeto: buildozer android debug
4. O APK será criado em bin/.

Observação: este ambiente de ChatGPT não possui o Android SDK/Buildozer instalado, então o APK binário não pôde ser compilado aqui. O projeto está preparado para build.
