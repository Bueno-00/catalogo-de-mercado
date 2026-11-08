# Catálogo de mercado

**Português** · [English](README.en.md) · **Demonstração:** https://bueno-00.github.io/catalogo-de-mercado/

Dado o nome de um produto de mercado, como um lojista digitaria (`Leite Condensado Moça 395g`), dizer a
**categoria de prateleira** (`Leite condensado e creme de leite`). Vários caminhos, medidos no **mesmo teste**
(1.587 produtos do Brasil, 41 categorias), com marcas que nenhum modelo viu no treino. Duas rodadas no mesmo dia:
**v1** (manhã de 08/11/2026) e **v2** (tarde de 08/11/2026).

> **Resultado (08/11/2026, tarde).** O clássico (TF-IDF, roda em CPU e no navegador) foi de **75,8%** para
> **79,1%** sem GPU, e já empata com a IA ajustada (LoRA, 79,0%). Sozinha, a IA não compensa. Como
> segunda opinião, compensa: **clássico + IA juntos acertam 81,5%** (faixa de 95%: 79,6 a 83,5), 2,6 pontos
> acima do melhor da manhã. Para produção, a recomendação é a **cascata barata**: o clássico responde sozinho quando
> está seguro e só 27% dos produtos passam por uma IA na GPU, com **81,4%** de acerto e 19 ms por
> produto em média. Revisando os rótulos duvidosos do teste, 70 estavam errados e 85 eram ambíguos; no teste
> revisado, clássico + IA acertam 87,0%.

| Caminho | Rodada | Acerto (faixa de 95%) | Teste revisado | F1 macro | Tempo por produto (lote / um por vez) | Onde roda |
|---|---|---|---|---|---|---|
| IA sem treino (Qwen 1,5 B) | v1 | **27,5%** (25,3 a 29,6) | 30,2% | 24,6% | 118 ms / 470 ms | GPU T4 |
| IA maior sem treino (Qwen 7 B) | v1 | **66,9%** (64,5 a 69,3) | 73,9% | 65,3% | 491 ms / 1.066 ms | GPU T4 |
| Clássico v1 (TF-IDF + regressão logística) | v1 | **75,8%** (73,7 a 78,1) | 80,7% | 75,4% | 0,37 ms / 8,2 ms | CPU ou navegador |
| IA ajustada v1 (LoRA que escreve a resposta) | v1 | **78,9%** (76,9 a 81,0) | 84,0% | 76,8% | 37 ms / 713 ms | GPU T4 |
| **Clássico v2 (+ quantidade)** | v2 | **79,1%** (77,1 a 81,2) | 84,2% | 77,5% | 0,16 ms / 3,6 ms | CPU ou navegador |
| BERTimbau ajustado (+ quantidade) | v2 | **72,4%** (70,3 a 74,7) | 76,9% | 70,8% | 0,42 ms / 12 ms | GPU T4 |
| IA ajustada v2 (LoRA classificador + quantidade) | v2 | **76,7%** (74,7 a 78,8) | 81,0% | 75,2% | 4,4 ms / 44 ms | GPU T4 |
| IA ajustada v2, 2ª rodada (5 épocas, sem a marca; não escolhida) | v2 | **77,3%** (75,2 a 79,5) | 82,7% | 75,5% | 4,4 ms / 44 ms | GPU T4 |
| IA v1 de novo, escrevendo, com confiança (LoRA fundido) | v2 | **79,0%** (76,9 a 81,0) | 84,1% | 76,8% | 20 ms / 350 ms | GPU T4 |
| IA v1 de novo, pontuando as 41 categorias | v2 | **78,8%** (76,7 a 80,9) | 83,9% | 76,6% | 525 ms / 523 ms | GPU T4 |
| 1ª combinação: clássico v2 + IA v2 + BERTimbau | v2 | **81,1%** (79,1 a 83,0) | 86,5% | 80,2% | 5,0 ms / 59 ms | GPU T4 |
| **Juntos: clássico v2 + IA** | v2 | **81,5%** (79,6 a 83,5) | 87,0% | 80,2% | 25 ms / 397 ms | GPU T4 |
| Cascata: clássico primeiro, IA só na dúvida | v2 | **81,5%** (79,6 a 83,5) | 87,1% | 80,3% | 9,6 ms / 155 ms | CPU + GPU em 39% dos produtos |
| **Cascata barata: clássico primeiro, IA classificadora só na dúvida** | v2 | **81,4%** (79,5 a 83,4) | 86,8% | 80,5% | 1,5 ms / 19 ms | CPU + GPU em 27% dos produtos |

**Teste revisado:** conta como certo quando a categoria da base estava errada (ou valia duas) e o modelo acertou o
produto. Veja [Rótulo errado não é erro do modelo](#rótulo-errado-não-é-erro-do-modelo). O número principal é
sempre o da primeira coluna (contra a base como veio). Tempos: GPU T4 do Kaggle (de 2018) para as IAs, com o LoRA
fundido nos pesos nas linhas da tarde; CPU comum de 2 núcleos para o clássico (no navegador, cerca de 0,13 ms por
produto).

Detalhe por categoria e confusões: [reports/resultados.md](reports/resultados.md). Resposta de cada caminho para
cada produto do teste: [reports/predicoes/](reports/predicoes/) e [reports/kaggle-v2/](reports/kaggle-v2/),
[kaggle-v2b/](reports/kaggle-v2b/), [kaggle-v2c/](reports/kaggle-v2c/).

## O que mudou da manhã para a tarde

1. **Clássico v2** (+3,3 pontos, faixa 2,0 a 4,6): outro modelo linear (LinearSVC no
   lugar da regressão logística), a **quantidade** em faixas como palavra extra e cada produto do treino repetido
   **sem as palavras da marca** (o lojista novo traz uma marca que o modelo nunca viu). Tudo escolhido por validação
   cruzada agrupada por marca dentro de treino + validação ([reports/classico_cv.json](reports/classico_cv.json)).
2. **IA como classificador** (o mesmo Qwen2.5-1.5B com LoRA, mas com uma cabeça de classificação no lugar de escrever o
   nome da categoria): uma passada, 41 probabilidades, 44 ms por produto. Mais rápida, mas **acertou menos no
   teste** (76,7%, -2,1 pontos contra a IA da manhã, faixa -3,8 a -0,5). Na validação parecia
   empatada (80,5% contra 81,5%). Leitura: escrever o nome da categoria aproveita o que o modelo
   já sabe dessas palavras; a cabeça de classificação começa do zero. Uma 2ª rodada (5 épocas e metade do treino sem
   a marca) ficou pior na validação (79,1%) e não foi escolhida.
3. **BERTimbau** (110 milhões de parâmetros, em português, ajustado inteiro): 72,4%, rápido (12 ms por produto
   na GPU, 62 ms em CPU), mas fraco aqui.
4. **A IA da manhã de volta, com confiança:** o mesmo adapter do v1 (nada treinado de novo) respondeu também a
   validação, guardando a probabilidade da resposta escrita, para poder entrar na combinação. Com o LoRA fundido nos
   pesos, o tempo um por vez caiu de 713 ms para 350 ms.
5. **Juntos:** média das probabilidades, com pesos escolhidos na validação (clássico v2 + IA da manhã (LoRA) + IA classificadora, pesos
   0,5 / 0,4 / 0,1). Eles erram coisas diferentes: quando o clássico e a IA concordam (80% dos produtos), acertam
   90,2%.
6. **Cascatas:** o clássico responde sozinho quando a confiança dele passa de um limite (escolhido na validação); o
   resto vai para a IA. Cascata com os três: 81,5%, 39% na GPU. Cascata barata (só a IA classificadora):
   81,4%, 27% na GPU.
7. **Revisão do teste:** 673 produtos revistos um a um ([reports/revisao_teste.csv](reports/revisao_teste.csv)).

**Uma decisão veio depois de olhar o teste, e fica registrada:** a ideia de trazer a IA da manhã de volta (item 4)
surgiu porque, no teste, a IA como classificador acertou menos. Os pesos e a escolha continuaram saindo da validação,
e a primeira combinação (clássico v2 + IA classificadora + BERTimbau) fica nos relatórios: 81,1% no teste. A
diferença para a final é de 0,4 ponto (faixa -0,7 a 1,6), dentro da margem.

### O que testamos e não entrou

Tudo medido só com treino + validação ([reports/experimentos_descartados.json](reports/experimentos_descartados.json)):
quantidade combinada com a 1ª palavra do nome (piorou 0,2 ponto), LightGBM em cima do clássico (piorou 1,8),
tirar do treino os produtos de rótulo suspeito (piorou 0,8) e o Qwen2.5-3B (faltou memória na T4 e dobraria o
tempo de resposta).

## Vale a pena o LoRA? Custo x ganho

**Sozinho, não.** De manhã, a IA ajustada ganhava do clássico v1 por 3,1 pontos e levava
87 vezes mais tempo por produto, um por vez (713 ms contra 8,2 ms), e precisava de GPU. À tarde, o
clássico v2 chegou ao mesmo acerto sem GPU (79,1% contra 79,0%; diferença de 0,1 ponto, faixa
-1,8 a 2,0).

| Caminho | Acerto | Erros a cada 1.000 | Máquina para 1.000 (lote) | Um produto na hora | GPU? |
|---|---|---|---|---|---|
| IA ajustada v1 (LoRA que escreve a resposta) | 78,9% | 211 | 37 s GPU | 713 ms | sim |
| Clássico v2 (+ quantidade) | 79,1% | 209 | 0,16 s CPU | 3,6 ms | não |
| IA v1 de novo, escrevendo, com confiança (LoRA fundido) | 79,0% | 210 | 20 s GPU | 350 ms | sim |
| IA ajustada v2 (LoRA classificador + quantidade) | 76,7% | 233 | 4,4 s GPU | 44 ms | sim |
| Juntos: clássico v2 + IA | 81,5% | 185 | 25 s GPU | 397 ms | sim |
| Cascata: clássico primeiro, IA só na dúvida | 81,5% | 185 | 9,6 s GPU | 155 ms | 39% dos produtos |
| Cascata barata: clássico primeiro, IA classificadora só na dúvida | 81,4% | 186 | 1,5 s GPU | 19 ms | 27% dos produtos |

- **Não vale: o LoRA sozinho**, nem responder na hora no navegador ou no celular do lojista (lá não tem GPU). O
  clássico v2 dá o mesmo acerto em 3,6 ms, de graça.
- **Vale: como segunda opinião, em lote.** A cada 1.000 produtos, clássico + IA tiram
  25 erros a mais (faixa 1,0 a 4,0 pontos). Se uma pessoa leva uns 30 segundos para achar e
  corrigir um produto na categoria errada (estimativa, não medida), são uns
  12 minutos de trabalho poupados a cada 1.000 produtos.
- **O custo de verdade é a GPU ligada**, não o produto: uma máquina com GPU esperando cadastro custa o mês inteiro.
  Por isso a cascata manda para a IA só o que o clássico não tem certeza.

**Recomendação para produção: a cascata barata.** (1) O clássico v2 responde na hora, em CPU ou no navegador; quando a
confiança dele passa de 68% (73% dos produtos), ele acerta 91,1%. (2) O resto (27%) vai
para a IA classificadora, em lote, com a GPU ligada só nessa hora. (3) Quando os dois discordam, o produto vai para
uma pessoa. No teste: **81,4%**, 19 ms por produto em média. A cascata com os três juntos dá
81,5% (diferença dentro da margem: -1,0 a 1,3 pontos) e custa 8 vezes mais por produto.

## A quantidade (gramas, litros, unidades)

Ideia do Rafael: “Leite Nestlé 34 g” pode ser leite ou chocolate, mas não existe caixa de leite de 34 g. O
`src/catalogo/quantidade.py` lê a quantidade do texto (`395g`, `1,5 L`, `6x350ml`, `1.000 g`, `2 unidades`),
normaliza (tudo em gramas, mililitros ou unidades) e coloca em faixas (até 20 g, 20 a 45 g, 45 a 90 g...). O clássico
recebe o tipo e a faixa como palavras extras; as IAs recebem a quantidade normalizada no fim do texto. A mesma
leitura roda no navegador (`docs/classificador.js`), e os testes conferem que Python e JavaScript leem igual em
todos os 7.933 produtos.

| Mesmo modelo, sem e com a quantidade | Sem | Com |
|---|---|---|
| Clássico, validação cruzada (onde escolhemos) | 77,9% | 78,5% |
| Clássico, teste | 79,0% | 79,1% |
| BERTimbau, teste | 72,3% | 72,4% |

**Leitura honesta:** a quantidade ajuda a desempatar, mas pesa pouco no total, porque a maioria dos nomes já diz o
que é o produto. No clássico ela muda a resposta de 51 produtos do teste, com saldo quase zero. Também
testamos a faixa combinada com a primeira palavra do nome (“leite” + 20 a 45 g): na validação cruzada piorou, e
saiu. No próprio “Leite Nestlé 34 g”, o nome “Leite” ainda pesa mais que os 34 g.

## Rótulo errado não é erro do modelo

O Open Food Facts é colaborativo e tem erro. Revisamos, produto por produto e olhando só o nome, os
**673 produtos do teste** em que pelo menos um caminho da manhã (clássico v1, IA v1, 7 B) errou:

- **70 rótulos errados** (cerveja em “vinhos e destilados”, leite fermentado em “leite”, bala em “geleias”,
  requeijão em “creme de leite”, Monster em “refrigerantes”);
- **85 ambíguos**, que valem duas categorias (mel, que a regra das tags põe em açúcar mas o nome da outra
  categoria diz mel; nuggets e empanados entre carnes e pratos prontos; alfajor entre bolos e biscoitos);
- 518 com o rótulo certo (o erro era do modelo). Os outros 914 produtos (os três acertaram) não
  foram revistos.

Dos 335 erros da IA da manhã, **88 viram acerto** na revisão; dos 293 erros de clássico + IA,
94. O teste não foi mexido: o número principal é contra a base como veio. A revisão foi feita com ajuda
de IA (Claude), **antes** de medir os modelos da tarde, e está aberta para conferir. Ela favorece um pouco todos
os modelos (só revimos onde algum errou), por isso a comparação vale sempre pelo número original.

## Por categoria: onde ainda erra

As 8 categorias mais fracas em clássico + IA (todas as 41 em [reports/resultados.md](reports/resultados.md)):

| Categoria | n | F1 clássico v1 | F1 IA v1 | F1 clássico v2 | F1 clássico + IA | Rótulos revistos (errado / ambíguo) |
|---|---|---|---|---|---|---|
| Frutas, verduras e legumes | 12 | 27% | 29% | 27% | 29% | 4 / 1 |
| Vinhos e destilados | 17 | 44% | 45% | 44% | 48% | 5 / 0 |
| Conservas e enlatados | 12 | 52% | 48% | 50% | 50% | 1 / 3 |
| Pratos prontos e congelados | 36 | 57% | 59% | 54% | 64% | 5 / 2 |
| Chocolates e bombons | 75 | 63% | 65% | 63% | 67% | 0 / 4 |
| Energéticos e isotônicos | 10 | 67% | 67% | 60% | 67% | 0 / 0 |
| Castanhas e amendoim | 32 | 65% | 63% | 74% | 69% | 0 / 4 |
| Sobremesas e misturas para doce | 18 | 75% | 69% | 76% | 69% | 1 / 3 |

- **Frutas, verduras e legumes** é a categoria “sobra”: na base aparecem nela geleia, granola, farinha de coco e
  achocolatado.
- **Vinhos e destilados** recebe cerveja importada que só tinha a tag “bebida alcoólica”, e Skol Beats fica entre
  cerveja e drinque.
- **Conservas** x **grãos**: milho, ervilha e grão-de-bico em lata aparecem nos dois lados, conforme quem cadastrou.
- **Balas** x **chocolates**: bombom e trufa ficam no limite; Tic Tac e balas aparecem até em geleias.
- **Pratos prontos** faz fronteira com massas (lasanha, mac’n cheese) e com carnes (nuggets, empanados).

O que resolveria de vez: regras melhores na hora de juntar as tags (rótulos v2, aplicadas no treino) e mais
informação que o nome (foto, código de barras, descrição).

## Erros comentados

| Produto | Base diz | Leitura |
|---|---|---|
| Leite Nestlé 34 g | Chocolates | **Ambíguo.** É a barra “Leite”. A quantidade entrou como pista, mas o nome ainda pesa mais. |
| Doritos Sabor Queso 90g | Salgadinhos | **Erro do modelo** (clássico v1: queijo). As IAs sabem o que é Doritos; no v2 o clássico também acerta. |
| Chocapic Nestlé 210 g | Cereais matinais | **Erro do modelo** (IA v1: chocolate). “Choc” puxa para chocolate. |
| Ristretto Nestlé 104 g | Café | **Erro do modelo.** Nenhuma palavra do treino diz café; só quem conhece o mundo sabe. |
| Quilmes Cerveza Argentina Clásica 710 ml | Vinhos e destilados | **Rótulo errado.** É cerveja; a base só tinha “bebida alcoólica”. |
| Ervilha em conserva Bonare 170g/280g | Geleias, mel e cremes | **Rótulo errado.** É conserva. |
| Leite Fermentado c/Fibras Danone Activia | Leite e bebida láctea | **Rótulo errado.** Leite fermentado é da categoria de iogurtes. |
| Mel Silvestre Da Matina 500g | Açúcar e adoçante | **Ambíguo.** A regra põe mel em açúcar; o nome da outra categoria diz mel. Os dois valem. |

Na página, cada um mostra quem acertou (clássico v1, IA v1, clássico v2, IA classificadora, juntos).

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
  paralelo, para um arquivo local esparso (2 a 5 min).
- **Rótulo:** `src/catalogo/rotulos.py` junta as tags em **41 categorias de prateleira** com nome em português e
  inglês; quando um produto bate em mais de uma, fica a mais específica.
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

- **Divisão por marca** (`StratifiedGroupKFold`): nenhuma marca do teste aparece no treino nem na validação. É o
  caso real de um lojista novo. Produto sem marca é agrupado pelas 3 primeiras palavras do nome.
- **O teste é o mesmo da manhã** (1.587 produtos) e foi usado **uma vez por versão**. Tudo o que foi escolhido
  (configuração do clássico, época das IAs, pesos da combinação, limite da cascata) foi escolhido na validação ou
  em validação cruzada agrupada por marca dentro de treino + validação.
- Todos os caminhos treinam **só no treino**.
- **Acerto** com faixa de 95% (bootstrap, 2.000 sorteios), **F1 macro** (a categoria pequena pesa igual à grande) e
  **diferença pareada** entre caminhos (bootstrap nos mesmos produtos).
- **Tempo** medido em lote e um produto por vez. O modelo do navegador é o mesmo medido no teste (pesos em `int8`):
  `tests/` confere scikit-learn x Python puro x JavaScript.

**Por que dividir por marca.** O mesmo clássico v1, com o mesmo tamanho de treino, num split aleatório (72% das
marcas do teste já vistas no treino) acerta **82,9%**, contra **75,8%** no split por marca. Toda a Nestlé,
por exemplo, ficou no teste: nenhum modelo viu KitKat, Moça ou Chocapic no treino.

## Limites

- **Base pequena e colaborativa:** 7,9 mil produtos rotulados, com erro de rótulo (veja a revisão).
- As **41 categorias** são uma taxonomia feita a partir das tags; outra taxonomia daria outros números.
- O **zero-shot** usa um prompt simples, sem exemplos. Mostra o ponto de partida, não o teto de uma IA sem treino.
- As IAs treinaram **uma vez** cada (a classificadora, duas), sem busca de hiperparâmetros (só a época foi escolhida
  na validação). A validação tem só 794 produtos: na IA classificadora, ela prometeu mais do que o teste entregou.
- A **revisão do teste** foi feita com ajuda de IA, olhando só o nome; ninguém abriu a embalagem.
- O tempo da IA é numa **T4** (GPU de 2018). O custo foi zero porque a cota do Kaggle é gratuita.

## Como rodar

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
make dados      # recorte Brasil do Open Food Facts -> data/off_brasil.parquet
make split      # 41 categorias + divisão por marca -> data/split/
make escolher   # validação cruzada por marca (treino + validação) para o clássico v2
make classico   # clássico v2 (docs/modelo.json), v1 e o teste de vazamento
make notebook   # notebooks do Kaggle (v1 e v2), ver kaggle/README.md
make combinar   # juntos + cascata, escolhidos na validação
make avaliar    # mede todos os caminhos no mesmo teste -> reports/ e docs/dados/
make testes     # 9 testes (inclui JavaScript = Python = scikit-learn)
make pagina     # http://127.0.0.1:8000
```

| Pasta | O que tem |
|---|---|
| `src/catalogo/` | dados, rótulos, divisão, quantidade, clássico, combinação, avaliação, modelo do navegador em Python puro |
| `kaggle/` | geradores dos notebooks da GPU (v1 e v2), metadados do dataset |
| `reports/` | resultados, revisão do teste, respostas e probabilidades de cada caminho, saída do Kaggle |
| `docs/` | página de demonstração (GitHub Pages), sem servidor |
| `tests/` | testes e o roteiro que abre a página no Playwright em 1440 px e 390 px |

## Licenças e atribuição

- Código: MIT (`LICENSE`).
- Dados derivados (`data/split/`, `docs/dados/`, `docs/modelo.json`, `reports/predicoes/`, `reports/kaggle-v2/`,
  `reports/revisao_teste.csv`): **ODbL 1.0**. Contém informações do [Open Food Facts](https://world.openfoodfacts.org),
  disponibilizadas sob a [Open Database License](https://opendatacommons.org/licenses/odbl/1-0/) (`DATA_LICENSE.md`).
- Modelos: Qwen2.5-1.5B-Instruct e Qwen2.5-7B-Instruct (Apache 2.0) e BERTimbau base (MIT), baixados do Hugging
  Face no Kaggle; não são redistribuídos aqui. Nenhuma API paga foi usada.

Projeto de estudo de Rafael Bueno ([github.com/Bueno-00](https://github.com/Bueno-00)), parte do mesmo portfólio do
[Raio-X Fiscal](https://github.com/Bueno-00/raio-x-fiscal) (classificação de descrição de produto em NCM).
