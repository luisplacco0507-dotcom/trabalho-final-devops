"""Aplicação CLI de processamento em lote de transações."""
import argparse
import json
import logging
import sys
import time
from pathlib import Path

from database import conectar, inicializar_banco, salvar_transacao
from regra_negocio import calcular_desconto_e_final, validar_transacao

BASE = Path(__file__).resolve().parent
LOGGER = logging.getLogger("processamento")


def configurar_logs(caminho: Path) -> None:
    LOGGER.setLevel(logging.INFO)
    LOGGER.handlers.clear()
    formato = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    for handler in (logging.FileHandler(caminho, encoding="utf-8"), logging.StreamHandler(sys.stdout)):
        handler.setFormatter(formato)
        LOGGER.addHandler(handler)


def processar_lote(arquivo: Path, banco: str) -> dict:
    inicio = time.perf_counter()
    with arquivo.open(encoding="utf-8") as f:
        transacoes = json.load(f)
    if not isinstance(transacoes, list):
        raise ValueError("O JSON deve conter uma lista de transações")
    aprovados = rejeitados = 0
    with conectar(banco) as db:
        inicializar_banco(db)
        LOGGER.info("Iniciando lote com %d transações", len(transacoes))
        for transacao in transacoes:
            valido, motivo = validar_transacao(transacao)
            desconto, valor_final = (calcular_desconto_e_final(
                transacao["valor_bruto"], transacao["idade"], transacao["categoria"])
                if valido else (0.0, 0.0))
            registro = {**transacao, "valor_final": valor_final,
                        "status": "APROVADO" if valido else "REJEITADO",
                        "motivo_rejeicao": None if valido else motivo}
            salvar_transacao(registro, db)
            if valido:
                aprovados += 1
                LOGGER.info("%s APROVADO | desconto=R$ %.2f | final=R$ %.2f",
                            transacao["id_transacao"], desconto, valor_final)
            else:
                rejeitados += 1
                LOGGER.warning("%s REJEITADO | %s", transacao.get("id_transacao"), motivo)
    duracao_ms = (time.perf_counter() - inicio) * 1000
    resumo = {"total": len(transacoes), "aprovados": aprovados,
              "rejeitados": rejeitados, "duracao_ms": round(duracao_ms, 2)}
    LOGGER.info("Resumo: total=%d aprovados=%d rejeitados=%d tempo=%.2f ms",
                resumo["total"], aprovados, rejeitados, duracao_ms)
    print(f"\nRESUMO: {resumo['total']} processados | {aprovados} aprovados | "
          f"{rejeitados} rejeitados | {duracao_ms:.2f} ms")
    return resumo


def main() -> int:
    parser = argparse.ArgumentParser(description="Processamento de transações em lote")
    parser.add_argument("--entrada", type=Path, default=BASE / "dados_processamento.json")
    parser.add_argument("--banco", default=str(BASE / "sistema.db"))
    parser.add_argument("--log", type=Path, default=BASE / "app.log")
    args = parser.parse_args()
    configurar_logs(args.log)
    try:
        processar_lote(args.entrada, args.banco)
        return 0
    except (OSError, ValueError, KeyError, TypeError, __import__('sqlite3').DatabaseError) as exc:
        LOGGER.exception("ERROR: falha no processamento: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
