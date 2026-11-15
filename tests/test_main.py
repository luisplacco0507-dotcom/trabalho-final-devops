import json
from pathlib import Path

from database import conectar
from main import configurar_logs, processar_lote


def test_lote_completo(tmp_path):
    entrada = Path(__file__).resolve().parents[1] / "dados_processamento.json"
    banco = str(tmp_path / "lote.db")
    log = tmp_path / "app.log"
    configurar_logs(log)
    resumo = processar_lote(entrada, banco)
    assert resumo["total"] == 10
    assert resumo["aprovados"] == 7
    assert resumo["rejeitados"] == 3
    with conectar(banco) as db:
        assert db.execute("SELECT COUNT(*) FROM transacoes").fetchone()[0] == 10
        assert db.execute("SELECT status FROM transacoes WHERE id_transacao='TX1005'").fetchone()[0] == "REJEITADO"
    conteudo = log.read_text(encoding="utf-8")
    assert "INFO" in conteudo and "WARNING" in conteudo and "tempo=" in conteudo
