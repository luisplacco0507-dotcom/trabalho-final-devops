# Trabalho Prático Final — Integração e Entrega Contínua (DevOps)

**Integrantes:** Luis Felipe Placco; Isabella Mozzer Hakime; Livia Ayumi; Mariana Melendez; João Gabriel Alves.

**Disciplina:** Integração e Entrega Contínua (DevOps)  
**Entrega e apresentação:** 09/11/2026

## Objetivo

Aplicação CLI Python 3.10+ para processar um lote fixo de 10 transações do arquivo `dados_processamento.json`, validar entradas, aplicar descontos, salvar aprovações/rejeições no SQLite e emitir logs e métricas de execução. Demonstra práticas de testes, migrações Expand-Contract, CI/CD e observabilidade.

## Repositório e evidências

- **Repositório:** https://github.com/luisplacco0507-dotcom/trabalho-final-devops
- **Workflow:** [`.github/workflows/ci.yml`](.github/workflows/ci.yml) — histórico em [Actions](https://github.com/luisplacco0507-dotcom/trabalho-final-devops/actions/workflows/ci.yml)
- **Pull Request de demonstração:** [#1 — Teste de CI/CD](https://github.com/luisplacco0507-dotcom/trabalho-final-devops/pull/1) (branch `teste-ci-cd` → `main`)

## Organização

- `regra_negocio.py`: validação e descontos, funções puras (sem banco).
- `database.py`: banco SQLite e *dual write* durante a migração.
- `main.py`: leitura do JSON, processamento, resumo, logs e código de saída.
- `alembic/`: scripts SQL de migração (opção permitida pelo enunciado, sem Alembic Python).
- `scripts/migrar.py`: executor sequencial das migrações SQL, com tabela `schema_migrations`.
- `tests/`: testes unitários, de integração e execução do lote.
- `pytest.ini`: configura `pythonpath` e `testpaths`, permitindo rodar `pytest` ou `python -m pytest`.
- `.github/workflows/ci.yml`: validação automática de pushes e PRs para `main`.
- `RELATORIO_TECNICO_FINAL.docx`: relatório técnico; `APRESENTACAO.md`: roteiro de fala.

## Como o projeto foi desenvolvido

1. **Regras de negócio isoladas** em funções puras (`validar_transacao`, `calcular_desconto_e_final`), testadas com particionamento de equivalência e análise de valor limite.
2. **Persistência SQLite** com consultas parametrizadas; a camada `database.py` lê as colunas existentes (`PRAGMA table_info`) e se adapta às fases do esquema.
3. **Evolução do esquema por Expand-Contract**, com scripts SQL versionados e um executor que registra o que já foi aplicado.
4. **Aplicação CLI** (`main.py`) que processa o lote, persiste aprovados e rejeitados, registra logs em arquivo e console e devolve código de saída 1 em caso de erro.
5. **Integração contínua** com GitHub Actions executando testes, migrações, a aplicação e verificações do banco a cada push e PR para `main`.

## Executar a aplicação

Requer Python 3.10+.

```bash
python -m pip install -r requirements.txt
python main.py
```

O comando gera `sistema.db` e `app.log` na pasta do projeto (ambos ignorados pelo Git). O log também aparece no console. **Resultado esperado:** 10 transações, 7 aprovadas e 3 rejeitadas (TX1005, TX1006 e TX1008). CPFs de exemplo são avaliados apenas pelo formato de 11 dígitos, como solicitado, não pelo dígito verificador.

**Atenção:** `id_transacao` é chave primária. Executar de novo no mesmo banco gera erro de chave duplicada e o programa termina com código 1. Para repetir, apague `sistema.db` (somente banco de demonstração) ou use outro caminho:

```bash
python main.py --banco demonstracao.db --log demonstracao.log
```

## Executar os testes

```bash
python -m pytest -v
```

São 31 testes:

- `tests/test_regra_negocio.py` (unitários): os 10 casos do JSON, idade 59/60, idades inválidas, CPFs inválidos (curto, letras, dígitos Unicode, número em vez de texto), valor negativo/zero/nulo, menor em eletrônicos, descontos acumulados com teto de 25% e arredondamento monetário.
- `tests/test_database.py` (integração): inserção e consulta em SQLite `:memory:`; evolução completa do esquema (v1 → Expand → Backfill/Dual Write → Contract) em arquivo temporário, incluindo idempotência da migração.
- `tests/test_main.py` (integração ponta a ponta): processamento do lote completo, totais 10/7/3 e presença de logs INFO/WARNING e do tempo de execução.

## Regras de negócio

1. `valor_bruto` > 0; `idade` entre 0 e 120; CPF com exatamente 11 dígitos numéricos.
2. Menores de 18 não podem comprar `eletronicos`.
3. Idosos a partir de 60 anos: 15% de desconto.
4. Categoria `livros`: 10% de desconto.
5. Descontos acumulados com teto de 25%, arredondados para centavos.
6. Rejeições também são persistidas, com motivo; `valor_final` das rejeitadas é 0.

## Database DevOps — Expand-Contract

A versão v1 da tabela `transacoes` contém a coluna legada `cliente` (nome completo). O objetivo é substituí-la por `primeiro_nome` e `sobrenome` sem quebrar a aplicação em nenhum momento:

1. **Expand (`001_expand.sql`)**: adiciona `primeiro_nome` e `sobrenome` como colunas opcionais, sem remover `cliente`. Versões antigas do código continuam funcionando.
2. **Dual Write + Backfill (`002_backfill.sql`)**: `database.py` passa a gravar ao mesmo tempo no campo antigo e nos novos (ele detecta quais colunas existem). O SQL preenche os registros anteriores: o primeiro termo do nome vira `primeiro_nome` e o restante, `sobrenome`.
3. **Contract (`003_contract.sql`)**: remove `cliente` somente depois que todas as aplicações leem os campos novos. Antes de aplicar, `scripts/migrar.py` confere que não há registros com `primeiro_nome`/`sobrenome` nulos e aborta se o backfill estiver incompleto.

O executor `scripts/migrar.py` registra cada versão aplicada na tabela `schema_migrations`, por isso pode ser executado novamente sem reaplicar scripts. O parâmetro `--ate` define até qual etapa migrar.

```bash
python -c "from database import inicializar_banco; inicializar_banco()"   # cria o esquema v1
python scripts/migrar.py --ate 2                                          # Expand + Backfill
python main.py                                                            # grava com dual write
python scripts/migrar.py --ate 3                                          # Contract (após verificar a transição)
```

O banco é local; a demonstração de *zero downtime* é de compatibilidade entre esquemas, não comprova disponibilidade contínua em produção. Requer SQLite 3.35+ para `DROP COLUMN`.

## CI/CD com GitHub Actions

O workflow `CI - Testes, Migrações e Execução` (`.github/workflows/ci.yml`) é disparado automaticamente em **push** e **pull_request** para a branch `main`, em `ubuntu-latest`, com permissões mínimas (`contents: read`). Passos:

| # | Passo | O que faz |
|---|-------|-----------|
| 1 | Checkout | baixa o código (`actions/checkout@v7`) |
| 2 | Python 3.10 | instala Python 3.10 (`actions/setup-python@v7`) |
| 3 | Instalar dependências | `python -m pip install -r requirements.txt` |
| 4 | Testes automatizados | `python -m pytest -v` (unitários e integração) |
| 5 | Criar banco e aplicar Expand + Backfill | cria o esquema v1 e roda `scripts/migrar.py --ate 2` |
| 6 | Executar lote ponta a ponta | `python main.py` |
| 7 | Verificar 10 registros e estados | confere 10 registros, 3 rejeitados e nenhum `primeiro_nome`/`sobrenome` nulo |
| 8 | Validar etapa Contract em cópia do banco | roda `--ate 3` em `contrato.db` e confere que `cliente` saiu sem perda de registros |
| 9 | Salvar log como artefato | publica `app.log` como artefato `logs-ci` (sempre, mesmo em falha) |

**Como o pipeline falha:** o GitHub executa cada passo com `bash -e`, então qualquer comando com código de saída diferente de zero interrompe o job e marca o check como falho (vermelho). Isso inclui um teste com falha no pytest, uma exceção nas migrações (por exemplo, backfill incompleto antes do Contract), o `main.py` terminando com código 1 ou um `assert` dos passos de verificação. A proteção de branch que *impede* o merge com check vermelho não está configurada; ela pode ser ativada em *Settings → Branches* do repositório.

## Validações efetivamente realizadas

Todas as execuções abaixo são reais e podem ser conferidas nos links.

**GitHub Actions (15/11/2026, horário UTC):**

| Execução | Evento | Commit | Resultado |
|----------|--------|--------|-----------|
| [43741705440](https://github.com/luisplacco0507-dotcom/trabalho-final-devops/actions/runs/43741705440) | push em `main` | `daedb87` (correção do CI) | ✅ success — 31 passed; aviso de Node.js 20 nas actions |
| [43741830093](https://github.com/luisplacco0507-dotcom/trabalho-final-devops/actions/runs/43741830093) | push em `main` | `2ac36e1` (actions v7) | ✅ success — 31 passed; aviso de Node.js 20 eliminado |
| [43742055811](https://github.com/luisplacco0507-dotcom/trabalho-final-devops/actions/runs/43742055811) | pull_request (PR #1) | `ec1c8b4` (badge no README) | ✅ success — 31 passed |

Saídas registradas nos logs dessas execuções:

- Python `3.10.22` no runner; pytest `31 passed`.
- `Migração 1 aplicada: 001_expand.sql` e `Migração 2 aplicada: 002_backfill.sql`.
- `RESUMO: 10 processados | 7 aprovados | 3 rejeitados`.
- Verificação: `total=10 rejeitados=3 sem_nome=0`.
- Contract: `Migração 3 aplicada: 003_contract.sql`; colunas finais sem `cliente`, `total=10`.
- Artefato `logs-ci` publicado.

**Pull Request:** o [PR #1](https://github.com/luisplacco0507-dotcom/trabalho-final-devops/pull/1) disparou o workflow automaticamente no evento `pull_request`; o check `validar` passou. O PR foi mantido aberto, sem merge, aguardando a confirmação do grupo.

**Localmente (Windows, Python 3.14.7, SQLite 3.50.4):**

- `python -m pytest`: 31 passed, código de saída 0.
- Simulação do pipeline em cópia limpa do projeto: criação do banco, Expand + Backfill, `main.py` (10/7/3), verificação e Contract, todos com código 0.
- Falha esperada: executar `main.py` duas vezes no mesmo banco termina com código 1 (`UNIQUE constraint failed`), com o erro registrado no log.
- A linha original do passo de verificação do CI, executada em `bash -e`, falhou com `syntax error near unexpected token '('` (código 2), o que confirmou o defeito corrigido.

**Não demonstrado no GitHub:** uma execução com check vermelho. O comportamento de falha foi verificado localmente e decorre do `bash -e` mostrado nos logs, mas não houve push intencional de código quebrado.

## Problemas encontrados e correções

1. **Passo de verificação do CI quebrado (crítico).** O passo "Verificar 10 registros e estados" usava `python -c "..."` com aspas duplas internas (`"select ... status='REJEITADO'"`). O bash encerrava a string no meio e falhava com erro de sintaxe, então o pipeline nunca passaria. **Correção:** o script Python foi movido para um *heredoc* (`python - <<'EOF'`), que também passou a verificar o dual write/backfill.
2. **Contract sem verificação.** O passo só executava a migração 3. **Correção:** depois do Contract, o CI confere que `cliente` foi removida, que `primeiro_nome`/`sobrenome` existem e que os 10 registros permanecem.
3. **Actions em Node.js 20 (descontinuado).** A primeira execução gerou um aviso de depreciação. **Correção:** `checkout`, `setup-python` e `upload-artifact` foram atualizadas para `@v7` (Node.js 24); o aviso não aparece mais.
4. **`.gitignore` incompleto.** Faltavam ambientes virtuais alternativos, `.env`/credenciais, logs genéricos, arquivos temporários e de editores. **Correção:** o arquivo foi ampliado; `sistema.db` e `app.log` gerados localmente não são versionados.
5. **`pytest` sem `python -m`.** Só funcionava como `python -m pytest`, porque a raiz do projeto não entrava no `sys.path`. **Correção:** `pytest.ini` com `pythonpath = .`.

A lógica de negócio, os testes, as migrações SQL e o `main.py` não foram alterados.

## Logs e observabilidade

- `INFO`: início, aprovações e sumário.
- `WARNING`: rejeições e seus motivos.
- `ERROR`: falhas inesperadas de leitura, persistência ou formato, com stack trace.
- `time.perf_counter()`: duração total do lote em milissegundos.

## Roteiro de apresentação (10–15 minutos)

1. **Luis Felipe Placco (2 min)**: objetivo, arquitetura e estrutura do repositório.
2. **Isabella Mozzer Hakime (2–3 min)**: regras de negócio e testes de limites; executar `pytest`.
3. **Livia Ayumi (2–3 min)**: SQLite, Expand, Dual Write, Backfill e Contract.
4. **Mariana Melendez (2–3 min)**: GitHub Actions; mostrar o PR #1 e o status dos checks.
5. **João Gabriel Alves (2–3 min)**: executar `python main.py`, abrir `app.log`, explicar total e tempo.

## Limitações deliberadas

O JSON contém exatamente os 10 registros do enunciado. A validação de CPF é apenas estrutural. Rodadas repetidas no mesmo banco geram erro de chave primária (para evitar sobrescrever histórico); utilize um banco novo para a demonstração. O projeto não exige interface web, API, Docker nem implantação em nuvem.
