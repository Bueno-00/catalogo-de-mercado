"""Do recorte Brasil do Open Food Facts ao conjunto rotulado e dividido.

1. Rótulo: cada produto traz várias tags de categoria (da mais geral à mais específica). Usamos uma lista
   curada de categorias de prateleira (`rotulos.py`) e ficamos com a mais específica que aparecer.
   Produto sem nenhuma dessas tags sai do conjunto.
2. Texto de entrada: nome + marca + quantidade, como uma linha de catálogo de loja.
3. Repetidos: mesmo texto normalizado com a mesma categoria vira um só (o Open Food Facts tem o mesmo
   produto com vários códigos de barras). Mesmo texto com categorias diferentes também sai (rótulo
   contraditório).
4. Divisão por MARCA (StratifiedGroupKFold): nenhuma marca aparece em dois lados. Produto sem marca é
   agrupado pelas 3 primeiras palavras do nome. Assim o teste mede "marca que o modelo nunca viu", que é
   o caso real de um lojista novo cadastrando produtos.
   Treino ~70%, validação ~10% (para escolher configuração), teste ~20% (só para medir no fim).

Uso:  python -m catalogo.preparar
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold

from .rotulos import CATEGORIAS, rotular
from .texto import marca_principal, norm, texto_produto

RAIZ = Path(__file__).resolve().parents[2]
ENTRADA = RAIZ / "data" / "off_brasil.parquet"
SPLIT = RAIZ / "data" / "split"
SEED = 42
MIN_POR_CLASSE = 40  # categoria com menos exemplos que isso sai (não dá para medir com honestidade)


def grupo_de(row) -> str:
    m = marca_principal(row["brands"])
    if m:
        return "marca:" + m
    return "nome:" + " ".join(norm(row["nome"]).split()[:3])


def preparar(entrada: Path = ENTRADA, saida: Path = SPLIT) -> dict:
    raw = pd.read_parquet(entrada)
    n0 = len(raw)
    raw["categoria"] = raw["categorias"].map(lambda c: rotular(list(c)))
    df = raw.dropna(subset=["categoria"]).copy()
    n_rot = len(df)
    df["texto"] = [texto_produto(n, b, q) for n, b, q in zip(df["nome"], df["brands"], df["quantity"])]
    df["chave"] = df["texto"].map(norm)
    df = df[df["chave"].str.len() >= 3]
    # rótulo contraditório: mesmo texto com categorias diferentes
    conflito = df.groupby("chave")["categoria"].nunique()
    df = df[~df["chave"].isin(conflito[conflito > 1].index)]
    n_conf = int((conflito > 1).sum())
    df = df.drop_duplicates("chave").copy()
    n_dedup = len(df)
    vc = df["categoria"].value_counts()
    fora = vc[vc < MIN_POR_CLASSE].index.tolist()
    df = df[~df["categoria"].isin(fora)].copy()
    df["grupo"] = df.apply(grupo_de, axis=1)
    df["id"] = df["code"].astype(str).map(lambda c: hashlib.sha1(c.encode()).hexdigest()[:12])
    df = df.sample(frac=1, random_state=SEED).reset_index(drop=True)

    sgkf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=SEED)
    resto_idx, teste_idx = next(sgkf.split(df, df["categoria"], df["grupo"]))
    resto, teste = df.iloc[resto_idx], df.iloc[teste_idx]
    sgkf2 = StratifiedGroupKFold(n_splits=8, shuffle=True, random_state=SEED)
    tr_idx, va_idx = next(sgkf2.split(resto, resto["categoria"], resto["grupo"]))
    treino, valid = resto.iloc[tr_idx], resto.iloc[va_idx]
    assert not (set(treino.grupo) & set(teste.grupo)) and not (set(valid.grupo) & set(teste.grupo))
    assert not (set(treino.grupo) & set(valid.grupo))

    cols = ["id", "code", "texto", "nome", "brands", "quantity", "categoria", "grupo"]
    saida.mkdir(parents=True, exist_ok=True)
    for nome, parte in (("treino", treino), ("validacao", valid), ("teste", teste)):
        parte[cols].reset_index(drop=True).to_parquet(saida / f"{nome}.parquet", index=False)
    usadas = sorted(df["categoria"].unique())
    cat = {"chaves": usadas, "nomes": {c: CATEGORIAS[c]["pt"] for c in usadas},
           "nomes_en": {c: CATEGORIAS[c]["en"] for c in usadas},
           "tags_off": {c: CATEGORIAS[c]["tags"] for c in usadas}}
    (saida / "categorias.json").write_text(json.dumps(cat, ensure_ascii=False, indent=1))

    resumo = {
        "produtos_brasil_com_nome_e_categoria": n0, "com_rotulo_curado": n_rot,
        "textos_contraditorios_removidos": n_conf, "depois_de_tirar_repetidos": n_dedup,
        "categorias_removidas_por_poucos_exemplos": fora, "categorias": len(usadas),
        "treino": len(treino), "validacao": len(valid), "teste": len(teste),
        "grupos_treino": treino.grupo.nunique(), "grupos_teste": teste.grupo.nunique(),
        "produtos_sem_marca": int(df["grupo"].str.startswith("nome:").sum()),
        "por_categoria": {c: {"treino": int((treino.categoria == c).sum()), "validacao": int((valid.categoria == c).sum()),
                              "teste": int((teste.categoria == c).sum())} for c in usadas},
    }
    (RAIZ / "reports").mkdir(exist_ok=True)
    (RAIZ / "reports" / "dados.json").write_text(json.dumps(resumo, ensure_ascii=False, indent=1))
    print(json.dumps({k: v for k, v in resumo.items() if k != "por_categoria"}, ensure_ascii=False, indent=1))
    return resumo


def split_aleatorio(saida: Path = RAIZ / "data" / "split_aleatorio") -> None:
    """Mesmos produtos, divisão aleatória (marca pode cair nos dois lados): só para mostrar o vazamento."""
    from sklearn.model_selection import train_test_split

    partes = [pd.read_parquet(SPLIT / f"{n}.parquet") for n in ("treino", "validacao", "teste")]
    df = pd.concat(partes, ignore_index=True)
    resto, teste = train_test_split(df, test_size=len(partes[2]), random_state=SEED, stratify=df["categoria"])
    saida.mkdir(parents=True, exist_ok=True)
    resto.to_parquet(saida / "treino_validacao.parquet", index=False)
    teste.to_parquet(saida / "teste.parquet", index=False)
    print("split aleatório:", len(resto), len(teste), "marcas em comum:", len(set(resto.grupo) & set(teste.grupo)))


if __name__ == "__main__":
    preparar()
    split_aleatorio()
    np.random.seed(SEED)
