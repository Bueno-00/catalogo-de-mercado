#!/usr/bin/env python3
"""Gera o notebook v2c do Kaggle (GPU T4 grátis): a IA ajustada da MANHÃ (v1) com confiança, para entrar na combinação.

Por que: no teste, a IA v1 (LoRA que escreve o nome da categoria) acertou mais que a IA v2 (cabeça de classificação),
e ela erra coisas diferentes do clássico. Mas o v1 só guardou a resposta do teste, sem confiança e sem a validação, e
sem a validação não dá para escolher pesos. Aqui o MESMO adapter do v1 (dataset privado
`rafabueno/catalogo-mercado-lora-v1-adapter`, nada é treinado de novo) responde validação e teste de dois jeitos:

1. **Escrevendo** a resposta, igual ao v1 (mesmo prompt, mesma geração gulosa), e guardando a probabilidade da
   resposta escrita (produto das probabilidades de cada pedaço). Custo igual ao v1.
2. **Pontuando** as 41 categorias: a probabilidade de o modelo escrever cada nome inteiro. Dá a distribuição
   completa, mas custa 41 passadas curtas por produto.

O tempo é medido com o LoRA fundido nos pesos (como em produção). A escolha entre 1 e 2, e os pesos da combinação,
saem da validação (`src/catalogo/combinar.py`).

Saída em /kaggle/working: probs_lora_v1_escrita.parquet, probs_lora_v1_pontos.parquet e resultados_v2.json.

Uso:
  python kaggle/gerar_notebook_v2c.py            # escreve kaggle/notebook-v2c/catalogo-mercado-v2c.ipynb
  python kaggle/gerar_notebook_v2c.py --local    # roda aqui com um modelo minúsculo (teste do código, CPU)
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "notebook-v2c" / "catalogo-mercado-v2c.ipynb"

C: list[tuple[str, str]] = []

C.append(("md", r"""# Catálogo de mercado v2c: a IA ajustada do v1 com confiança (GPU T4 do Kaggle)

**Português** (English summary at the end). Repositório: https://github.com/Bueno-00/catalogo-de-mercado

O mesmo adapter LoRA do v1 (nada é treinado de novo) responde a **validação** e o **teste**, para poder entrar na
combinação com o clássico com pesos escolhidos na validação. Dois jeitos: **escrevendo** a resposta (igual ao v1,
com a probabilidade da resposta escrita) e **pontuando** as 41 categorias (distribuição completa, mais caro)."""))

C.append(("code", r'''import os, gc, time, json, math, difflib, subprocess, sys
from pathlib import Path
import numpy as np
import pandas as pd

LOCAL = os.environ.get("CATALOGO_LOCAL") == "1"
LIMITE = int(os.environ.get("CATALOGO_LIMITE", "0"))
MODELO = os.environ.get("CATALOGO_MODELO", "Qwen/Qwen2.5-1.5B-Instruct")

def achar(nome, raizes):
    for raiz in raizes:
        if raiz.exists():
            achados = sorted(raiz.rglob(nome))
            if achados:
                return achados[0].parent
    raise FileNotFoundError(nome)

DADOS = achar("teste.parquet", [Path("/kaggle/input"), Path(os.environ.get("CATALOGO_DADOS", "data/split"))])
ADAPTER = achar("adapter_config.json", [Path("/kaggle/input"), Path(os.environ.get("CATALOGO_ADAPTER", ".tmp/adapter-ds"))])
SAIDA = Path("/kaggle/working") if Path("/kaggle/working").exists() else Path(os.environ.get("CATALOGO_SAIDA", ".tmp/kv2c-local"))
SAIDA.mkdir(parents=True, exist_ok=True)
import torch
import transformers
GPU = torch.cuda.is_available()
DISP = "cuda" if GPU else "cpu"
if Path("/kaggle/working").exists():
    subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "-q", "torchao"], check=False)
try:
    import peft
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "peft>=0.13"], check=True)
    import peft
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer
print(f"dados={DADOS} | adapter={ADAPTER} | gpu={GPU} {torch.cuda.get_device_name(0) if GPU else ''} | "
      f"transformers {transformers.__version__} | peft {peft.__version__}")

va = pd.read_parquet(DADOS / "validacao.parquet")
te = pd.read_parquet(DADOS / "teste.parquet")
cat = json.loads((DADOS / "categorias.json").read_text())
CLASSES = list(cat["chaves"]); NOMES = cat["nomes"]
CHAVE_DE = {v.lower(): k for k, v in NOMES.items()}
if LIMITE:
    va, te = va.head(LIMITE), te.head(LIMITE)
RES = {"modelos": {}}

def salvar():
    (SAIDA / "resultados_v2.json").write_text(json.dumps(RES, indent=1, ensure_ascii=False))
'''))

C.append(("md", r"""## O modelo do v1 (mesmo prompt e mesma geração)"""))
C.append(("code", r'''tok = AutoTokenizer.from_pretrained(MODELO)
if tok.pad_token is None:
    tok.pad_token = tok.eos_token
tipo = torch.float16 if GPU else torch.float32
base = AutoModelForCausalLM.from_pretrained(MODELO, dtype=tipo).to(DISP)
modelo = PeftModel.from_pretrained(base, str(ADAPTER)).merge_and_unload()   # LoRA fundido nos pesos
modelo.eval()
FIM = "<|im_end|>" if "<|im_end|>" in tok.get_vocab() else tok.eos_token

def prompt_lora(texto):
    return f"Categoria de prateleira do produto de supermercado: {texto}"

def texto_chat(conteudo):
    return tok.apply_chat_template([{"role": "user", "content": conteudo}], tokenize=False, add_generation_prompt=True)

def mapear(resposta):
    r = resposta.strip().split("\n")[0].strip().strip(".:-* ").lower()
    if r in CHAVE_DE:
        return CHAVE_DE[r]
    m = difflib.get_close_matches(r, list(CHAVE_DE), n=1, cutoff=0.0)
    return CHAVE_DE[m[0]] if m else CLASSES[0]

@torch.no_grad()
def escrever(prompts, lote=64):
    """Geração gulosa igual ao v1 + probabilidade da resposta escrita (até o fim da resposta)."""
    tok.padding_side = "left"
    out_txt, out_p = [None] * len(prompts), [None] * len(prompts)
    ordem = np.argsort([len(p) for p in prompts])
    fim_id = tok.convert_tokens_to_ids(FIM)
    for i in range(0, len(prompts), lote):
        idx = ordem[i:i + lote]
        enc = tok([prompts[j] for j in idx], return_tensors="pt", padding=True, add_special_tokens=False).to(DISP)
        g = modelo.generate(**enc, max_new_tokens=12, do_sample=False, temperature=None, top_p=None, top_k=None,
                            pad_token_id=tok.pad_token_id, output_scores=True, return_dict_in_generate=True)
        novos = g.sequences[:, enc["input_ids"].shape[1]:]
        lp = modelo.compute_transition_scores(g.sequences, g.scores, normalize_logits=True).float().cpu().numpy()
        txt = tok.batch_decode(novos, skip_special_tokens=True)
        for k, j in enumerate(idx):
            ids = novos[k].tolist()
            n = ids.index(fim_id) + 1 if fim_id in ids else len(ids)
            out_txt[j], out_p[j] = txt[k], float(np.exp(lp[k, :n].sum()))
    return out_txt, out_p

NOMES_IDS = [tok(NOMES[c] + FIM, add_special_tokens=False)["input_ids"] for c in CLASSES]

@torch.no_grad()
def pontuar(prompts, por_lote=3):
    """Log-probabilidade de escrever cada um dos 41 nomes inteiros; só calcula a saída nas posições da resposta."""
    tok.padding_side = "right"
    K = len(CLASSES); out = np.zeros((len(prompts), K), dtype=np.float32)
    for i in range(0, len(prompts), por_lote):
        seqs, alvos = [], []
        for p in prompts[i:i + por_lote]:
            pid = tok(p, add_special_tokens=False)["input_ids"]
            for r in NOMES_IDS:
                seqs.append(pid + r); alvos.append((len(pid), r))
        n = max(len(s) for s in seqs)
        ids = torch.full((len(seqs), n), tok.pad_token_id); att = torch.zeros((len(seqs), n), dtype=torch.long)
        for k, s in enumerate(seqs):
            ids[k, :len(s)] = torch.tensor(s); att[k, :len(s)] = 1
        h = modelo.model(input_ids=ids.to(DISP), attention_mask=att.to(DISP)).last_hidden_state
        linhas, colunas, alvo, dono = [], [], [], []
        for k, (ini, r) in enumerate(alvos):
            for t, tid in enumerate(r):
                linhas.append(k); colunas.append(ini + t - 1); alvo.append(tid); dono.append(k)
        hs = h[torch.tensor(linhas, device=DISP), torch.tensor(colunas, device=DISP)]
        lp = torch.log_softmax(modelo.lm_head(hs).float(), -1)[torch.arange(len(alvo), device=DISP), torch.tensor(alvo, device=DISP)]
        soma = torch.zeros(len(seqs), device=DISP).index_add_(0, torch.tensor(dono, device=DISP), lp)
        out[i:i + por_lote] = soma.view(-1, K).cpu().numpy()
    return out

def softmax(z):
    z = z - z.max(axis=1, keepdims=True); e = np.exp(z); return e / e.sum(axis=1, keepdims=True)

def guardar(chave, pva, pte, info):
    linhas = [("validacao", i, p) for i, p in zip(va["id"], pva)] + [("teste", i, p) for i, p in zip(te["id"], pte)]
    d = pd.DataFrame([p for _, _, p in linhas], columns=CLASSES).round(5)
    d.insert(0, "id", [i for _, i, _ in linhas]); d.insert(0, "parte", [a for a, _, _ in linhas])
    d.to_parquet(SAIDA / f"probs_{chave}.parquet", index=False)
    RES["modelos"][chave] = info; salvar()
    print(chave, json.dumps(info, ensure_ascii=False), flush=True)
'''))

C.append(("md", r"""## 1. Escrevendo a resposta (igual ao v1) + a probabilidade dela

A distribuição usada na combinação: a probabilidade da resposta escrita vai para a categoria escrita, e o resto
é dividido igualmente entre as outras 40."""))
C.append(("code", r'''def distribuicao_escrita(respostas, probs):
    K = len(CLASSES); out = np.zeros((len(respostas), K), dtype=np.float32)
    for k, (r, p) in enumerate(zip(respostas, probs)):
        p = min(max(p, 1e-4), 1 - 1e-4)
        out[k] = (1 - p) / (K - 1); out[k, CLASSES.index(mapear(r))] = p
    return out

pv, pt = [texto_chat(prompt_lora(t)) for t in va["texto"]], [texto_chat(prompt_lora(t)) for t in te["texto"]]
if GPU: torch.cuda.synchronize()
t0 = time.time(); rv, cv = escrever(pv); rt, ct = escrever(pt)
if GPU: torch.cuda.synchronize()
ms_lote = 1000 * (time.time() - t0) / (len(pv) + len(pt))
um = []
for p in pt[:30]:
    if GPU: torch.cuda.synchronize()
    t1 = time.time(); escrever([p], lote=1)
    if GPU: torch.cuda.synchronize()
    um.append(time.time() - t1)
yv, yt = np.array([CLASSES.index(c) for c in va["categoria"]]), np.array([CLASSES.index(c) for c in te["categoria"]])
dv, dt = distribuicao_escrita(rv, cv), distribuicao_escrita(rt, ct)
pd.DataFrame({"id": te["id"], "resposta": rt, "pred": [mapear(r) for r in rt], "prob": np.round(ct, 5)}).to_csv(SAIDA / "lora_v1_escrita_teste.csv", index=False)
guardar("lora_v1_escrita", dv, dt, {"jeito": "escrevendo (igual ao v1), LoRA fundido", "acerto_validacao": float((dv.argmax(1) == yv).mean()),
        "acerto_teste_rapido": float((dt.argmax(1) == yt).mean()), "ms_por_item_lote_gpu": round(ms_lote, 2),
        "ms_um_a_um_gpu": round(1000 * float(np.median(um)), 1)})
'''))

C.append(("md", r"""## 2. Pontuando as 41 categorias (distribuição completa)"""))
C.append(("code", r'''if GPU: torch.cuda.synchronize()
t0 = time.time(); sv = pontuar(pv); st = pontuar(pt)
if GPU: torch.cuda.synchronize()
ms_lote = 1000 * (time.time() - t0) / (len(pv) + len(pt))
um = []
for p in pt[:20]:
    if GPU: torch.cuda.synchronize()
    t1 = time.time(); pontuar([p], por_lote=1)
    if GPU: torch.cuda.synchronize()
    um.append(time.time() - t1)
qv, qt = softmax(sv), softmax(st)
guardar("lora_v1_pontos", qv, qt, {"jeito": "pontuando as 41 categorias, LoRA fundido", "acerto_validacao": float((qv.argmax(1) == yv).mean()),
        "acerto_teste_rapido": float((qt.argmax(1) == yt).mean()), "ms_por_item_lote_gpu": round(ms_lote, 2),
        "ms_um_a_um_gpu": round(1000 * float(np.median(um)), 1)})
print(json.dumps(RES, indent=1, ensure_ascii=False))
'''))

C.append(("md", r"""---

## English summary

**Grocery catalog v2c.** The same LoRA adapter from v1 (nothing is retrained) answers the **validation** and **test**
sets so it can be combined with the TF-IDF baseline using weights picked on validation. Two ways: **writing** the
answer (same prompt and greedy decoding as v1, plus the probability of the written answer) and **scoring** all 41
category names (full distribution, 41 short passes per product). Latency is measured with the LoRA merged into the
weights. Repo: https://github.com/Bueno-00/catalogo-de-mercado
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
