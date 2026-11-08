"""Junta o clássico v2 com as IAs ajustadas v2, e monta a cascata (o caminho recomendado para produção).

Tudo é escolhido na VALIDAÇÃO (794 produtos, marcas fora do treino e do teste). O teste só é lido no fim, uma
vez, para medir o que foi escolhido.

1. Juntos: média geométrica ponderada das probabilidades (soma dos log com pesos). Testamos algumas combinações e
   uma grade de pesos (passo 0,1); fica a de maior acerto na validação. Se outra combinação ficar a até 0,3 ponto
   dela, conta como empate e fica a que gasta menos GPU.
2. Cascata: o clássico responde sozinho quando a confiança dele passa de um limite; abaixo do limite, o produto vai
   para a combinação com a IA. O limite é o menor que, na validação, fica a até 0,5 ponto do acerto da combinação
   inteira. Resultado: quase o mesmo acerto mandando só uma parte dos produtos para a GPU.

Entradas: reports/predicoes/probs_classico_v2.parquet e reports/kaggle-v2*/probs_*.parquet.
Saídas: reports/combinacao.json, reports/predicoes/juntos.csv, reports/predicoes/cascata.csv.

Uso:  python -m catalogo.combinar
"""

from __future__ import annotations

import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
SPLIT = RAIZ / "data" / "split"
PRED = RAIZ / "reports" / "predicoes"
KV2S = [RAIZ / "reports" / "kaggle-v2", RAIZ / "reports" / "kaggle-v2b", RAIZ / "reports" / "kaggle-v2c"]  # rodadas da tarde
QWEN = ["qwen15_lora_q5m", "qwen15_lora_q"]  # as duas rodadas da IA ajustada v2; fica a de maior acerto na validação
V1 = ["lora_v1_escrita", "lora_v1_pontos"]  # a IA da manhã respondendo de novo, agora com confiança (v2c)
IAS = QWEN + ["bertimbau_q"] + V1
EMPATE = 0.003  # combinações a até 0,3 ponto da melhor na validação contam como empate: fica a mais barata
FOLGA = 0.005  # a cascata pode perder até 0,5 ponto na validação em troca de mandar menos produtos para a GPU


def carregar_probs() -> tuple[dict, list[str]]:
    """{modelo: {"validacao": DataFrame id x classe, "teste": ...}} com as classes na mesma ordem."""
    cat = json.loads((SPLIT / "categorias.json").read_text())
    classes = list(cat["chaves"])
    fontes = {"classico_v2": PRED / "probs_classico_v2.parquet"}
    for m in IAS + ["bertimbau_sem_q"]:
        for pasta in KV2S:
            if (pasta / f"probs_{m}.parquet").exists():
                fontes[m] = pasta / f"probs_{m}.parquet"
    out = {}
    for nome, arq in fontes.items():
        if not arq.exists():
            continue
        d = pd.read_parquet(arq)
        out[nome] = {parte: g.set_index("id")[classes] for parte, g in d.groupby("parte")}
    return out, classes


def custos() -> dict:
    """Tempo de GPU por produto, em lote, de cada IA (LoRA fundido quando houver)."""
    out = {}
    for pasta in KV2S:
        arq = pasta / "resultados_v2.json"
        if arq.exists():
            for m, k in json.loads(arq.read_text())["modelos"].items():
                if "ms_por_item_lote_gpu" in k:
                    out[m] = k["ms_por_item_lote_gpu"]
    if "qwen15_lora_q5m" in out and "qwen15_lora_q" in out:
        out["qwen15_lora_q"] = out["qwen15_lora_q5m"]  # mesmo modelo e tamanho; o tempo fundido foi medido na 2ª rodada
    return out


def mistura(probs: list[np.ndarray], pesos) -> np.ndarray:
    z = sum(w * np.log(np.clip(p, 1e-9, 1.0)) for w, p in zip(pesos, probs))
    z = np.exp(z - z.max(axis=1, keepdims=True))
    return z / z.sum(axis=1, keepdims=True)


def grade_pesos(n: int, passo: float = 0.1):
    k = round(1 / passo)
    for c in itertools.product(range(1, k), repeat=n - 1):
        if sum(c) < k:
            yield [x / k for x in c] + [(k - sum(c)) / k]


def main():
    P, classes = carregar_probs()
    va = pd.read_parquet(SPLIT / "validacao.parquet").set_index("id")
    te = pd.read_parquet(SPLIT / "teste.parquet").set_index("id")
    yv = np.searchsorted(classes, va["categoria"].to_numpy())
    yt = np.searchsorted(classes, te["categoria"].to_numpy())

    def arr(m, parte, ids):
        return P[m][parte].loc[ids].to_numpy()

    acc_va = {m: float((arr(m, "validacao", va.index).argmax(1) == yv).mean()) for m in P}
    qwens = [m for m in QWEN if m in P]
    if not qwens:
        raise SystemExit("faltam as probabilidades das IAs (reports/kaggle-v2/probs_*.parquet)")
    ia = max(qwens, key=lambda m: acc_va[m])
    print("acerto na validação:", {m: round(100 * a, 2) for m, a in acc_va.items()}, "| IA principal:", ia)
    candidatos = [["classico_v2", ia]]
    if "bertimbau_q" in P:
        candidatos += [["classico_v2", "bertimbau_q"], ["classico_v2", ia, "bertimbau_q"]]
    for v1 in (m for m in V1 if m in P):
        candidatos += [["classico_v2", v1], ["classico_v2", v1, ia]]
    custo = custos()
    linhas, melhor = [], None
    for cand in candidatos:
        pv = [arr(m, "validacao", va.index) for m in cand]
        bom = None
        for w in grade_pesos(len(cand)):
            mv = mistura(pv, w)
            acc = float((mv.argmax(1) == yv).mean())
            ll = float(-np.log(np.clip(mv[np.arange(len(yv)), yv], 1e-9, 1)).mean())
            if bom is None or (acc, -ll) > (bom["acuracia_validacao"], -bom["log_loss_validacao"]):
                bom = {"modelos": cand, "pesos": w, "acuracia_validacao": acc, "log_loss_validacao": ll}
        bom["ms_por_item_lote_gpu"] = sum(custo.get(m, 0.0) for m in cand)
        linhas.append(bom)
        print(cand, [round(x, 1) for x in bom["pesos"]], f"validação {100 * bom['acuracia_validacao']:.2f}%", f"{bom['ms_por_item_lote_gpu']:.1f} ms")
    topo = max(c["acuracia_validacao"] for c in linhas)
    empatadas = [c for c in linhas if c["acuracia_validacao"] >= topo - EMPATE]
    melhor = min(empatadas, key=lambda c: (c["ms_por_item_lote_gpu"], -c["acuracia_validacao"]))
    print("escolhida na validação (empate a até 0,3 ponto fica com a mais barata):", melhor["modelos"], melhor["pesos"])

    # cascata: clássico sozinho quando confiante; o resto vai para a combinação escolhida
    cv = arr("classico_v2", "validacao", va.index)
    jv = mistura([arr(m, "validacao", va.index) for m in melhor["modelos"]], melhor["pesos"])
    alvo = melhor["acuracia_validacao"] - FOLGA
    curva, limite = [], None
    for tau in np.round(np.arange(0.30, 1.0001, 0.02), 2):
        usa_ia = cv.max(1) < tau
        pred = np.where(usa_ia, jv.argmax(1), cv.argmax(1))
        acc = float((pred == yv).mean())
        curva.append({"limite": float(tau), "vai_para_ia": float(usa_ia.mean()), "acuracia_validacao": acc})
        if limite is None and acc >= alvo:
            limite = float(tau)
    if limite is None:
        limite = 1.0

    # teste, uma vez, com tudo já escolhido
    ct = arr("classico_v2", "teste", te.index)
    jt = mistura([arr(m, "teste", te.index) for m in melhor["modelos"]], melhor["pesos"])
    usa_ia = ct.max(1) < limite
    cas = np.where(usa_ia, jt.argmax(1), ct.argmax(1))
    C = np.array(classes)
    pd.DataFrame({"id": te.index, "pred": C[jt.argmax(1)], "confianca": jt.max(1).round(4)}).to_csv(PRED / "juntos.csv", index=False)
    pd.DataFrame({"id": te.index, "pred": C[cas], "foi_para_ia": usa_ia}).to_csv(PRED / "cascata.csv", index=False)
    res = {
        "escolhida": melhor, "candidatas": linhas,
        "cascata": {"limite": limite, "folga": FOLGA, "curva_validacao": curva,
                    "vai_para_ia_validacao": next(c["vai_para_ia"] for c in curva if c["limite"] == limite) if limite < 1 else 1.0,
                    "vai_para_ia_teste": float(usa_ia.mean()), "acuracia_teste": float((cas == yt).mean()),
                    "acuracia_teste_so_classico_quando_confiante": float((ct.argmax(1)[~usa_ia] == yt[~usa_ia]).mean())},
        "acuracia_teste_juntos": float((jt.argmax(1) == yt).mean()),
        "ia_principal": ia, "acuracia_validacao_por_modelo": acc_va,
    }
    # quando o clássico v2 e a IA de maior peso na combinação concordam
    ia_comb = max((m for m in melhor["modelos"] if m != "classico_v2"), key=lambda m: melhor["pesos"][melhor["modelos"].index(m)])
    res["ia_da_combinacao"] = ia_comb
    it = arr(ia_comb, "teste", te.index).argmax(1)
    junto = it == ct.argmax(1)
    res["concordam"] = {"ia": ia_comb, "cobertura": float(junto.mean()), "acuracia": float((it[junto] == yt[junto]).mean()),
                        "acuracia_quando_discordam_ia": float((it[~junto] == yt[~junto]).mean()),
                        "acuracia_quando_discordam_classico": float((ct.argmax(1)[~junto] == yt[~junto]).mean())}
    (RAIZ / "reports" / "combinacao.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    print(json.dumps({k: v for k, v in res.items() if k not in ("candidatas",)}, indent=1, ensure_ascii=False)[:2500])


if __name__ == "__main__":
    main()
