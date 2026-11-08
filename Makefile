PY ?= .venv/bin/python
export PYTHONPATH := src

dados:        ## baixa o recorte Brasil do Open Food Facts (~270 MB lidos, 2 a 5 min)
	$(PY) -m catalogo.dados
split:        ## rótulos curados + divisão por marca (treino, validação, teste)
	$(PY) -m catalogo.preparar
classico:     ## TF-IDF + regressão logística, escolhe na validação, mede no teste, exporta docs/modelo.json
	$(PY) -m catalogo.classico && $(PY) -m catalogo.classico --vazamento
notebook:     ## gera o notebook do Kaggle (zero-shot + LoRA na GPU)
	$(PY) kaggle/gerar_notebook.py
avaliar:      ## junta as respostas dos 3 caminhos e escreve reports/ e docs/dados/
	$(PY) -m catalogo.avaliar
testes:
	$(PY) -m pytest -q tests
pagina:       ## abre a página em http://127.0.0.1:8000
	cd docs && python3 -m http.server 8000 --bind 127.0.0.1

.PHONY: dados split classico notebook avaliar testes pagina
