"""Caminho clássico: TF-IDF (palavras + pedaços de palavra) + modelo linear. Roda em CPU e no navegador.

Duas versões, as duas medidas no mesmo teste:
- v1 (08/11/2026, manhã): regressão logística, só o texto. Fica para comparar (`reports/predicoes/tfidf.csv`).
- v2 (08/11/2026, tarde): LinearSVC, + a QUANTIDADE em faixas (`quantidade.py`), + cada produto do treino
  repetido sem as palavras da marca (o lojista novo traz uma marca que o modelo nunca viu). A configuração foi
  escolhida por validação cruzada agrupada por marca, só com treino + validação (`--escolher`); o teste não
  escolhe nada. A probabilidade sai de um softmax com uma "temperatura" ajustada na validação.

O modelo vai para o navegador em JSON (docs/modelo.json). A mesma conta é refeita em `web_modelo.py` (Python
puro) e em `docs/classificador.js`; os testes conferem que as três dão a mesma resposta.

Uso:
  python -m catalogo.classico              # v2: treina no treino, mede no teste, exporta docs/modelo.json
  python -m catalogo.classico --escolher   # validação cruzada por marca (treino + validação) -> reports/classico_cv.json
  python -m catalogo.classico --v1         # refaz o v1 (regressão logística, só texto)
  python -m catalogo.classico --vazamento  # o mesmo v1 num split aleatório (marca nos dois lados)
"""

from __future__ import annotations

import base64
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.sparse as sp
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import GroupKFold
from sklearn.svm import LinearSVC

from .quantidade import faixa_tokens
from .texto import _limpo, norm

RAIZ = Path(__file__).resolve().parents[2]
SPLIT = RAIZ / "data" / "split"
SAIDA_PRED = RAIZ / "reports" / "predicoes"
WEB = RAIZ / "docs" / "modelo.json"
TOKEN = r"(?u)\b\w+\b"
V2 = {"modelo": "svc", "C": 0.3, "peso_q": 0.6, "sem_marca": True}


def sem_marca(texto_norm: str, brands) -> str:
    """O texto sem as palavras da marca ("leite condensado moca nestle 395 g" -> "leite condensado moca 395 g")."""
    marca = set()
    for b in _limpo(brands).split(","):
        marca |= set(norm(b).split())
    return " ".join(w for w in texto_norm.split() if w not in marca) or texto_norm


class Classico:
    def __init__(self, modelo: str = "svc", C: float = 0.3, peso_q: float = 0.0, sem_marca: bool = False,
                 max_w: int = 30_000, max_c: int = 60_000):
        self.modelo, self.C, self.peso_q, self.sem_marca = modelo, C, peso_q, sem_marca
        self.vw = TfidfVectorizer(analyzer="word", token_pattern=TOKEN, ngram_range=(1, 2), min_df=2,
                                  sublinear_tf=True, max_features=max_w, lowercase=False, dtype=np.float32)
        self.vc = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=3,
                                  sublinear_tf=True, max_features=max_c, lowercase=False, dtype=np.float32)
        self.vq = TfidfVectorizer(analyzer="word", token_pattern=r"\S+", min_df=2, sublinear_tf=True,
                                  lowercase=False, dtype=np.float32)
        self.clf = LogisticRegression(C=C, max_iter=3000) if modelo == "lr" else LinearSVC(C=C)
        self.temperatura = 1.0

    def _x(self, textos, fit=False, normalizados=None):
        t = normalizados if normalizados is not None else [norm(s) for s in textos]
        blocos = [(self.vw, t), (self.vc, t)]
        if self.peso_q:
            blocos.append((self.vq, [faixa_tokens(s) for s in textos]))
        mats = [(v.fit_transform(x) if fit else v.transform(x)) for v, x in blocos]
        if self.peso_q:
            mats[2] = mats[2] * self.peso_q
        return sp.hstack(mats, format="csr")

    def fit(self, textos, y, brands=None):
        textos, y = list(textos), list(y)
        t = [norm(s) for s in textos]
        if self.sem_marca and brands is not None:
            # cada produto entra 2 vezes: com e sem as palavras da marca (a quantidade continua a mesma)
            t = t + [sem_marca(n, b) for n, b in zip(t, brands)]
            textos, y = textos * 2, y * 2
        self.clf.fit(self._x(textos, fit=True, normalizados=t), y)
        self.classes_ = self.clf.classes_
        return self

    def pontos(self, textos):
        x = self._x(list(textos))
        return self.clf.decision_function(x) if self.modelo == "svc" else self.clf.predict_log_proba(x)

    def proba(self, textos):
        z = self.temperatura * self.pontos(textos)
        z = np.exp(z - z.max(axis=1, keepdims=True))
        return z / z.sum(axis=1, keepdims=True)

    def predict(self, textos):
        return self.classes_[self.pontos(textos).argmax(1)]

    def calibrar(self, textos, y):
        """Temperatura do softmax que dá a menor perda (log loss) na validação. Não muda a resposta, só a confiança."""
        s = self.pontos(textos)
        idx = np.searchsorted(self.classes_, np.asarray(y))
        melhor = (np.inf, 1.0)
        for T in np.geomspace(0.2, 40, 120):
            z = T * s
            z = z - z.max(axis=1, keepdims=True)
            perda = -(z[np.arange(len(idx)), idx] - np.log(np.exp(z).sum(axis=1))).mean()
            melhor = min(melhor, (float(perda), float(T)))
        self.temperatura = melhor[1]
        return melhor

    def exportar(self, destino: Path, rotulos_pt: dict[str, str]) -> dict:
        """JSON compacto: vocabulários em ordem de índice, idf e pesos em int8 com escala por classe."""
        coef = self.clf.coef_.astype(np.float32)
        escala = np.abs(coef).max(axis=1) / 127.0
        q = np.round(coef / escala[:, None]).astype(np.int8)

        def vocab(v):
            return [k for k, _ in sorted(v.vocabulary_.items(), key=lambda kv: kv[1])]

        modelo = {
            "versao": 2,
            "normalizacao": "NFKD sem acento, minúsculas, não alfanumérico vira espaço, número e letra separados",
            "palavras": vocab(self.vw), "idf_palavras": [round(float(x), 4) for x in self.vw.idf_],
            "pedacos": vocab(self.vc), "idf_pedacos": [round(float(x), 4) for x in self.vc.idf_],
            "quantidade": vocab(self.vq) if self.peso_q else [],
            "idf_quantidade": [round(float(x), 4) for x in self.vq.idf_] if self.peso_q else [],
            "peso_quantidade": self.peso_q, "temperatura": round(self.temperatura, 5),
            "classes": list(self.classes_), "nomes": [rotulos_pt[c] for c in self.classes_],
            "escala": [float(x) for x in escala], "intercepto": [round(float(x), 5) for x in self.clf.intercept_],
            "pesos_int8_b64": base64.b64encode(q.tobytes()).decode(),  # [classe][atributo], achatado
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


GRADE = [  # o que foi testado na validação cruzada (nome, configuração)
    ("v1: regressão logística, só texto", {"modelo": "lr", "C": 3.0}),
    ("LinearSVC, só texto", {"modelo": "svc", "C": 0.3}),
    ("LinearSVC C=0,1", {"modelo": "svc", "C": 0.1}),
    ("LinearSVC C=1", {"modelo": "svc", "C": 1.0}),
    ("+ quantidade (peso 0,3)", {"modelo": "svc", "C": 0.3, "peso_q": 0.3}),
    ("+ quantidade (peso 0,6)", {"modelo": "svc", "C": 0.3, "peso_q": 0.6}),
    ("+ quantidade (peso 1,0)", {"modelo": "svc", "C": 0.3, "peso_q": 1.0}),
    ("+ quantidade + treino sem a marca (v2)", V2),
    ("+ quantidade + treino sem a marca, C=0,2", {**V2, "C": 0.2}),
]


def escolher(n_folds: int = 5) -> list[dict]:
    """Validação cruzada agrupada por marca em treino + validação (o teste fica de fora)."""
    tr, va, _ = carregar_split()
    df = pd.concat([tr, va], ignore_index=True)
    folds = list(GroupKFold(n_splits=n_folds).split(df, df["categoria"], df["grupo"]))
    linhas = []
    for nome, cfg in GRADE:
        t0, accs, f1s = time.time(), [], []
        for a, b in folds:
            A, B = df.iloc[a], df.iloc[b]
            m = Classico(**cfg).fit(A["texto"], A["categoria"], A["brands"])
            p = m.predict(B["texto"])
            accs.append(accuracy_score(B["categoria"], p))
            f1s.append(f1_score(B["categoria"], p, average="macro"))
        linhas.append({"nome": nome, "config": cfg, "acuracia_media": float(np.mean(accs)),
                       "acuracia_por_fold": [float(x) for x in accs], "f1_macro_media": float(np.mean(f1s)),
                       "seg": round(time.time() - t0, 1)})
        print(f"{nome:45s} {100 * np.mean(accs):.2f}%  F1 {100 * np.mean(f1s):.2f}%  {linhas[-1]['seg']}s", flush=True)
    (RAIZ / "reports" / "classico_cv.json").write_text(json.dumps(
        {"folds": n_folds, "itens": len(df), "agrupado_por": "marca", "linhas": linhas}, indent=1, ensure_ascii=False))
    return linhas


def latencias(m: Classico, textos) -> tuple[float, float]:
    t0 = time.time()
    m.proba(textos)
    lote = 1000 * (time.time() - t0) / len(textos)
    lat = []
    for s in list(textos)[:200]:
        t1 = time.perf_counter()
        m.predict([s])
        lat.append(time.perf_counter() - t1)
    return lote, 1000 * float(np.median(lat))


def main():
    tr, va, te = carregar_split()
    rotulos_pt = json.loads((SPLIT / "categorias.json").read_text())["nomes"]
    t0 = time.time()
    m = Classico(**V2).fit(tr["texto"], tr["categoria"], tr["brands"])
    t_treino = time.time() - t0
    perda, T = m.calibrar(va["texto"], va["categoria"])
    pva, pte = m.proba(va["texto"]), m.proba(te["texto"])
    lote, um = latencias(m, te["texto"])
    SAIDA_PRED.mkdir(parents=True, exist_ok=True)
    pred = m.classes_[pte.argmax(1)]
    pd.DataFrame({"id": te["id"], "pred": pred, "confianca": pte.max(1).round(4)}).to_csv(SAIDA_PRED / "classico_v2.csv", index=False)
    probs = pd.DataFrame(np.vstack([pva, pte]).round(5), columns=list(m.classes_))
    probs.insert(0, "id", list(va["id"]) + list(te["id"]))
    probs.insert(0, "parte", ["validacao"] * len(va) + ["teste"] * len(te))
    probs.to_parquet(SAIDA_PRED / "probs_classico_v2.parquet", index=False)
    modelo = m.exportar(WEB, rotulos_pt)
    info = {
        "versao": 2, "config": V2, "temperatura": T, "log_loss_validacao": perda,
        "validacao": metricas(va["categoria"], m.classes_[pva.argmax(1)]), "teste": metricas(te["categoria"], pred),
        "treino_seg": round(t_treino, 1), "ms_por_item_lote": lote, "ms_por_item_um_a_um_mediana": um,
        "n_atributos": modelo["n_atributos"], "tamanho_json_bytes": WEB.stat().st_size,
    }
    # o que a quantidade traz: o mesmo v2 sem o bloco da quantidade (só para comparar; não escolhe nada)
    sem_q = Classico(**{**V2, "peso_q": 0.0}).fit(tr["texto"], tr["categoria"], tr["brands"])
    p_sem_q = sem_q.predict(te["texto"])
    pd.DataFrame({"id": te["id"], "pred": p_sem_q}).to_csv(SAIDA_PRED / "classico_v2_sem_quantidade.csv", index=False)
    info["teste_sem_quantidade"] = metricas(te["categoria"], p_sem_q)
    (RAIZ / "reports" / "classico_v2.json").write_text(json.dumps(info, indent=1, ensure_ascii=False))
    print(json.dumps(info, indent=1, ensure_ascii=False))


def main_v1():
    """O v1 como foi medido de manhã: regressão logística C=3, só texto (escolhida na validação)."""
    tr, _, te = carregar_split()
    m = Classico(modelo="lr", C=3.0).fit(tr["texto"], tr["categoria"])
    pte = m.clf.predict_proba(m._x(list(te["texto"])))
    pred = m.classes_[pte.argmax(1)]
    pd.DataFrame({"id": te["id"], "pred": pred, "confianca": pte.max(1).round(4)}).to_csv(SAIDA_PRED / "tfidf.csv", index=False)
    print("v1 no teste:", metricas(te["categoria"], pred))


def vazamento():
    """Mesmo modelo v1 e mesma configuração num split ALEATÓRIO (marca nos dois lados): mostra quanto o número
    fica inflado quando o teste tem marcas que o modelo já viu."""
    d = RAIZ / "data" / "split_aleatorio"
    tr, te = pd.read_parquet(d / "treino_validacao.parquet"), pd.read_parquet(d / "teste.parquet")
    # mesmo tamanho de treino do split por marca, para comparar só o efeito da marca
    n = len(pd.read_parquet(SPLIT / "treino.parquet"))
    tr = tr.sample(n=n, random_state=42)
    m = Classico(modelo="lr", C=3.0).fit(tr["texto"], tr["categoria"])
    r = {**metricas(te["categoria"], m.predict(te["texto"])), "n_treino": len(tr), "n_teste": len(te),
         "marcas_do_teste_vistas_no_treino": float(te["grupo"].isin(set(tr["grupo"])).mean())}
    (RAIZ / "reports" / "vazamento.json").write_text(json.dumps(r, indent=1))
    print("split aleatório:", r)


if __name__ == "__main__":
    import sys

    if "--escolher" in sys.argv:
        escolher()
    elif "--v1" in sys.argv:
        main_v1()
    elif "--vazamento" in sys.argv:
        vazamento()
    else:
        main()
