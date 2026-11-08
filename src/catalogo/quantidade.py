"""Quantidade do produto (peso, volume ou unidades) lida do texto, como sinal extra para a categoria.

Ideia do Rafael (08/11/2026): "Leite Nestlé 34 g" pode ser chocolate ou leite, mas não existe leite de 34 g.
Então lemos a quantidade, normalizamos (tudo em gramas, mililitros ou unidades) e colocamos em faixas.
- Modelo clássico: recebe o tipo e a faixa como palavras extras ("qt_m qf_m1" = peso entre 20 e 45 g). Também
  testamos a faixa combinada com a 1ª palavra do nome ("leite" + 20 a 45 g): na validação cruzada piorou, saiu.
- IAs: recebem a quantidade normalizada no fim do texto ("... | quantidade: 34 g").
A mesma leitura é refeita no navegador (docs/classificador.js) e os testes conferem que Python e JavaScript
leem igual.
"""

from __future__ import annotations

import re
import unicodedata

# número com vírgula ou ponto (decimal ou milhar), um "x" opcional de pacote antes, e a unidade
_NUM = r"\d+(?:[.,]\d+)?"
_UNIDADE = (r"kg|kgs|kilos?|quilos?|g|gr|grs|grama|gramas|mg|ml|mls|cl|l|lt|lts|litro|litros|oz"
            r"|un|und|unds|unid|unids|unidade|unidades|uni|cap|caps|capsula|capsulas|sache|saches|sachet|sachets")
_QTD = re.compile(r"(?:(\d{1,3})\s*x\s*)?(" + _NUM + r")\s*(" + _UNIDADE + r")(?![a-z])")
_PACOTE = re.compile(r"(?<![a-z0-9])(\d{1,3})\s*x(?![a-z])")

MASSA = {"kg": 1000.0, "kgs": 1000.0, "kilo": 1000.0, "kilos": 1000.0, "quilo": 1000.0, "quilos": 1000.0,
         "g": 1.0, "gr": 1.0, "grs": 1.0, "grama": 1.0, "gramas": 1.0, "mg": 0.001, "oz": 28.35}
VOLUME = {"ml": 1.0, "mls": 1.0, "cl": 10.0, "l": 1000.0, "lt": 1000.0, "lts": 1000.0, "litro": 1000.0, "litros": 1000.0}
# faixas (limite de cima de cada uma); a última vai até o infinito
FAIXAS = {"massa": [20, 45, 90, 180, 350, 700, 1500], "volume": [250, 400, 700, 1200, 2200], "unid": [1, 6, 20]}
NOME_TIPO = {"massa": "m", "volume": "v", "unid": "u"}


def _ascii(s: str) -> str:
    return unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()


def _numero(txt: str, unidade: str) -> float:
    """"1,5" = 1.5; "1.000" com g ou ml = 1000 (milhar); "0,500" com kg = 0.5."""
    if re.fullmatch(r"\d+[.,]\d{3}", txt) and not txt.startswith("0") and unidade in ("g", "gr", "grs", "ml", "mg"):
        return float(txt.replace(".", "").replace(",", ""))
    return float(txt.replace(",", "."))


def ler(texto: str) -> dict:
    """Última quantidade do texto (a do campo quantidade vem no fim da linha). Peso em gramas, volume em ml.

    >>> ler("Leite Nestlé 34 g")["valor"], ler("Cerveja 6x350ml")["pacote"], ler("Arroz 5kg")["valor"]
    (34.0, 6, 5000.0)
    """
    s = _ascii(texto)
    achados = list(_QTD.finditer(s))
    if not achados:
        return {"tipo": "nenhum", "valor": 0.0, "pacote": 1, "faixa": -1}
    m = achados[-1]
    unidade = m.group(3)
    valor = _numero(m.group(2), unidade)
    if unidade in MASSA:
        tipo, valor = "massa", valor * MASSA[unidade]
    elif unidade in VOLUME:
        tipo, valor = "volume", valor * VOLUME[unidade]
    else:
        tipo = "unid"
    pacote = int(m.group(1)) if m.group(1) else 1
    if pacote == 1:
        p = _PACOTE.search(s)
        if p and tipo != "unid":
            pacote = int(p.group(1))
    faixa = sum(valor > lim for lim in FAIXAS[tipo])
    return {"tipo": tipo, "valor": round(valor, 3), "pacote": pacote, "faixa": faixa}


def faixa_tokens(texto: str) -> str:
    """Palavras extras para o modelo clássico: o tipo da quantidade e a faixa.

    >>> faixa_tokens("Leite Nestlé 34 g"), faixa_tokens("Leite UHT 1 L"), faixa_tokens("Pão de forma")
    ('qt_m qf_m1', 'qt_v qf_v3', 'qt_nada')
    """
    q = ler(texto)
    if q["tipo"] == "nenhum":
        return "qt_nada"
    t = NOME_TIPO[q["tipo"]]
    return f"qt_{t} qf_{t}{q['faixa']}"


def texto_com_quantidade(texto: str) -> str:
    """Para as IAs: a linha do produto + a quantidade normalizada ("| quantidade: 34 g")."""
    q = ler(texto)
    if q["tipo"] == "nenhum":
        return str(texto)
    v = q["valor"] if q["valor"] < 10 else round(q["valor"])
    if q["tipo"] == "massa":
        txt = f"{v / 1000:g} kg" if v >= 1000 else f"{v:g} g"
    elif q["tipo"] == "volume":
        txt = f"{v / 1000:g} L" if v >= 1000 else f"{v:g} ml"
    else:
        txt = f"{v:g} unidades"
    if q["pacote"] > 1:
        txt = f"{q['pacote']} x {txt}"
    return f"{texto} | quantidade: {txt}"
