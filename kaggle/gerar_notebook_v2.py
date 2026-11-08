#!/usr/bin/env python3
"""Gera o notebook v2 do Kaggle (GPU T4 grátis): as IAs ajustadas viram CLASSIFICADORES, com a quantidade no texto.

O que muda em relação ao v1 (`gerar_notebook.py`, que fica como registro do primeiro resultado):
- o LoRA deixa de GERAR o nome da categoria palavra por palavra e passa a ter uma "cabeça de classificação": uma
  passada pelo modelo devolve a probabilidade de cada uma das 41 categorias. Mais rápido um por vez, nunca
  responde fora da lista e dá a confiança, que permite juntar com o clássico;
- a quantidade lida e normalizada vai no texto ("... | quantidade: 34 g"), com o mesmo código de
  `src/catalogo/quantidade.py` (copiado para dentro do notebook);
- a época é escolhida pela validação (o teste nunca escolhe nada);
- modelos: BERTimbau base (110 milhões de parâmetros, ajuste completo), Qwen2.5-1.5B + LoRA e, como extra,
  Qwen2.5-3B + LoRA. BERTimbau também sem a quantidade, para medir o que ela traz.

Saída em /kaggle/working: probs_<modelo>.parquet (probabilidade das 41 categorias para validação e teste) e
resultados_v2.json (tempos, épocas, acerto na validação). As métricas do teste saem de `src/catalogo/avaliar.py`.

Uso:
  python kaggle/gerar_notebook_v2.py            # escreve kaggle/notebook-v2/catalogo-mercado-v2.ipynb
  python kaggle/gerar_notebook_v2.py --local    # roda aqui com modelos minúsculos (teste do código, CPU)
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "notebook-v2" / "catalogo-mercado-v2.ipynb"
QUANTIDADE = (HERE.parent / "src" / "catalogo" / "quantidade.py").read_text()

C: list[tuple[str, str]] = []

C.append(("md", r"""# Catálogo de mercado v2: IA ajustada como classificador, com a quantidade (GPU T4 do Kaggle)

**Português** (English summary at the end). Repositório: https://github.com/Bueno-00/catalogo-de-mercado

No v1 o LoRA gerava o nome da categoria como texto (uma palavra por vez, 0,7 s por produto um por vez). Aqui ele
ganha uma **cabeça de classificação**: uma passada pelo modelo dá a probabilidade de cada categoria. A
quantidade lida e normalizada vai no texto (`Leite Nestlé 34 g | quantidade: 34 g`). Modelos:

1. **BERTimbau base** (110 M de parâmetros, ajuste completo), com e sem a quantidade;
2. **Qwen2.5-1.5B + LoRA** com cabeça de classificação;
3. extra: **Qwen2.5-3B + LoRA**.

Mesmo dataset privado do v1 (divisão por marca). A época de cada modelo é escolhida pela **validação**. As
métricas do teste são calculadas fora daqui, pelo mesmo script dos outros caminhos."""))

C.append(("code", r'''import os, re, gc, time, json, math, random, subprocess, sys, unicodedata
from pathlib import Path
import numpy as np
import pandas as pd

LOCAL = os.environ.get("CATALOGO_LOCAL") == "1"
SEED = 42
LIMITE = int(os.environ.get("CATALOGO_LIMITE", "0"))
MAX_LEN = 64

def achar_dados():
    for raiz in [Path("/kaggle/input"), Path(os.environ.get("CATALOGO_DADOS", "data/split"))]:
        if raiz.exists():
            achados = sorted(raiz.rglob("teste.parquet"))
            if achados:
                return achados[0].parent
    raise FileNotFoundError("teste.parquet não encontrado")

DADOS = achar_dados()
SAIDA = Path("/kaggle/working") if Path("/kaggle/working").exists() else Path(os.environ.get("CATALOGO_SAIDA", ".tmp/kaggle-v2-local"))
SAIDA.mkdir(parents=True, exist_ok=True)
random.seed(SEED); np.random.seed(SEED)
import torch
torch.manual_seed(SEED)
GPU = torch.cuda.is_available()
DISP = "cuda" if GPU else "cpu"
import transformers
if Path("/kaggle/working").exists():
    subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "-q", "torchao"], check=False)
try:
    import peft
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "peft>=0.13"], check=True)
    import peft
print(f"dados={DADOS} | gpu={GPU} {torch.cuda.get_device_name(0) if GPU else ''} | torch {torch.__version__} | "
      f"transformers {transformers.__version__} | peft {peft.__version__} | cpus={os.cpu_count()}")
'''))

C.append(("md", r"""## Quantidade (o mesmo código de `src/catalogo/quantidade.py`)"""))
C.append(("code", "# --- copiado de src/catalogo/quantidade.py ---\n" + QUANTIDADE.split('"""', 2)[2]))

C.append(("code", r'''tr = pd.read_parquet(DADOS / "treino.parquet")
va = pd.read_parquet(DADOS / "validacao.parquet")
te = pd.read_parquet(DADOS / "teste.parquet")
cat = json.loads((DADOS / "categorias.json").read_text())
CLASSES = list(cat["chaves"])
K = len(CLASSES)
Y = {c: i for i, c in enumerate(CLASSES)}
if LIMITE:
    tr, va, te = tr.head(LIMITE), va.head(max(LIMITE // 4, 8)), te.head(max(LIMITE // 4, 8))
for d in (tr, va, te):
    d["texto_q"] = [texto_com_quantidade(t) for t in d["texto"]]
print(f"treino {len(tr):,} | validação {len(va):,} | teste {len(te):,} | {K} categorias")
print(te[["texto", "texto_q"]].head(5).to_string())
RES = {"classes": CLASSES, "n_teste": len(te), "modelos": {}}

def salvar():
    (SAIDA / "resultados_v2.json").write_text(json.dumps(RES, indent=1, ensure_ascii=False))
'''))

C.append(("md", r"""## Treino e resposta

Laço simples em PyTorch: AdamW, aquecimento + cosseno, fp16 com *GradScaler* na T4. No LoRA, os pesos do modelo
ficam congelados em fp16 e só o adapter (r=16 em todas as projeções) e a cabeça de classificação treinam, em fp32.
Ao fim de cada época: acerto na validação; a melhor época guarda as probabilidades da validação e do teste."""))

C.append(("code", r'''from transformers import AutoTokenizer, AutoModelForSequenceClassification
from peft import LoraConfig, get_peft_model

ALVOS_LORA = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]

def lotes(tok, textos, ys, tam, embaralhar):
    idx = list(range(len(textos)))
    if embaralhar:
        random.shuffle(idx)
    for i in range(0, len(idx), tam):
        parte = idx[i:i + tam]
        enc = tok([textos[j] for j in parte], padding=True, truncation=True, max_length=MAX_LEN, return_tensors="pt")
        enc = {k: v.to(DISP) for k, v in enc.items()}
        yield enc, (torch.tensor([ys[j] for j in parte], device=DISP) if ys is not None else None)

@torch.no_grad()
def probabilidades(modelo, tok, textos, lote=128):
    modelo.eval()
    out = np.zeros((len(textos), K), dtype=np.float32)
    ordem = np.argsort([len(t) for t in textos])
    for i in range(0, len(textos), lote):
        idx = ordem[i:i + lote]
        enc = tok([textos[j] for j in idx], padding=True, truncation=True, max_length=MAX_LEN, return_tensors="pt").to(modelo.device)
        with torch.autocast(DISP, dtype=torch.float16, enabled=GPU):
            logits = modelo(**enc).logits.float()
        out[idx] = torch.softmax(logits, -1).cpu().numpy()
    return out

@torch.no_grad()
def latencia(modelo, tok, textos, n):
    """Mediana de n produtos, um por vez (como um cadastro feito na hora), com a tokenização incluída."""
    modelo.eval(); disp = next(modelo.parameters()).device; ts = []
    usa_gpu = disp.type == "cuda"
    for t in textos[:n]:
        if usa_gpu: torch.cuda.synchronize()
        t0 = time.perf_counter()
        enc = tok([t], truncation=True, max_length=MAX_LEN, return_tensors="pt").to(disp)
        with torch.autocast(disp.type, dtype=torch.float16, enabled=usa_gpu):
            modelo(**enc).logits.argmax(-1).item()
        if usa_gpu: torch.cuda.synchronize()
        ts.append(time.perf_counter() - t0)
    return round(1000 * float(np.median(ts)), 2)

def treinar(chave, nome, coluna, lora, epocas, lr, batch=32, cpu_lat=0):
    t_ini = time.time()
    tok = AutoTokenizer.from_pretrained(nome)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    tok.padding_side = "right"
    tipo = torch.float16 if (lora and GPU) else torch.float32
    modelo = AutoModelForSequenceClassification.from_pretrained(
        nome, num_labels=K, dtype=tipo, id2label=dict(enumerate(CLASSES)), label2id=Y, ignore_mismatched_sizes=True)
    modelo.config.pad_token_id = tok.pad_token_id
    if lora:
        modelo = get_peft_model(modelo, LoraConfig(task_type="SEQ_CLS", r=16, lora_alpha=32, lora_dropout=0.05,
                                                   bias="none", target_modules=ALVOS_LORA))
    modelo.to(DISP)
    treinaveis = [p for p in modelo.parameters() if p.requires_grad]
    for p in treinaveis:
        p.data = p.data.float()
    n_trein, n_total = sum(p.numel() for p in treinaveis), sum(p.numel() for p in modelo.parameters())
    print(f"{chave}: {n_trein:,} de {n_total:,} parâmetros treinam ({100 * n_trein / n_total:.2f}%)")
    opt = torch.optim.AdamW(treinaveis, lr=lr, weight_decay=0.0 if lora else 0.01)
    passos = epocas * math.ceil(len(tr) / batch)
    aquec = max(1, int(0.06 * passos))
    sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: min(1.0, (s + 1) / aquec) * 0.5 * (1 + math.cos(math.pi * min(1.0, s / passos))))
    scaler = torch.amp.GradScaler("cuda", enabled=GPU)
    xtr, ytr = list(tr[coluna]), [Y[c] for c in tr["categoria"]]
    xva, yva, xte = list(va[coluna]), np.array([Y[c] for c in va["categoria"]]), list(te[coluna])
    hist, melhor = [], {"acc": -1}
    t_treino = 0.0
    for ep in range(epocas):
        modelo.train(); soma = n = 0; t0 = time.time()
        for enc, y in lotes(tok, xtr, ytr, batch, True):
            with torch.autocast(DISP, dtype=torch.float16, enabled=GPU):
                logits = modelo(**enc).logits
            perda = torch.nn.functional.cross_entropy(logits.float(), y)
            opt.zero_grad(set_to_none=True)
            scaler.scale(perda).backward()
            scaler.unscale_(opt); torch.nn.utils.clip_grad_norm_(treinaveis, 1.0)
            scaler.step(opt); scaler.update(); sched.step()
            soma += perda.item(); n += 1
        t_treino += time.time() - t0
        pva = probabilidades(modelo, tok, xva)
        acc = float((pva.argmax(1) == yva).mean())
        hist.append({"epoca": ep + 1, "perda_treino": round(soma / max(n, 1), 4), "acerto_validacao": round(acc, 4),
                     "min_treino": round(t_treino / 60, 2)})
        print(chave, hist[-1], flush=True)
        if acc > melhor["acc"]:
            if GPU: torch.cuda.synchronize()
            t0 = time.time(); pte = probabilidades(modelo, tok, xte)
            if GPU: torch.cuda.synchronize()
            melhor = {"acc": acc, "epoca": ep + 1, "pva": pva, "pte": pte, "ms_lote": 1000 * (time.time() - t0) / len(xte)}
    linhas = [("validacao", i, p) for i, p in zip(va["id"], melhor["pva"])] + [("teste", i, p) for i, p in zip(te["id"], melhor["pte"])]
    probs = pd.DataFrame([p for _, _, p in linhas], columns=CLASSES).round(5)
    probs.insert(0, "id", [i for _, i, _ in linhas]); probs.insert(0, "parte", [a for a, _, _ in linhas])
    probs.to_parquet(SAIDA / f"probs_{chave}.parquet", index=False)
    info = {"nome": nome, "coluna": coluna, "lora": lora, "epocas": epocas, "lr": lr, "batch": batch,
            "epoca_escolhida": melhor["epoca"], "acerto_validacao": round(melhor["acc"], 4), "historico": hist,
            "min_treino": round(t_treino / 60, 2), "parametros_treinaveis": int(n_trein), "parametros_total": int(n_total),
            "ms_por_item_lote_gpu": round(melhor["ms_lote"], 3), "ms_um_a_um_gpu": latencia(modelo, tok, xte, 50) if GPU else None}
    if cpu_lat:
        try:
            m_cpu = modelo.merge_and_unload() if lora else modelo
            m_cpu = m_cpu.float().cpu()
            info["ms_um_a_um_cpu"] = latencia(m_cpu, tok, xte, cpu_lat)
            info["cpu_threads"] = torch.get_num_threads()
            del m_cpu
        except Exception as e:
            info["ms_um_a_um_cpu_erro"] = repr(e)[:300]
    info["min_total"] = round((time.time() - t_ini) / 60, 2)
    RES["modelos"][chave] = info
    salvar()
    print(chave, {k: v for k, v in info.items() if k != "historico"}, flush=True)
    del modelo, opt, scaler
    gc.collect()
    if GPU: torch.cuda.empty_cache()
'''))

C.append(("code", r'''BERT = os.environ.get("CATALOGO_BERT", "neuralmind/bert-base-portuguese-cased")
QWEN = os.environ.get("CATALOGO_QWEN", "Qwen/Qwen2.5-1.5B-Instruct")
QWEN3B = os.environ.get("CATALOGO_QWEN3B", "Qwen/Qwen2.5-3B-Instruct")
E = 1 if LOCAL else None

treinar("bertimbau_q", BERT, "texto_q", lora=False, epocas=E or 6, lr=5e-5, cpu_lat=30)
treinar("qwen15_lora_q", QWEN, "texto_q", lora=True, epocas=E or 3, lr=2e-4, cpu_lat=10)
treinar("bertimbau_sem_q", BERT, "texto", lora=False, epocas=E or 6, lr=5e-5)
'''))

C.append(("md", r"""## Extra: Qwen2.5-3B + LoRA (o dobro do tamanho)

Se faltar memória ou tempo, a célula registra o motivo e segue (os outros resultados já estão salvos)."""))
C.append(("code", r'''if not LOCAL and GPU:
    try:
        treinar("qwen3b_lora_q", QWEN3B, "texto_q", lora=True, epocas=3, lr=1e-4, batch=32)
    except Exception as e:
        RES["modelos"]["qwen3b_lora_q"] = {"pulado": repr(e)[:500]}
        print("3B pulado:", repr(e)[:500]); salvar()
salvar()
print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk != "historico"} for k, v in RES["modelos"].items()}, indent=1, ensure_ascii=False))
'''))

C.append(("md", r"""---

## English summary

**Grocery catalog v2.** The tuned models become **classifiers** (a classification head instead of generating the
category name token by token): one forward pass returns a probability for each of the 41 categories, so it is faster
one item at a time, never answers outside the list, and gives a confidence score that can be combined with the
TF-IDF baseline. The parsed, normalized **quantity** goes into the text (`... | quantidade: 34 g`). Models: BERTimbau
base (full fine-tune, with and without the quantity), Qwen2.5-1.5B + LoRA and, as an extra, Qwen2.5-3B + LoRA, on a
free Kaggle T4. The epoch is picked on **validation**; test metrics are computed outside, by the same script as the
other approaches. Repo: https://github.com/Bueno-00/catalogo-de-mercado
"""))


def build():
    import nbformat as nbf

    nb = nbf.v4.new_notebook()
    nb.metadata = {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                   "language_info": {"name": "python"}}
    nb.cells = [nbf.v4.new_markdown_cell(s.strip()) if k == "md" else nbf.v4.new_code_cell(s.strip()) for k, s in C]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    nbf.write(nb, OUT)
    print("escrito:", OUT)


def run_local():
    import os

    os.environ.setdefault("CATALOGO_LOCAL", "1")
    ns = {"display": print}
    for k, s in C:
        if k == "code":
            exec(compile(s, "<cell>", "exec"), ns)  # noqa: S102 (teste local do código)


if __name__ == "__main__":
    run_local() if "--local" in sys.argv else build()
