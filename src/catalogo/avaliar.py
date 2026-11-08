"""Mede todos os caminhos no MESMO teste (1.587 produtos), com o mesmo código, e escreve os relatórios e os dados
da página.

Dois números de acerto para cada caminho:
- **original**: contra a categoria do Open Food Facts, como veio (o número principal, comparável com o de manhã);
- **revisado**: contra `reports/revisao_teste.csv`. Revisamos, produto por produto e olhando só o nome, os 673
  produtos do teste em que pelo menos um dos 3 caminhos do v1 (clássico v1, LoRA v1, 7 B) errou. Cada um ficou como
  "rótulo certo", "rótulo errado" (com a categoria certa) ou "ambíguo" (vale mais de uma). A revisão foi fechada
  ANTES de medir os modelos v2 no teste. Os 914 produtos em que os três acertaram não foram revistos.

Entradas: data/split/teste.parquet, reports/predicoes/*.csv, reports/kaggle/ (v1), reports/kaggle-v2/ e reports/kaggle-v2b/ (v2),
reports/combinacao.json, reports/revisao_teste.csv.
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
KV2S = [RAIZ / "reports" / "kaggle-v2", RAIZ / "reports" / "kaggle-v2b", RAIZ / "reports" / "kaggle-v2c"]  # rodadas da tarde
DOCS = RAIZ / "docs" / "dados"
SEED = 42
CHIPS: list[str] = ["Leite Condensado Integral Moça 395g", "Leite Nestlé 34 g", "Doritos Sabor Queso 90g",
                     "Chocapic Nestlé 210 g", "Ristretto Nestlé 104 g", "Quilmes Cerveza Argentina Clásica 710 ml"]

# (coluna, versão, nome curto em português, nome em inglês)
CAMINHOS = [
    ("zero_shot_1_5b", "v1", "IA sem treino (Qwen 1,5 B)", "AI, no training (Qwen 1.5B)"),
    ("zero_shot_7b_4bit", "v1", "IA maior sem treino (Qwen 7 B)", "Bigger AI, no training (Qwen 7B)"),
    ("tfidf", "v1", "Clássico v1 (TF-IDF + regressão logística)", "Classic v1 (TF-IDF + logistic regression)"),
    ("lora_1_5b", "v1", "IA ajustada v1 (LoRA que escreve a resposta)", "Tuned AI v1 (LoRA writing the answer)"),
    ("classico_v2", "v2", "Clássico v2 (+ quantidade)", "Classic v2 (+ quantity)"),
    ("bertimbau_q", "v2", "BERTimbau ajustado (+ quantidade)", "Fine-tuned BERTimbau (+ quantity)"),
    ("qwen15_lora_q", "v2", "IA ajustada v2 (LoRA classificador + quantidade)", "Tuned AI v2 (LoRA classifier + quantity)"),
    ("qwen15_lora_q5m", "v2", "IA ajustada v2, 2ª rodada (5 épocas, sem a marca; não escolhida)", "Tuned AI v2, 2nd run (5 epochs, no brand; not chosen)"),
    ("lora_v1_escrita", "v2", "IA v1 de novo, escrevendo, com confiança (LoRA fundido)", "AI v1 again, writing, with confidence (merged LoRA)"),
    ("lora_v1_pontos", "v2", "IA v1 de novo, pontuando as 41 categorias", "AI v1 again, scoring all 41 categories"),
    ("juntos_ia_v2", "v2", "1ª combinação: clássico v2 + IA v2 + BERTimbau", "1st combination: classic v2 + AI v2 + BERTimbau"),
    ("juntos", "v2", "Juntos: clássico v2 + IA", "Together: classic v2 + AI"),
    ("cascata", "v2", "Cascata: clássico primeiro, IA só na dúvida", "Cascade: classic first, AI only when unsure"),
    ("cascata_ia_v2", "v2", "Cascata barata: clássico primeiro, IA classificadora só na dúvida", "Cheap cascade: classic first, classifier AI only when unsure"),
]


def bootstrap(acerto: np.ndarray, y=None, p=None, n: int = 2000, seed: int = SEED) -> dict:
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(acerto), size=(n, len(acerto)))
    acc = acerto[idx].mean(axis=1)
    out = {"acuracia_ic95": [float(np.percentile(acc, 2.5)), float(np.percentile(acc, 97.5))]}
    if y is not None:
        f1 = np.array([f1_score(y[i], p[i], average="macro", zero_division=0) for i in idx[:400]])
        out["f1_macro_ic95"] = [float(np.percentile(f1, 2.5)), float(np.percentile(f1, 97.5))]
    return out


def diferenca(a_ok: np.ndarray, b_ok: np.ndarray, n: int = 2000, seed: int = SEED) -> list[float]:
    """IC 95% da diferença de acerto (a - b), bootstrap pareado (mesmos itens nos dois)."""
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(a_ok), size=(n, len(a_ok)))
    d = a_ok[idx].mean(axis=1) - b_ok[idx].mean(axis=1)
    return [float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))]


def fora_da_lista(respostas: pd.Series, nomes: dict) -> dict:
    """Respostas que não são o nome de uma categoria (só nos caminhos que escrevem a resposta)."""
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
    return {"fora": n_fora, "cortadas_validas": n_cortada, "total": len(respostas)}


def carregar() -> tuple[pd.DataFrame, dict]:
    te = pd.read_parquet(SPLIT / "teste.parquet")
    cat = json.loads((SPLIT / "categorias.json").read_text())
    df = te[["id", "texto", "categoria", "grupo"]].copy()
    df = df.merge(pd.read_csv(PRED / "tfidf.csv")[["id", "pred"]].rename(columns={"pred": "tfidf"}), on="id", how="left")
    if (PRED / "kaggle.csv").exists():
        df = df.merge(pd.read_csv(PRED / "kaggle.csv"), on="id", how="left")
    for nome in ("classico_v2", "juntos", "cascata", "classico_v2_sem_quantidade", "juntos_ia_v2", "cascata_ia_v2"):
        if (PRED / f"{nome}.csv").exists():
            df = df.merge(pd.read_csv(PRED / f"{nome}.csv")[["id", "pred"]].rename(columns={"pred": nome}), on="id", how="left")
    for arq in sorted(a for pasta in KV2S for a in pasta.glob("probs_*.parquet")):
        nome = arq.stem.removeprefix("probs_")
        d = pd.read_parquet(arq)
        d = d[d["parte"] == "teste"].set_index("id")[cat["chaves"]]
        df = df.merge(pd.DataFrame({"id": d.index, nome: np.array(cat["chaves"])[d.to_numpy().argmax(1)]}), on="id", how="left")
    rev = pd.read_csv(RAIZ / "reports" / "revisao_teste.csv")
    df = df.merge(rev[["id", "situacao", "aceitas"]], on="id", how="left")
    df["situacao"] = df["situacao"].fillna("nao_revisto")
    df["aceitas"] = [a.split("|") if isinstance(a, str) else [c] for a, c in zip(df["aceitas"], df["categoria"])]
    return df, cat


def tempos(col: str, json_v1: dict, kag: dict, kv2: dict, comb: dict) -> dict:
    """Tempo por produto (lote e um por vez) e onde roda, de cada caminho."""
    if col == "tfidf":
        return {"ms_lote": json_v1["ms_por_item_lote"], "ms_um": json_v1["ms_por_item_um_a_um_mediana"], "hardware": "cpu"}
    if col == "classico_v2":
        c = json.loads((RAIZ / "reports" / "classico_v2.json").read_text())
        return {"ms_lote": c["ms_por_item_lote"], "ms_um": c["ms_por_item_um_a_um_mediana"], "hardware": "cpu"}
    if col in kag:
        return {"ms_lote": kag[col]["ms_por_item_lote"], "ms_um": kag[col]["ms_um_a_um_mediana"], "hardware": "gpu"}
    if col in kv2:
        k = kv2[col]
        if k.get("lora") and "ms_um_a_um_gpu_adapter" not in k and "qwen15_lora_q5m" in kv2:
            # 1ª rodada: medida com o adapter separado. Em produção o LoRA é fundido nos pesos; o tempo fundido foi
            # medido na 2ª rodada (mesmo modelo, mesmo tamanho, mesma entrada: os valores dos pesos não mudam o tempo)
            f = kv2["qwen15_lora_q5m"]
            return {"ms_lote": f["ms_por_item_lote_gpu"], "ms_um": f["ms_um_a_um_gpu"], "ms_um_cpu": f.get("ms_um_a_um_cpu"),
                    "ms_lote_adapter": k["ms_por_item_lote_gpu"], "ms_um_adapter": k["ms_um_a_um_gpu"], "tempo_fundido_da_2a_rodada": True,
                    "hardware": "gpu", "min_treino": k["min_treino"], "epoca": k["epoca_escolhida"], "epocas": k["epocas"],
                    "parametros_treinaveis": k["parametros_treinaveis"], "parametros_total": k["parametros_total"]}
        return {"ms_lote": k["ms_por_item_lote_gpu"], "ms_um": k["ms_um_a_um_gpu"], "ms_um_cpu": k.get("ms_um_a_um_cpu"),
                "hardware": "gpu", "min_treino": k.get("min_treino"), "epoca": k.get("epoca_escolhida"), "epocas": k.get("epocas"),
                "parametros_treinaveis": k.get("parametros_treinaveis"), "parametros_total": k.get("parametros_total")}
    if col in ("juntos_ia_v2", "cascata_ia_v2") and (RAIZ / "reports" / "combinacao_ia_v2.json").exists():
        c1 = json.loads((RAIZ / "reports" / "combinacao_ia_v2.json").read_text())
        partes = [tempos(m, json_v1, kag, kv2, comb) for m in c1["escolhida"]["modelos"]]
        lote, um = sum(p["ms_lote"] for p in partes), sum(p["ms_um"] for p in partes)
        if col == "cascata_ia_v2":
            f, c = c1["cascata"]["vai_para_ia_teste"], partes[0]
            return {"ms_lote": c["ms_lote"] + f * (lote - c["ms_lote"]), "ms_um": c["ms_um"] + f * (um - c["ms_um"]),
                    "hardware": "gpu", "fracao_gpu": f, "limite": c1["cascata"]["limite"],
                    "acuracia_quando_classico_seguro": c1["cascata"]["acuracia_teste_so_classico_quando_confiante"]}
        return {"ms_lote": lote, "ms_um": um, "hardware": "gpu"}
    if col in ("juntos", "cascata") and comb:
        partes = [tempos(m, json_v1, kag, kv2, comb) for m in comb["escolhida"]["modelos"]]
        lote, um = sum(p["ms_lote"] for p in partes), sum(p["ms_um"] for p in partes)
        if col == "cascata":
            f = comb["cascata"]["vai_para_ia_teste"]
            c = partes[0]
            return {"ms_lote": c["ms_lote"] + f * (lote - c["ms_lote"]), "ms_um": c["ms_um"] + f * (um - c["ms_um"]),
                    "hardware": "gpu", "fracao_gpu": f}
        return {"ms_lote": lote, "ms_um": um, "hardware": "gpu"}
    return {}


def main():
    df, cat = carregar()
    nomes, chaves = cat["nomes"], cat["chaves"]
    json_v1 = json.loads((RAIZ / "reports" / "classico.json").read_text())
    kag = json.loads((KAGGLE / "resultados_kaggle.json").read_text()) if (KAGGLE / "resultados_kaggle.json").exists() else {}
    kv2 = {}
    for pasta in KV2S:
        if (pasta / "resultados_v2.json").exists():
            kv2.update(json.loads((pasta / "resultados_v2.json").read_text())["modelos"])
    kv2 = {k: v for k, v in kv2.items() if "pulado" not in v}
    comb = json.loads((RAIZ / "reports" / "combinacao.json").read_text()) if (RAIZ / "reports" / "combinacao.json").exists() else {}
    dados = json.loads((RAIZ / "reports" / "dados.json").read_text())
    y = df["categoria"].to_numpy()
    aceitas = df["aceitas"].tolist()
    presentes = [c for c in CAMINHOS if c[0] in df.columns and df[c[0]].notna().all()]
    res = {"n_teste": len(df), "categorias": len(chaves), "caminhos": {}}
    ok, okr = {}, {}
    for col, versao, pt, en in presentes:
        p = df[col].to_numpy()
        ok[col] = (p == y).astype(float)
        okr[col] = np.array([a in s for a, s in zip(p, aceitas)], dtype=float)
        r = {"nome": pt, "nome_en": en, "versao": versao, "acuracia": float(ok[col].mean()),
             "f1_macro": float(f1_score(y, p, average="macro", zero_division=0)), **bootstrap(ok[col], y, p),
             "acuracia_revisada": float(okr[col].mean()),
             "acuracia_revisada_ic95": bootstrap(okr[col])["acuracia_ic95"], **tempos(col, json_v1, kag, kv2, comb)}
        if col + "_resposta" in df.columns:
            r["fora_da_lista"] = fora_da_lista(df[col + "_resposta"], nomes)
        if col == "lora_1_5b" and "lora_treino" in kag:
            r["treino"] = {kk: v for kk, v in kag["lora_treino"].items() if kk != "historico"}
        # erros contra o rótulo original, separados pela revisão
        erro = ok[col] == 0
        r["erros"] = {"total": int(erro.sum()),
                      "rotulo_errado": int((erro & (df["situacao"] == "rotulo_errado").to_numpy()).sum()),
                      "ambiguo": int((erro & (df["situacao"] == "ambiguo").to_numpy()).sum()),
                      "aceitos_na_revisao": int((erro & (okr[col] == 1)).sum())}
        prf = precision_recall_fscore_support(y, p, labels=chaves, zero_division=0)
        r["por_categoria"] = {c: {"precisao": float(prf[0][i]), "recall": float(prf[1][i]), "f1": float(prf[2][i]),
                                  "n": int(prf[3][i])} for i, c in enumerate(chaves)}
        conf = pd.Series(list(zip(y[y != p], p[y != p]))).value_counts().head(8)
        r["confusoes"] = [{"certo": nomes[a], "previsto": nomes[b], "vezes": int(v)} for (a, b), v in conf.items()]
        res["caminhos"][col] = r

    def par(a, b, chave):
        if a in ok and b in ok:
            res[chave] = {"original": diferenca(ok[a], ok[b]), "revisado": diferenca(okr[a], okr[b]),
                          "pontos": float(ok[a].mean() - ok[b].mean()), "pontos_revisado": float(okr[a].mean() - okr[b].mean())}

    par("lora_1_5b", "tfidf", "lora_menos_tfidf")
    par("lora_1_5b", "zero_shot_1_5b", "lora_menos_zero_shot")
    par("classico_v2", "tfidf", "classico_v2_menos_v1")
    ia = comb.get("ia_principal", "qwen15_lora_q")
    res["ia_principal"], res["ia_da_combinacao"] = ia, comb.get("ia_da_combinacao", ia)
    par(ia, "lora_1_5b", "lora_v2_menos_v1")
    par(ia, "classico_v2", "lora_v2_menos_classico_v2")
    par("juntos", "juntos_ia_v2", "juntos_menos_1a_combinacao")
    par("cascata_ia_v2", "classico_v2", "cascata_barata_menos_classico_v2")
    par("cascata", "cascata_ia_v2", "cascata_menos_cascata_barata")
    par("lora_v1_escrita", "classico_v2", "lora_v1_menos_classico_v2")
    par("juntos", "classico_v2", "juntos_menos_classico_v2")
    par("juntos", "lora_1_5b", "juntos_menos_lora_v1")
    par("cascata", "classico_v2", "cascata_menos_classico_v2")
    if "lora_1_5b" in df and "tfidf" in df:
        a, b = df["lora_1_5b"].to_numpy(), df["tfidf"].to_numpy()
        j = a == b
        res["quando_concordam_v1"] = {"cobertura": float(j.mean()), "acuracia": float((a[j] == y[j]).mean())}
    if comb:
        res["combinacao"] = comb
    # o que a quantidade trouxe (o mesmo modelo com e sem ela)
    q = {}
    if "classico_v2_sem_quantidade" in df and "classico_v2" in ok:
        cv = json.loads((RAIZ / "reports" / "classico_cv.json").read_text())["linhas"]
        cvd = {x["nome"]: x["acuracia_media"] for x in cv}
        sem = (df["classico_v2_sem_quantidade"] == df["categoria"]).to_numpy().astype(float)
        q["classico"] = {"teste_com": float(ok["classico_v2"].mean()), "teste_sem": float(sem.mean()),
                         "mudaram": int((df["classico_v2"] != df["classico_v2_sem_quantidade"]).sum()),
                         "cv_com": cvd.get("+ quantidade (peso 0,6)"), "cv_sem": cvd.get("LinearSVC, só texto")}
    if "bertimbau_sem_q" in df and "bertimbau_q" in ok and "bertimbau_sem_q" in kv2:
        sem = (df["bertimbau_sem_q"] == df["categoria"]).to_numpy().astype(float)
        q["bertimbau"] = {"teste_com": float(ok["bertimbau_q"].mean()), "teste_sem": float(sem.mean()),
                          "com_menos_sem_ic95": diferenca(ok["bertimbau_q"], sem),
                          "validacao_com": kv2["bertimbau_q"]["acerto_validacao"], "validacao_sem": kv2["bertimbau_sem_q"]["acerto_validacao"]}
    res["quantidade"] = q
    # revisão do teste
    rev = pd.read_csv(RAIZ / "reports" / "revisao_teste.csv")
    por_cat = rev[rev["situacao"] != "rotulo_certo"].groupby(["rotulo_original", "situacao"]).size().unstack(fill_value=0)
    res["revisao"] = {"revistos": len(rev), "nao_revistos": len(df) - len(rev),
                      **{k: int(v) for k, v in rev["situacao"].value_counts().items()},
                      "por_categoria": {c: {k: int(v) for k, v in linha.items()} for c, linha in por_cat.iterrows()}}
    vaz = RAIZ / "reports" / "vazamento.json"
    if vaz.exists():
        res["split_aleatorio_tfidf"] = json.loads(vaz.read_text())
    res["dados"] = {k: v for k, v in dados.items() if k != "por_categoria"}
    (RAIZ / "reports" / "resultados.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))

    # dados da página: resumo + todos os produtos do teste com a resposta de cada caminho
    DOCS.mkdir(parents=True, exist_ok=True)
    pagina = dict(res)
    pagina["nomes"], pagina["nomes_en"] = nomes, cat["nomes_en"]
    pagina["chips"] = [c for c in CHIPS if c in set(df["texto"])]
    (DOCS / "resultados.json").write_text(json.dumps(pagina, ensure_ascii=False, separators=(",", ":")))
    cols = [c[0] for c in presentes]
    extras = [c for c in ("zero_shot_1_5b_resposta",) if c in df.columns]
    ex = df[["texto", "categoria"] + cols + extras].rename(columns={"categoria": "certo"}).copy()
    ex["aceitas"] = ["|".join(a) for a in aceitas]
    ex["situacao"] = df["situacao"]
    (DOCS / "exemplos.json").write_text(json.dumps({"colunas": list(ex.columns), "linhas": ex.values.tolist()},
                                                   ensure_ascii=False, separators=(",", ":")))
    escrever_md(res, nomes)
    for c, r in res["caminhos"].items():
        print(f"{c:22s} {100 * r['acuracia']:.1f}% (revisado {100 * r['acuracia_revisada']:.1f}%)  F1 {100 * r['f1_macro']:.1f}%")


def pct(x, d=1):
    return f"{100 * x:.{d}f}%".replace(".", ",")


def ms(x):
    if x is None:
        return ""
    return (f"{x:.2f}" if x < 1 else f"{x:.0f}").replace(".", ",") + " ms"


def escrever_md(res, nomes):
    rv = res["revisao"]
    L = ["# Resultados (gerado por `python -m catalogo.avaliar`)", "",
         f"Teste: **{res['n_teste']:,} produtos** do Brasil, **{res['categorias']} categorias**, marcas que não aparecem no treino.".replace(",", "."),
         ("Acerto **original** = contra a categoria do Open Food Facts como veio. **Revisado** = contra a revisão do teste "
          f"(`reports/revisao_teste.csv`: {rv['revistos']} produtos revistos, {rv.get('rotulo_errado', 0)} rótulos errados, "
          f"{rv.get('ambiguo', 0)} ambíguos; os outros {rv['nao_revistos']} ficam com o rótulo original)."), "",
         "| Caminho | Versão | Acerto original (IC 95%) | Acerto revisado | F1 macro | Tempo por produto (lote / um por vez) | Onde |",
         "|---|---|---|---|---|---|---|"]
    for r in res["caminhos"].values():
        ic = r["acuracia_ic95"]
        onde = "CPU ou navegador" if r.get("hardware") == "cpu" else "GPU T4 (Kaggle grátis)"
        L.append(f"| {r['nome']} | {r['versao']} | **{pct(r['acuracia'])}** ({pct(ic[0])} a {pct(ic[1])}) | {pct(r['acuracia_revisada'])} | "
                 f"{pct(r['f1_macro'])} | {ms(r.get('ms_lote'))} / {ms(r.get('ms_um'))} | {onde} |")
    L.append("")
    for chave, txt in (("classico_v2_menos_v1", "Clássico v2 menos v1"), ("lora_v2_menos_v1", "IA ajustada v2 menos v1"),
                       ("lora_v2_menos_classico_v2", "IA ajustada v2 menos clássico v2"), ("juntos_menos_classico_v2", "Juntos menos clássico v2"),
                       ("juntos_menos_lora_v1", "Juntos menos IA ajustada v1"), ("cascata_menos_classico_v2", "Cascata menos clássico v2"),
                       ("lora_menos_tfidf", "IA ajustada v1 menos clássico v1")):
        if chave in res:
            a, b = res[chave]["original"]
            L.append(f"- {txt}: {pct(res[chave]['pontos'])} pontos (faixa de 95%: {pct(a)} a {pct(b)}).")
    if "combinacao" in res:
        cb = res["combinacao"]
        L.append(f"- Combinação escolhida na validação: {' + '.join(cb['escolhida']['modelos'])}, pesos {cb['escolhida']['pesos']}.")
        ca = cb["cascata"]
        L.append(f"- Cascata: o clássico responde sozinho quando a confiança dele passa de {pct(ca['limite'], 0)}; no teste, "
                 f"{pct(ca['vai_para_ia_teste'], 0)} dos produtos foram para a IA e o acerto foi {pct(ca['acuracia_teste'])}.")
    q = res.get("quantidade", {})
    if "classico" in q:
        L.append(f"- Quantidade no clássico: teste {pct(q['classico']['teste_sem'])} sem e {pct(q['classico']['teste_com'])} com; "
                 f"validação cruzada {pct(q['classico']['cv_sem'])} sem e {pct(q['classico']['cv_com'])} com.")
    if "bertimbau" in q:
        b = q["bertimbau"]
        L.append(f"- Quantidade no BERTimbau: teste {pct(b['teste_sem'])} sem e {pct(b['teste_com'])} com (faixa da diferença "
                 f"{pct(b['com_menos_sem_ic95'][0])} a {pct(b['com_menos_sem_ic95'][1])}).")
    L += ["", "## Erros de cada caminho e a revisão do teste", "",
          "| Caminho | Erros (original) | Rótulo errado | Ambíguo | Aceitos na revisão |", "|---|---|---|---|---|"]
    for r in res["caminhos"].values():
        e = r["erros"]
        L.append(f"| {r['nome']} | {e['total']} | {e['rotulo_errado']} | {e['ambiguo']} | {e['aceitos_na_revisao']} |")
    mostrar = [c for c in ("tfidf", "lora_1_5b", "classico_v2", res.get("ia_principal"), "juntos", "cascata") if c in res["caminhos"]]
    rpc = rv["por_categoria"]
    L += ["", "## F1 por categoria (original)", "",
          "| Categoria | n | " + " | ".join(res["caminhos"][c]["nome"] for c in mostrar) + " | Rótulos revistos (errado / ambíguo) |",
          "|---|---|" + "---|" * len(mostrar) + "---|"]
    base = res["caminhos"][mostrar[0]]["por_categoria"]
    for k in sorted(nomes, key=lambda k: -base[k]["n"]):
        x = rpc.get(k, {})
        L.append(f"| {nomes[k]} | {base[k]['n']} | " + " | ".join(pct(res["caminhos"][c]["por_categoria"][k]["f1"]) for c in mostrar) +
                 f" | {x.get('rotulo_errado', 0)} / {x.get('ambiguo', 0)} |")
    for c in mostrar:
        r = res["caminhos"][c]
        L += ["", f"## Confusões mais comuns: {r['nome']}", ""]
        L += [f"- {x['certo']} → {x['previsto']}: {x['vezes']}" for x in r["confusoes"]]
    (RAIZ / "reports" / "resultados.md").write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
