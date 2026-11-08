import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from catalogo.rotulos import CATEGORIAS, rotular
from catalogo.texto import marca_principal, norm, texto_produto
from catalogo.web_modelo import ModeloWeb, ngramas_pedacos

RAIZ = Path(__file__).resolve().parents[1]
SPLIT = RAIZ / "data" / "split"
MODELO = RAIZ / "docs" / "modelo.json"


def test_norm():
    assert norm("Leite Condensado Moça 395g") == "leite condensado moca 395 g"
    assert norm("  AÇÚCAR   Refinado União 1kg ") == "acucar refinado uniao 1 kg"
    assert norm("Coca-Cola 2L") == "coca cola 2 l"
    assert norm(None) == ""


def test_texto_produto_sem_nan_e_sem_repetir():
    assert texto_produto("Leite condensado", "Moça, Nestlé", "395 g") == "Leite condensado Moça 395 g"
    assert texto_produto("Biscoito Maizena Isabela", "Isabela", float("nan")) == "Biscoito Maizena Isabela"
    assert marca_principal("Nestlé, Moça") == "nestle"
    assert marca_principal(None) == ""


def test_rotulo_prioridade():
    # biscoito de chocolate fica em biscoitos; achocolatado não vira chocolate
    assert rotular(["en:snacks", "en:chocolates", "en:biscuits", "en:chocolate-biscuits"]) == "biscoitos"
    assert rotular(["en:beverages", "en:cocoa-and-chocolate-powders", "en:chocolates"]) == "achocolatado"
    assert rotular(["en:dairies", "en:milks", "en:condensed-milks"]) == "leite_condensado_creme"
    assert rotular(["en:waters", "en:carbonated-drinks"]) == "aguas"
    # só nós genéricos: sem rótulo
    assert rotular(["en:snacks", "en:plant-based-foods-and-beverages"]) is None
    assert len(CATEGORIAS) >= 40


def test_char_wb_igual_ao_sklearn():
    from sklearn.feature_extraction.text import TfidfVectorizer

    v = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5))
    analisar = v.build_analyzer()
    for t in ["leite condensado moca 395 g", "a", "ab cd efghij", "x 1 yz"]:
        assert ngramas_pedacos(t) == analisar(t)


@pytest.mark.skipif(not (SPLIT / "teste.parquet").exists(), reason="rode python -m catalogo.preparar")
def test_split_sem_marca_repetida():
    tr, va, te = (pd.read_parquet(SPLIT / f"{n}.parquet") for n in ("treino", "validacao", "teste"))
    assert not set(tr.grupo) & set(te.grupo)
    assert not set(va.grupo) & set(te.grupo)
    assert not set(tr.grupo) & set(va.grupo)
    chaves = pd.concat([tr, va, te]).texto.map(norm)
    assert chaves.is_unique  # sem repetidos entre e dentro das partes
    assert set(te.categoria) <= set(tr.categoria)


@pytest.mark.skipif(not MODELO.exists(), reason="rode python -m catalogo.classico")
def test_modelo_web_igual_ao_medido():
    """O modelo do navegador (pesos em int8) responde igual ao medido no teste em >= 99,5% dos produtos."""
    te = pd.read_parquet(SPLIT / "teste.parquet")
    medido = pd.read_csv(RAIZ / "reports" / "predicoes" / "tfidf.csv").set_index("id")["pred"]
    m = ModeloWeb(MODELO)
    web = [m.prever(t, 1)[0][0] for t in te.texto]
    iguais = np.mean([a == b for a, b in zip(web, medido.loc[te.id])])
    assert iguais >= 0.995, iguais


@pytest.mark.skipif(not MODELO.exists() or shutil.which("node") is None, reason="precisa do modelo e do Node")
def test_javascript_igual_ao_python():
    te = pd.read_parquet(SPLIT / "teste.parquet").head(300)
    m = ModeloWeb(MODELO)
    py = [m.prever(t, 1)[0] for t in te.texto]
    script = f"""
    const C = require({json.dumps(str(RAIZ / 'docs' / 'classificador.js'))});
    const fs = require('fs');
    const clf = C.criar(JSON.parse(fs.readFileSync({json.dumps(str(MODELO))}, 'utf8')));
    const textos = JSON.parse(fs.readFileSync(0, 'utf8'));
    console.log(JSON.stringify(textos.map(t => {{ const r = clf.prever(t, 1).top[0]; return [r.chave, r.p]; }})));
    """
    out = subprocess.run(["node", "-e", script], input=json.dumps(list(te.texto)), capture_output=True, text=True, check=True)
    js = json.loads(out.stdout)
    assert [c for c, _ in js] == [c for c, _ in py]
    assert max(abs(a - b) for (_, a), (_, b) in zip(js, py)) < 1e-4
    # normalização igual nos dois lados, inclusive com acento e símbolo
    casos = ["Leite Condensado Moça 395g", "AÇÚCAR União 1kg", "Pão de Queijo Forno de Minas", "Coca-Cola Zero 2L", "Guaraná Antarctica"]
    out = subprocess.run(["node", "-e", f"const C=require({json.dumps(str(RAIZ / 'docs' / 'classificador.js'))});"
                          f"console.log(JSON.stringify({json.dumps(casos)}.map(C.norm)))"], capture_output=True, text=True, check=True)
    assert json.loads(out.stdout) == [norm(c) for c in casos]
