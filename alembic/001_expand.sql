-- EXPAND: adiciona primeiro_nome e sobrenome (opcionais) e mantém cliente,
-- que passa a aceitar valores nulos (o enunciado pede "mantendo cliente aceitando valores nulos").
-- O SQLite não permite remover NOT NULL com ALTER COLUMN; por isso a tabela é reconstruída
-- (procedimento documentado em https://sqlite.org/lang_altertable.html), dentro de uma transação.
-- Nenhum dado é perdido: todas as linhas são copiadas para a nova estrutura.
BEGIN;

CREATE TABLE transacoes_expand (
    id_transacao TEXT PRIMARY KEY,
    cliente TEXT,
    cpf TEXT NOT NULL,
    idade INTEGER,
    valor_bruto REAL,
    valor_final REAL,
    status TEXT CHECK(status IN ('APROVADO','REJEITADO')),
    motivo_rejeicao TEXT,
    data_processamento TIMESTAMP,
    primeiro_nome TEXT,
    sobrenome TEXT
);

INSERT INTO transacoes_expand (id_transacao, cliente, cpf, idade, valor_bruto, valor_final,
                               status, motivo_rejeicao, data_processamento)
SELECT id_transacao, cliente, cpf, idade, valor_bruto, valor_final,
       status, motivo_rejeicao, data_processamento
FROM transacoes;

DROP TABLE transacoes;
ALTER TABLE transacoes_expand RENAME TO transacoes;

COMMIT;
