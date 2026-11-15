import json
from pathlib import Path

import pytest
from regra_negocio import validar_transacao, calcular_desconto_e_final

CASOS = json.loads((Path(__file__).resolve().parents[1] / "dados_processamento.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("transacao", CASOS, ids=[x["id_transacao"] for x in CASOS])
def test_todos_os_dez_casos(transacao):
    valido, motivo = validar_transacao(transacao)
    assert valido == (transacao["id_transacao"] not in {"TX1005", "TX1006", "TX1008"})
    assert motivo == "OK" if valido else motivo != "OK"


def test_limite_de_idade_59_60():
    assert calcular_desconto_e_final(100, 59, "vestuario") == (0, 100)
    assert calcular_desconto_e_final(100, 60, "vestuario") == (15, 85)


def test_desconto_acumulado_maximo_25():
    assert calcular_desconto_e_final(200, 65, "livros") == (50, 150)


def test_livros_menor_de_idade():
    assert calcular_desconto_e_final(80, 17, "livros") == (8, 72)


def test_eletronicos_menor_de_idade():
    t = {**CASOS[0], "idade": 17}
    assert validar_transacao(t)[0] is False
    with pytest.raises(ValueError):
        calcular_desconto_e_final(100, 17, "eletronicos")


@pytest.mark.parametrize("idade", [-1, 121, "60", True])
def test_idades_invalidas(idade):
    assert validar_transacao({**CASOS[0], "idade": idade})[0] is False


@pytest.mark.parametrize("cpf", ["123", "abcdefghijk", "1234567890a", "１２３４５６７８９０１", 12345678901])
def test_cpfs_invalidos(cpf):
    assert validar_transacao({**CASOS[0], "cpf": cpf})[0] is False


@pytest.mark.parametrize("valor", [-50, 0, None, True])
def test_valores_invalidos(valor):
    assert validar_transacao({**CASOS[0], "valor_bruto": valor})[0] is False


def test_arredondamento_monetario():
    assert calcular_desconto_e_final(10.05, 60, "vestuario") == (1.51, 8.54)
