-- BACKFILL: preenche os nomes anteriores; o código passa a fazer dual write.
-- SQLite instr(): posição do primeiro espaço, 0 quando não existe.
UPDATE transacoes
SET primeiro_nome = CASE WHEN instr(trim(cliente), ' ') = 0 THEN trim(cliente)
                         ELSE substr(trim(cliente), 1, instr(trim(cliente), ' ') - 1) END,
    sobrenome = CASE WHEN instr(trim(cliente), ' ') = 0 THEN ''
                     ELSE ltrim(substr(trim(cliente), instr(trim(cliente), ' ') + 1)) END
WHERE primeiro_nome IS NULL OR sobrenome IS NULL;
