"""Extrai do Open Food Facts (licença ODbL) só os produtos vendidos no Brasil.

O Parquet público do Open Food Facts no Hugging Face tem ~8 GB (4,9 milhões de produtos, 145 colunas),
mas só ~270 MB são das 7 colunas que usamos. Ler pelo DuckDB remoto funciona, porém faz dezenas de
milhares de pedidos pequenos em sequência (300 produtos levaram 6 min). Aqui baixamos só os pedaços
dessas colunas, em paralelo, para um arquivo local "esparso" (os buracos não ocupam disco), e o
pyarrow lê o arquivo como se estivesse inteiro. Leva 2 a 4 min numa conexão comum.

Uso:
  python -m catalogo.dados                      # recorte completo -> data/off_brasil.parquet
  python -m catalogo.dados --max-grupos 50      # teste rápido (só os primeiros 50 grupos de linhas)
"""

from __future__ import annotations

import argparse
import os
import struct
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
import pyarrow.compute as pc
import pyarrow.parquet as pq
import requests

URL = "https://huggingface.co/datasets/openfoodfacts/product-database/resolve/main/food.parquet"
COLUNAS = ["code", "product_name", "brands", "quantity", "lang", "categories_tags", "countries_tags"]
RAIZ = Path(__file__).resolve().parents[2]
SAIDA = RAIZ / "data" / "off_brasil.parquet"
CACHE = RAIZ / "data" / ".off_esparso.parquet"
AGENTE = {"User-Agent": "catalogo-de-mercado/0.1 (estudo; https://github.com/Bueno-00)"}


def nome_de(lista) -> str:
    """`product_name` vem como lista de {lang, text}: prefere pt, depois main, depois o primeiro."""
    itens = [] if lista is None else list(lista)
    por_lingua = {d.get("lang"): (d.get("text") or "") for d in itens if isinstance(d, dict)}
    for chave in ("pt", "main"):
        if por_lingua.get(chave, "").strip():
            return por_lingua[chave].strip()
    return next((v.strip() for v in por_lingua.values() if v and v.strip()), "")


def _resolver(url: str) -> tuple[str, int]:
    """Segue o redirecionamento do Hugging Face uma vez (CDN) e devolve (url final, tamanho)."""
    r = requests.head(url, allow_redirects=True, headers=AGENTE, timeout=60)
    r.raise_for_status()
    return r.url, int(r.headers["content-length"])


def _baixar_trechos(url: str, trechos: list[tuple[int, int]], destino: Path, paralelo: int = 24) -> None:
    sessao = requests.Session()
    sessao.headers.update(AGENTE)
    fd = os.open(destino, os.O_RDWR)

    def um(tr):
        ini, fim = tr
        for tentativa in range(5):
            try:
                r = sessao.get(url, headers={"Range": f"bytes={ini}-{fim - 1}"}, timeout=120)
                r.raise_for_status()
                if len(r.content) != fim - ini:
                    raise OSError(f"trecho incompleto {ini}-{fim}")
                os.pwrite(fd, r.content, ini)
                return
            except Exception:  # noqa: BLE001 (tenta de novo; rede instável)
                time.sleep(1 + tentativa * 2)
        raise RuntimeError(f"falhou o trecho {ini}-{fim}")

    try:
        with ThreadPoolExecutor(paralelo) as ex:
            list(ex.map(um, trechos))
    finally:
        os.close(fd)


def montar_esparso(max_grupos: int | None = None, cache: Path = CACHE) -> Path:
    url, tamanho = _resolver(URL)
    cache.parent.mkdir(parents=True, exist_ok=True)
    with open(cache, "wb") as f:
        f.truncate(tamanho)  # arquivo esparso: ocupa só o que for escrito
    # rodapé: últimos 8 bytes = tamanho dos metadados + "PAR1"
    r = requests.get(url, headers={**AGENTE, "Range": f"bytes={tamanho - 8}-{tamanho - 1}"}, timeout=60)
    tam_meta = struct.unpack("<I", r.content[:4])[0]
    _baixar_trechos(url, [(tamanho - 8 - tam_meta, tamanho)], cache)
    md = pq.ParquetFile(cache).metadata
    grupos = range(md.num_row_groups if max_grupos is None else min(max_grupos, md.num_row_groups))
    trechos = []
    for i in grupos:
        rg = md.row_group(i)
        for j in range(rg.num_columns):
            c = rg.column(j)
            if c.path_in_schema.split(".")[0] in COLUNAS:
                ini = c.data_page_offset
                if c.has_dictionary_page and c.dictionary_page_offset:
                    ini = min(ini, c.dictionary_page_offset)
                trechos.append((ini, ini + c.total_compressed_size))
    t0 = time.time()
    _baixar_trechos(url, trechos, cache)
    total = sum(b - a for a, b in trechos)
    print(f"{len(trechos):,} trechos, {total / 1e6:.0f} MB em {time.time() - t0:.0f}s ({len(grupos)} grupos de linhas)")
    return cache


def extrair(max_grupos: int | None = None, saida: Path = SAIDA) -> pd.DataFrame:
    t0 = time.time()
    cache = montar_esparso(max_grupos)
    pf = pq.ParquetFile(cache)
    n = pf.metadata.num_row_groups if max_grupos is None else min(max_grupos, pf.metadata.num_row_groups)
    partes = []
    for i in range(0, n, 200):
        tb = pf.read_row_groups(list(range(i, min(i + 200, n))), columns=COLUNAS)
        col = tb["countries_tags"].combine_chunks()
        pais = pc.list_parent_indices(col)
        achou = pc.equal(pc.list_flatten(col), "en:brazil")
        linhas = pc.unique(pc.filter(pais, pc.fill_null(achou, False)))
        partes.append(tb.take(linhas).drop(["countries_tags"]).to_pandas())
    raw = pd.concat(partes, ignore_index=True)
    raw["nome"] = raw["product_name"].map(nome_de)
    raw["categorias"] = raw["categories_tags"].map(
        lambda ts: [t for t in ([] if ts is None else list(ts)) if isinstance(t, str) and t.startswith("en:")]
    )
    n_br = len(raw)
    raw = raw[(raw["nome"] != "") & (raw["categorias"].map(len) > 0)]
    raw = raw.drop(columns=["product_name", "categories_tags"]).reset_index(drop=True)
    saida.parent.mkdir(parents=True, exist_ok=True)
    raw.to_parquet(saida, index=False)
    cache.unlink(missing_ok=True)
    print(f"{n_br:,} produtos com 'en:brazil'; {len(raw):,} com nome e categoria; {time.time() - t0:.0f}s -> {saida}")
    return raw


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-grupos", type=int, default=None)
    ap.add_argument("--saida", type=Path, default=SAIDA)
    a = ap.parse_args()
    extrair(a.max_grupos, a.saida)
