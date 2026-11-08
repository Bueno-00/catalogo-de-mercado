# Kaggle (GPU T4 grátis): zero-shot e LoRA

- Dataset **privado** `rafabueno/catalogo-mercado-br`: `data/split/` (treino, validação, teste) + `categorias.json`. Metadados em `dataset/dataset-metadata.json` (licença ODbL).
- Notebook **privado** `rafabueno/catalogo-mercado-lora`: gerado por `gerar_notebook.py` (fonte única; não edite o `.ipynb` à mão).

```bash
# 1. gerar o notebook (e testar o código aqui na CPU com um modelo minúsculo)
python kaggle/gerar_notebook.py
CATALOGO_LOCAL=1 CATALOGO_LIMITE=40 CATALOGO_MODELO=trl-internal-testing/tiny-Qwen2ForCausalLM-2.5 \
  python kaggle/gerar_notebook.py --local          # precisa de torch, transformers e peft (CPU)

# 2. subir o dataset (primeira vez: create; depois: version)
cp data/split/*.parquet data/split/categorias.json kaggle/dataset/
kaggle datasets create -p kaggle/dataset             # privado por padrão
kaggle datasets version -p kaggle/dataset -m "novo split"

# 3. rodar na GPU e baixar a saída
cp kaggle/notebook-metadata.json kaggle/notebook/kernel-metadata.json
kaggle kernels push -p kaggle/notebook
kaggle kernels status rafabueno/catalogo-mercado-lora
kaggle kernels output rafabueno/catalogo-mercado-lora -p reports/kaggle
```

Depois de baixar: copie `reports/kaggle/predicoes_teste.csv` para `reports/predicoes/kaggle.csv` e rode
`python -m catalogo.avaliar` (as métricas dos 3 caminhos saem do mesmo script).

O notebook salva tudo a cada etapa (`predicoes_teste.csv`, `resultados_kaggle.json`), então, se a sessão cair no
modelo 7 B (o extra), os resultados principais já estão gravados.
