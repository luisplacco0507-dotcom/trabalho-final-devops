"""Regras puras: sem dependências de banco de dados."""
from decimal import Decimal, ROUND_HALF_UP


def validar_transacao(transacao: dict) -> tuple[bool, str]:
    valor = transacao.get("valor_bruto")
    if isinstance(valor, bool) or not isinstance(valor, (int, float)) or not (0 < valor < float("inf")):
        return False, "valor_bruto deve ser maior que zero"
    idade = transacao.get("idade")
    if isinstance(idade, bool) or not isinstance(idade, int) or not 0 <= idade <= 120:
        return False, "idade deve estar entre 0 e 120 anos"
    cpf = transacao.get("cpf")
    if not isinstance(cpf, str) or len(cpf) != 11 or not cpf.isascii() or not cpf.isdecimal():
        return False, "cpf deve conter exatamente 11 dígitos numéricos"
    if idade < 18 and transacao.get("categoria") == "eletronicos":
        return False, "menores de 18 anos não podem comprar eletrônicos"
    return True, "OK"


def calcular_desconto_e_final(valor_bruto: float, idade: int, categoria: str) -> tuple[float, float]:
    """Devolve desconto em reais e valor final, com arredondamento monetário."""
    if idade < 18 and categoria == "eletronicos":
        raise ValueError("menores de 18 anos não podem comprar eletrônicos")
    taxa = min((Decimal("0.15") if idade >= 60 else Decimal("0")) +
               (Decimal("0.10") if categoria == "livros" else Decimal("0")), Decimal("0.25"))
    bruto = Decimal(str(valor_bruto))
    desconto = (bruto * taxa).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    final = bruto - desconto
    return float(desconto), float(final)
