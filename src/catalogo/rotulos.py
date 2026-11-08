"""Categorias de prateleira (curadas) a partir das tags do Open Food Facts.

A árvore de categorias do Open Food Facts mistura nós gerais ("plant-based-foods") e específicos
("condensed-milks"), e no recorte do Brasil aparecem tags fora do padrão em espanhol ("en:Galletas",
"en:Yogures"). Aqui cada categoria de prateleira junta as tags que a representam. A ORDEM é a prioridade:
se um produto bate em mais de uma, fica a primeira da lista (as mais específicas vêm antes, por exemplo
"Achocolatado" antes de "Chocolates" e "Biscoitos" antes de "Chocolates", para o biscoito de chocolate
ficar em biscoitos). Nós genéricos demais (snacks, beverages, dairies, plant-based-foods) não rotulam nada.
"""

from __future__ import annotations

# chave: (português, inglês, tags do Open Food Facts)
_LISTA: list[tuple[str, str, str, list[str]]] = [
    ("leite_condensado_creme", "Leite condensado e creme de leite", "Condensed milk and cream",
     ["condensed-milks", "sweetened-condensed-milks", "creams", "cooking-creams", "whipped-creams"]),
    ("achocolatado", "Achocolatado e cacau em pó", "Chocolate drink mixes and cocoa powder",
     ["cocoa-and-chocolate-powders", "cocoa-powders", "chocolate-powders", "instant-chocolate-drinks"]),
    ("iogurtes", "Iogurtes e leites fermentados", "Yogurts and fermented milks",
     ["yogurts", "Yogures", "yogures", "greek-style-yogurts", "Yogures batidos", "fruit-yogurts", "Yogures de frutas",
      "fermented-milk-drinks", "fermented-dairy-desserts", "fermented-dairy-desserts-with-fruits", "drinkable-yogurts"]),
    ("sorvetes", "Sorvetes e picolés", "Ice cream and popsicles",
     ["ice-creams-and-sorbets", "ice-creams", "Helados", "helados", "frozen-desserts", "sorbets", "ice-cream-tubs", "ice-pops"]),
    ("queijos", "Queijos e requeijão", "Cheese and cream cheese",
     ["cheeses", "Quesos", "quesos", "cream-cheeses", "cow-cheeses", "grated-cheeses", "processed-cheese", "mozzarella"]),
    ("manteiga_margarina", "Manteiga e margarina", "Butter and margarine",
     ["butters", "margarines", "dairy-spreads", "spreadable-fats", "milkfat", "salted-butters"]),
    ("bebidas_vegetais", "Bebidas vegetais", "Plant-based drinks",
     ["plant-based-milk-alternatives", "milk-substitutes", "soy-milks", "almond-milks", "oat-milks"]),
    ("leites", "Leite e bebida láctea", "Milk and dairy drinks",
     ["milks", "milks-liquid-and-powder", "Leches", "uht-milks", "milk-powders", "Leches saborizadas", "leches", "dairy-drinks",
      "whole-milks", "homogenized-milks", "lactose-free-milk", "flavoured-milks", "skimmed-milks", "semi-skimmed-milks"]),
    ("biscoitos", "Biscoitos e bolachas", "Biscuits and crackers",
     ["biscuits", "biscuits-and-crackers", "Galletas", "galletas", "wafers", "filled-biscuits", "stuffed-wafers",
      "chocolate-biscuits", "crackers", "cookies", "dry-biscuits", "shortbread-cookies", "crackers-appetizers"]),
    ("chocolates", "Chocolates e bombons", "Chocolates and bonbons",
     ["chocolates", "chocolate-candies", "bonbons", "candy-chocolate-bars", "milk-chocolates", "dark-chocolates",
      "white-chocolates", "flavoured-chocolates", "filled-chocolates"]),
    ("barras", "Barras de cereal e de proteína", "Cereal and protein bars",
     ["bars", "cereal-bars", "protein-bars", "Barras de proteína", "Barras de proteínas", "barras-de-proteina", "Barras de cereal"]),
    ("bolos_panetones", "Bolos, panetones e doces de padaria", "Cakes, panettone and pastries",
     ["cakes", "panettone", "sweet-pastries-and-pies", "viennoiseries", "brioches", "alfajores", "christmas-sweets",
      "muffins", "sponge-cakes"]),
    ("paes", "Pães e torradas", "Bread and toast",
     ["breads", "sliced-breads", "special-breads", "Pan", "Panes", "toasts", "rusks", "wholemeal-breads", "tortillas"]),
    ("balas_doces", "Balas, gomas e doces", "Candy, gummies and sweets",
     ["candies", "confectioneries", "Dulces", "dulces", "gummies", "chewing-gum", "lollipops", "Snacks dulces",
      "marshmallows", "jellies"]),
    ("salgadinhos", "Salgadinhos e batata chips", "Chips and salty snacks",
     ["salty-snacks", "chips-and-fries", "crisps", "potato-crisps", "corn-chips", "popcorn", "Papas fritas",
      "extruded-snacks", "puffed-salty-snacks"]),
    ("castanhas", "Castanhas e amendoim", "Nuts and peanuts",
     ["nuts", "peanuts", "nuts-and-their-products", "Frutos secos", "frutos-secos", "cashew-nuts", "brazil-nuts", "mixed-nuts"]),
    ("suplementos", "Suplementos e proteína em pó", "Supplements and protein powder",
     ["dietary-supplements", "bodybuilding-supplements", "Suplementos", "Proteínas", "Suplementos alimenticios",
      "suplementos-alimenticios", "suplementos", "proteinas", "protein-powders", "whey-proteins"]),
    ("cereais_matinais", "Cereais matinais e aveia", "Breakfast cereals and oats",
     ["breakfast-cereals", "mueslis", "cereal-flakes", "rolled-oats", "rolled-flakes", "Cereales para desayuno",
      "granolas", "oat-flakes", "extruded-cereals", "flakes"]),
    ("massas", "Massas e macarrão instantâneo", "Pasta and instant noodles",
     ["pastas", "dry-pastas", "noodles", "instant-noodles", "cereal-pastas", "durum-wheat-pasta", "spaghetti",
      "fresh-pastas"]),
    ("farinhas", "Farinhas, amidos e tapioca", "Flours, starches and tapioca",
     ["flours", "cereal-flours", "wheat-flours", "starches", "tapioca", "corn-flours", "cassava-flours",
      "breadcrumbs"]),
    ("graos", "Arroz, feijão e grãos", "Rice, beans and grains",
     ["rices", "legumes", "common-beans", "pulses", "legume-seeds", "cereal-grains", "lentils", "chickpeas",
      "white-rices", "brown-rices", "quinoa", "seeds"]),
    ("acucar_adocante", "Açúcar e adoçante", "Sugar and sweeteners",
     ["sugars", "sweeteners", "white-sugars", "brown-sugars", "artificial-sweeteners"]),
    ("geleias_mel", "Geleias, mel e cremes de passar", "Jams, honey and sweet spreads",
     ["jams", "honeys", "sweet-spreads", "Dulces untables", "dulces-untables", "hazelnut-spreads", "cocoa-and-hazelnuts-spreads",
      "peanut-butters", "legume-butters", "oilseed-purees", "milk-jams", "fruit-jams", "bee-products"]),
    ("molhos", "Molhos, ketchup e maionese", "Sauces, ketchup and mayonnaise",
     ["sauces", "tomato-sauces", "ketchup", "mayonnaises", "Salsas", "mustards", "hot-sauces", "pasta-sauces",
      "soy-sauces", "salad-dressings"]),
    ("oleos_azeites", "Óleos e azeites", "Oils and olive oils",
     ["vegetable-oils", "olive-oils", "extra-virgin-olive-oils", "virgin-olive-oils", "sunflower-oils",
      "soybean-oils"]),
    ("temperos", "Temperos, sal e caldos", "Seasonings, salt and stock",
     ["spices", "herbs-and-spices", "salts", "condiments", "cooking-helpers", "bouillon-cubes", "broths",
      "seasoning-mixes", "vinegars"]),
    ("peixes", "Peixes, atum e sardinha", "Fish, tuna and sardines",
     ["fishes", "canned-fishes", "tunas", "sardines", "canned-sardines", "seafood", "Atún", "Pescados",
      "fatty-fishes", "canned-tunas", "fishes-and-their-products"]),
    ("carnes_frios", "Carnes, frios e embutidos", "Meat, cold cuts and sausages",
     ["meats", "prepared-meats", "sausages", "Embutidos", "Carnes", "carnes", "chickens", "poultries", "frozen-meats",
      "hams", "meat-preparations", "chicken-and-its-products", "meats-and-their-products"]),
    ("pratos_prontos", "Pratos prontos e congelados", "Ready meals and frozen dishes",
     ["meals", "pasta-dishes", "meals-with-meat", "meals-with-chicken", "poultry-meals", "pizzas", "soups",
      "sandwiches", "lasagnas", "frozen-ready-made-meals"]),
    ("cafe", "Café", "Coffee",
     ["coffees", "instant-coffees", "ground-coffees", "Cafés", "coffee-capsules", "coffee-beans"]),
    ("chas", "Chás", "Tea",
     ["teas", "herbal-teas", "tea-based-beverages", "green-teas", "black-teas", "iced-teas"]),
    ("aguas", "Águas", "Water", ["waters", "mineral-waters", "spring-waters", "sparkling-waters", "flavored-waters"]),
    ("refrigerantes", "Refrigerantes", "Soft drinks",
     ["sodas", "colas", "carbonated-drinks", "soft-drinks", "Bebidas gaseosas", "lemon-flavored-sodas",
      "guarana-sodas"]),
    ("sucos", "Sucos e néctares", "Juices and nectars",
     ["juices-and-nectars", "fruit-juices", "fruit-nectars", "Jugos de fruta", "orange-juices", "grape-juices",
      "fruit-based-beverages"]),
    ("energeticos", "Energéticos e isotônicos", "Energy and sports drinks",
     ["energy-drinks", "sports-drinks", "isotonic-drinks"]),
    ("cervejas", "Cervejas", "Beer", ["beers", "Cervezas", "lagers", "pilsners", "non-alcoholic-beers"]),
    ("alcoolicas", "Vinhos e destilados", "Wine and spirits",
     ["alcoholic-beverages", "wines", "spirits", "Bebidas alcohólicas", "bebidas-alcoholicas", "cachacas",
      "red-wines", "vodkas", "liqueurs"]),
    ("conservas", "Conservas e enlatados", "Canned and preserved foods",
     ["canned-vegetables", "canned-plant-based-foods", "fruit-and-vegetable-preserves", "canned-foods",
      "pickles", "olives", "canned-fruits", "tomatoes-and-their-products"]),
    ("sobremesas", "Sobremesas e misturas para doce", "Desserts and dessert mixes",
     ["desserts", "dairy-desserts", "Postres", "postres", "dessert-mixes", "puddings", "gelatin-desserts",
      "cake-mixes"]),
    ("ovos", "Ovos", "Eggs", ["eggs", "chicken-eggs"]),
    ("hortifruti", "Frutas, verduras e legumes", "Fruit and vegetables",
     ["fruits", "vegetables", "fresh-fruits", "fresh-vegetables", "fruits-based-foods", "dried-fruits"]),
]

CATEGORIAS: dict[str, dict] = {k: {"pt": pt, "en": en, "tags": [f"en:{t}" for t in tags]} for k, pt, en, tags in _LISTA}
_PRIORIDADE = [(k, set(v["tags"])) for k, v in CATEGORIAS.items()]


def rotular(tags: list[str]) -> str | None:
    """Primeira categoria da lista (mais específica) que tenha alguma das tags do produto."""
    s = set(tags)
    for chave, alvo in _PRIORIDADE:
        if s & alvo:
            return chave
    return None
