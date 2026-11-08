# Grocery catalog (Catálogo de mercado)

[Português](README.md) · **English** · **Demo:** https://bueno-00.github.io/catalogo-de-mercado/?lang=en

Given a grocery product name the way a store would type it (`Leite Condensado Moça 395g`, Brazilian Portuguese),
predict its **shelf category** (`Condensed milk and cream`). Several approaches, measured on the **same test set**
(1,587 Brazilian products, 41 categories), with brands that no model saw in training. Two rounds on the same day:
**v1** (morning of 2026-11-08) and **v2** (afternoon of 2026-11-08).

> **Result (2026-11-08, afternoon).** The classic model (TF-IDF, runs on a CPU and in the browser) went from
> **75.8%** to **79.1%** with no GPU, and now ties the tuned AI (LoRA, 79.0%). On its own, the AI is not
> worth it. As a second opinion, it is: **classic + AI together get 81.5%** (95% range: 79.6 to 83.5), 2.6
> points above the morning’s best. For production, the recommendation is the **cheap cascade**: the classic model
> answers alone when confident and only 27% of products go through an AI on the GPU, at **81.4%** accuracy
> and 19 ms per product on average. Reviewing the doubtful test labels, 70 were wrong and 85 were ambiguous; on
> the reviewed test, classic + AI get 87.0%.

| Approach | Round | Accuracy (95% range) | Reviewed test | Macro F1 | Time per product (batched / one at a time) | Runs on |
|---|---|---|---|---|---|---|
| AI, no training (Qwen 1.5B) | v1 | **27.5%** (25.3 to 29.6) | 30.2% | 24.6% | 118 ms / 470 ms | T4 GPU |
| Bigger AI, no training (Qwen 7B) | v1 | **66.9%** (64.5 to 69.3) | 73.9% | 65.3% | 491 ms / 1,066 ms | T4 GPU |
| Classic v1 (TF-IDF + logistic regression) | v1 | **75.8%** (73.7 to 78.1) | 80.7% | 75.4% | 0.37 ms / 8.2 ms | CPU or browser |
| Tuned AI v1 (LoRA writing the answer) | v1 | **78.9%** (76.9 to 81.0) | 84.0% | 76.8% | 37 ms / 713 ms | T4 GPU |
| **Classic v2 (+ quantity)** | v2 | **79.1%** (77.1 to 81.2) | 84.2% | 77.5% | 0.16 ms / 3.6 ms | CPU or browser |
| Fine-tuned BERTimbau (+ quantity) | v2 | **72.4%** (70.3 to 74.7) | 76.9% | 70.8% | 0.42 ms / 12 ms | T4 GPU |
| Tuned AI v2 (LoRA classifier + quantity) | v2 | **76.7%** (74.7 to 78.8) | 81.0% | 75.2% | 4.4 ms / 44 ms | T4 GPU |
| Tuned AI v2, 2nd run (5 epochs, no brand; not chosen) | v2 | **77.3%** (75.2 to 79.5) | 82.7% | 75.5% | 4.4 ms / 44 ms | T4 GPU |
| AI v1 again, writing, with confidence (merged LoRA) | v2 | **79.0%** (76.9 to 81.0) | 84.1% | 76.8% | 20 ms / 350 ms | T4 GPU |
| AI v1 again, scoring all 41 categories | v2 | **78.8%** (76.7 to 80.9) | 83.9% | 76.6% | 525 ms / 523 ms | T4 GPU |
| 1st combination: classic v2 + AI v2 + BERTimbau | v2 | **81.1%** (79.1 to 83.0) | 86.5% | 80.2% | 5.0 ms / 59 ms | T4 GPU |
| **Together: classic v2 + AI** | v2 | **81.5%** (79.6 to 83.5) | 87.0% | 80.2% | 25 ms / 397 ms | T4 GPU |
| Cascade: classic first, AI only when unsure | v2 | **81.5%** (79.6 to 83.5) | 87.1% | 80.3% | 9.6 ms / 155 ms | CPU + GPU for 39% of products |
| **Cheap cascade: classic first, classifier AI only when unsure** | v2 | **81.4%** (79.5 to 83.4) | 86.8% | 80.5% | 1.5 ms / 19 ms | CPU + GPU for 27% of products |

**Reviewed test:** counts as right when the database category was wrong (or two categories fit) and the model got
the product right. See [A wrong label is not a model error](#a-wrong-label-is-not-a-model-error). The headline number
is always the first column (against the database as it came). Timing: Kaggle T4 GPU (from 2018) for the AIs, with
the LoRA merged into the weights in the afternoon rows; a regular 2-core CPU for the classic model (in the browser,
about 0.13 ms per product).

Per-category detail and confusions: [reports/resultados.md](reports/resultados.md). Every approach’s answer for every
test product: [reports/predicoes/](reports/predicoes/) and [reports/kaggle-v2/](reports/kaggle-v2/),
[kaggle-v2b/](reports/kaggle-v2b/), [kaggle-v2c/](reports/kaggle-v2c/).

## What changed from morning to afternoon

1. **Classic v2** (+3.3 points, range 2.0 to 4.6): a different linear model (LinearSVC instead of
   logistic regression), the **quantity** as range tokens, and every training product repeated **without its brand
   words** (a new store brings a brand the model never saw). All chosen by brand-grouped cross-validation inside
   train + validation ([reports/classico_cv.json](reports/classico_cv.json)).
2. **AI as a classifier** (the same Qwen2.5-1.5B with LoRA, but with a classification head instead of writing the
   category name): one pass, 41 probabilities, 44 ms per product. Faster, but **less accurate on the
   test** (76.7%, -2.1 points vs the morning AI, range -3.8 to -0.5). On validation it looked like a tie
   (80.5% vs 81.5%). Reading: writing the category name uses what the model already knows
   about those words; a classification head starts from scratch. A 2nd run (5 epochs, half of training without the
   brand) was worse on validation (79.1%) and was not chosen.
3. **BERTimbau** (110 million parameters, Portuguese, fully fine-tuned): 72.4%, fast (12 ms per product on
   the GPU, 62 ms on a CPU), but weak here.
4. **The morning AI back, with a confidence:** the same v1 adapter (nothing retrained) also answered the validation
   set, keeping the probability of the written answer, so it could join the combination. With the LoRA merged into
   the weights, one-at-a-time latency went from 713 ms to 350 ms.
5. **Together:** average of the probabilities, weights picked on validation (classic v2 + morning AI (LoRA) + classifier AI, weights
   0.5 / 0.4 / 0.1). They make different mistakes: when the classic model and the AI agree (80% of
   products), they are right 90.2% of the time.
6. **Cascades:** the classic model answers alone when its confidence is above a threshold (picked on validation); the
   rest goes to the AI. Cascade with all three: 81.5%, 39% on GPU. Cheap cascade (classifier AI only):
   81.4%, 27% on GPU.
7. **Test review:** 673 products reviewed one by one ([reports/revisao_teste.csv](reports/revisao_teste.csv)).

**One decision came after looking at the test, and it is on record:** the idea of bringing the morning AI back (item
4) came from seeing the classifier AI do worse on the test. Weights and choices were still made on validation, and the
first combination (classic v2 + classifier AI + BERTimbau) stays in the reports: 81.1% on the test. The gap to
the final one is 0.4 point (range -0.7 to 1.6), within the margin.

### What we tried and dropped

All measured with train + validation only ([reports/experimentos_descartados.json](reports/experimentos_descartados.json)):
quantity combined with the first word of the name (0.2 point worse), LightGBM stacked on the classic model (1.8
worse), dropping training products with suspicious labels (0.8 worse) and Qwen2.5-3B (ran out of memory on the T4
and would double response time).

## Is LoRA worth it? Cost vs gain

**On its own, no.** In the morning, the tuned AI beat classic v1 by 3.1 points and took
87 times longer per product, one at a time (713 ms vs 8.2 ms), and needed a GPU. In the afternoon,
classic v2 reached the same accuracy with no GPU (79.1% vs 79.0%; a 0.1 point gap, range
-1.8 to 2.0).

| Approach | Accuracy | Errors per 1,000 | Compute for 1,000 (batched) | One product, live | GPU? |
|---|---|---|---|---|---|
| Tuned AI v1 (LoRA writing the answer) | 78.9% | 211 | 37 s GPU | 713 ms | yes |
| Classic v2 (+ quantity) | 79.1% | 209 | 0.16 s CPU | 3.6 ms | no |
| AI v1 again, writing, with confidence (merged LoRA) | 79.0% | 210 | 20 s GPU | 350 ms | yes |
| Tuned AI v2 (LoRA classifier + quantity) | 76.7% | 233 | 4.4 s GPU | 44 ms | yes |
| Together: classic v2 + AI | 81.5% | 185 | 25 s GPU | 397 ms | yes |
| Cascade: classic first, AI only when unsure | 81.5% | 185 | 9.6 s GPU | 155 ms | 39% of products |
| Cheap cascade: classic first, classifier AI only when unsure | 81.4% | 186 | 1.5 s GPU | 19 ms | 27% of products |

- **Not worth it: LoRA alone**, or answering live in the store’s browser or phone (no GPU there). Classic v2 gives the
  same accuracy in 3.6 ms, for free.
- **Worth it: as a second opinion, in batch.** Per 1,000 products, classic + AI remove
  25 more errors (range 1.0 to 4.0 points). If a person takes about 30 seconds to find and fix
  a product in the wrong category (an estimate, not measured), that is about
  12 minutes of work saved per 1,000 products.
- **The real cost is a GPU left on**, not the product: a GPU machine waiting for listings costs the whole month.
  That is why the cascade only sends what the classic model is unsure about.

**Recommendation for production: the cheap cascade.** (1) Classic v2 answers live, on a CPU or in the browser; when
its confidence is above 68% (73% of products), it is right 91.1% of the time. (2) The rest
(27%) goes to the classifier AI, in batch, with the GPU on only then. (3) When the two disagree, a person checks
it. On the test: **81.4%**, 19 ms per product on average. The cascade with all three together gets
81.5% (difference within the margin: -1.0 to 1.3 points) and costs 8 times more per product.

## Quantity (grams, liters, units)

Rafael’s idea: “Leite Nestlé 34 g” could be milk or chocolate, but there is no 34 g carton of milk.
`src/catalogo/quantidade.py` reads the quantity from the text (`395g`, `1,5 L`, `6x350ml`, `1.000 g`, `2 unidades`),
normalizes it (grams, milliliters or units) and buckets it (up to 20 g, 20 to 45 g, 45 to 90 g...). The classic
model gets the type and range as extra tokens; the AIs get the normalized quantity at the end of the text. The same
parser runs in the browser (`docs/classificador.js`), and the tests check that Python and JavaScript read all 7,933
products the same way.

| Same model, without and with quantity | Without | With |
|---|---|---|
| Classic, cross-validation (where we chose) | 77.9% | 78.5% |
| Classic, test | 79.0% | 79.1% |
| BERTimbau, test | 72.3% | 72.4% |

**Honest reading:** quantity helps break ties but weighs little overall, because most names already say what the
product is. In the classic model it changes the answer for 51 test products, with a net effect near zero.
We also tried the range combined with the first word of the name (“leite” + 20 to 45 g): it was worse in
cross-validation, so it was dropped. For “Leite Nestlé 34 g” itself, the word “Leite” (milk) still outweighs the 34 g.

## A wrong label is not a model error

Open Food Facts is crowdsourced and has errors. Product by product, looking only at the name, we reviewed the
**673 test products** where at least one morning approach (classic v1, AI v1, 7B) was wrong:

- **70 wrong labels** (beer under “wine and spirits”, fermented milk under “milk”, candy under “jams”,
  cream cheese under “cream”, Monster under “soft drinks”);
- **85 ambiguous**, fitting two categories (honey, which the tag rule puts in sugar while the other category
  is literally named “honey”; nuggets between meat and ready meals; alfajor between cakes and biscuits);
- 518 with the right label (the model was wrong). The other 914 products (all three right) were not reviewed.

Of the morning AI’s 335 errors, **88 become correct** after the review; of the 293 errors of classic + AI,
94. The test set was not touched: the headline number is against the database as it came. The review
was done with AI help (Claude), **before** measuring the afternoon models, and it is open for anyone to check. It
slightly favors every model (we only reviewed where some model was wrong), so comparisons always use the original
number.

## Per category: where it still fails

The 8 weakest categories for classic + AI (all 41 in [reports/resultados.md](reports/resultados.md)):

| Category | n | F1 classic v1 | F1 AI v1 | F1 classic v2 | F1 classic + AI | Reviewed labels (wrong / ambiguous) |
|---|---|---|---|---|---|---|
| Fruit and vegetables | 12 | 27% | 29% | 27% | 29% | 4 / 1 |
| Wine and spirits | 17 | 44% | 45% | 44% | 48% | 5 / 0 |
| Canned and preserved foods | 12 | 52% | 48% | 50% | 50% | 1 / 3 |
| Ready meals and frozen dishes | 36 | 57% | 59% | 54% | 64% | 5 / 2 |
| Chocolates and bonbons | 75 | 63% | 65% | 63% | 67% | 0 / 4 |
| Energy and sports drinks | 10 | 67% | 67% | 60% | 67% | 0 / 0 |
| Nuts and peanuts | 32 | 65% | 63% | 74% | 69% | 0 / 4 |
| Desserts and dessert mixes | 18 | 75% | 69% | 76% | 69% | 1 / 3 |

- **Fruit and vegetables** is the “leftover” category: jam, granola, coconut flour and cocoa mix show up in it.
- **Wine and spirits** gets imported beer that only had the “alcoholic beverage” tag, and Skol Beats sits between
  beer and a mixed drink.
- **Canned food** vs **grains**: canned corn, peas and chickpeas show up on both sides, depending on who entered them.
- **Candy** vs **chocolates**: bonbons and truffles sit on the border; Tic Tac and candies even show up as jams.
- **Ready meals** borders on pasta (lasagna, mac’n cheese) and on meat (nuggets, breaded chicken).

What would fix it for good: better rules when mapping the tags (labels v2, applied to training) and more
information than the name (photo, barcode, description).

## Commented errors

| Product | Database says | Reading |
|---|---|---|
| Leite Nestlé 34 g | Chocolates | **Ambiguous.** It is the “Leite” bar. Quantity went in as a clue, but the name still weighs more. |
| Doritos Sabor Queso 90g | Chips and salty snacks | **Model error** (classic v1: cheese). The AIs know Doritos; in v2 the classic model gets it right too. |
| Chocapic Nestlé 210 g | Breakfast cereals | **Model error** (AI v1: chocolate). “Choc” pulls toward chocolate. |
| Ristretto Nestlé 104 g | Coffee | **Model error.** No training word says coffee; only world knowledge helps. |
| Quilmes Cerveza Argentina Clásica 710 ml | Wine and spirits | **Wrong label.** It is beer; the database only had “alcoholic beverage”. |
| Ervilha em conserva Bonare 170g/280g | Jams, honey and spreads | **Wrong label.** It is canned food. |
| Leite Fermentado c/Fibras Danone Activia | Milk and dairy drinks | **Wrong label.** Fermented milk belongs with yogurts. |
| Mel Silvestre Da Matina 500g | Sugar and sweeteners | **Ambiguous.** The rule puts honey in sugar; the other category is named “honey”. Both are fine. |

On the page, each one shows who got it right (classic v1, AI v1, classic v2, classifier AI, together).

## The real problem

In food and grocery marketplaces, the store types the product: short, abbreviated, inconsistent text
(`LEITE COND MOCA 395G`). A wrong category drops out of search, lands on the wrong shelf and hurts
recommendations. This is the problem iFood’s catalog team works on: classifying offers into a taxonomy and using
LLMs to label data and monitor classifiers ([Castro & Menezes, iFood, WAMLM workshop at KDD 2024](https://wamlm-kdd.github.io/wamlm/roundtables/wamlm_kdd24_anna_castro.pdf)).
Open Food Facts has its own robot for it ([Robotoff](https://github.com/openfoodfacts/robotoff)).

This repository is a **small, public** slice of that problem. It is not a product: it is an honest measurement of
when training an AI is worth it and when the classic model is enough, with the cost and latency of each approach.

## Data

- **Open Food Facts** (ODbL), only products with `en:brazil` in `countries_tags`. The public Parquet file is
  ~8 GB with 4.9 million products; `src/catalogo/dados.py` downloads only the ~270 MB of the 7 columns used, in
  parallel, into a local sparse file (2 to 5 min).
- **Label:** `src/catalogo/rotulos.py` maps tags into **41 shelf categories** with Portuguese and English names;
  when a product matches several, the most specific wins.
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
  of a new store. Products without a brand are grouped by the first 3 words of the name.
- **The test set is the same as in the morning** (1,587 products) and was used **once per version**. Everything that
  was chosen (classic settings, AI epoch, combination weights, cascade threshold) was chosen on validation or in
  brand-grouped cross-validation inside train + validation.
- Every approach trains **on the train set only**.
- **Accuracy** with a 95% range (bootstrap, 2,000 resamples), **macro F1** (small categories weigh as much as big
  ones) and **paired differences** between approaches (bootstrap on the same products).
- **Latency** measured batched and one product at a time. The browser model is the same one measured on the test set
  (`int8` weights): `tests/` checks scikit-learn vs. pure Python vs. JavaScript.

**Why split by brand.** The same classic v1 model, with the same training size, on a random split (72% of test brands
already seen in training) scores **82.9%**, versus **75.8%** on the brand split. All of Nestlé, for
example, landed in the test set: no model saw KitKat, Moça or Chocapic in training.

## Limits

- **Small, crowdsourced data:** 7.9k labeled products, with label errors (see the review).
- The **41 categories** are a taxonomy built from the tags; another taxonomy would give other numbers.
- **Zero-shot** uses a simple prompt with no examples. It shows the starting point, not the ceiling.
- Each AI was trained **once** (the classifier, twice), with no hyperparameter search (only the epoch was picked on
  validation). The validation set has only 794 products: for the classifier AI it promised more than the test gave.
- The **test review** was done with AI help, looking only at the name; nobody opened the package.
- AI latency is on a **T4** (a 2018 GPU). Cost was zero because Kaggle’s GPU quota is free.

## How to run

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
make dados      # Brazilian slice of Open Food Facts -> data/off_brasil.parquet
make split      # 41 categories + split by brand -> data/split/
make escolher   # brand-grouped cross-validation (train + validation) for classic v2
make classico   # classic v2 (docs/modelo.json), v1 and the leakage check
make notebook   # Kaggle notebooks (v1 and v2), see kaggle/README.md
make combinar   # together + cascade, chosen on validation
make avaliar    # measures every approach on the same test -> reports/ and docs/dados/
make testes     # 9 tests (including JavaScript = Python = scikit-learn)
make pagina     # http://127.0.0.1:8000
```

## Licenses and attribution

- Code: MIT (`LICENSE`).
- Derived data (`data/split/`, `docs/dados/`, `docs/modelo.json`, `reports/predicoes/`, `reports/kaggle-v2/`,
  `reports/revisao_teste.csv`): **ODbL 1.0**. Contains information from [Open Food Facts](https://world.openfoodfacts.org),
  made available here under the [Open Database License](https://opendatacommons.org/licenses/odbl/1-0/) (`DATA_LICENSE.md`).
- Models: Qwen2.5-1.5B-Instruct and Qwen2.5-7B-Instruct (Apache 2.0) and BERTimbau base (MIT), downloaded from
  Hugging Face on Kaggle; not redistributed here. No paid API was used.

A study project by Rafael Bueno ([github.com/Bueno-00](https://github.com/Bueno-00)), part of the same portfolio as
[Raio-X Fiscal](https://github.com/Bueno-00/raio-x-fiscal) (product description to tax code classification).
