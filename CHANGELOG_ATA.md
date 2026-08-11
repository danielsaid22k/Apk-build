# v6.1.2 — ATA automática e pré-validação de SOL

- Mantém integralmente o fluxo Helius/RPC, Cloudflare, Telegram, backup e migração da v6.1.1.
- Detecta se a Associated Token Account (ATA) do destinatário existe.
- Quando não existe, inclui a criação idempotente da ATA na mesma transação SPL.
- Usa `TransferChecked` após a criação da ATA.
- Consulta o aluguel da conta SPL e calcula a taxa real com `getFeeForMessage`.
- Mostra saldo SOL disponível, custo da ATA, taxa, total necessário e valor faltante.
- A Phantom continua sendo a única responsável pela assinatura manual.
