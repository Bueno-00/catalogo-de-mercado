#!/usr/bin/env python3
"""Gera o notebook do Kaggle (GPU T4 grátis) que roda os 2 caminhos com IA no MESMO teste:

- zero-shot: Qwen2.5-1.5B-Instruct sem treino (e, se der, Qwen2.5-7B-Instruct em 4 bits, sem treino);
- LoRA: o mesmo Qwen2.5-1.5B com um adapter LoRA treinado no conjunto de treino.

Os dados vêm do dataset PRIVADO `rafabueno/catalogo-mercado-br` (treino, validação e teste já divididos por
marca, ver src/catalogo/preparar.py). Saída em /kaggle/working: predicoes_teste.csv (uma linha por produto do
teste, com a resposta de cada modelo), resultados_kaggle.json (tempos, perda do treino) e adapter/ (poucos MB).

Uso:
  python kaggle/gerar_notebook.py            # escreve kaggle/notebook/catalogo-mercado-lora.ipynb
  python kaggle/gerar_notebook.py --local    # roda as células aqui com um modelo minúsculo (teste do código, CPU)
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "notebook" / "catalogo-mercado-lora.ipynb"

C: list[tuple[str, str]] = []

C.append(("md", r"""# Catálogo de mercado: IA sem treino x IA ajustada com LoRA (GPU T4 do Kaggle)

**Português** (English summary at the end). Repositório: https://github.com/Bueno-00/catalogo-de-mercado

Dado o nome de um produto de mercado (ex.: `Leite Condensado Moça 395 g`), dizer a categoria de prateleira.
Este notebook roda os dois caminhos com IA no **mesmo teste** que o modelo clássico (TF-IDF, que roda em CPU
e no navegador, fora daqui):

1. **Zero-shot**: `Qwen2.5-1.5B-Instruct` recebe a lista de categorias e o produto, sem treino nenhum.
   Extra: `Qwen2.5-7B-Instruct` em 4 bits, também sem treino, para ver se um modelo 5 vezes maior resolve.
2. **LoRA**: o mesmo `Qwen2.5-1.5B` com um *adapter* LoRA (camadas pequenas treinadas por cima dos pesos
   congelados). Só a resposta entra na perda.

Dados: produtos vendidos no Brasil do **Open Food Facts** (licença ODbL), divididos **por marca**: nenhuma
marca do teste aparece no treino. As métricas (acerto, F1 macro, intervalo de confiança) são calculadas fora
daqui, pelo mesmo script para os 3 caminhos (`src/catalogo/avaliar.py`).
"""))

C.append(("code", r'''import os, re, gc, time, json, math, random, difflib, subprocess, sys
from pathlib import Path
import numpy as np
import pandas as pd

LOCAL = os.environ.get("CATALOGO_LOCAL") == "1"      # teste do código fora do Kaggle (modelo minúsculo, CPU)
SEED = 42
MODELO = os.environ.get("CATALOGO_MODELO", "Qwen/Qwen2.5-1.5B-Instruct")
MODELO_GRANDE = "Qwen/Qwen2.5-7B-Instruct"
FAZER_GRANDE = not LOCAL                              # zero-shot com o 7B em 4 bits (pula sozinho se falhar)
EPOCAS, LR, LORA_R, LORA_ALPHA, MAX_LEN = 2, 2e-4, 16, 32, 64
BATCH, ACUM = 16, 2                                   # 32 exemplos por passo
LIMITE = int(os.environ.get("CATALOGO_LIMITE", "0"))  # 0 = tudo; no teste local, poucos itens

def achar_dados():
    for raiz in [Path("/kaggle/input"), Path(os.environ.get("CATALOGO_DADOS", "data/split"))]:
        if raiz.exists():
            achados = sorted(raiz.rglob("teste.parquet"))
            if achados:
                return achados[0].parent
    raise FileNotFoundError("teste.parquet não encontrado")

DADOS = achar_dados()
SAIDA = Path("/kaggle/working") if Path("/kaggle/working").exists() else Path(os.environ.get("CATALOGO_SAIDA", ".tmp/kaggle-local"))
SAIDA.mkdir(parents=True, exist_ok=True)
random.seed(SEED); np.random.seed(SEED)

import torch
torch.manual_seed(SEED)
GPU = torch.cuda.is_available()
DISP = "cuda" if GPU else "cpu"
print(f"dados={DADOS} | saída={SAIDA} | gpu={GPU} {torch.cuda.get_device_name(0) if GPU else ''}")
import transformers
if Path("/kaggle/working").exists():
    # a imagem do Kaggle (nov/2026) traz torchao 0.10, e o peft 0.21 recusa versões < 0.16 ao criar o LoRA;
    # não usamos torchao, então ele sai antes de importar o peft
    subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "-q", "torchao"], check=False)
try:
    import peft
except ImportError:                                   # nem toda imagem do Kaggle traz o peft
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "peft>=0.13"], check=True)
    import peft
print("torch", torch.__version__, "| transformers", transformers.__version__, "| peft", peft.__version__)
'''))

C.append(("code", r'''tr = pd.read_parquet(DADOS / "treino.parquet")
va = pd.read_parquet(DADOS / "validacao.parquet")
te = pd.read_parquet(DADOS / "teste.parquet")
cat = json.loads((DADOS / "categorias.json").read_text())
NOMES = cat["nomes"]                       # chave -> nome em português (o que o modelo lê e responde)
CHAVE_DE = {v.lower(): k for k, v in NOMES.items()}
LISTA = sorted(NOMES.values())
if LIMITE:
    tr, va, te = tr.head(LIMITE), va.head(max(LIMITE // 4, 8)), te.head(max(LIMITE // 4, 8))
print(f"treino {len(tr):,} | validação {len(va):,} | teste {len(te):,} | {len(LISTA)} categorias")
res = {"modelo": MODELO, "n_teste": len(te), "categorias": len(LISTA)}
pred = pd.DataFrame({"id": te["id"]})

def salvar():
    pred.to_csv(SAIDA / "predicoes_teste.csv", index=False)
    (SAIDA / "resultados_kaggle.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
'''))

C.append(("md", r"""## 1. Zero-shot (sem treino)

O prompt traz a lista das categorias em português e pede só o nome. A resposta é ligada à categoria mais
parecida (`difflib`) e contamos quantas vezes o modelo respondeu algo fora da lista."""))

C.append(("code", r'''from transformers import AutoTokenizer, AutoModelForCausalLM

def prompt_zero_shot(texto):
    lista = "\n".join(f"- {n}" for n in LISTA)
    return ("Você organiza o catálogo de um supermercado. Escolha a categoria de prateleira do produto.\n"
            f"Categorias possíveis:\n{lista}\n\nProduto: {texto}\n"
            "Responda só com o nome exato de uma categoria da lista, sem explicar.")

def prompt_lora(texto):
    return f"Categoria de prateleira do produto de supermercado: {texto}"

def mapear(resposta):
    r = resposta.strip().split("\n")[0].strip().strip(".:-* ").lower()
    if r in CHAVE_DE:
        return CHAVE_DE[r], True
    m = difflib.get_close_matches(r, list(CHAVE_DE), n=1, cutoff=0.0)
    return (CHAVE_DE[m[0]] if m else cat["chaves"][0]), False

def carregar(nome, quantizar=False):
    tok = AutoTokenizer.from_pretrained(nome)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    kw = {}
    if quantizar:
        from transformers import BitsAndBytesConfig
        kw["quantization_config"] = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                                                       bnb_4bit_compute_dtype=torch.float16)
        kw["device_map"] = "auto"
    tipo = torch.float16 if GPU else torch.float32
    novo = tuple(int(x) for x in transformers.__version__.split(".")[:2]) >= (4, 56)   # "dtype" substituiu "torch_dtype"
    modelo = AutoModelForCausalLM.from_pretrained(nome, **({"dtype": tipo} if novo else {"torch_dtype": tipo}), **kw)
    if not quantizar:
        modelo.to(DISP)
    modelo.eval()
    return tok, modelo

def texto_chat(tok, conteudo):
    return tok.apply_chat_template([{"role": "user", "content": conteudo}], tokenize=False, add_generation_prompt=True)

@torch.no_grad()
def gerar(tok, modelo, prompts, lote=32, max_new=12):
    tok.padding_side = "left"
    saidas = []
    ordem = np.argsort([len(p) for p in prompts])            # lotes com tamanhos parecidos = menos padding
    for i in range(0, len(prompts), lote):
        idx = ordem[i:i + lote]
        enc = tok([prompts[j] for j in idx], return_tensors="pt", padding=True, add_special_tokens=False).to(modelo.device)
        out = modelo.generate(**enc, max_new_tokens=max_new, do_sample=False, temperature=None, top_p=None, top_k=None,
                              pad_token_id=tok.pad_token_id)
        txt = tok.batch_decode(out[:, enc["input_ids"].shape[1]:], skip_special_tokens=True)
        saidas += list(zip(idx, txt))
    saidas.sort()
    return [t for _, t in saidas]

def medir(tok, modelo, prompts, nome, lote):
    if GPU: torch.cuda.synchronize()
    t0 = time.time()
    respostas = gerar(tok, modelo, prompts, lote=lote)
    if GPU: torch.cuda.synchronize()
    dt = time.time() - t0
    mapeado = [mapear(r) for r in respostas]
    pred[nome] = [m for m, _ in mapeado]
    pred[nome + "_resposta"] = respostas
    # latência de 1 produto por vez (mediana de 20), como num cadastro feito na hora
    um = []
    for p in prompts[:20]:
        t1 = time.time(); gerar(tok, modelo, [p], lote=1)
        if GPU: torch.cuda.synchronize()
        um.append(time.time() - t1)
    res[nome] = {"seg_total": round(dt, 1), "ms_por_item_lote": round(1000 * dt / len(prompts), 2),
                 "ms_um_a_um_mediana": round(1000 * float(np.median(um)), 1), "lote": lote,
                 "fora_da_lista": int(sum(not ok for _, ok in mapeado)),
                 "acerto_rapido": float(np.mean([m == c for (m, _), c in zip(mapeado, te["categoria"])]))}
    print(nome, json.dumps(res[nome], ensure_ascii=False))
    salvar()

tok, base = carregar(MODELO)
# conferência de fp16: se a T4 gerar NaN, volta para fp32 (mais lento, mas certo)
with torch.no_grad():
    enc = tok([texto_chat(tok, prompt_lora("Leite condensado Moça 395 g"))], return_tensors="pt").to(DISP)
    if not torch.isfinite(base(**enc).logits).all():
        print("NaN em fp16: recarregando em fp32"); base = base.float()
prompts_zs = [texto_chat(tok, prompt_zero_shot(t)) for t in te["texto"]]
print(prompts_zs[0][:600])
medir(tok, base, prompts_zs, "zero_shot_1_5b", lote=32)
'''))

C.append(("md", r"""## 2. LoRA: treino

- pesos do modelo congelados em fp16; adapter LoRA (r=16, alpha=32, dropout 0,05) em todas as projeções
  (`q, k, v, o, gate, up, down`);
- prompt curto (o modelo aprende as categorias no treino, não precisa da lista); só os tokens da
  resposta entram na perda (os do prompt recebem `-100`);
- laço de treino simples em PyTorch (AdamW, cosseno com aquecimento, fp16 com *GradScaler*), 2 épocas, perda
  na validação ao fim de cada época;
- o adapter (poucos MB) fica em `/kaggle/working/adapter`."""))

C.append(("code", r'''from peft import LoraConfig, get_peft_model

FIM = "<|im_end|>" if "<|im_end|>" in tok.get_vocab() else tok.eos_token

def exemplo(texto, chave):
    p = tok(texto_chat(tok, prompt_lora(texto)), add_special_tokens=False)["input_ids"]
    r = tok(NOMES[chave] + FIM, add_special_tokens=False)["input_ids"]
    ids = (p + r)[-MAX_LEN:]
    lab = ([-100] * len(p) + r)[-MAX_LEN:]
    return ids, lab

def lotes(df, tamanho, embaralhar):
    ex = [exemplo(t, c) for t, c in zip(df["texto"], df["categoria"])]
    idx = list(range(len(ex)))
    if embaralhar: random.shuffle(idx)
    for i in range(0, len(idx), tamanho):
        parte = [ex[j] for j in idx[i:i + tamanho]]
        n = max(len(a) for a, _ in parte)
        ids = torch.full((len(parte), n), tok.pad_token_id); lab = torch.full((len(parte), n), -100); att = torch.zeros((len(parte), n), dtype=torch.long)
        for k, (a, b) in enumerate(parte):
            ids[k, :len(a)] = torch.tensor(a); lab[k, :len(b)] = torch.tensor(b); att[k, :len(a)] = 1
        yield ids.to(DISP), att.to(DISP), lab.to(DISP)

cfg = LoraConfig(r=LORA_R, lora_alpha=LORA_ALPHA, lora_dropout=0.05, bias="none", task_type="CAUSAL_LM",
                 target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"])
modelo = get_peft_model(base, cfg)
modelo.print_trainable_parameters()
treinaveis = [p for p in modelo.parameters() if p.requires_grad]
for p in treinaveis:            # adapter em fp32 (estável); base segue em fp16
    p.data = p.data.float()
opt = torch.optim.AdamW(treinaveis, lr=LR, weight_decay=0.0)
passos = EPOCAS * math.ceil(math.ceil(len(tr) / BATCH) / ACUM)
aquec = max(1, int(0.03 * passos))
sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: min(1.0, (s + 1) / aquec) * 0.5 * (1 + math.cos(math.pi * min(1.0, s / passos))))
scaler = torch.amp.GradScaler("cuda", enabled=GPU)

@torch.no_grad()
def perda_validacao():
    modelo.eval(); soma = n = 0
    for ids, att, lab in lotes(va, 64, False):
        with torch.autocast(DISP, dtype=torch.float16, enabled=GPU):
            soma += modelo(input_ids=ids, attention_mask=att, labels=lab).loss.item(); n += 1
    modelo.train(); return soma / max(n, 1)

historico = []
modelo.train(); passo = 0; t0 = time.time()
for ep in range(EPOCAS):
    acum = 0; soma = cont = 0
    for ids, att, lab in lotes(tr, BATCH, True):
        with torch.autocast(DISP, dtype=torch.float16, enabled=GPU):
            perda = modelo(input_ids=ids, attention_mask=att, labels=lab).loss / ACUM
        scaler.scale(perda).backward(); acum += 1; soma += perda.item() * ACUM; cont += 1
        if acum == ACUM:
            scaler.unscale_(opt); torch.nn.utils.clip_grad_norm_(treinaveis, 1.0)
            scaler.step(opt); scaler.update(); opt.zero_grad(set_to_none=True); sched.step(); acum = 0; passo += 1
            if passo % 25 == 0:
                historico.append({"passo": passo, "perda_treino": round(soma / cont, 4), "min": round((time.time() - t0) / 60, 1)})
                print(historico[-1], flush=True); soma = cont = 0
    pv = perda_validacao()
    historico.append({"epoca": ep + 1, "perda_validacao": round(pv, 4), "min": round((time.time() - t0) / 60, 1)})
    print(historico[-1], flush=True)
t_treino = time.time() - t0
modelo.save_pretrained(str(SAIDA / "adapter"))
res["lora_treino"] = {"min": round(t_treino / 60, 1), "passos": passo, "exemplos": len(tr), "epocas": EPOCAS,
                      "lr": LR, "r": LORA_R, "alpha": LORA_ALPHA, "historico": historico,
                      "parametros_treinaveis": int(sum(p.numel() for p in treinaveis)),
                      "parametros_total": int(sum(p.numel() for p in modelo.parameters()))}
salvar()
print(f"treino: {t_treino / 60:.1f} min, {passo} passos")
'''))

C.append(("md", r"""## 3. LoRA: resposta no mesmo teste"""))

C.append(("code", r'''modelo.eval()
prompts_lora = [texto_chat(tok, prompt_lora(t)) for t in te["texto"]]
medir(tok, modelo, prompts_lora, "lora_1_5b", lote=64)
del modelo, base; gc.collect()
if GPU: torch.cuda.empty_cache()
'''))

C.append(("md", r"""## 4. Extra: modelo 5 vezes maior, sem treino (Qwen2.5-7B-Instruct em 4 bits)

Quantização em 4 bits (NF4, bitsandbytes) para caber na T4. Se a instalação ou a memória falharem, a célula
registra o motivo e segue (os resultados principais já estão salvos)."""))

C.append(("code", r'''if FAZER_GRANDE and GPU:
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "bitsandbytes>=0.45"], check=True)
        tok7, m7 = carregar(MODELO_GRANDE, quantizar=True)
        p7 = [texto_chat(tok7, prompt_zero_shot(t)) for t in te["texto"]]
        medir(tok7, m7, p7, "zero_shot_7b_4bit", lote=24)
        del m7; gc.collect(); torch.cuda.empty_cache()
    except Exception as e:  # registra e segue
        res["zero_shot_7b_4bit"] = {"pulado": repr(e)[:500]}
        print("7B pulado:", repr(e)[:500]); salvar()
salvar()
print(json.dumps({k: v for k, v in res.items() if k != "lora_treino"}, indent=1, ensure_ascii=False))
'''))

C.append(("md", r"""---

## English summary

**Grocery catalog: untrained LLM vs. LoRA-tuned LLM, on the same test as a TF-IDF baseline.** Products sold in
Brazil from **Open Food Facts** (ODbL), split **by brand** (no test brand is seen in training). This notebook runs
the two LLM paths on a free Kaggle T4: **zero-shot** `Qwen2.5-1.5B-Instruct` (and, as an extra, `Qwen2.5-7B-Instruct`
in 4-bit NF4), and the same 1.5B model with a **LoRA adapter** (r=16 on all projections, response-only loss, plain
PyTorch loop with fp16 autocast, 2 epochs). Outputs: per-item predictions for the test set, timings (batched and
one-at-a-time), training loss curve and the adapter. Metrics (accuracy, macro F1, bootstrap CIs) are computed
outside, by the same script for all three paths. Repo: https://github.com/Bueno-00/catalogo-de-mercado
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
