"""Aplica as migrações SQL na ordem, com rastreamento de versões."""
import argparse
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARQUIVOS = ["001_expand.sql", "002_backfill.sql", "003_contract.sql"]


def migrar(caminho: str, ate: int = 2) -> None:
    if ate not in (1, 2, 3):
        raise ValueError("--ate deve ser 1, 2 ou 3")
    with sqlite3.connect(caminho) as db:
        db.execute("CREATE TABLE IF NOT EXISTS schema_migrations (versao INTEGER PRIMARY KEY)")
        for versao, arquivo in enumerate(ARQUIVOS[:ate], start=1):
            if db.execute("SELECT 1 FROM schema_migrations WHERE versao=?", (versao,)).fetchone():
                continue
            if versao == 3:
                pendentes = db.execute("SELECT count(*) FROM transacoes WHERE primeiro_nome IS NULL OR sobrenome IS NULL").fetchone()[0]
                if pendentes:
                    raise RuntimeError("Backfill incompleto: não é seguro remover cliente")
            script = (ROOT / "alembic" / arquivo).read_text(encoding="utf-8")
            # Scripts controlados pelo projeto, executados em ordem; o registro é feito ao final.
            db.executescript(script)
            db.execute("INSERT INTO schema_migrations (versao) VALUES (?)", (versao,))
            db.commit()
            print(f"Migração {versao} aplicada: {arquivo}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--banco", default=str(ROOT / "sistema.db"))
    parser.add_argument("--ate", type=int, choices=[1, 2, 3], default=2)
    args = parser.parse_args()
    migrar(args.banco, args.ate)
