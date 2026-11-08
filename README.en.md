# Grocery catalog (Catálogo de mercado)

[Português](README.md) · **English** · **Demo:** https://bueno-00.github.io/catalogo-de-mercado/?lang=en

Given a grocery product name the way a store would type it (`Leite Condensado Moça 395g`, Brazilian Portuguese),
predict its **shelf category** (`Condensed milk and cream`). Three approaches, measured on the **same test set**,
with brands that no model saw in training:

1. **Untrained AI (zero-shot):** an open language model (`Qwen2.5-1.5B-Instruct`) gets the category list and the
   product. Extra: `Qwen2.5-7B-Instruct`, 5x bigger, also untrained.
2. **Classic:** TF-IDF (words and character n-grams) + logistic regression. Runs on a CPU and in the browser.
3. **Tuned AI (LoRA):** the same `Qwen2.5-1.5B` with a LoRA adapter trained on Kaggle's free T4 GPU.

> **Results (2026-11-08).** Test set of **1,587 Brazilian products**, **41 categories**, brands not seen in
> training. Untrained AI (Qwen2.5-1.5B): **27.5%** accuracy. The same model with LoRA (8 minutes of training on a
> free T4): **78.9%**. Classic (TF-IDF): **75.8%**, on a CPU, 100x faster. A 5x bigger untrained model
> (Qwen2.5-7B): **66.9%**. LoRA beats the classic model by **3.1 points** (95% range: 1.1 to 4.9), a real but small
> edge. When the two agree (78% of products), they are right **89%** of the time.

| Approach | Accuracy (95% range) | Macro F1 | Time per product (batched / one at a time) | Runs on |
|---|---|---|---|---|
| Untrained AI, Qwen2.5-1.5B (zero-shot) | **27.5%** (25.3 to 29.6) | 24.6% | 118 ms / 470 ms | T4 GPU |
| Bigger untrained AI, Qwen2.5-7B 4-bit (extra) | **66.9%** (64.5 to 69.3) | 65.3% | 491 ms / 1,066 ms | T4 GPU |
| Classic: TF-IDF + logistic regression | **75.8%** (73.7 to 78.1) | 75.4% | 0.37 ms / 8 ms | CPU or browser |
| Tuned AI: Qwen2.5-1.5B + LoRA | **78.9%** (76.9 to 81.0) | 76.8% | 37 ms / 713 ms | T4 GPU |

Per-category detail and most common confusions: [reports/resultados.md](reports/resultados.md). Every approach's
answer for every test product: [reports/predicoes/](reports/predicoes/).

### What it means

1. **Training is what makes the AI useful.** Without examples, the 1.5B model does not know this store's rules
   and shows position bias: 4 of the 5 categories it answers most are among the first in the alphabetical list
   ("Açúcar e adoçante", sugar, came out 192 times). With LoRA the same model gains **51 points** (48.8 to 54.1).
   We trained 18.5 million parameters, 1.18% of the model; the adapter is 74 MB.
2. **The classic model is a tough baseline.** LoRA wins by 3.1 accuracy points and 1.4 macro-F1 points, at the cost
   of a GPU. Where it wins: world knowledge of brands and misleading words ("Doritos Sabor Queso" is a chip, not a
   cheese). Where it loses: a word that pulls the wrong way ("Chocapic" becomes chocolate).
3. **Together they make a review queue.** When the classic model and LoRA agree (78% of products), accuracy is 89%:
   auto-approve those and send only the remaining 22% to a person. When they disagree, LoRA is right 41% of the
   time and the classic model 27%.
4. **A bigger untrained model helps, but is not enough.** The untrained 7B (66.9%) stays below both the classic
   model and LoRA, and is 13x slower than LoRA batched. It shines where world knowledge matters ("Ristretto" is
   coffee).

### Cost and latency

Everything ran for free: the machine's CPU for the classic model and the T4 GPU from Kaggle's free quota for the
AIs (the whole notebook, with all 3 AI runs, took about 30 GPU minutes). Per 1,000 products, batched: classic 0.4 s
of CPU; LoRA 37 s of GPU; zero-shot 1.5B 118 s; zero-shot 7B 491 s. One product at a time (live listing): classic
8 ms, LoRA 0.7 s. No paid API.

## The real problem

In food and grocery marketplaces, the store types the product: short, abbreviated, inconsistent text
(`LEITE COND MOCA 395G`). A wrong category drops out of search, lands on the wrong shelf and hurts
recommendations. This is the problem iFood's catalog team works on: classifying offers into a taxonomy and using
LLMs to label data and monitor classifiers ([Castro & Menezes, iFood, WAMLM workshop at KDD 2024](https://wamlm-kdd.github.io/wamlm/roundtables/wamlm_kdd24_anna_castro.pdf)).
Open Food Facts has its own robot for it ([Robotoff](https://github.com/openfoodfacts/robotoff)).

This repository is a **small, public** slice of that problem. It is not a product: it is an honest measurement of
when training an AI is worth it and when the classic model is enough, with the cost and latency of each approach.

## Data

- **Open Food Facts** (ODbL), only products with `en:brazil` in `countries_tags`. The public Parquet file is
  ~8 GB with 4.9 million products; `src/catalogo/dados.py` downloads only the ~270 MB of the 7 columns used, in
  parallel, into a local sparse file (2 to 5 min), instead of reading through remote DuckDB (6 min for 300 products).
- **Label:** the Open Food Facts category tree mixes generic and specific nodes, and the Brazilian slice has
  non-canonical Spanish tags (`en:Galletas`, `en:Yogures`). `src/catalogo/rotulos.py` maps tags into **41 shelf
  categories** with Portuguese and English names; when a product matches several, the most specific wins (a
  chocolate biscuit is a biscuit, a cocoa drink mix is not a chocolate).
- **Input text:** name + brand + quantity, like a catalog line.
- **Cleaning:** the same normalized text with the same category is kept once; the same text with conflicting
  categories is dropped.

| Step | Products |
|---|---|
| Brazil in Open Food Facts (`en:brazil`) | 37,992 |
| With a name and a category | 9,654 |
| With one of the 41 shelf categories | 8,115 |
| Deduplicated, no conflicting labels | **7,933** |
| Train / validation / test (by brand) | 5,552 / 794 / 1,587 |

## How it was measured (what makes the number trustworthy)

- **Split by brand** (`StratifiedGroupKFold`): no test brand appears in train or validation, which is the real case
  of a new store listing products. Products without a brand are grouped by the first 3 words of the name.
- **Separate validation set** to pick the classic model's settings; the test set was used **once**, at the end.
- All three approaches train (when they train) **on the train set only**.
- **Accuracy** with a 95% range (bootstrap, 2,000 resamples), **macro F1** (small categories weigh as much as big
  ones) and **paired differences** between approaches (bootstrap on the same items).
- **Latency** measured batched and one product at a time. The browser model is the same one measured on the test
  set (`int8` weights): `tests/` checks scikit-learn vs. pure Python vs. JavaScript.

**Why split by brand.** The same classic model, same settings, same training size, on a random split (72% of
test brands already seen in training) scores **82.9%**, versus **75.8%** on the brand split. That is 7 points of
optimism that vanish when a new store shows up. All of Nestlé, for example, landed in the test set: no model saw
KitKat, Moça or Chocapic in training.

## Commented errors

| Product | Database says | Model says | Reading |
|---|---|---|---|
| Doritos Sabor Queso 90g | Chips and salty snacks | Classic: Cheese | **Model error.** The classic model only sees words ("queso"); LoRA and the 7B know what Doritos is. |
| Chocapic Nestlé 210 g | Breakfast cereals | LoRA: Chocolates | **Model error.** "Choc" pulls toward chocolate; the classic model and the 7B get it right. |
| Ristretto Nestlé 104 g | Coffee | LoRA: Chocolates | **Model error.** No training word says coffee; only the 7B knows. |
| Quilmes Cerveza Argentina Clásica 710 ml | Wine and spirits | All three: Beer | **Wrong label.** The database only had "alcoholic beverage"; the models are right. |
| Ervilha em conserva Bonare 170g/280g | Jams, honey and spreads | All three: Canned food | **Wrong label** in the crowdsourced database. |
| Leite Nestlé 34 g | Chocolates | Classic: Milk | **Ambiguous.** It is the "Leite" chocolate bar; only the 34 g hints at it. |

## Limits

- **Small, crowdsourced data:** 7.9k labeled products. Some Open Food Facts labels are wrong (see the commented
  errors); one accuracy point here means little.
- The **41 categories** are a taxonomy I built from the tags; another taxonomy would give other numbers.
- **Zero-shot** uses a simple prompt, with no examples (few-shot) and no prompt tuning. It shows the starting
  point, not the ceiling of an untrained AI.
- LoRA was trained **once**, with a fixed configuration (no hyperparameter search), and answers by text generation
  mapped to the closest category.
- AI latency is on a **T4** (a 2018 GPU); a current GPU would be much faster. Cost is zero here because Kaggle's
  GPU quota is free.

## How to run

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
make dados      # Brazilian slice of Open Food Facts -> data/off_brasil.parquet
make split      # 41 categories + split by brand -> data/split/
make classico   # TF-IDF + logistic regression -> reports/predicoes/tfidf.csv and docs/modelo.json
make notebook   # Kaggle notebook (zero-shot + LoRA on GPU), see kaggle/README.md
make avaliar    # measures the 3 approaches on the same test -> reports/resultados.md and docs/dados/
make testes     # 7 tests (including JavaScript = Python = scikit-learn)
make pagina     # http://127.0.0.1:8000
```

## Licenses and attribution

- Code: MIT (`LICENSE`).
- Derived data (`data/split/`, `docs/dados/`, `docs/modelo.json`, `reports/predicoes/`): **ODbL 1.0**. Contains
  information from [Open Food Facts](https://world.openfoodfacts.org), which is made available here under the
  [Open Database License](https://opendatacommons.org/licenses/odbl/1-0/) (`DATA_LICENSE.md`).
- Models: Qwen2.5-1.5B-Instruct and Qwen2.5-7B-Instruct (Apache 2.0), downloaded from Hugging Face on Kaggle; not
  redistributed here. No paid API was used.

A study project by Rafael Bueno ([github.com/Bueno-00](https://github.com/Bueno-00)), part of the same portfolio as
[Raio-X Fiscal](https://github.com/Bueno-00/raio-x-fiscal) (product description to tax code classification).
