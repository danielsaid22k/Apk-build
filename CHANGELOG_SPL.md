# v6.1.1

- Montagem de transações SPL Token com TransferChecked.
- Criação idempotente da Associated Token Account do destino.
- Validação on-chain de mint, decimais e saldo da conta de origem.
- Assinatura continua exclusivamente manual na Phantom.
- Deduplicação de propostas pendentes para evitar loop.
