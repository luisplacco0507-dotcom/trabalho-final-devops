# Trabalho Prático Final — Integração e Entrega Contínua (DevOps)

**Integrantes:** Luis Felipe Placco; Isabella Mozzer Hakime; Livia Ayumi; Mariana Melendez; João Gabriel Alves.

**Disciplina:** Integração e Entrega Contínua (DevOps)  
**Entrega e apresentação:** 09/11/2026

## Objetivo

Aplicação CLI Python 3.10+ para processar um lote fixo de 10 transações do arquivo `dados_processamento.json`, validar entradas, aplicar descontos, salvar aprovações/rejeições no SQLite e emitir logs e métricas de execução. Demonstra práticas de testes, migrações Expand-Contract, CI/CD e observabilidade.

## Organização

- `regra_negocio.py`: validação e descontos, funções puras.
- `database.py`: banco SQLite e dual write durante migração.
- `main.py`: leitura do JSON, processamento, resumo e logs.
- `alembic/`: scripts SQL de migração (opção permitida pelo enunciado, sem Alembic Python).
- `scripts/migrar.py`: executor sequencial das migrações SQL.
- `tests/`: testes unitários, de integração e execução do lote.
- `.github/workflows/ci.yml`: validação automática de pushes e PRs para `main`.

## Executar localmente

Requer Python 3.10+.

```bash
python -m pip install -r requirements.txt
python -m pytest -v
python main.py
```

O último comando gera `sistema.db` e `app.log` na pasta do projeto. O log também aparece no console. **Resultado esperado:** 10 transações, 7 aprovadas e 3 rejeitadas (TX1005, TX1006 e TX1008). CPFs de exemplo são avaliados apenas pelo formato de 11 dígitos, como solicitado, não pelo dígito verificador.

**Atenção:** `id_transacao` é chave primária. Para executar novamente no mesmo banco, apague `sistema.db` (somente banco de demonstração) ou use outro caminho:

```bash
python main.py --banco demonstracao.db --log demonstracao.log
```

## Regras de negócio

1. `valor_bruto` > 0; `idade` entre 0 e 120; CPF com exatamente 11 dígitos numéricos.
2. Menores de 18 não podem comprar `eletronicos`.
3. Idosos a partir de 60 anos: 15% de desconto.
4. Categoria `livros`: 10% de desconto.
5. Descontos acumulados com teto de 25%, arredondados para centavos.
6. Rejeições também são persistidas, com motivo; `valor_final` das rejeitadas é 0.

## Database DevOps — Expand-Contract

A versão v1 contém a coluna legada `cliente`. A migração segue a sequência:

1. **Expand (`001_expand.sql`)**: adiciona `primeiro_nome` e `sobrenome`, sem remover `cliente`.
2. **Dual Write + Backfill (`002_backfill.sql`)**: o código grava nos campos antigos e novos, e o SQL preenche os registros anteriores. O primeiro termo do nome é `primeiro_nome`, o restante é `sobrenome`.
3. **Contract (`003_contract.sql`)**: remove `cliente` somente depois da compatibilidade das aplicações ser garantida. A camada `database.py` detecta as colunas existentes e funciona tanto na fase intermediária quanto na final.

Com um banco inicializado, executar:

```bash
python -c "from database import inicializar_banco; inicializar_banco()"
python scripts/migrar.py --ate 2
python main.py
# Execute Contract apenas após a verificação da transição:
python scripts/migrar.py --ate 3
```

O banco é local; a demonstração de *zero downtime* é de compatibilidade entre esquemas, não comprova disponibilidade contínua em produção. Os arquivos SQL ficam na pasta `alembic/`, mas são aplicados por um executor SQL próprio (o enunciado aceita scripts `.sql`). Requer SQLite 3.35+ para `DROP COLUMN`.

## Testes

- `test_regra_negocio.py`: os 10 casos do JSON, idade 59/60, CPF inválido, valor negativo/zero, menor em eletrônicos, descontos acumulados e arredondamento.
- `test_database.py`: inserção e consulta em `:memory:`; teste da evolução do esquema em arquivo temporário.
- `test_main.py`: processamento do lote completo, totalização e presença de logs.

## CI/CD

No GitHub Actions, a cada push e pull request para `main`, o fluxo configura Python 3.10, instala dependências, executa `pytest`, aplica Expand e Backfill, roda o lote, valida os totais, executa Contract em cópia do banco e publica `app.log` como artefato. **É preciso publicar este diretório em um repositório GitHub para a esteira rodar de verdade.** O arquivo de workflow está pronto, mas não há alegação de execução remota sem publicar.

## Logs e observabilidade

- `INFO`: início, aprovações e sumário.
- `WARNING`: rejeições e seus motivos.
- `ERROR`: falhas inesperadas de leitura, persistência ou formato, com stack trace.
- `time.perf_counter()`: duração total do lote em milissegundos.

## Roteiro de apresentação (10–15 minutos)

1. **Luis (2 min)**: objetivo, arquitetura e estrutura do repositório.
2. **Isabella (2–3 min)**: regras de negócio e testes de limites; executar `pytest`.
3. **Livia (2–3 min)**: SQLite, Expand, Dual Write, Backfill e Contract.
4. **Mariana (2–3 min)**: GitHub Actions; mostrar o PR e o status dos checks.
5. **João (2–3 min)**: executar `python main.py`, abrir `app.log`, explicar total e tempo.

**Demonstração de PR:** publicar o repositório; criar branch; alterar um teste ou regra; abrir PR para `main`; mostrar a aba Actions e o check de testes. O resultado só pode ser mostrado ao vivo depois da execução real no GitHub.

## Limitações deliberadas

O JSON contém exatamente os 10 registros do enunciado. A validação de CPF é apenas estrutural. Rodadas repetidas no mesmo banco geram erro de chave primária (para evitar sobrescrever histórico); utilize um banco novo para a demonstração. O projeto não exige interface web, API, Docker nem implantação em nuvem.
