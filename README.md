# Catálogo de mercado

**Português** · [English](README.en.md) · **Demonstração:** https://bueno-00.github.io/catalogo-de-mercado/

Dado o nome de um produto de mercado, como um lojista digitaria (`Leite Condensado Moça 395g`), dizer a
**categoria de prateleira** (`Leite condensado e creme de leite`). Três jeitos de responder, medidos no **mesmo
teste**, com marcas que nenhum modelo viu no treino:

1. **IA sem treino (zero-shot):** um modelo de linguagem aberto (`Qwen2.5-1.5B-Instruct`) recebe a lista de
   categorias e o produto. Extra: o `Qwen2.5-7B-Instruct`, 5 vezes maior, também sem treino.
2. **Clássico:** TF-IDF (palavras e pedaços de palavra) + regressão logística. Roda em CPU e no navegador.
3. **IA ajustada (LoRA):** o mesmo `Qwen2.5-1.5B` com um *adapter* LoRA treinado na GPU T4 gratuita do Kaggle.

> **Resultados (08/11/2026).** Teste com **1.587 produtos** do Brasil, **41 categorias**, marcas que não aparecem
> no treino. IA sem treino (Qwen2.5-1.5B): **27,5%** de acerto. A mesma IA com LoRA (8 minutos de treino numa T4
> grátis): **78,9%**. Clássico (TF-IDF): **75,8%**, em CPU, 100 vezes mais rápido. Uma IA 5 vezes maior sem treino
> (Qwen2.5-7B): **66,9%**. O LoRA ganha do clássico por **3,1 pontos** (faixa de 95%: 1,1 a 4,9), uma vantagem real
> mas pequena. Quando os dois concordam (78% dos produtos), acertam **89%**.

| Caminho | Acerto (faixa de 95%) | F1 macro | Tempo por produto (lote / um por vez) | Onde roda |
|---|---|---|---|---|
| IA sem treino, Qwen2.5-1.5B (zero-shot) | **27,5%** (25,3 a 29,6) | 24,6% | 118 ms / 470 ms | GPU T4 |
| IA maior sem treino, Qwen2.5-7B em 4 bits (extra) | **66,9%** (64,5 a 69,3) | 65,3% | 491 ms / 1.066 ms | GPU T4 |
| Clássico: TF-IDF + regressão logística | **75,8%** (73,7 a 78,1) | 75,4% | 0,37 ms / 8 ms | CPU ou navegador |
| IA ajustada: Qwen2.5-1.5B + LoRA | **78,9%** (76,9 a 81,0) | 76,8% | 37 ms / 713 ms | GPU T4 |

Detalhe por categoria e confusões mais comuns: [reports/resultados.md](reports/resultados.md). Respostas de cada
caminho para cada produto do teste: [reports/predicoes/](reports/predicoes/).

### O que isso quer dizer

1. **O treino é o que faz a IA servir.** Sem exemplos, o modelo de 1,5 B não conhece a régua desta loja e ainda
   tem viés de posição: 4 das 5 categorias que ele mais responde estão entre as primeiras da lista em ordem
   alfabética ("Açúcar e adoçante" saiu 192 vezes). Com LoRA, a mesma IA sobe **51 pontos** (48,8 a 54,1).
   Treinamos 18,5 milhões de parâmetros, 1,18% do modelo; o *adapter* tem 74 MB.
2. **O clássico é um adversário duro.** O LoRA ganha por 3,1 pontos no acerto e 1,4 no F1 macro, custando GPU.
   Onde ele ganha: marca conhecida do mundo e palavra enganosa ("Doritos Sabor Queso" é salgadinho, não queijo).
   Onde ele perde: palavra que puxa para o lado errado ("Chocapic" vira chocolate).
3. **Juntos viram uma fila de revisão.** Quando clássico e LoRA dão a mesma resposta (78% dos produtos), o acerto
   é 89%: dá para aprovar sozinho e mandar só os 22% restantes para uma pessoa. Nos que discordam, o LoRA acerta
   41% e o clássico 27%.
4. **Modelo maior sem treino ajuda, mas não basta.** O 7 B sem treino (66,9%) fica abaixo do clássico e do LoRA,
   e é 13 vezes mais lento que o LoRA em lote. Ele brilha onde precisa saber do mundo ("Ristretto" é café).

### Custo e tempo

Tudo rodou de graça: CPU da máquina para o clássico e a GPU T4 da cota gratuita do Kaggle para as IAs (o notebook
inteiro, com os 3 modelos de IA, levou cerca de 30 minutos de GPU). Por 1.000 produtos, em lote: clássico 0,4 s de
CPU; LoRA 37 s de GPU; zero-shot 1,5 B 118 s; zero-shot 7 B 491 s. Um produto por vez (cadastro na hora): clássico
8 ms, LoRA 0,7 s. Nenhuma API paga.

## O problema real

Em marketplace de comida e de mercado, quem cadastra o produto é o lojista: texto curto, abreviado, sem padrão
(`LEITE COND MOCA 395G`, `Bisc. Recheado Choc 140g`). Categoria errada some da busca, cai na vitrine errada e
atrapalha a recomendação. É o problema do time de catálogo do iFood, que classifica ofertas numa taxonomia e usa
LLM para rotular dados e vigiar os classificadores ([Castro e Menezes, iFood, workshop WAMLM no KDD 2024](https://wamlm-kdd.github.io/wamlm/roundtables/wamlm_kdd24_anna_castro.pdf)).
O próprio Open Food Facts tem um robô para isso ([Robotoff](https://github.com/openfoodfacts/robotoff)).

Este repositório é um recorte **pequeno e público** desse problema. Não é um produto: é uma medição honesta de
quando vale treinar uma IA e quando o clássico resolve, com custo e tempo de cada caminho.

## Dados

- **Open Food Facts** (licença ODbL), só produtos com `en:brazil` em `countries_tags`. O arquivo público tem
  ~8 GB e 4,9 milhões de produtos; `src/catalogo/dados.py` baixa só os ~270 MB das 7 colunas usadas, em
  paralelo, para um arquivo local esparso (2 a 5 min), em vez de ler pelo DuckDB remoto (que levou 6 min
  para 300 produtos).
- **Rótulo:** a árvore de categorias do Open Food Facts mistura nós gerais e específicos, e no recorte do Brasil
  aparecem tags fora do padrão em espanhol (`en:Galletas`, `en:Yogures`). `src/catalogo/rotulos.py` junta as tags
  em **41 categorias de prateleira** com nome em português e inglês; quando um produto bate em mais de uma, fica
  a mais específica (biscoito de chocolate vai para biscoitos, achocolatado não vira chocolate).
- **Texto de entrada:** nome + marca + quantidade, como uma linha de catálogo.
- **Limpeza:** mesmo texto normalizado com a mesma categoria vira um só; mesmo texto com categorias diferentes sai.

| Etapa | Produtos |
|---|---|
| Brasil no Open Food Facts (`en:brazil`) | 37.992 |
| Com nome e categoria | 9.654 |
| Com uma das 41 categorias de prateleira | 8.115 |
| Sem repetidos e sem rótulo contraditório | **7.933** |
| Treino / validação / teste (por marca) | 5.552 / 794 / 1.587 |

## Como foi medido (o que torna o número confiável)

- **Divisão por marca** (`StratifiedGroupKFold`): nenhuma marca do teste aparece no treino nem na validação.
  É o caso real de um lojista novo. Produto sem marca é agrupado pelas 3 primeiras palavras do nome.
- **Validação separada** para escolher a configuração do clássico; o teste foi usado **uma vez**, no fim.
- Os três caminhos treinam (quando treinam) **só no treino**.
- **Acerto** com faixa de 95% (bootstrap, 2.000 sorteios), **F1 macro** (média por categoria: a pequena pesa igual
  à grande) e **diferença pareada** entre caminhos (bootstrap nos mesmos itens).
- **Tempo** medido em lote e um produto por vez. O modelo do navegador é o mesmo medido no teste (pesos em
  `int8`): `tests/` confere scikit-learn x Python puro x JavaScript.

**Por que dividir por marca.** O mesmo modelo clássico, com a mesma configuração e o mesmo tamanho de treino, num
split aleatório (72% das marcas do teste já vistas no treino) acerta **82,9%**, contra **75,8%** no split por marca.
São 7 pontos de otimismo que não existem quando chega um lojista novo. Toda a Nestlé, por exemplo, ficou no teste:
nenhum modelo viu KitKat, Moça ou Chocapic no treino.

## Erros comentados

| Produto | Base diz | Modelo diz | Leitura |
|---|---|---|---|
| Doritos Sabor Queso 90g | Salgadinhos | Clássico: Queijos | **Erro do modelo.** O clássico só vê palavras ("queso"); o LoRA e o 7 B sabem o que é Doritos. |
| Chocapic Nestlé 210 g | Cereais matinais | LoRA: Chocolates | **Erro do modelo.** "Choc" puxa para chocolate; o clássico e o 7 B acertam. |
| Ristretto Nestlé 104 g | Café | LoRA: Chocolates | **Erro do modelo.** Nenhuma palavra do treino diz café; só o 7 B sabe. |
| Quilmes Cerveza Argentina Clásica 710 ml | Vinhos e destilados | Os três: Cervejas | **Rótulo errado.** A base só tinha "bebida alcoólica"; os modelos estão certos. |
| Ervilha em conserva Bonare 170g/280g | Geleias, mel e cremes | Os três: Conservas | **Rótulo errado** na base colaborativa. |
| Leite Nestlé 34 g | Chocolates | Clássico: Leite | **Ambíguo.** É a barra de chocolate "Leite"; só os 34 g dão a pista. |

## Limites

- **Base pequena e colaborativa:** 7,9 mil produtos rotulados. Parte dos rótulos do Open Food Facts está errada
  (veja os erros comentados); um ponto de acerto aqui vale pouco.
- As **41 categorias** são uma taxonomia feita por mim a partir das tags; outra taxonomia daria outros números.
- O **zero-shot** usa um prompt simples, sem exemplos (few-shot) e sem ajuste fino de prompt. Ele mostra o ponto
  de partida, não o teto de uma IA sem treino.
- O LoRA treinou **uma vez**, com uma configuração fixa (sem busca de hiperparâmetros), e a resposta é por geração
  de texto ligada à categoria mais parecida.
- O tempo da IA é numa **T4** (GPU de 2018); numa GPU atual seria bem menor. O custo é zero aqui porque a cota do
  Kaggle é gratuita.

## Como rodar

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
make dados      # recorte Brasil do Open Food Facts -> data/off_brasil.parquet
make split      # 41 categorias + divisão por marca -> data/split/
make classico   # TF-IDF + regressão logística -> reports/predicoes/tfidf.csv e docs/modelo.json
make notebook   # notebook do Kaggle (zero-shot + LoRA na GPU), ver kaggle/README.md
make avaliar    # mede os 3 caminhos no mesmo teste -> reports/resultados.md e docs/dados/
make testes     # 7 testes (inclui JavaScript = Python = scikit-learn)
make pagina     # http://127.0.0.1:8000
```

| Pasta | O que tem |
|---|---|
| `src/catalogo/` | dados, rótulos, divisão, clássico, avaliação, modelo do navegador em Python puro |
| `kaggle/` | gerador do notebook da GPU (zero-shot e LoRA), metadados do dataset |
| `reports/` | resultados (`resultados.md`), respostas de cada caminho por produto, saída do Kaggle |
| `docs/` | página de demonstração (GitHub Pages), sem servidor |
| `tests/` | testes e o roteiro que abre a página no Playwright em 1440 px e 390 px |

## Licenças e atribuição

- Código: MIT (`LICENSE`).
- Dados derivados (`data/split/`, `docs/dados/`, `docs/modelo.json`, `reports/predicoes/`): **ODbL 1.0**.
  Contém informações do [Open Food Facts](https://world.openfoodfacts.org), disponibilizadas sob a
  [Open Database License](https://opendatacommons.org/licenses/odbl/1-0/) (`DATA_LICENSE.md`).
- Modelos: Qwen2.5-1.5B-Instruct e Qwen2.5-7B-Instruct (Apache 2.0), baixados do Hugging Face no Kaggle; não são
  redistribuídos aqui. Nenhuma API paga foi usada.

Projeto de estudo de Rafael Bueno ([github.com/Bueno-00](https://github.com/Bueno-00)), parte do mesmo portfólio do
[Raio-X Fiscal](https://github.com/Bueno-00/raio-x-fiscal) (classificação de descrição de produto em NCM).
