"""Caminho clássico: TF-IDF (palavras + pedaços de palavra) + regressão logística.

Treina no treino, escolhe a configuração na validação (nunca olha o teste para escolher), mede no teste e
exporta o modelo em JSON para rodar no navegador (docs/modelo.json). A mesma conta é refeita em
`web_modelo.py` (Python puro, a partir do JSON) e em `docs/app.js`; os testes conferem que as três dão a
mesma resposta.

Uso:  python -m catalogo.classico
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.sparse as sp
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score

from .texto import norm

RAIZ = Path(__file__).resolve().parents[2]
SPLIT = RAIZ / "data" / "split"
SAIDA_PRED = RAIZ / "reports" / "predicoes"
WEB = RAIZ / "docs" / "modelo.json"
TOKEN = r"(?u)\b\w+\b"


class Classico:
    def __init__(self, max_w: int, max_c: int, C: float):
        self.max_w, self.max_c, self.C = max_w, max_c, C
        self.vw = TfidfVectorizer(analyzer="word", token_pattern=TOKEN, ngram_range=(1, 2), min_df=2,
                                  sublinear_tf=True, max_features=max_w, lowercase=False, dtype=np.float32)
        self.vc = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=3,
                                  sublinear_tf=True, max_features=max_c, lowercase=False, dtype=np.float32)
        self.lr = LogisticRegression(C=C, max_iter=3000)

    def _x(self, textos, fit=False):
        t = [norm(s) for s in textos]
        if fit:
            return sp.hstack([self.vw.fit_transform(t), self.vc.fit_transform(t)], format="csr")
        return sp.hstack([self.vw.transform(t), self.vc.transform(t)], format="csr")

    def fit(self, textos, y):
        self.lr.fit(self._x(textos, fit=True), y)
        return self

    def proba(self, textos):
        return self.lr.predict_proba(self._x(textos))

    def predict(self, textos):
        return self.lr.classes_[self.proba(textos).argmax(1)]

    def exportar(self, destino: Path, rotulos_pt: dict[str, str]) -> dict:
        """JSON compacto: vocabulário em ordem de índice, idf e pesos em int8 com escala por classe."""
        coef = self.lr.coef_.astype(np.float32)
        escala = np.abs(coef).max(axis=1) / 127.0
        q = np.round(coef / escala[:, None]).astype(np.int8)
        vw = sorted(self.vw.vocabulary_.items(), key=lambda kv: kv[1])
        vc = sorted(self.vc.vocabulary_.items(), key=lambda kv: kv[1])
        modelo = {
            "versao": 1,
            "normalizacao": "NFKD sem acento, minúsculas, não alfanumérico vira espaço, número e letra separados",
            "palavras": [k for k, _ in vw], "idf_palavras": [round(float(x), 4) for x in self.vw.idf_],
            "pedacos": [k for k, _ in vc], "idf_pedacos": [round(float(x), 4) for x in self.vc.idf_],
            "classes": list(self.lr.classes_), "nomes": [rotulos_pt[c] for c in self.lr.classes_],
            "escala": [float(x) for x in escala], "intercepto": [round(float(x), 5) for x in self.lr.intercept_],
            # pesos [classe][atributo] em int8, achatado, em base64 para caber pequeno
            "pesos_int8_b64": __import__("base64").b64encode(q.tobytes()).decode(),
            "n_atributos": int(coef.shape[1]),
        }
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(json.dumps(modelo, ensure_ascii=False, separators=(",", ":")))
        return modelo


def carregar_split():
    tr = pd.read_parquet(SPLIT / "treino.parquet")
    va = pd.read_parquet(SPLIT / "validacao.parquet")
    te = pd.read_parquet(SPLIT / "teste.parquet")
    return tr, va, te


def metricas(y, p) -> dict:
    return {"acuracia": float(accuracy_score(y, p)), "f1_macro": float(f1_score(y, p, average="macro", zero_division=0))}


def main():
    tr, va, te = carregar_split()
    rotulos_pt = json.loads((SPLIT / "categorias.json").read_text())["nomes"]
    grade = [(mw, mc, C) for mw, mc in [(5_000, 10_000), (30_000, 60_000)] for C in (1.0, 3.0, 10.0)]
    linhas = []
    for mw, mc, C in grade:
        t0 = time.time()
        m = Classico(mw, mc, C).fit(tr["texto"], tr["categoria"])
        r = metricas(va["categoria"], m.predict(va["texto"]))
        linhas.append({"max_palavras": mw, "max_pedacos": mc, "C": C, **r, "seg": round(time.time() - t0, 1)})
        print(linhas[-1], flush=True)
    grade_df = pd.DataFrame(linhas)
    # escolhe pelo F1 macro na validação; empate fica com o modelo menor (cabe melhor no navegador)
    melhor = grade_df.sort_values(["f1_macro", "max_palavras"], ascending=[False, True]).iloc[0]
    print("escolhido na validação:", melhor.to_dict())

    # modelo final: só o treino (o mesmo que o LoRA usa), configuração escolhida na validação
    t0 = time.time()
    m = Classico(int(melhor.max_palavras), int(melhor.max_pedacos), float(melhor.C)).fit(tr["texto"], tr["categoria"])
    t_treino = time.time() - t0
    t0 = time.time()
    prob = m.proba(te["texto"])
    t_lote = time.time() - t0
    pred = m.lr.classes_[prob.argmax(1)]
    # latência de 1 produto por vez (como no navegador), mediana de 200
    lat = []
    for s in te["texto"].head(200):
        t1 = time.perf_counter(); m.predict([s]); lat.append(time.perf_counter() - t1)
    SAIDA_PRED.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"id": te["id"], "pred": pred, "confianca": prob.max(1).round(4)}).to_csv(SAIDA_PRED / "tfidf.csv", index=False)
    modelo = m.exportar(WEB, rotulos_pt)
    info = {
        "config": {k: (float(v) if k == "C" else int(v)) for k, v in melhor[["max_palavras", "max_pedacos", "C"]].items()},
        "grade_validacao": linhas, "teste": metricas(te["categoria"], pred),
        "treino_seg": round(t_treino, 1), "ms_por_item_lote": 1000 * t_lote / len(te),
        "ms_por_item_um_a_um_mediana": 1000 * float(np.median(lat)),
        "n_atributos": modelo["n_atributos"], "tamanho_json_bytes": WEB.stat().st_size,
    }
    (RAIZ / "reports" / "classico.json").write_text(json.dumps(info, indent=1, ensure_ascii=False))
    print(json.dumps({k: v for k, v in info.items() if k != "grade_validacao"}, indent=1, ensure_ascii=False))


def vazamento():
    """Mesmo modelo e mesma configuração num split ALEATÓRIO (marca nos dois lados): mostra quanto o número
    fica inflado quando o teste tem marcas que o modelo já viu."""
    cfg = json.loads((RAIZ / "reports" / "classico.json").read_text())["config"]
    d = RAIZ / "data" / "split_aleatorio"
    tr, te = pd.read_parquet(d / "treino_validacao.parquet"), pd.read_parquet(d / "teste.parquet")
    # mesmo tamanho de treino do split por marca, para comparar só o efeito da marca
    n = len(pd.read_parquet(SPLIT / "treino.parquet"))
    tr = tr.sample(n=n, random_state=42)
    m = Classico(cfg["max_palavras"], cfg["max_pedacos"], cfg["C"]).fit(tr["texto"], tr["categoria"])
    r = {**metricas(te["categoria"], m.predict(te["texto"])), "n_treino": len(tr), "n_teste": len(te),
         "marcas_do_teste_vistas_no_treino": float(te["grupo"].isin(set(tr["grupo"])).mean())}
    (RAIZ / "reports" / "vazamento.json").write_text(json.dumps(r, indent=1))
    print("split aleatório:", r)


if __name__ == "__main__":
    import sys

    vazamento() if "--vazamento" in sys.argv else main()
