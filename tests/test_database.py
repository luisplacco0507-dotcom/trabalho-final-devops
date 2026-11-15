import sqlite3

from database import inicializar_banco, salvar_transacao, buscar_transacao_por_id
from scripts.migrar import migrar


def registro(id_transacao="TEST1"):
    return {"id_transacao": id_transacao, "cliente": "Ana Maria Souza", "cpf": "12345678901",
            "idade": 30, "valor_bruto": 100, "valor_final": 90,
            "status": "APROVADO", "motivo_rejeicao": None}


def test_insercao_consulta_em_memoria():
    with sqlite3.connect(":memory:") as db:
        db.row_factory = sqlite3.Row
        inicializar_banco(db)
        salvar_transacao(registro(), db)
        item = buscar_transacao_por_id("TEST1", db)
        assert item["cliente"] == "Ana Maria Souza"
        assert item["valor_final"] == 90
        assert buscar_transacao_por_id("NAO_EXISTE", db) is None


def test_expand_backfill_dual_write_contract(tmp_path):
    banco = str(tmp_path / "teste.db")
    with sqlite3.connect(banco) as db:
        inicializar_banco(db)
        salvar_transacao(registro("ANTES"), db)
    migrar(banco, 2)
    with sqlite3.connect(banco) as db:
        db.row_factory = sqlite3.Row
        antigo = buscar_transacao_por_id("ANTES", db)
        assert antigo["primeiro_nome"] == "Ana"
        assert antigo["sobrenome"] == "Maria Souza"
        salvar_transacao(registro("DURANTE"), db)
        novo = buscar_transacao_por_id("DURANTE", db)
        assert novo["cliente"] == "Ana Maria Souza"
        assert novo["primeiro_nome"] == "Ana"
    migrar(banco, 3)
    with sqlite3.connect(banco) as db:
        db.row_factory = sqlite3.Row
        salvar_transacao(registro("DEPOIS"), db)
        novo = buscar_transacao_por_id("DEPOIS", db)
        assert "cliente" not in novo
        assert novo["sobrenome"] == "Maria Souza"
    migrar(banco, 3)  # idempotência
