# Resultados (gerado por `python -m catalogo.avaliar`)

Teste: **1.587 produtos** do Brasil. **41 categorias**. marcas que não aparecem no treino.

| Caminho | Acerto | IC 95% | F1 macro | Tempo por produto | Onde roda |
|---|---|---|---|---|---|
| IA sem treino (1,5 B) | **27,5%** | 25,3% a 29,6% | 24,6% | 118 ms (lote) / 470 ms (um a um) | GPU T4 (grátis no Kaggle) |
| IA sem treino (7 B) | **66,9%** | 64,5% a 69,3% | 65,3% | 491 ms (lote) / 1066 ms (um a um) | GPU T4 (grátis no Kaggle) |
| Clássico (TF-IDF) | **75,8%** | 73,7% a 78,1% | 75,4% | 0.37 ms (lote) / 8 ms (um a um) | CPU comum (ou o navegador); sem GPU |
| IA ajustada (LoRA) | **78,9%** | 76,9% a 81,0% | 76,8% | 37 ms (lote) / 713 ms (um a um) | GPU T4 (grátis no Kaggle) |

- LoRA menos TF-IDF (bootstrap pareado): 1,1% a 4,9% pontos.
- LoRA menos zero-shot do mesmo modelo: 48,8% a 54,1% pontos.
- Quando LoRA e TF-IDF dão a mesma resposta (78,4% dos produtos), o acerto é 89,3%.
- O mesmo TF-IDF num split aleatório (marca nos dois lados): 82,9% de acerto, contra 75,8% no split por marca.

## F1 por categoria

| Categoria | n | IA sem treino (1,5 B) | IA sem treino (7 B) | Clássico (TF-IDF) | IA ajustada (LoRA) |
|---|---|---|---|---|---|
| Biscoitos e bolachas | 136 | 56,8% | 69,8% | 67,9% | 70,7% |
| Iogurtes e leites fermentados | 88 | 13,9% | 81,7% | 81,8% | 82,3% |
| Chocolates e bombons | 75 | 0,0% | 48,6% | 62,7% | 65,0% |
| Queijos e requeijão | 72 | 2,7% | 90,1% | 84,0% | 93,1% |
| Leite e bebida láctea | 69 | 0,0% | 70,3% | 83,6% | 75,9% |
| Molhos, ketchup e maionese | 60 | 37,8% | 82,9% | 92,4% | 87,1% |
| Pães e torradas | 60 | 30,1% | 81,6% | 85,7% | 91,2% |
| Salgadinhos e batata chips | 57 | 18,5% | 76,5% | 75,0% | 88,5% |
| Suplementos e proteína em pó | 55 | 70,2% | 81,4% | 76,0% | 82,5% |
| Carnes, frios e embutidos | 53 | 33,0% | 74,7% | 80,7% | 91,6% |
| Geleias, mel e cremes de passar | 50 | 0,0% | 28,6% | 61,2% | 65,2% |
| Balas, gomas e doces | 47 | 0,0% | 47,6% | 48,4% | 69,7% |
| Cereais matinais e aveia | 47 | 38,6% | 53,7% | 70,2% | 64,9% |
| Bolos, panetones e doces de padaria | 44 | 54,4% | 81,9% | 88,4% | 93,2% |
| Massas e macarrão instantâneo | 44 | 0,0% | 66,7% | 65,8% | 75,3% |
| Arroz, feijão e grãos | 39 | 70,9% | 77,8% | 81,5% | 86,1% |
| Temperos, sal e caldos | 38 | 34,8% | 66,7% | 75,4% | 76,5% |
| Pratos prontos e congelados | 36 | 40,9% | 48,3% | 57,1% | 58,7% |
| Sucos e néctares | 36 | 0,0% | 71,4% | 81,8% | 83,1% |
| Farinhas, amidos e tapioca | 35 | 51,4% | 79,5% | 83,6% | 88,6% |
| Sorvetes e picolés | 35 | 0,0% | 67,9% | 58,8% | 74,6% |
| Barras de cereal e de proteína | 33 | 11,4% | 61,0% | 76,7% | 74,6% |
| Castanhas e amendoim | 32 | 18,6% | 72,5% | 64,5% | 63,5% |
| Manteiga e margarina | 30 | 42,1% | 94,9% | 94,9% | 94,9% |
| Peixes, atum e sardinha | 30 | 32,7% | 82,1% | 94,7% | 96,8% |
| Refrigerantes | 28 | 0,0% | 52,4% | 69,8% | 80,9% |
| Açúcar e adoçante | 27 | 6,4% | 35,0% | 92,3% | 96,2% |
| Café | 26 | 6,9% | 93,9% | 90,2% | 90,6% |
| Chás | 26 | 55,6% | 87,5% | 98,0% | 96,0% |
| Óleos e azeites | 21 | 33,0% | 81,8% | 90,0% | 90,0% |
| Cervejas | 20 | 0,0% | 86,4% | 73,9% | 77,6% |
| Leite condensado e creme de leite | 20 | 26,4% | 52,9% | 69,6% | 79,1% |
| Sobremesas e misturas para doce | 18 | 19,5% | 26,9% | 75,0% | 68,8% |
| Vinhos e destilados | 17 | 10,0% | 19,0% | 44,4% | 45,2% |
| Achocolatado e cacau em pó | 16 | 10,5% | 41,2% | 90,3% | 48,0% |
| Bebidas vegetais | 14 | 4,6% | 18,0% | 63,6% | 72,7% |
| Conservas e enlatados | 12 | 14,5% | 40,0% | 52,2% | 47,6% |
| Frutas, verduras e legumes | 12 | 17,0% | 41,2% | 27,3% | 28,6% |
| Águas | 10 | 81,8% | 77,8% | 95,2% | 78,3% |
| Energéticos e isotônicos | 10 | 63,6% | 66,7% | 66,7% | 66,7% |
| Ovos | 9 | 0,0% | 100,0% | 100,0% | 90,0% |

## Confusões mais comuns: IA sem treino (1,5 B)

- Iogurtes e leites fermentados → Ovos: 44
- Leite e bebida láctea → Bebidas vegetais: 39
- Molhos, ketchup e maionese → Açúcar e adoçante: 35
- Queijos e requeijão → Massas e macarrão instantâneo: 34
- Chocolates e bombons → Achocolatado e cacau em pó: 28
- Salgadinhos e batata chips → Biscoitos e bolachas: 24
- Refrigerantes → Bebidas vegetais: 24
- Massas e macarrão instantâneo → Farinhas, amidos e tapioca: 23

## Confusões mais comuns: IA sem treino (7 B)

- Chocolates e bombons → Balas, gomas e doces: 25
- Açúcar e adoçante → Geleias, mel e cremes de passar: 16
- Refrigerantes → Bebidas vegetais: 14
- Pães e torradas → Biscoitos e bolachas: 12
- Carnes, frios e embutidos → Pratos prontos e congelados: 11
- Cereais matinais e aveia → Achocolatado e cacau em pó: 10
- Geleias, mel e cremes de passar → Balas, gomas e doces: 8
- Chocolates e bombons → Achocolatado e cacau em pó: 8

## Confusões mais comuns: Clássico (TF-IDF)

- Chocolates e bombons → Biscoitos e bolachas: 11
- Balas, gomas e doces → Chocolates e bombons: 10
- Sorvetes e picolés → Biscoitos e bolachas: 9
- Massas e macarrão instantâneo → Pratos prontos e congelados: 7
- Barras de cereal e de proteína → Suplementos e proteína em pó: 6
- Geleias, mel e cremes de passar → Castanhas e amendoim: 5
- Leite e bebida láctea → Iogurtes e leites fermentados: 5
- Pães e torradas → Biscoitos e bolachas: 5

## Confusões mais comuns: IA ajustada (LoRA)

- Chocolates e bombons → Biscoitos e bolachas: 13
- Cereais matinais e aveia → Biscoitos e bolachas: 11
- Massas e macarrão instantâneo → Pratos prontos e congelados: 9
- Vinhos e destilados → Cervejas: 8
- Cereais matinais e aveia → Chocolates e bombons: 6
- Biscoitos e bolachas → Chocolates e bombons: 6
- Biscoitos e bolachas → Salgadinhos e batata chips: 5
- Iogurtes e leites fermentados → Biscoitos e bolachas: 5
