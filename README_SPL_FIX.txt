CCS v6.1.1 — TRANSFERÊNCIA SPL COM PHANTOM
===========================================

Esta versão adiciona montagem de transferência SPL Token (programa legado Tokenkeg):

- valida a carteira de origem conectada;
- valida o mint e os decimais diretamente na rede;
- localiza a conta SPL de origem com saldo suficiente;
- deriva a Associated Token Account do destino;
- cria a conta associada do destino, se necessário;
- usa TransferChecked com a quantidade bruta exata;
- exige revisão e assinatura manual dentro da Phantom;
- não armazena seed phrase nem chave privada;
- impede criação repetida da mesma proposta pendente.

IMPORTANTE
- Teste primeiro com um token/quantidade de baixo valor.
- A quantidade mostrada na proposta é a quantidade que será enviada.
- A carteira de origem precisa ter SOL para taxa e, se necessário, aluguel da conta SPL do destino.
- Esta versão trata o SPL Token Program legado. Token-2022 permanece bloqueado até suporte específico.
