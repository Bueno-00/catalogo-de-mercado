"""Mede os 3 caminhos no MESMO teste, com o mesmo código, e escreve os relatórios e os dados da página.

Entradas: data/split/teste.parquet, reports/predicoes/tfidf.csv (do `classico.py`) e
reports/predicoes/kaggle.csv + reports/kaggle/resultados_kaggle.json (baixados do notebook do Kaggle).
Saídas: reports/resultados.json, reports/resultados.md, docs/dados/resultados.json, docs/dados/exemplos.json.

Uso:  python -m catalogo.avaliar
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, precision_recall_fscore_support

RAIZ = Path(__file__).resolve().parents[2]
SPLIT = RAIZ / "data" / "split"
PRED = RAIZ / "reports" / "predicoes"
KAGGLE = RAIZ / "reports" / "kaggle"
DOCS = RAIZ / "docs" / "dados"
SEED = 42
# exemplos de botão na página (produtos do teste), escolhidos olhando os resultados
CHIPS: list[str] = ["Leite Condensado Integral Moça 395g", "Doritos Sabor Queso 90g", "KitKat Nestlé 45g",
                     "Chocapic Nestlé 210 g", "Ristretto Nestlé 104 g"]

CAMINHOS = [  # (coluna, nome curto, descrição)
    ("zero_shot_1_5b", "IA sem treino (1,5 B)", "Qwen2.5-1.5B-Instruct, zero-shot, lista de categorias no prompt"),
    ("zero_shot_7b_4bit", "IA sem treino (7 B)", "Qwen2.5-7B-Instruct em 4 bits, zero-shot (extra)"),
    ("tfidf", "Clássico (TF-IDF)", "TF-IDF de palavras e pedaços + regressão logística, CPU"),
    ("lora_1_5b", "IA ajustada (LoRA)", "Qwen2.5-1.5B-Instruct + adapter LoRA treinado no treino"),
]


def bootstrap(y: np.ndarray, p: np.ndarray, n: int = 2000, seed: int = SEED) -> dict:
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(y), size=(n, len(y)))
    acc = (y[idx] == p[idx]).mean(axis=1)
    f1 = np.array([f1_score(y[i], p[i], average="macro", zero_division=0) for i in idx[:400]])
    return {"acuracia_ic95": [float(np.percentile(acc, 2.5)), float(np.percentile(acc, 97.5))],
            "f1_macro_ic95": [float(np.percentile(f1, 2.5)), float(np.percentile(f1, 97.5))]}


def fora_da_lista(respostas: pd.Series, nomes: dict) -> dict:
    """Respostas que não são o nome de uma categoria. Resposta cortada pelo limite de tokens (prefixo de um nome
    com 12+ letras) conta como válida, porque é ligada à categoria certa pela semelhança."""
    validos = [v.lower() for v in nomes.values()]
    n_fora = n_cortada = 0
    for r in respostas.fillna("").astype(str):
        x = r.strip().split("\n")[0].strip().strip(".:-* ").lower()
        if x in validos:
            continue
        if len(x) >= 12 and any(v.startswith(x) for v in validos):
            n_cortada += 1
            continue
        n_fora += 1
    return {"fora": n_fora, "cortadas_validas": n_cortada, "total": int(len(respostas))}


def diferenca(y, a, b, n: int = 2000, seed: int = SEED) -> list[float]:
    """IC 95% da diferença de acerto (a - b), bootstrap pareado (mesmos itens nos dois)."""
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(y), size=(n, len(y)))
    d = (y[idx] == a[idx]).mean(axis=1) - (y[idx] == b[idx]).mean(axis=1)
    return [float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))]


def carregar() -> tuple[pd.DataFrame, dict, dict]:
    te = pd.read_parquet(SPLIT / "teste.parquet")
    cat = json.loads((SPLIT / "categorias.json").read_text())
    df = te[["id", "texto", "categoria", "grupo"]].copy()
    tf = pd.read_csv(PRED / "tfidf.csv").rename(columns={"pred": "tfidf", "confianca": "tfidf_confianca"})
    df = df.merge(tf, on="id", how="left")
    kag = {}
    if (PRED / "kaggle.csv").exists():
        kp = pd.read_csv(PRED / "kaggle.csv")
        df = df.merge(kp, on="id", how="left")
        kag = json.loads((KAGGLE / "resultados_kaggle.json").read_text())
    return df, cat, kag


def main():
    df, cat, kag = carregar()
    classico = json.loads((RAIZ / "reports" / "classico.json").read_text())
    dados = json.loads((RAIZ / "reports" / "dados.json").read_text())
    y = df["categoria"].to_numpy()
    nomes = cat["nomes"]
    presentes = [c for c in CAMINHOS if c[0] in df.columns and df[c[0]].notna().all()]
    res = {"n_teste": len(df), "categorias": len(cat["chaves"]), "caminhos": {}}
    for col, curto, desc in presentes:
        p = df[col].to_numpy()
        r = {"nome": curto, "descricao": desc, "acuracia": float((y == p).mean()),
             "f1_macro": float(f1_score(y, p, average="macro", zero_division=0)), **bootstrap(y, p)}
        if col == "tfidf":
            r.update({"ms_por_item_lote_cpu": classico["ms_por_item_lote"],
                      "ms_um_a_um_cpu": classico["ms_por_item_um_a_um_mediana"], "treino_seg_cpu": classico["treino_seg"],
                      "custo": "CPU comum (ou o navegador); sem GPU"})
        elif col in kag:
            k = kag[col]
            r.update({"ms_por_item_lote_gpu": k["ms_por_item_lote"], "ms_um_a_um_gpu": k["ms_um_a_um_mediana"],
                      "lote": k["lote"], "fora_da_lista_bruto": k["fora_da_lista"],
                      "gpu_seg_por_1000": round(k["ms_por_item_lote"], 1),  # ms/item x 1000 itens / 1000 = s
                      "custo": "GPU T4 (grátis no Kaggle)"})
            if col == "lora_1_5b" and "lora_treino" in kag:
                r["treino"] = {kk: v for kk, v in kag["lora_treino"].items() if kk != "historico"}
                r["historico_treino"] = kag["lora_treino"]["historico"]
        if col + "_resposta" in df.columns:
            r["fora_da_lista"] = fora_da_lista(df[col + "_resposta"], nomes)
            r["fora_da_lista_kaggle"] = r.pop("fora_da_lista_bruto", None)
        res["caminhos"][col] = r
        prf = precision_recall_fscore_support(y, p, labels=cat["chaves"], zero_division=0)
        r["por_categoria"] = {c: {"precisao": float(prf[0][i]), "recall": float(prf[1][i]), "f1": float(prf[2][i]),
                                  "n": int(prf[3][i])} for i, c in enumerate(cat["chaves"])}
        conf = pd.Series(list(zip(y[y != p], p[y != p]))).value_counts().head(8)
        r["confusoes"] = [{"certo": nomes[a], "previsto": nomes[b], "vezes": int(v)} for (a, b), v in conf.items()]
    cols = [c[0] for c in presentes]
    if "lora_1_5b" in cols and "tfidf" in cols:
        a, b = df["lora_1_5b"].to_numpy(), df["tfidf"].to_numpy()
        res["lora_menos_tfidf_ic95"] = diferenca(y, a, b)
        juntos = a == b
        res["quando_concordam"] = {"cobertura": float(juntos.mean()), "acuracia": float((a[juntos] == y[juntos]).mean()),
                                   "acuracia_quando_discordam_lora": float((a[~juntos] == y[~juntos]).mean()),
                                   "acuracia_quando_discordam_tfidf": float((b[~juntos] == y[~juntos]).mean())}
    if "zero_shot_1_5b" in cols and "lora_1_5b" in cols:
        res["lora_menos_zero_shot_ic95"] = diferenca(y, df["lora_1_5b"].to_numpy(), df["zero_shot_1_5b"].to_numpy())
    # vazamento: o mesmo clássico num split aleatório (marca nos dois lados)
    vaz = RAIZ / "reports" / "vazamento.json"
    if vaz.exists():
        res["split_aleatorio_tfidf"] = json.loads(vaz.read_text())
    res["dados"] = {k: v for k, v in dados.items() if k != "por_categoria"}
    (RAIZ / "reports" / "resultados.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))

    # dados da página: resumo + todos os produtos do teste com a resposta de cada caminho
    DOCS.mkdir(parents=True, exist_ok=True)
    pagina = {k: v for k, v in res.items()}
    pagina["caminhos"] = {c: {kk: vv for kk, vv in r.items()} for c, r in res["caminhos"].items()}
    pagina["nomes"], pagina["nomes_en"] = nomes, cat["nomes_en"]
    pagina["chips"] = [c for c in CHIPS if c in set(df["texto"])]
    (DOCS / "resultados.json").write_text(json.dumps(pagina, ensure_ascii=False, separators=(",", ":")))
    extras = [c for c in ("zero_shot_1_5b_resposta",) if c in df.columns]
    ex = df[["texto", "categoria"] + cols + extras].rename(columns={"categoria": "certo"})
    (DOCS / "exemplos.json").write_text(json.dumps({"colunas": list(ex.columns), "linhas": ex.values.tolist()},
                                                   ensure_ascii=False, separators=(",", ":")))
    escrever_md(res, nomes, df, cols)
    print(json.dumps({c: {k: r[k] for k in ("acuracia", "f1_macro", "acuracia_ic95")} for c, r in res["caminhos"].items()},
                     indent=1, ensure_ascii=False))
    for k in ("lora_menos_tfidf_ic95", "lora_menos_zero_shot_ic95", "quando_concordam", "split_aleatorio_tfidf"):
        if k in res:
            print(k, res[k])


def pct(x):
    return f"{100 * x:.1f}%".replace(".", ",")


def escrever_md(res, nomes, df, cols):
    L = ["# Resultados (gerado por `python -m catalogo.avaliar`)", "",
         f"Teste: **{res['n_teste']:,} produtos** do Brasil, **{res['categorias']} categorias**, marcas que não aparecem no treino.".replace(",", "."), "",
         "| Caminho | Acerto | IC 95% | F1 macro | Tempo por produto | Onde roda |", "|---|---|---|---|---|---|"]
    for c, r in res["caminhos"].items():
        ic = r["acuracia_ic95"]
        if c == "tfidf":
            t = f"{r['ms_por_item_lote_cpu']:.2f} ms (lote) / {r['ms_um_a_um_cpu']:.0f} ms (um a um)"
        else:
            t = f"{r.get('ms_por_item_lote_gpu', 0):.0f} ms (lote) / {r.get('ms_um_a_um_gpu', 0):.0f} ms (um a um)"
        L.append(f"| {r['nome']} | **{pct(r['acuracia'])}** | {pct(ic[0])} a {pct(ic[1])} | {pct(r['f1_macro'])} | {t} | {r['custo']} |")
    L.append("")
    if "lora_menos_tfidf_ic95" in res:
        a, b = res["lora_menos_tfidf_ic95"]
        L.append(f"- LoRA menos TF-IDF (bootstrap pareado): {pct(a)} a {pct(b)} pontos.")
    if "lora_menos_zero_shot_ic95" in res:
        a, b = res["lora_menos_zero_shot_ic95"]
        L.append(f"- LoRA menos zero-shot do mesmo modelo: {pct(a)} a {pct(b)} pontos.")
    if "quando_concordam" in res:
        q = res["quando_concordam"]
        L.append(f"- Quando LoRA e TF-IDF dão a mesma resposta ({pct(q['cobertura'])} dos produtos), o acerto é {pct(q['acuracia'])}.")
    if "split_aleatorio_tfidf" in res:
        s = res["split_aleatorio_tfidf"]
        L.append(f"- O mesmo TF-IDF num split aleatório (marca nos dois lados): {pct(s['acuracia'])} de acerto, contra {pct(res['caminhos']['tfidf']['acuracia'])} no split por marca.")
    L += ["", "## F1 por categoria", "", "| Categoria | n | " + " | ".join(res["caminhos"][c]["nome"] for c in res["caminhos"]) + " |",
          "|---|---|" + "---|" * len(res["caminhos"])]
    for k in sorted(nomes, key=lambda k: -next(iter(res["caminhos"].values()))["por_categoria"][k]["n"]):
        n = next(iter(res["caminhos"].values()))["por_categoria"][k]["n"]
        L.append(f"| {nomes[k]} | {n} | " + " | ".join(pct(res["caminhos"][c]["por_categoria"][k]["f1"]) for c in res["caminhos"]) + " |")
    for c, r in res["caminhos"].items():
        L += ["", f"## Confusões mais comuns: {r['nome']}", ""]
        L += [f"- {x['certo']} → {x['previsto']}: {x['vezes']}" for x in r["confusoes"]]
    (RAIZ / "reports" / "resultados.md").write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
