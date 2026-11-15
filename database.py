"""Persistência SQLite. A estrutura inicial v1 é criada apenas em bancos novos."""
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_DB = "sistema.db"


def conectar(caminho: str = DEFAULT_DB) -> sqlite3.Connection:
    conexao = sqlite3.connect(caminho)
    conexao.row_factory = sqlite3.Row
    return conexao


def inicializar_banco(conexao: sqlite3.Connection | None = None) -> None:
    propria = conexao is None
    db = conexao if conexao is not None else conectar()
    try:
        db.execute("""CREATE TABLE IF NOT EXISTS transacoes (
            id_transacao TEXT PRIMARY KEY,
            cliente TEXT NOT NULL,
            cpf TEXT NOT NULL,
            idade INTEGER,
            valor_bruto REAL,
            valor_final REAL,
            status TEXT CHECK(status IN ('APROVADO','REJEITADO')),
            motivo_rejeicao TEXT,
            data_processamento TIMESTAMP
        )""")
        db.commit()
    finally:
        if propria:
            db.close()


def salvar_transacao(dados: dict, conexao: sqlite3.Connection | None = None) -> None:
    propria = conexao is None
    db = conexao if conexao is not None else conectar()
    try:
        colunas = {linha[1] for linha in db.execute("PRAGMA table_info(transacoes)")}
        nome = str(dados.get("cliente", ""))
        partes = nome.strip().split(maxsplit=1)
        registro = {
            "id_transacao": dados["id_transacao"], "cpf": dados["cpf"],
            "idade": dados["idade"], "valor_bruto": dados["valor_bruto"],
            "valor_final": dados["valor_final"], "status": dados["status"],
            "motivo_rejeicao": dados.get("motivo_rejeicao"),
            "data_processamento": dados.get("data_processamento") or datetime.now(timezone.utc).isoformat(),
        }
        # Dual Write: durante a transição, escreve no legado e nos campos novos.
        if "cliente" in colunas:
            registro["cliente"] = nome
        if "primeiro_nome" in colunas:
            registro["primeiro_nome"] = partes[0] if partes else ""
        if "sobrenome" in colunas:
            registro["sobrenome"] = partes[1] if len(partes) > 1 else ""
        campos = list(registro)
        db.execute(f"INSERT INTO transacoes ({', '.join(campos)}) VALUES ({', '.join('?' for _ in campos)})",
                   [registro[c] for c in campos])
        db.commit()
    finally:
        if propria:
            db.close()


def buscar_transacao_por_id(id_transacao: str, conexao: sqlite3.Connection | None = None) -> dict | None:
    propria = conexao is None
    db = conexao if conexao is not None else conectar()
    try:
        row = db.execute("SELECT * FROM transacoes WHERE id_transacao = ?", (id_transacao,)).fetchone()
        return dict(row) if row else None
    finally:
        if propria:
            db.close()
