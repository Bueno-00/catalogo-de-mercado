import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from catalogo.quantidade import faixa_tokens, ler, texto_com_quantidade
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


def test_quantidade():
    assert ler("Leite Nestlé 34 g")["tipo"] == "massa" and ler("Leite Nestlé 34 g")["valor"] == 34
    assert ler("Arroz 5kg")["valor"] == 5000 and ler("Coca-Cola 2L")["valor"] == 2000
    assert ler("Chá 22,5g")["valor"] == 22.5 and ler("Azeite 1.000 ml")["valor"] == 1000
    assert ler("Queijo 0,500 kg")["valor"] == 500 and ler("Cerveja 6x350ml")["pacote"] == 6
    assert ler("Bombom 2 UNIDADES")["tipo"] == "unid"
    # "12 garrafas" e "1 lata" não são unidade de medida
    assert ler("12 garrafas")["tipo"] == "nenhum" and ler("Milho 1 lata")["tipo"] == "nenhum"
    # a última quantidade vale (o campo quantidade vem no fim da linha)
    assert ler("Batata Palha 215g 120g")["valor"] == 120
    assert faixa_tokens("Leite Nestlé 34 g") == "qt_m qf_m1" and faixa_tokens("Leite UHT 1 L") == "qt_v qf_v3"
    assert texto_com_quantidade("Leite Moça 1kg") == "Leite Moça 1kg | quantidade: 1 kg"
    assert texto_com_quantidade("Pão de forma") == "Pão de forma"


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
    medido = pd.read_csv(RAIZ / "reports" / "predicoes" / "classico_v2.csv").set_index("id")["pred"]
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
    js_norm = (f"const C=require({json.dumps(str(RAIZ / 'docs' / 'classificador.js'))});"
               f"console.log(JSON.stringify({json.dumps(casos)}.map(C.norm)))")
    out = subprocess.run(["node", "-e", js_norm], capture_output=True, text=True, check=True)
    assert json.loads(out.stdout) == [norm(c) for c in casos]


@pytest.mark.skipif(not (SPLIT / "teste.parquet").exists() or shutil.which("node") is None, reason="precisa do split e do Node")
def test_quantidade_javascript_igual_ao_python():
    """A leitura da quantidade no navegador é a mesma do Python, em todos os produtos de treino, validação e teste."""
    textos = list(pd.concat([pd.read_parquet(SPLIT / f"{n}.parquet") for n in ("treino", "validacao", "teste")]).texto)
    textos += ["Chá 22,5g", "Azeite 1.000 ml", "Queijo 0,500 kg", "Whey 50 g / 1.7 oz", "12 garrafas", "Cerveja 6x350ml"]
    script = f"""
    const C = require({json.dumps(str(RAIZ / 'docs' / 'classificador.js'))});
    const textos = JSON.parse(require('fs').readFileSync(0, 'utf8'));
    console.log(JSON.stringify(textos.map(t => C.faixaTokens(t).join(" "))));
    """
    out = subprocess.run(["node", "-e", script], input=json.dumps(textos), capture_output=True, text=True, check=True)
    assert json.loads(out.stdout) == [faixa_tokens(t) for t in textos]
