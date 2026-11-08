"""Normalização de texto usada no treino e repetida igual no navegador (docs/app.js)."""

from __future__ import annotations

import math
import re
import unicodedata

_NAO_ALNUM = re.compile(r"[^a-z0-9]+")
# "395g" -> "395 g", "1,5l" -> "1 5 l": separa número de unidade, igual no JS
_NUM_LETRA = re.compile(r"(?<=[0-9])(?=[a-z])|(?<=[a-z])(?=[0-9])")


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()
    s = _NAO_ALNUM.sub(" ", s)
    s = _NUM_LETRA.sub(" ", s)
    return " ".join(s.split())


def marca_principal(brands: str | None) -> str:
    """Primeira marca da lista ("Nestlé, Moça" -> "nestle")."""
    return norm(_limpo(brands).split(",")[0])


def _limpo(x) -> str:
    """None, NaN e "nan" viram vazio."""
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return ""
    s = str(x).strip()
    return "" if s.lower() in ("nan", "none", "null") else s


def texto_produto(nome: str, marca: str | None, quantidade: str | None) -> str:
    """Linha de catálogo como um lojista digitaria: nome + marca + quantidade."""
    nome = _limpo(nome)
    partes = [nome]
    m = _limpo(marca).split(",")[0].strip()
    if m and norm(m) not in norm(nome):
        partes.append(m)
    q = _limpo(quantidade)
    if q and norm(q) not in norm(nome):
        partes.append(q)
    return " ".join(p for p in partes if p)
