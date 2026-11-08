PY ?= .venv/bin/python
export PYTHONPATH := src

dados:        ## baixa o recorte Brasil do Open Food Facts (~270 MB lidos, 2 a 5 min)
	$(PY) -m catalogo.dados
split:        ## rótulos curados + divisão por marca (treino, validação, teste)
	$(PY) -m catalogo.preparar
escolher:     ## validação cruzada por marca (só treino + validação) para escolher o clássico v2
	$(PY) -m catalogo.classico --escolher
classico:     ## clássico v2 (exporta docs/modelo.json), v1 e o teste de vazamento
	$(PY) -m catalogo.classico && $(PY) -m catalogo.classico --v1 && $(PY) -m catalogo.classico --vazamento
notebook:     ## gera os notebooks do Kaggle (v1: zero-shot + LoRA; v2: classificadores com a quantidade)
	$(PY) kaggle/gerar_notebook.py && $(PY) kaggle/gerar_notebook_v2.py && $(PY) kaggle/gerar_notebook_v2b.py && $(PY) kaggle/gerar_notebook_v2c.py
combinar:     ## junta clássico v2 + IAs v2 e monta a cascata (tudo escolhido na validação)
	$(PY) -m catalogo.combinar
avaliar:      ## mede todos os caminhos no mesmo teste -> reports/ e docs/dados/
	$(PY) -m catalogo.avaliar
testes:
	$(PY) -m pytest -q tests
pagina:       ## abre a página em http://127.0.0.1:8000
	cd docs && python3 -m http.server 8000 --bind 127.0.0.1

.PHONY: dados split escolher classico notebook combinar avaliar testes pagina
