# Kaggle (GPU T4 grátis): as IAs

Tudo **privado** na conta `rafabueno`. Dataset `rafabueno/catalogo-mercado-br`: `data/split/` (treino, validação,
teste) + `categorias.json` (licença ODbL). Os notebooks são gerados por script (fonte única; não edite o `.ipynb` à mão).

| Notebook (privado) | Gerador | O que roda | Saída no repositório |
|---|---|---|---|
| `rafabueno/catalogo-mercado-lora` (v1, manhã de 08/11/2026) | `gerar_notebook.py` | Qwen2.5-1.5B sem treino, Qwen2.5-7B sem treino, Qwen2.5-1.5B + LoRA que escreve a categoria | `reports/kaggle/`, `reports/predicoes/kaggle.csv` |
| `rafabueno/catalogo-mercado-v2` (v2, tarde de 08/11/2026) | `gerar_notebook_v2.py` | BERTimbau (com e sem a quantidade), Qwen2.5-1.5B + LoRA com cabeça de classificação (o extra de 3 B faltou memória) | `reports/kaggle-v2/` (probabilidades da validação e do teste) |
| `rafabueno/catalogo-mercado-v2b` (v2, 2ª rodada) | `gerar_notebook_v2b.py` | a IA classificadora com 5 épocas e metade do treino sem a marca; tempo com o LoRA fundido | `reports/kaggle-v2b/` |
| `rafabueno/catalogo-mercado-v2c` (v2, IA da manhã de volta) | `gerar_notebook_v2c.py` | o adapter do v1 (dataset privado `rafabueno/catalogo-mercado-lora-v1-adapter`, nada treinado de novo) respondendo validação e teste, com confiança | `reports/kaggle-v2c/` |

```bash
# 1. gerar e testar aqui na CPU com modelos minúsculos
python kaggle/gerar_notebook_v2.py
CATALOGO_LOCAL=1 CATALOGO_LIMITE=40 CATALOGO_BERT=hf-internal-testing/tiny-random-bert \
  CATALOGO_QWEN=trl-internal-testing/tiny-Qwen2ForCausalLM-2.5 python kaggle/gerar_notebook_v2.py --local

# 2. subir o dataset (só se o split mudar)
cp data/split/*.parquet data/split/categorias.json kaggle/dataset/
kaggle datasets version -p kaggle/dataset -m "novo split"

# 3. rodar na GPU e baixar a saída
cp kaggle/notebook-v2-metadata.json kaggle/notebook-v2/kernel-metadata.json
kaggle kernels push -p kaggle/notebook-v2
kaggle kernels status rafabueno/catalogo-mercado-v2
kaggle kernels output rafabueno/catalogo-mercado-v2 -p reports/kaggle-v2
```

Cada rodada vai para a sua pasta (`kaggle kernels output rafabueno/catalogo-mercado-v2b -p reports/kaggle-v2b`, idem v2c).
Depois de baixar: `make combinar avaliar` (as métricas de todos os caminhos saem do mesmo script). O notebook salva a
cada modelo, então, se a sessão cair no extra de 3 B, os outros resultados já estão gravados.
