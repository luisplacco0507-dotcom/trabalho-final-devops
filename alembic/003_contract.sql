-- CONTRACT: SQLite moderno (3.35+) permite DROP COLUMN.
-- Execute SOMENTE após todas as versões da aplicação lerem primeiro_nome/sobrenome.
ALTER TABLE transacoes DROP COLUMN cliente;
