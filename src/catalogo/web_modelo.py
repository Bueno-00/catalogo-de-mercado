"""O modelo clássico refeito em Python puro a partir de docs/modelo.json (a mesma conta do docs/app.js).

Serve para provar que o que roda no navegador é o mesmo modelo medido no teste: `tests/test_catalogo.py` compara
esta função com o scikit-learn e com o JavaScript (Node).
"""

from __future__ import annotations

import base64
import json
import math
from collections import Counter
from itertools import pairwise
from pathlib import Path

import numpy as np

from .quantidade import faixa_tokens
from .texto import norm

RAIZ = Path(__file__).resolve().parents[2]


def ngramas_palavras(t: str) -> list[str]:
    toks = t.split()
    return toks + [f"{a} {b}" for a, b in pairwise(toks)]


def ngramas_pedacos(t: str, nmin: int = 3, nmax: int = 5) -> list[str]:
    """Igual ao analyzer="char_wb" do scikit-learn."""
    out = []
    for w in t.split():
        w = f" {w} "
        for n in range(nmin, nmax + 1):
            off = 0
            out.append(w[off:off + n])
            while off + n < len(w):
                off += 1
                out.append(w[off:off + n])
            if off == 0:
                break
    return out


class ModeloWeb:
    def __init__(self, caminho: Path = RAIZ / "docs" / "modelo.json"):
        m = json.loads(Path(caminho).read_text())
        self.classes, self.nomes = m["classes"], m["nomes"]
        self.iw = {k: i for i, k in enumerate(m["palavras"])}
        self.ic = {k: i for i, k in enumerate(m["pedacos"])}
        self.idf_w, self.idf_c = np.array(m["idf_palavras"]), np.array(m["idf_pedacos"])
        # v2: tipo e faixa da quantidade, com peso; v1 não tem esse bloco
        self.iq = {k: i for i, k in enumerate(m.get("quantidade", []))}
        self.idf_q = np.array(m.get("idf_quantidade", []))
        self.peso_q = float(m.get("peso_quantidade", 0.0))
        self.T = float(m.get("temperatura", 1.0))
        n = m["n_atributos"]
        q = np.frombuffer(base64.b64decode(m["pesos_int8_b64"]), dtype=np.int8).reshape(len(self.classes), n)
        self.W = q.astype(np.float32) * np.array(m["escala"], dtype=np.float32)[:, None]
        self.b = np.array(m["intercepto"], dtype=np.float32)
        self.nw = len(self.iw)

    def _bloco(self, grams, idx, idf, desloc, peso=1.0):
        cont = Counter(g for g in grams if g in idx)
        if not cont:
            return {}
        v = {desloc + idx[g]: (1.0 + math.log(c)) * idf[idx[g]] for g, c in cont.items()}
        norma = math.sqrt(sum(x * x for x in v.values()))
        return {k: peso * x / norma for k, x in v.items()}

    def proba(self, texto: str) -> np.ndarray:
        t = norm(texto)
        x = {**self._bloco(ngramas_palavras(t), self.iw, self.idf_w, 0),
             **self._bloco(ngramas_pedacos(t), self.ic, self.idf_c, self.nw)}
        if self.peso_q:
            x.update(self._bloco(faixa_tokens(texto).split(), self.iq, self.idf_q, self.nw + len(self.ic), self.peso_q))
        z = self.b.copy()
        for j, v in x.items():
            z += self.W[:, j] * v
        z = self.T * z
        z = np.exp(z - z.max())
        return z / z.sum()

    def prever(self, texto: str, k: int = 3) -> list[tuple[str, float]]:
        p = self.proba(texto)
        top = np.argsort(-p)[:k]
        return [(self.classes[i], float(p[i])) for i in top]
