# Passo a passo — o que foi feito no trabalho

**Integrantes:** Luis Felipe Placco; Isabella Mozzer Hakime; Livia Ayumi; Mariana Melendez; João Gabriel Alves.
**Disciplina:** Integração e Entrega Contínua (DevOps)

Este documento descreve, em ordem, o que foi construído e como cada etapa foi verificada. Os detalhes técnicos estão no [README](README.md) e no [relatório técnico](RELATORIO_TECNICO_FINAL.docx). Todos os resultados citados podem ser conferidos nos links do GitHub.

---

## Passo 1 — Regras de negócio (`regra_negocio.py`)

Criamos duas funções puras, sem acesso a banco:

- `validar_transacao(transacao)` → devolve `(True, "OK")` ou `(False, motivo)`. Rejeita:
  - `valor_bruto` menor ou igual a zero;
  - `idade` fora do intervalo 0–120 (ou que não seja inteiro);
  - `cpf` que não tenha exatamente 11 dígitos numéricos (validação só de formato);
  - menor de 18 anos comprando `eletronicos`.
- `calcular_desconto_e_final(valor_bruto, idade, categoria)` → 15% para quem tem 60 anos ou mais, 10% para `livros`, acumuláveis até 25%, com arredondamento em centavos (`Decimal`, `ROUND_HALF_UP`).

## Passo 2 — Testes automatizados (`tests/`)

Escrevemos 32 testes com pytest:

- **Unitários** (`test_regra_negocio.py`): os 10 casos do JSON, limites de idade 59/60, idades inválidas, CPFs inválidos, valores negativo/zero/nulo, menor comprando eletrônicos, desconto máximo de 25% e arredondamento.
- **Integração com banco** (`test_database.py`): gravar e ler em SQLite em memória e percorrer toda a migração Expand-Contract em um arquivo temporário, além de comprovar que `cliente` passa a aceitar NULL após o Expand.
- **Ponta a ponta** (`test_main.py`): processar o lote completo e conferir os totais 10/7/3 e os logs.

Como rodar:

```bash
python -m pip install -r requirements.txt
python -m pytest -v
```

## Passo 3 — Banco SQLite (`database.py`)

Criamos a tabela `transacoes` (versão v1, com a coluna `cliente` guardando o nome completo) e as funções `inicializar_banco()`, `salvar_transacao()` e `buscar_transacao_por_id()`, todas com SQL parametrizado. Aprovadas e rejeitadas são gravadas, e as rejeitadas levam o motivo.

## Passo 4 — Migração Expand-Contract (`alembic/` e `scripts/migrar.py`)

Objetivo: trocar `cliente` por `primeiro_nome` + `sobrenome` sem quebrar a aplicação.

| Etapa | Arquivo | O que faz |
|-------|---------|-----------|
| Expand | `001_expand.sql` | adiciona `primeiro_nome` e `sobrenome`; `cliente` continua existindo e passa a aceitar NULL (tabela reconstruída, sem perda de dados) |
| Dual Write | `database.py` | durante a transição, grava no campo antigo **e** nos novos |
| Backfill | `002_backfill.sql` | preenche os campos novos dos registros antigos |
| Contract | `003_contract.sql` | remove `cliente`; o executor só aplica se não houver nome vazio |

O `scripts/migrar.py` aplica os scripts em ordem e anota cada versão em `schema_migrations`, por isso pode ser executado de novo sem reaplicar nada.

```bash
python -c "from database import inicializar_banco; inicializar_banco()"
python scripts/migrar.py --ate 2   # Expand + Backfill
python main.py                     # grava com dual write
python scripts/migrar.py --ate 3   # Contract
```

## Passo 5 — Aplicação de processamento (`main.py`)

Lê `dados_processamento.json` (10 transações), valida, calcula descontos, grava no banco e registra logs:

- `INFO` para início, aprovações e resumo; `WARNING` para rejeições; `ERROR` para falhas.
- O tempo total é medido com `time.perf_counter()` e exibido em milissegundos.
- Em caso de erro, o programa termina com código 1.

Resultado: **10 processadas, 7 aprovadas, 3 rejeitadas** (TX1005 por valor negativo, TX1006 por CPF curto e TX1008 por valor zero).

```bash
python main.py
```

## Passo 6 — Pipeline de CI no GitHub Actions (`.github/workflows/ci.yml`)

A cada push ou pull request para `main`, o GitHub executa automaticamente:

1. instalação do Python 3.10 e das dependências;
2. `pytest` com todos os testes;
3. criação do banco e migrações Expand + Backfill;
4. `python main.py`;
5. verificação no banco: 10 registros, 3 rejeitados, nenhum nome vazio e `cliente` aceitando NULL;
6. Contract em uma cópia do banco, conferindo que `cliente` saiu sem perder registros;
7. publicação do `app.log` como artefato.

Cada passo roda com `bash -e`: se qualquer comando falhar, o pipeline fica vermelho.

## Passo 7 — Revisão antes de publicar

Ao revisar o projeto, encontramos e corrigimos:

1. **Erro no CI:** o passo de verificação tinha aspas duplas dentro de aspas duplas, e o bash dava erro de sintaxe. O pipeline nunca passaria. O script foi reescrito em bloco separado (heredoc).
2. **Contract sem conferência:** adicionamos a verificação depois da remoção da coluna.
3. **Aviso de Node.js 20 descontinuado:** atualizamos as actions para a versão `@v7`.
4. **`.gitignore` incompleto:** agora exclui ambientes virtuais, credenciais, bancos, logs e temporários.
5. **`pytest` sem `python -m` não funcionava:** criamos o `pytest.ini`.
6. **Expand não deixava `cliente` aceitar nulos** (exigência do enunciado): a migração 001 passou a reconstruir a tabela com `cliente` opcional; um teste novo e o CI verificam isso.
7. **`app.log` fora do repositório** (listado na estrutura do enunciado): passou a ser versionado com o log de uma execução real.

A lógica de negócio, o `main.py` e os testes originais não foram alterados; a migração 001 foi ajustada e um teste foi acrescentado.

## Passo 8 — Publicação no GitHub

- Repositório público: https://github.com/luisplacco0507-dotcom/trabalho-final-devops
- O primeiro commit guarda o projeto exatamente como estava no ZIP de entrega; os commits seguintes mostram cada correção.

## Passo 9 — Validação real do pipeline

Execuções no GitHub Actions em 15/11/2026, todas aprovadas, com 31 testes passando e lote 10/7/3:

| Execução | O que disparou |
|----------|----------------|
| [43741705440](https://github.com/luisplacco0507-dotcom/trabalho-final-devops/actions/runs/43741705440) | push com a correção do CI |
| [43741830093](https://github.com/luisplacco0507-dotcom/trabalho-final-devops/actions/runs/43741830093) | push com as actions atualizadas |
| [43742055811](https://github.com/luisplacco0507-dotcom/trabalho-final-devops/actions/runs/43742055811) | Pull Request #1 |
| [43742542954](https://github.com/luisplacco0507-dotcom/trabalho-final-devops/actions/runs/43742542954) | push com a documentação |
| [43742953406](https://github.com/luisplacco0507-dotcom/trabalho-final-devops/actions/runs/43742953406) | merge do Pull Request #1 na `main` |

Depois do ajuste do Expand (itens 6 e 7 do Passo 7), o pytest passa a ter 32 testes. Commits posteriores também disparam o pipeline; o histórico completo está em [Actions](https://github.com/luisplacco0507-dotcom/trabalho-final-devops/actions).

## Passo 10 — Demonstração com Pull Request

1. Criamos a branch `teste-ci-cd`.
2. Fizemos uma alteração segura no README (badge de status do CI).
3. Abrimos o [Pull Request #1](https://github.com/luisplacco0507-dotcom/trabalho-final-devops/pull/1) para `main`.
4. O GitHub Actions rodou sozinho no PR e o check `validar` passou.
5. Depois da confirmação do grupo, o PR foi integrado à `main` (commit de merge `0da66ff`), e o pipeline da `main` passou novamente.

## O que não foi feito

- Não houve demonstração de um pipeline **vermelho** no GitHub. O comportamento de falha foi conferido localmente e pelo `bash -e` dos logs.
- A proteção de branch, que bloquearia o merge com check falho, não foi configurada.
- A validação de CPF é só de formato, e o banco local não comprova *zero downtime* em produção.
