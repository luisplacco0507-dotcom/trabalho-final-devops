-- EXPAND: novas colunas opcionais; o campo cliente continua disponível.
ALTER TABLE transacoes ADD COLUMN primeiro_nome TEXT;
ALTER TABLE transacoes ADD COLUMN sobrenome TEXT;
