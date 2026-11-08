# Resultados (gerado por `python -m catalogo.avaliar`)

Teste: **1.587 produtos** do Brasil. **41 categorias**. marcas que não aparecem no treino.
Acerto **original** = contra a categoria do Open Food Facts como veio. **Revisado** = contra a revisão do teste (`reports/revisao_teste.csv`: 673 produtos revistos, 70 rótulos errados, 85 ambíguos; os outros 914 ficam com o rótulo original).

| Caminho | Versão | Acerto original (IC 95%) | Acerto revisado | F1 macro | Tempo por produto (lote / um por vez) | Onde |
|---|---|---|---|---|---|---|
| IA sem treino (Qwen 1,5 B) | v1 | **27,5%** (25,3% a 29,6%) | 30,2% | 24,6% | 118 ms / 470 ms | GPU T4 (Kaggle grátis) |
| IA maior sem treino (Qwen 7 B) | v1 | **66,9%** (64,5% a 69,3%) | 73,9% | 65,3% | 491 ms / 1066 ms | GPU T4 (Kaggle grátis) |
| Clássico v1 (TF-IDF + regressão logística) | v1 | **75,8%** (73,7% a 78,1%) | 80,7% | 75,4% | 0,37 ms / 8 ms | CPU ou navegador |
| IA ajustada v1 (LoRA que escreve a resposta) | v1 | **78,9%** (76,9% a 81,0%) | 84,0% | 76,8% | 37 ms / 713 ms | GPU T4 (Kaggle grátis) |
| Clássico v2 (+ quantidade) | v2 | **79,1%** (77,1% a 81,2%) | 84,2% | 77,5% | 0,16 ms / 4 ms | CPU ou navegador |
| BERTimbau ajustado (+ quantidade) | v2 | **72,4%** (70,3% a 74,7%) | 76,9% | 70,8% | 0,42 ms / 12 ms | GPU T4 (Kaggle grátis) |
| IA ajustada v2 (LoRA classificador + quantidade) | v2 | **76,7%** (74,7% a 78,8%) | 81,0% | 75,2% | 4 ms / 44 ms | GPU T4 (Kaggle grátis) |
| IA ajustada v2, 2ª rodada (5 épocas, sem a marca; não escolhida) | v2 | **77,3%** (75,2% a 79,5%) | 82,7% | 75,5% | 4 ms / 44 ms | GPU T4 (Kaggle grátis) |
| IA v1 de novo, escrevendo, com confiança (LoRA fundido) | v2 | **79,0%** (76,9% a 81,0%) | 84,1% | 76,8% | 20 ms / 350 ms | GPU T4 (Kaggle grátis) |
| IA v1 de novo, pontuando as 41 categorias | v2 | **78,8%** (76,7% a 80,9%) | 83,9% | 76,6% | 525 ms / 523 ms | GPU T4 (Kaggle grátis) |
| 1ª combinação: clássico v2 + IA v2 + BERTimbau | v2 | **81,1%** (79,1% a 83,0%) | 86,5% | 80,2% | 5 ms / 59 ms | GPU T4 (Kaggle grátis) |
| Juntos: clássico v2 + IA | v2 | **81,5%** (79,6% a 83,5%) | 87,0% | 80,2% | 25 ms / 397 ms | GPU T4 (Kaggle grátis) |
| Cascata: clássico primeiro, IA só na dúvida | v2 | **81,5%** (79,6% a 83,5%) | 87,1% | 80,3% | 10 ms / 155 ms | GPU T4 (Kaggle grátis) |
| Cascata barata: clássico primeiro, IA classificadora só na dúvida | v2 | **81,4%** (79,5% a 83,4%) | 86,8% | 80,5% | 1 ms / 19 ms | GPU T4 (Kaggle grátis) |

- Clássico v2 menos v1: 3,3% pontos (faixa de 95%: 2,0% a 4,6%).
- IA ajustada v2 menos v1: -2,1% pontos (faixa de 95%: -3,8% a -0,5%).
- IA ajustada v2 menos clássico v2: -2,3% pontos (faixa de 95%: -4,2% a -0,5%).
- Juntos menos clássico v2: 2,5% pontos (faixa de 95%: 1,0% a 4,0%).
- Juntos menos IA ajustada v1: 2,6% pontos (faixa de 95%: 1,4% a 3,8%).
- Cascata menos clássico v2: 2,5% pontos (faixa de 95%: 1,0% a 4,0%).
- IA ajustada v1 menos clássico v1: 3,1% pontos (faixa de 95%: 1,1% a 4,9%).
- Combinação escolhida na validação: classico_v2 + lora_v1_escrita + qwen15_lora_q, pesos [0.5, 0.4, 0.1].
- Cascata: o clássico responde sozinho quando a confiança dele passa de 88%; no teste, 39% dos produtos foram para a IA e o acerto foi 81,5%.
- Quantidade no clássico: teste 79,0% sem e 79,1% com; validação cruzada 77,9% sem e 78,5% com.
- Quantidade no BERTimbau: teste 72,3% sem e 72,4% com (faixa da diferença -1,1% a 1,5%).

## Erros de cada caminho e a revisão do teste

| Caminho | Erros (original) | Rótulo errado | Ambíguo | Aceitos na revisão |
|---|---|---|---|---|
| IA sem treino (Qwen 1,5 B) | 1151 | 66 | 78 | 48 |
| IA maior sem treino (Qwen 7 B) | 525 | 66 | 78 | 114 |
| Clássico v1 (TF-IDF + regressão logística) | 384 | 64 | 45 | 83 |
| IA ajustada v1 (LoRA que escreve a resposta) | 335 | 63 | 45 | 88 |
| Clássico v2 (+ quantidade) | 332 | 67 | 46 | 84 |
| BERTimbau ajustado (+ quantidade) | 438 | 62 | 49 | 80 |
| IA ajustada v2 (LoRA classificador + quantidade) | 369 | 57 | 51 | 81 |
| IA ajustada v2, 2ª rodada (5 épocas, sem a marca; não escolhida) | 360 | 67 | 46 | 88 |
| IA v1 de novo, escrevendo, com confiança (LoRA fundido) | 334 | 63 | 45 | 88 |
| IA v1 de novo, pontuando as 41 categorias | 336 | 63 | 45 | 88 |
| 1ª combinação: clássico v2 + IA v2 + BERTimbau | 300 | 62 | 51 | 93 |
| Juntos: clássico v2 + IA | 293 | 63 | 46 | 94 |
| Cascata: clássico primeiro, IA só na dúvida | 293 | 64 | 45 | 94 |
| Cascata barata: clássico primeiro, IA classificadora só na dúvida | 295 | 62 | 49 | 94 |

## F1 por categoria (original)

| Categoria | n | Clássico v1 (TF-IDF + regressão logística) | IA ajustada v1 (LoRA que escreve a resposta) | Clássico v2 (+ quantidade) | IA ajustada v2 (LoRA classificador + quantidade) | Juntos: clássico v2 + IA | Cascata: clássico primeiro, IA só na dúvida | Rótulos revistos (errado / ambíguo) |
|---|---|---|---|---|---|---|---|---|
| Biscoitos e bolachas | 136 | 67,9% | 70,7% | 75,3% | 70,9% | 73,6% | 73,6% | 1 / 6 |
| Iogurtes e leites fermentados | 88 | 81,8% | 82,3% | 84,8% | 80,2% | 84,1% | 84,6% | 0 / 1 |
| Chocolates e bombons | 75 | 62,7% | 65,0% | 63,1% | 67,6% | 66,7% | 66,2% | 0 / 4 |
| Queijos e requeijão | 72 | 84,0% | 93,1% | 91,8% | 88,1% | 92,5% | 92,5% | 1 / 0 |
| Leite e bebida láctea | 69 | 83,6% | 75,9% | 81,2% | 75,0% | 83,2% | 83,2% | 7 / 0 |
| Molhos, ketchup e maionese | 60 | 92,4% | 87,1% | 93,1% | 88,9% | 90,8% | 90,8% | 1 / 3 |
| Pães e torradas | 60 | 85,7% | 91,2% | 88,7% | 86,4% | 91,2% | 91,2% | 0 / 0 |
| Salgadinhos e batata chips | 57 | 75,0% | 88,5% | 84,6% | 88,5% | 87,5% | 87,5% | 0 / 4 |
| Suplementos e proteína em pó | 55 | 76,0% | 82,5% | 84,0% | 85,7% | 85,5% | 86,2% | 0 / 1 |
| Carnes, frios e embutidos | 53 | 80,7% | 91,6% | 87,7% | 82,6% | 91,7% | 91,7% | 4 / 9 |
| Geleias, mel e cremes de passar | 50 | 61,2% | 65,2% | 64,4% | 62,6% | 69,6% | 68,1% | 13 / 5 |
| Balas, gomas e doces | 47 | 48,4% | 69,7% | 49,4% | 56,8% | 69,7% | 67,4% | 4 / 4 |
| Cereais matinais e aveia | 47 | 70,2% | 64,9% | 75,0% | 64,3% | 71,4% | 71,4% | 1 / 0 |
| Bolos, panetones e doces de padaria | 44 | 88,4% | 93,2% | 92,5% | 90,1% | 92,3% | 92,3% | 1 / 1 |
| Massas e macarrão instantâneo | 44 | 65,8% | 75,3% | 73,7% | 68,4% | 80,5% | 80,5% | 3 / 4 |
| Arroz, feijão e grãos | 39 | 81,5% | 86,1% | 79,0% | 86,1% | 85,0% | 85,0% | 2 / 4 |
| Temperos, sal e caldos | 38 | 75,4% | 76,5% | 75,0% | 75,0% | 78,0% | 78,0% | 4 / 5 |
| Pratos prontos e congelados | 36 | 57,1% | 58,7% | 54,1% | 46,9% | 64,0% | 64,0% | 5 / 2 |
| Sucos e néctares | 36 | 81,8% | 83,1% | 81,8% | 82,9% | 86,6% | 86,6% | 4 / 0 |
| Farinhas, amidos e tapioca | 35 | 83,6% | 88,6% | 80,0% | 82,4% | 87,0% | 87,0% | 0 / 1 |
| Sorvetes e picolés | 35 | 58,8% | 74,6% | 73,5% | 76,5% | 84,5% | 84,5% | 0 / 0 |
| Barras de cereal e de proteína | 33 | 76,7% | 74,6% | 81,8% | 83,3% | 77,4% | 79,4% | 0 / 0 |
| Castanhas e amendoim | 32 | 64,5% | 63,5% | 73,8% | 69,8% | 68,9% | 68,9% | 0 / 4 |
| Manteiga e margarina | 30 | 94,9% | 94,9% | 94,9% | 94,7% | 96,6% | 96,6% | 0 / 0 |
| Peixes, atum e sardinha | 30 | 94,7% | 96,8% | 95,1% | 90,6% | 98,4% | 98,4% | 0 / 0 |
| Refrigerantes | 28 | 69,8% | 80,9% | 75,5% | 79,2% | 85,7% | 85,7% | 4 / 0 |
| Açúcar e adoçante | 27 | 92,3% | 96,2% | 88,0% | 71,1% | 94,3% | 94,3% | 0 / 20 |
| Café | 26 | 90,2% | 90,6% | 88,0% | 90,9% | 92,3% | 92,3% | 0 / 0 |
| Chás | 26 | 98,0% | 96,0% | 96,2% | 94,1% | 100,0% | 100,0% | 0 / 0 |
| Óleos e azeites | 21 | 90,0% | 90,0% | 92,7% | 90,0% | 90,0% | 90,0% | 0 / 0 |
| Cervejas | 20 | 73,9% | 77,6% | 72,3% | 76,0% | 76,0% | 76,0% | 0 / 0 |
| Leite condensado e creme de leite | 20 | 69,6% | 79,1% | 69,6% | 69,4% | 76,2% | 76,2% | 2 / 0 |
| Sobremesas e misturas para doce | 18 | 75,0% | 68,8% | 76,5% | 64,9% | 69,0% | 73,3% | 1 / 3 |
| Vinhos e destilados | 17 | 44,4% | 45,2% | 44,4% | 53,3% | 48,3% | 48,3% | 5 / 0 |
| Achocolatado e cacau em pó | 16 | 90,3% | 48,0% | 90,3% | 59,3% | 83,9% | 83,9% | 0 / 0 |
| Bebidas vegetais | 14 | 63,6% | 72,7% | 80,0% | 60,9% | 80,0% | 80,0% | 2 / 0 |
| Conservas e enlatados | 12 | 52,2% | 47,6% | 50,0% | 66,7% | 50,0% | 50,0% | 1 / 3 |
| Frutas, verduras e legumes | 12 | 27,3% | 28,6% | 27,3% | 26,7% | 28,6% | 28,6% | 4 / 1 |
| Águas | 10 | 95,2% | 78,3% | 95,2% | 78,3% | 95,2% | 95,2% | 0 / 0 |
| Energéticos e isotônicos | 10 | 66,7% | 66,7% | 60,0% | 58,8% | 66,7% | 66,7% | 0 / 0 |
| Ovos | 9 | 100,0% | 90,0% | 94,7% | 100,0% | 94,7% | 94,7% | 0 / 0 |

## Confusões mais comuns: Clássico v1 (TF-IDF + regressão logística)

- Chocolates e bombons → Biscoitos e bolachas: 11
- Balas, gomas e doces → Chocolates e bombons: 10
- Sorvetes e picolés → Biscoitos e bolachas: 9
- Massas e macarrão instantâneo → Pratos prontos e congelados: 7
- Barras de cereal e de proteína → Suplementos e proteína em pó: 6
- Geleias, mel e cremes de passar → Castanhas e amendoim: 5
- Leite e bebida láctea → Iogurtes e leites fermentados: 5
- Pães e torradas → Biscoitos e bolachas: 5

## Confusões mais comuns: IA ajustada v1 (LoRA que escreve a resposta)

- Chocolates e bombons → Biscoitos e bolachas: 13
- Cereais matinais e aveia → Biscoitos e bolachas: 11
- Massas e macarrão instantâneo → Pratos prontos e congelados: 9
- Vinhos e destilados → Cervejas: 8
- Cereais matinais e aveia → Chocolates e bombons: 6
- Biscoitos e bolachas → Chocolates e bombons: 6
- Biscoitos e bolachas → Salgadinhos e batata chips: 5
- Iogurtes e leites fermentados → Biscoitos e bolachas: 5

## Confusões mais comuns: Clássico v2 (+ quantidade)

- Massas e macarrão instantâneo → Pratos prontos e congelados: 11
- Balas, gomas e doces → Chocolates e bombons: 11
- Chocolates e bombons → Biscoitos e bolachas: 11
- Leite e bebida láctea → Iogurtes e leites fermentados: 5
- Vinhos e destilados → Cervejas: 5
- Pratos prontos e congelados → Carnes, frios e embutidos: 5
- Biscoitos e bolachas → Chocolates e bombons: 5
- Sorvetes e picolés → Biscoitos e bolachas: 4

## Confusões mais comuns: IA ajustada v2 (LoRA classificador + quantidade)

- Chocolates e bombons → Biscoitos e bolachas: 17
- Cereais matinais e aveia → Biscoitos e bolachas: 11
- Massas e macarrão instantâneo → Pratos prontos e congelados: 11
- Pratos prontos e congelados → Carnes, frios e embutidos: 8
- Biscoitos e bolachas → Pães e torradas: 7
- Biscoitos e bolachas → Chocolates e bombons: 6
- Vinhos e destilados → Cervejas: 6
- Bebidas vegetais → Leite e bebida láctea: 5

## Confusões mais comuns: Juntos: clássico v2 + IA

- Chocolates e bombons → Biscoitos e bolachas: 14
- Massas e macarrão instantâneo → Pratos prontos e congelados: 9
- Cereais matinais e aveia → Biscoitos e bolachas: 8
- Vinhos e destilados → Cervejas: 8
- Biscoitos e bolachas → Chocolates e bombons: 7
- Balas, gomas e doces → Chocolates e bombons: 6
- Iogurtes e leites fermentados → Biscoitos e bolachas: 5
- Geleias, mel e cremes de passar → Castanhas e amendoim: 5

## Confusões mais comuns: Cascata: clássico primeiro, IA só na dúvida

- Chocolates e bombons → Biscoitos e bolachas: 14
- Massas e macarrão instantâneo → Pratos prontos e congelados: 9
- Cereais matinais e aveia → Biscoitos e bolachas: 8
- Vinhos e destilados → Cervejas: 8
- Balas, gomas e doces → Chocolates e bombons: 7
- Biscoitos e bolachas → Chocolates e bombons: 7
- Iogurtes e leites fermentados → Biscoitos e bolachas: 5
- Geleias, mel e cremes de passar → Castanhas e amendoim: 5
