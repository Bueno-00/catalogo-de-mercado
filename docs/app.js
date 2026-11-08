/* Página do Catálogo de mercado: demonstração + resultados (antes e depois). Sem servidor: tudo vem de arquivos estáticos. */
(function () {
  "use strict";

  var T = {
    pt: {
      marca: "Catálogo de mercado", nav_demo: "Experimente", nav_res: "Resultados", nav_custo: "Vale a pena?", nav_como: "Como foi medido",
      selo: "Projeto de estudo · Rafael Bueno", titulo: "Qual é a categoria deste produto?",
      lead: "Lojista cadastra “LEITE COND MOÇA 395G” e o sistema precisa saber que é leite condensado, para a busca e as vitrines acharem o produto. Aqui, vários jeitos de responder, medidos no mesmo teste, com marcas que nenhum modelo viu no treino. Duas rodadas: a de 08/11/2026 de manhã (v1) e a da tarde (v2).",
      demo_t: "Experimente",
      demo_i: "Digite um produto como ele apareceria num catálogo. O clássico responde na hora, aqui no seu navegador, e mostra a quantidade que leu. As respostas da IA ajustada e dos dois juntos foram calculadas na GPU gratuita do Kaggle para os produtos do teste (não há servidor ligado): escolha um produto do teste para ver as três lado a lado.",
      rotulo_q: "Produto", btn_ok: "Classificar", exemplos: "Exemplos:", btn_sortear: "Sortear",
      f_todos: "Qualquer produto do teste", f_ia: "Onde a IA ajustada errou", f_classico: "Onde o clássico errou", f_juntos: "Onde até os dois juntos erraram", f_revisto: "Rótulo revisto (errado ou ambíguo)",
      sug_t: "Produtos parecidos no teste (com as três respostas):",
      aviso: "Categoria “certa” = a do Open Food Facts, base colaborativa: às vezes ela mesma está errada. Revisamos os casos duvidosos do teste (veja abaixo).",
      res_t: "Resultados no teste: antes e depois", custo_t: "Vale a pena a IA? Custo x ganho", mil_t: "A cada 1.000 produtos", quando_t: "Quando vale e quando não vale",
      ach_t: "O que isso quer dizer", q_t: "A quantidade como pista (gramas, litros, unidades)", rev_t: "Rótulo errado não é erro do modelo",
      cat_t: "Acerto por categoria e onde ainda erra", err_t: "Erros comentados",
      imp_t: "Por que isso importa",
      imp_p1: "Em marketplace de comida e de mercado, quem cadastra o produto é o lojista, com texto curto, abreviado e sem padrão. Categoria errada some da busca, aparece na vitrine errada e atrapalha a recomendação. O time de catálogo do iFood descreve exatamente esse problema: classificar ofertas numa taxonomia e usar LLM para rotular dados e vigiar os classificadores.",
      imp_p2: "Este projeto é um recorte pequeno e público desse problema, feito para medir com honestidade quando vale treinar uma IA e quando o clássico resolve.",
      ref1: "Castro e Menezes (iFood), workshop WAMLM no KDD 2024", ref2: "Robotoff, o robô de categorias do próprio Open Food Facts",
      como_t: "Como foi medido",
      rod1: "Dados: Open Food Facts (world.openfoodfacts.org), base aberta sob a licença ODbL. O recorte usado aqui também é ODbL. Código sob licença MIT.",
      rod2: "Modelos abertos: Qwen2.5 (Apache 2.0) e BERTimbau (MIT). Nenhuma API paga foi usada.",
      k_classico: "Clássico (CPU)", k_ia: "IA ajustada", k_juntos: "Clássico + IA", k_cascata: "Cascata barata", antes: "antes", acerto: "acerto",
      certo: "Categoria certa (Open Food Facts):", acertou: "Acertou", errou: "Errou",
      so_teste: "A IA precisa de GPU e não roda no seu navegador. Toque num produto parecido abaixo para ver a resposta dela.",
      so_teste_sem: "A IA precisa de GPU e não roda no seu navegador. Toque em Sortear para ver a resposta dela num produto do teste.",
      digite: "Digite um produto acima.", desconhecido: "Nenhuma palavra conhecida: o modelo está chutando a categoria mais comum.",
      th_c: "Caminho", th_a: "Acerto (faixa de 95%)", th_r: "Teste revisado", th_f: "F1 macro", th_t: "Tempo por produto", th_o: "Onde roda",
      lote: "em lote", um: "um por vez", cpu: "CPU comum ou navegador", gpu: "GPU T4 (grátis no Kaggle)",
      g_v1: "Antes (v1, manhã de 08/11/2026)", g_v2: "Depois (v2, tarde de 08/11/2026)",
      th_mil_a: "Acerto", th_mil_e: "Erros a cada 1.000", th_mil_m: "Máquina para 1.000 (lote)", th_mil_u: "Um produto na hora", th_mil_g: "Precisa de GPU?",
      sim: "sim", nao: "não", parte: "em parte",
    },
    en: {
      marca: "Grocery catalog", nav_demo: "Try it", nav_res: "Results", nav_custo: "Worth it?", nav_como: "How it was measured",
      selo: "Study project · Rafael Bueno", titulo: "Which category is this product?",
      lead: "A store types “LEITE COND MOÇA 395G” and the system has to know it is condensed milk, so search and shelves can find it. Here are several ways to answer, measured on the same test, with brands no model saw in training. Two rounds: the morning of Nov 8, 2026 (v1) and the afternoon (v2).",
      demo_t: "Try it",
      demo_i: "Type a product the way it would show up in a catalog (products are Brazilian, in Portuguese). The classic model answers instantly, right in your browser, and shows the quantity it read. The tuned AI and the combined answers were computed on Kaggle’s free GPU for the test products (no server running): pick a test product to see all three side by side.",
      rotulo_q: "Product", btn_ok: "Classify", exemplos: "Examples:", btn_sortear: "Random",
      f_todos: "Any test product", f_ia: "Where the tuned AI was wrong", f_classico: "Where the classic model was wrong", f_juntos: "Where even both together were wrong", f_revisto: "Reviewed label (wrong or ambiguous)",
      sug_t: "Similar products in the test set (with all three answers):",
      aviso: "“Correct” category = the one in Open Food Facts, a crowdsourced database: sometimes it is wrong itself. We reviewed the doubtful test cases (see below).",
      res_t: "Test results: before and after", custo_t: "Is the AI worth it? Cost vs gain", mil_t: "Per 1,000 products", quando_t: "When it pays off and when it does not",
      ach_t: "What it means", q_t: "Quantity as a clue (grams, liters, units)", rev_t: "A wrong label is not a model error",
      cat_t: "Per-category accuracy and where it still fails", err_t: "Commented errors",
      imp_t: "Why it matters",
      imp_p1: "In food and grocery marketplaces, the store types the product, in short, abbreviated, inconsistent text. A wrong category drops out of search, lands on the wrong shelf and hurts recommendations. iFood’s catalog team describes exactly this problem: classifying offers into a taxonomy and using LLMs to label data and monitor classifiers.",
      imp_p2: "This project is a small, public slice of that problem, built to measure honestly when training an AI is worth it and when the classic model is enough.",
      ref1: "Castro and Menezes (iFood), WAMLM workshop at KDD 2024", ref2: "Robotoff, Open Food Facts’ own category robot",
      como_t: "How it was measured",
      rod1: "Data: Open Food Facts (world.openfoodfacts.org), open database under the ODbL. The subset used here is ODbL too. Code under the MIT license.",
      rod2: "Open models: Qwen2.5 (Apache 2.0) and BERTimbau (MIT). No paid API was used.",
      k_classico: "Classic (CPU)", k_ia: "Tuned AI", k_juntos: "Classic + AI", k_cascata: "Cheap cascade", antes: "before", acerto: "accuracy",
      certo: "Correct category (Open Food Facts):", acertou: "Right", errou: "Wrong",
      so_teste: "The AI needs a GPU and does not run in your browser. Tap a similar product below to see its answer.",
      so_teste_sem: "The AI needs a GPU and does not run in your browser. Tap Random to see its answer on a test product.",
      digite: "Type a product above.", desconhecido: "No known word: the model is guessing the most common category.",
      th_c: "Approach", th_a: "Accuracy (95% range)", th_r: "Reviewed test", th_f: "Macro F1", th_t: "Time per product", th_o: "Runs on",
      lote: "batched", um: "one at a time", cpu: "Regular CPU or browser", gpu: "T4 GPU (free on Kaggle)",
      g_v1: "Before (v1, morning of Nov 8, 2026)", g_v2: "After (v2, afternoon of Nov 8, 2026)",
      th_mil_a: "Accuracy", th_mil_e: "Errors per 1,000", th_mil_m: "Compute for 1,000 (batched)", th_mil_u: "One product, live", th_mil_g: "Needs a GPU?",
      sim: "yes", nao: "no", parte: "partly",
    },
  };

  var L = "pt";
  try { if ((localStorage.getItem("cm_lang") || "") === "en") L = "en"; } catch (e) { /* sem armazenamento */ }
  if (/[?&]lang=en\b/.test(location.search)) L = "en";
  function t(k) { return T[L][k]; }
  function fmtNum(x, d) { return Number(x).toLocaleString(L === "pt" ? "pt-BR" : "en-US", { minimumFractionDigits: d, maximumFractionDigits: d }); }
  function fmtInt(x) { return Number(x).toLocaleString(L === "pt" ? "pt-BR" : "en-US"); }
  function pct(x, d) { return fmtNum(100 * x, d == null ? 1 : d) + "%"; }
  function pts(x, d) { return fmtNum(100 * x, d == null ? 1 : d); }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function $(id) { return document.getElementById(id); }
  function ms(x) { return x == null ? "" : (x < 1 ? fmtNum(x, 2) : x < 10 ? fmtNum(x, 1) : fmtNum(x, 0)) + " ms"; }
  function seg(msPorItem) { var s = msPorItem; return (s < 1 ? fmtNum(s, 2) : s < 10 ? fmtNum(s, 1) : fmtNum(s, 0)) + " s"; }

  var COR = { tfidf: "var(--c-classico)", classico_v2: "var(--c-classico)", zero_shot_1_5b: "var(--c-zero)", zero_shot_7b_4bit: "var(--c-zero7)",
    lora_1_5b: "var(--c-lora)", lora_v1_escrita: "var(--c-lora)", qwen15_lora_q: "var(--c-cls)", qwen15_lora_q5m: "var(--c-cls)", cascata_ia_v2: "var(--c-juntos)", bertimbau_q: "var(--c-bert)", juntos: "var(--c-juntos)", cascata: "var(--c-juntos)" };
  var ORDEM = ["zero_shot_1_5b", "zero_shot_7b_4bit", "tfidf", "lora_1_5b", "classico_v2", "bertimbau_q", "qwen15_lora_q", "lora_v1_escrita", "juntos", "cascata", "cascata_ia_v2"];
  var ONDE = {
    pt: { zero_shot_1_5b: "Recebe a lista de categorias, sem treino.", zero_shot_7b_4bit: "5 vezes maior, em 4 bits, sem treino.", tfidf: "Palavras e pedaços de palavra + regressão logística.",
      lora_1_5b: "Qwen2.5-1.5B com LoRA, escreve o nome da categoria.", classico_v2: "LinearSVC + faixa da quantidade + treino sem a marca. Roda no navegador.",
      bertimbau_q: "Modelo de 110 milhões de parâmetros em português, ajustado inteiro.", qwen15_lora_q: "Qwen2.5-1.5B com LoRA e cabeça de classificação: uma passada, 41 probabilidades. LoRA fundido.",
      lora_v1_escrita: "O LoRA da manhã, com o adapter fundido nos pesos e a probabilidade da resposta escrita.", juntos: "Clássico v2 + IA (LoRA) + IA classificadora, pesos escolhidos na validação.", cascata: "O clássico responde quando está seguro; o resto vai para os três juntos.",
      cascata_ia_v2: "O clássico responde quando está seguro; o resto vai para a IA classificadora (mais barata)." },
    en: { zero_shot_1_5b: "Gets the category list, no training.", zero_shot_7b_4bit: "5x bigger, 4-bit, no training.", tfidf: "Words and word pieces + logistic regression.",
      lora_1_5b: "Qwen2.5-1.5B with LoRA, writes the category name.", classico_v2: "LinearSVC + quantity range + training without the brand. Runs in the browser.",
      bertimbau_q: "110-million-parameter Portuguese model, fully fine-tuned.", qwen15_lora_q: "Qwen2.5-1.5B with LoRA and a classification head: one pass, 41 probabilities. Merged LoRA.",
      lora_v1_escrita: "The morning LoRA, with the adapter merged into the weights and the probability of the written answer.", juntos: "Classic v2 + AI (LoRA) + classifier AI, weights picked on validation.", cascata: "The classic model answers when confident; the rest goes to all three together.",
      cascata_ia_v2: "The classic model answers when confident; the rest goes to the classifier AI (cheaper)." },
  };

  var clf = null, R = null, EX = null, idx = new Map(), df = new Map(), linhas = [], col = {}, erros = [];
  var atual = { texto: "", linha: null };
  var IA = null, CL = null, JU = null;

  function nomeCat(chave) { return (L === "pt" ? R.nomes : R.nomes_en)[chave] || chave; }
  function C(c) { return R.caminhos[c]; }
  function nomeC(c) { var n = NOMES_PAG[L][c]; return n || (L === "pt" ? C(c).nome : C(c).nome_en); }
  var NOMES_PAG = {
    pt: { lora_v1_escrita: "IA ajustada (LoRA da manhã, fundido)", qwen15_lora_q: "IA ajustada v2 como classificador (+ quantidade)", cascata_ia_v2: "Cascata barata: clássico primeiro, IA classificadora só na dúvida" },
    en: { lora_v1_escrita: "Tuned AI (morning LoRA, merged)", qwen15_lora_q: "Tuned AI v2 as a classifier (+ quantity)", cascata_ia_v2: "Cheap cascade: classic first, classifier AI only when unsure" },
  };
  function tem(c) { return !!(R && R.caminhos[c]); }

  /* ---------------- dados ---------------- */
  function carregar() {
    return Promise.all(["modelo.json", "dados/resultados.json", "dados/exemplos.json", "dados/erros_comentados.json"].map(function (u) {
      return fetch(u).then(function (r) { return r.ok ? r.json() : null; });
    })).then(function (v) {
      clf = Classificador.criar(v[0]); R = v[1]; EX = v[2]; erros = (v[3] && v[3].erros) || [];
      EX.colunas.forEach(function (c, i) { col[c] = i; });
      linhas = EX.linhas;
      linhas.forEach(function (l, i) {
        var n = Classificador.norm(l[col.texto]);
        idx.set(n, i);
        new Set(n.split(" ")).forEach(function (w) { if (w.length >= 2) df.set(w, (df.get(w) || 0) + 1); });
      });
      IA = [R.ia_da_combinacao, R.ia_principal, "lora_1_5b"].filter(tem)[0];
      CL = tem("classico_v2") ? "classico_v2" : "tfidf";
      JU = tem("juntos") ? "juntos" : null;
    });
  }

  function aceitas(i) { return String(linhas[i][col.aceitas] || linhas[i][col.certo]).split("|"); }
  function certoRev(i, c) { return aceitas(i).indexOf(linhas[i][col[c]]) >= 0; }

  function parecidos(q, k) {
    var toks = Array.from(new Set(Classificador.norm(q).split(" "))).filter(function (w) { return w.length >= 2; });
    if (!toks.length) return [];
    var N = linhas.length, pont = [];
    linhas.forEach(function (l, i) {
      var n = " " + Classificador.norm(l[col.texto]) + " ", s = 0;
      toks.forEach(function (w) { if (n.indexOf(" " + w + " ") >= 0) s += Math.log(1 + N / (df.get(w) || 1)); });
      if (s > 0) pont.push([s, i]);
    });
    pont.sort(function (a, b) { return b[0] - a[0]; });
    return pont.slice(0, k).map(function (p) { return p[1]; });
  }

  /* ---------------- textos fixos ---------------- */
  function aplicarIdioma() {
    document.documentElement.lang = L === "pt" ? "pt-BR" : "en";
    document.querySelectorAll("[data-t]").forEach(function (el) {
      var v = T[L][el.getAttribute("data-t")];
      if (typeof v === "string") el.textContent = v;
    });
    document.querySelectorAll(".idioma button").forEach(function (b) { b.setAttribute("aria-pressed", String(b.dataset.lang === L)); });
    if (R) { montarTudo(); render(); }
  }

  /* ---------------- placar ---------------- */
  function montarPlacar() {
    var k = [[CL, "k_classico", "tfidf"]];
    if (JU) k.push([JU, "k_juntos", "lora_1_5b"]);
    if (tem("cascata_ia_v2")) k.push(["cascata_ia_v2", "k_cascata", null]);
    $("placar").innerHTML = k.map(function (x) {
      var r = C(x[0]), sub = x[2] && tem(x[2]) ? t("antes") + " " + pct(C(x[2]).acuracia) : DIN[L].k_cascata_sub(r);
      return '<div class="kpi"><div class="rot"><span class="ponto" style="background:' + COR[x[0]] + '"></span>' + esc(t(x[1])) +
        '</div><div class="val num">' + pct(r.acuracia) + '</div><div class="sub">' + esc(sub) + "</div></div>";
    }).join("");
  }

  /* ---------------- tabela principal ---------------- */
  function linhaTabela(c, melhor) {
    var r = C(c), ic = r.acuracia_ic95;
    var tempo = "<span class='nw'>" + ms(r.ms_lote) + " " + t("lote") + "</span><br><span class='ic-txt nw'>" + ms(r.ms_um) + " " + t("um") + "</span>";
    var onde = r.hardware === "cpu" ? t("cpu") : t("gpu");
    if (r.fracao_gpu != null) onde = t("cpu") + " + " + (L === "pt" ? "GPU em " : "GPU for ") + pct(r.fracao_gpu, 0) + (L === "pt" ? " dos produtos" : " of products");
    return '<tr class="' + (c === melhor ? "lider" : "") + (r.versao === "v1" ? " antes" : "") + '"><td><div class="nome-c"><span class="ponto" style="background:' + COR[c] + '"></span><div>' + esc(nomeC(c)) + "<small>" + esc(ONDE[L][c] || "") + "</small></div></div></td>" +
      '<td data-r="' + esc(t("th_a")) + '"><div style="display:flex;align-items:center;gap:12px"><span class="v-acerto num">' + pct(r.acuracia) + '</span><div class="escala" style="flex:1"><div class="fundo"></div><div class="fill" style="width:' + (100 * r.acuracia) + "%;background:" + COR[c] + '"></div><div class="ic" style="left:' + (100 * ic[0]) + "%;width:" + (100 * (ic[1] - ic[0])) + '%"></div></div></div><span class="ic-txt num">' + pct(ic[0]) + (L === "pt" ? " a " : " to ") + pct(ic[1]) + "</span></td>" +
      '<td class="num" data-r="' + esc(t("th_r")) + '">' + pct(r.acuracia_revisada) + "</td>" +
      '<td class="num" data-r="' + esc(t("th_f")) + '">' + pct(r.f1_macro) + "</td>" +
      '<td class="num" data-r="' + esc(t("th_t")) + '">' + tempo + "</td>" +
      '<td data-r="' + esc(t("th_o")) + '">' + esc(onde) + "</td></tr>";
  }

  function montarTabela() {
    $("res_i").textContent = DIN[L].res_i(R);
    var cs = ORDEM.filter(tem);
    var melhor = cs.reduce(function (a, b) { return C(b).acuracia > C(a).acuracia ? b : a; }, cs[0]);
    var h = "<thead><tr><th>" + t("th_c") + "</th><th>" + t("th_a") + "</th><th>" + t("th_r") + "</th><th>" + t("th_f") + "</th><th>" + t("th_t") + "</th><th>" + t("th_o") + "</th></tr></thead><tbody>";
    ["v1", "v2"].forEach(function (v) {
      h += '<tr class="grupo"><td colspan="6">' + esc(t("g_" + v)) + "</td></tr>";
      cs.filter(function (c) { return C(c).versao === v; }).forEach(function (c) { h += linhaTabela(c, melhor); });
    });
    $("tabela").innerHTML = h + "</tbody>";
    $("res_rodape").textContent = DIN[L].res_rodape(R);
  }

  /* ---------------- custo x ganho ---------------- */
  function montarCusto() {
    $("custo_i").textContent = DIN[L].custo_i(R, CL, IA);
    var cs = ["lora_1_5b", CL, IA, "qwen15_lora_q", "juntos", "cascata", "cascata_ia_v2"].filter(function (c, i, a) { return tem(c) && a.indexOf(c) === i; });
    var h = "<thead><tr><th>" + t("th_c") + "</th><th>" + t("th_mil_a") + "</th><th>" + t("th_mil_e") + "</th><th>" + t("th_mil_m") + "</th><th>" + t("th_mil_u") + "</th><th>" + t("th_mil_g") + "</th></tr></thead><tbody>";
    cs.forEach(function (c) {
      var r = C(c), gpu = r.hardware === "cpu" ? t("nao") : r.fracao_gpu != null ? t("parte") + " (" + pct(r.fracao_gpu, 0) + ")" : t("sim");
      h += '<tr class="' + (r.versao === "v1" ? "antes" : "") + '"><td><div class="nome-c"><span class="ponto" style="background:' + COR[c] + '"></span>' + esc(nomeC(c)) + "</div></td>" +
        '<td class="num" data-r="' + esc(t("th_mil_a")) + '"><b>' + pct(r.acuracia) + "</b></td>" +
        '<td class="num" data-r="' + esc(t("th_mil_e")) + '">' + fmtInt(Math.round((1 - r.acuracia) * 1000)) + "</td>" +
        '<td class="num" data-r="' + esc(t("th_mil_m")) + '">' + seg(r.ms_lote) + " " + (r.hardware === "cpu" ? "CPU" : "GPU") + "</td>" +
        '<td class="num" data-r="' + esc(t("th_mil_u")) + '">' + ms(r.ms_um) + "</td>" +
        '<td data-r="' + esc(t("th_mil_g")) + '">' + esc(gpu) + "</td></tr>";
    });
    $("mil").innerHTML = h + "</tbody>";
    var cas = $("cascata");
    if (tem("cascata") && JU) {
      var linhasC = [[DIN[L].so_classico, C(CL).acuracia, 0, COR[CL]]];
      if (tem("cascata_ia_v2")) linhasC.push([DIN[L].cascata_rot(C("cascata_ia_v2").fracao_gpu, true), C("cascata_ia_v2").acuracia, 0, "var(--c-cls)"]);
      linhasC.push([DIN[L].cascata_rot(C("cascata").fracao_gpu, false), C("cascata").acuracia, 0, COR.cascata]);
      linhasC.push([DIN[L].tudo_ia, C(JU).acuracia, 1, COR.juntos]);
      cas.innerHTML = "<p class='mini'>" + esc(DIN[L].cascata_t) + "</p>" + linhasC.map(function (x) {
        return '<div class="l"><span>' + esc(x[0]) + '</span><div class="barra"><div class="trilho" style="height:10px"><div class="enche" style="width:' + (100 * x[1]) + "%;background:" + x[3] + '"></div></div></div><b class="num">' + pct(x[1]) + "</b></div>";
      }).join("");
    } else cas.innerHTML = "";
    $("quando").innerHTML = DIN[L].quando(R, CL, IA).map(function (x) { return "<li>" + x + "</li>"; }).join("");
    $("recomenda").innerHTML = DIN[L].recomenda(R, CL, IA);
  }

  /* ---------------- achados, quantidade, revisão ---------------- */
  function montarAchados() {
    $("achados").innerHTML = DIN[L].achados(R, CL, IA).map(function (a) {
      return '<div class="cartao achado"><div class="grande num" style="color:' + a.cor + '">' + a.grande + "</div><p>" + a.texto + "</p></div>";
    }).join("");
  }

  function barras(el, itens) {
    $(el).innerHTML = itens.map(function (x) {
      return '<div class="l"><span>' + esc(x[0]) + '</span><div class="barra"><div class="trilho" style="height:10px"><div class="enche" style="width:' + (100 * x[1]) + "%;background:" + x[2] + '"></div></div></div><b class="num">' + pct(x[1]) + "</b></div>";
    }).join("");
  }

  function montarQuantidade() {
    var q = R.quantidade || {}, D = DIN[L], it = [];
    $("q_p1").textContent = D.q_p1;
    if (q.classico) { it.push([D.q_sem("Clássico", "Classic"), q.classico.teste_sem, "var(--muted)"]); it.push([D.q_com("Clássico", "Classic"), q.classico.teste_com, COR.classico_v2]); }
    if (q.bertimbau) { it.push([D.q_sem("BERTimbau", "BERTimbau"), q.bertimbau.teste_sem, "var(--muted)"]); it.push([D.q_com("BERTimbau", "BERTimbau"), q.bertimbau.teste_com, COR.bertimbau_q]); }
    barras("q_barras", it);
    $("q_p2").innerHTML = D.q_p2(R, achar("Leite Nestlé 34 g"));
    var rv = R.revisao;
    $("rev_p1").textContent = D.rev_p1(rv);
    barras("rev_barras", [CL, IA, JU].filter(Boolean).reduce(function (a, c) {
      return a.concat([[nomeCurto(c) + " · " + D.original, C(c).acuracia, "var(--muted)"], [nomeCurto(c) + " · " + D.revisado, C(c).acuracia_revisada, COR[c]]]);
    }, []));
    $("rev_p2").innerHTML = D.rev_p2(R, CL, IA);
  }

  function nomeCurto(c) { return { classico_v2: t("k_classico"), tfidf: t("k_classico"), juntos: t("k_juntos") }[c] || t("k_ia"); }
  function achar(texto) { var i = idx.get(Classificador.norm(texto)); return i == null ? null : i; }

  /* ---------------- categorias ---------------- */
  function montarCategorias() {
    var cs = ["tfidf", "lora_1_5b", CL, JU].filter(function (c, i, a) { return c && tem(c) && a.indexOf(c) === i; });
    var base = C(cs[cs.length - 1]).por_categoria, rpc = (R.revisao && R.revisao.por_categoria) || {};
    var cats = Object.keys(base).sort(function (a, b) { return base[b].n - base[a].n; });
    var h = "<thead><tr><th>" + (L === "pt" ? "Categoria" : "Category") + "</th><th>n</th>" + cs.map(function (c) { return "<th>" + esc(nomeCurtoTab(c)) + "</th>"; }).join("") +
      "<th>" + (L === "pt" ? "Rótulos revistos (errado / ambíguo)" : "Reviewed labels (wrong / ambiguous)") + "</th></tr></thead><tbody>";
    cats.forEach(function (k) {
      var rv = rpc[k] || {};
      h += "<tr><td>" + esc(nomeCat(k)) + '</td><td class="num">' + base[k].n + "</td>" + cs.map(function (c) {
        var f = C(c).por_categoria[k].f1;
        var bg = "color-mix(in srgb, var(--ok) " + Math.round(f * 38) + "%, color-mix(in srgb, var(--erro) " + Math.round((1 - f) * 30) + "%, transparent))";
        return '<td><span class="calor" style="background:' + bg + '">' + pct(f, 0) + "</span></td>";
      }).join("") + '<td class="num">' + (rv.rotulo_errado || 0) + " / " + (rv.ambiguo || 0) + "</td></tr>";
    });
    $("f1t").innerHTML = h + "</tbody>";
    // onde ainda erra: as 6 categorias de menor F1 no melhor caminho, com a confusão mais comum (das respostas do teste)
    var alvo = cs[cs.length - 1];
    var piores = cats.slice().sort(function (a, b) { return base[a].f1 - base[b].f1; }).slice(0, 6);
    $("cat_onde").innerHTML = "<p class='mini'>" + esc(DIN[L].cat_i(nomeC(alvo))) + "</p><div class='cat-grid'>" + piores.map(function (k) {
      var conta = {};
      linhas.forEach(function (l, i) { if (l[col.certo] === k && l[col[alvo]] !== k) conta[l[col[alvo]]] = (conta[l[col[alvo]]] || 0) + 1; });
      var top = Object.keys(conta).sort(function (a, b) { return conta[b] - conta[a]; })[0];
      var rv = rpc[k] || {}, ant = tem("tfidf") ? C("tfidf").por_categoria[k].f1 : null;
      return '<div class="cat-c"><div class="prod">' + esc(nomeCat(k)) + '</div><div class="rot num">F1 ' + (ant != null ? pct(ant, 0) + " → " : "") + pct(base[k].f1, 0) + "</div><p>" +
        esc(DIN[L].cat_txt(top ? nomeCat(top) : null, top ? conta[top] : 0, rv.rotulo_errado || 0, rv.ambiguo || 0)) + (NOTAS[L][k] ? " " + esc(NOTAS[L][k]) : "") + "</p></div>";
    }).join("") + "</div>";
  }

  function nomeCurtoTab(c) {
    var m = { pt: { tfidf: "Clássico v1", lora_1_5b: "IA v1", classico_v2: "Clássico v2", qwen15_lora_q: "IA classif.", lora_v1_escrita: "IA (LoRA)", bertimbau_q: "BERTimbau", juntos: "Juntos", cascata: "Cascata", cascata_ia_v2: "Cascata barata" },
      en: { tfidf: "Classic v1", lora_1_5b: "AI v1", classico_v2: "Classic v2", qwen15_lora_q: "Classifier AI", lora_v1_escrita: "AI (LoRA)", bertimbau_q: "BERTimbau", juntos: "Together", cascata: "Cascade", cascata_ia_v2: "Cheap cascade" } };
    return m[L][c] || nomeC(c);
  }

  /* ---------------- erros comentados ---------------- */
  function montarErros() {
    var tipos = { rotulo: L === "pt" ? "rótulo errado" : "wrong label", modelo: L === "pt" ? "erro do modelo" : "model error", ambiguo: L === "pt" ? "ambíguo" : "ambiguous" };
    var cs = ["tfidf", "lora_1_5b", CL, "qwen15_lora_q", JU].filter(function (c, i, a) { return c && tem(c) && a.indexOf(c) === i; });
    $("erros").innerHTML = "<p class='mini' style='grid-column:1/-1;margin:0'>" + esc(DIN[L].err_i) + "</p>" + erros.map(function (e) {
      var i = achar(e.texto), chips = "", base = "";
      if (i != null) {
        var ac = aceitas(i), orig = linhas[i][col.certo];
        base = (L === "pt" ? "Base: " : "Label: ") + nomeCat(orig);
        if (ac[0] !== orig) base += (L === "pt" ? " · Revisão: " : " · Review: ") + ac.map(nomeCat).join(L === "pt" ? " ou " : " or ");
        else if (ac.length > 1) base += (L === "pt" ? " · Também vale: " : " · Also fine: ") + ac.slice(1).map(nomeCat).join(", ");
        chips = '<div class="chips-c">' + cs.map(function (c) {
          var ok = certoRev(i, c), p = linhas[i][col[c]];
          return '<span class="ch ' + (ok ? "ok" : "no") + '" title="' + esc(nomeCat(p)) + '">' + (ok ? "✓ " : "✕ ") + esc(nomeCurtoTab(c)) + "</span>";
        }).join("") + "</div>";
      }
      return '<div class="erro"><div class="prod">' + esc(e.texto) + '</div><div class="rot"><span class="tag ' + e.tipo + '">' + tipos[e.tipo] + "</span>" + esc(base) + "</div>" + chips + "<p>" + esc(e[L]) + "</p></div>";
    }).join("");
  }

  function montarComo() {
    var d = R.dados;
    $("como_l").innerHTML = COMO[L](R, d).map(function (x) { return "<li>" + x + "</li>"; }).join("");
    if (R.split_aleatorio_tfidf && tem("tfidf")) {
      var a = R.split_aleatorio_tfidf.acuracia, b = C("tfidf").acuracia;
      var rot = L === "pt" ? ["Split aleatório", "Split por marca"] : ["Random split", "Brand split"];
      barras("vaz", [[rot[0], a, "var(--muted)"], [rot[1], b, "var(--c-classico)"]]);
    }
  }

  function montarChips() {
    var quer = (R.chips || []).filter(function (s) { return idx.has(Classificador.norm(s)); }).slice(0, 5);
    $("chips").innerHTML = quer.map(function (s) { return '<button type="button" class="chip">' + esc(s) + "</button>"; }).join(" ");
    $("chips").querySelectorAll("button").forEach(function (b) { b.addEventListener("click", function () { $("q").value = b.textContent; classificar(b.textContent, true); }); });
  }

  function montarTudo() { montarPlacar(); montarTabela(); montarCusto(); montarAchados(); montarQuantidade(); montarCategorias(); montarErros(); montarComo(); montarChips(); }

  /* ---------------- demonstração ---------------- */
  function faixaTxt(q) {
    if (!q || q.tipo === "nenhum") return L === "pt" ? "Quantidade: não achei no texto." : "Quantity: none found in the text.";
    var lim = { massa: [20, 45, 90, 180, 350, 700, 1500], volume: [250, 400, 700, 1200, 2200], unid: [1, 6, 20] }[q.tipo];
    var un = { massa: "g", volume: "ml", unid: L === "pt" ? "un." : "units" }[q.tipo];
    var f = q.faixa, a = f === 0 ? null : lim[f - 1], b = f < lim.length ? lim[f] : null;
    var v = q.tipo === "unid" ? fmtNum(q.valor, 0) + " " + un : (q.valor >= 1000 ? fmtNum(q.valor / 1000, 2).replace(/[,.]?0+$/, "") + (q.tipo === "massa" ? " kg" : " L") : fmtNum(q.valor, q.valor % 1 ? 1 : 0) + " " + un);
    var faixa = a == null ? (L === "pt" ? "até " : "up to ") + fmtInt(b) + " " + un : b == null ? (L === "pt" ? "mais de " : "over ") + fmtInt(a) + " " + un : fmtInt(a) + (L === "pt" ? " a " : " to ") + fmtInt(b) + " " + un;
    return (L === "pt" ? "Quantidade lida: " : "Quantity read: ") + v + (L === "pt" ? " (faixa " : " (range ") + faixa + ")";
  }

  function cardClassico(texto) {
    if (!texto.trim()) return '<p class="vazio">' + t("digite") + "</p>";
    var r = clf.prever(texto, 3), h = '<div class="barras">';
    r.top.forEach(function (x, i) {
      h += '<div class="barra' + (i === 0 ? " prim" : "") + '"><div class="topo-b"><span>' + esc(nomeCat(x.chave)) + '</span><span class="num">' + (x.p < 0.005 ? "<1%" : pct(x.p, 0)) + '</span></div><div class="trilho"><div class="enche" style="width:' + (100 * x.p) + "%;background:var(--c-classico);opacity:" + (i === 0 ? 1 : 0.45) + '"></div></div></div>';
    });
    h += "</div>";
    if (clf.temQuantidade) h += '<div class="crua" style="margin-top:10px">' + esc(faixaTxt(r.quantidade)) + "</div>";
    if (!r.conhecidos) h += '<p class="aviso">' + t("desconhecido") + "</p>";
    if (atual.linha != null) h += marca(aceitas(atual.linha).indexOf(r.top[0].chave) >= 0);
    return h;
  }

  function marca(ok) { return ok ? '<span class="marca-ok">✓ ' + t("acertou") + "</span>" : '<span class="marca-erro">✕ ' + t("errou") + "</span>"; }

  function cardIA(c, temParecidos) {
    if (atual.linha == null) {
      if (!atual.texto.trim()) return '<p class="vazio">' + t("digite") + "</p>";
      return '<p class="nota-ia">' + esc(t(temParecidos ? "so_teste" : "so_teste_sem")) + "</p>";
    }
    var l = linhas[atual.linha], p = l[col[c]], h = '<div class="resposta">' + esc(nomeCat(p)) + "</div>";
    if (c === IA && tem("qwen15_lora_q") && col.qwen15_lora_q != null) {
      var p1 = l[col.qwen15_lora_q];
      h += '<div class="crua">' + esc((L === "pt" ? "A IA como classificador (v2) disse: " : "The classifier AI (v2) said: ") + nomeCat(p1)) + " " + (aceitas(atual.linha).indexOf(p1) >= 0 ? "✓" : "✕") + "</div>";
    }
    if (c === "juntos" && R.combinacao) {
      h += '<div class="crua">' + esc(DIN[L].juntos_nota(R.combinacao.escolhida)) + "</div>";
    }
    return h + marca(certoRev(atual.linha, c));
  }

  function render() {
    if (!R) return;
    var ps = atual.linha == null && atual.texto.trim().length >= 3 ? parecidos(atual.texto, 6) : [];
    var cards = [CL, IA, JU].filter(Boolean);
    $("res3").innerHTML = cards.map(function (c) {
      return '<article class="res' + (c === CL ? " res-cl" : "") + '"><header><span class="ponto" style="background:' + COR[c] + '"></span>' + esc(nomeC(c)) + '</header><div class="onde">' + esc(ONDE[L][c] || "") + "</div>" +
        (c === CL ? cardClassico(atual.texto) : cardIA(c, ps.length > 0)) + "</article>";
    }).join("");
    var certo = $("certo");
    if (atual.linha != null) {
      var i = atual.linha, orig = linhas[i][col.certo], ac = aceitas(i), extra = "";
      if (ac[0] !== orig) extra = " · " + (L === "pt" ? "Revisão: rótulo da base errado, o certo é " : "Review: the database label is wrong, correct is ") + "<b>" + esc(ac.map(nomeCat).join(L === "pt" ? " ou " : " or ")) + "</b>";
      else if (ac.length > 1) extra = " · " + (L === "pt" ? "Revisão: ambíguo, também vale " : "Review: ambiguous, also fine: ") + "<b>" + esc(ac.slice(1).map(nomeCat).join(", ")) + "</b>";
      certo.innerHTML = esc(t("certo")) + " <b>" + esc(nomeCat(orig)) + "</b>" + extra;
      certo.classList.add("on");
    } else certo.classList.remove("on");
    var sug = $("sug");
    if (atual.linha == null && atual.texto.trim().length >= 3) {
      if (ps.length) {
        $("sugl").innerHTML = ps.map(function (i) { return '<li><button type="button" data-i="' + i + '">' + esc(linhas[i][col.texto]) + "</button></li>"; }).join("");
        $("sugl").querySelectorAll("button").forEach(function (b) { b.addEventListener("click", function () { escolher(+b.dataset.i); }); });
        sug.classList.add("on");
      } else sug.classList.remove("on");
    } else sug.classList.remove("on");
  }

  function classificar(texto, mostrar) {
    atual.texto = texto;
    var i = idx.get(Classificador.norm(texto));
    atual.linha = i == null ? null : i;
    render();
    if (mostrar) mostrarResposta();
  }

  /* retorno visível: realça o cartão do clássico e rola até a resposta se ela estiver fora da tela */
  var semMovimento = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  function mostrarResposta() {
    var cl = document.querySelector("#res3 .res-cl");
    if (cl) { cl.classList.remove("realce"); void cl.offsetWidth; cl.classList.add("realce"); }
    var alvo = $("certo").classList.contains("on") ? $("certo") : $("res3");
    var r = alvo.getBoundingClientRect(), topo = 72;
    if (r.top < topo || r.top > window.innerHeight * 0.55) {
      window.scrollTo({ top: window.scrollY + r.top - topo, behavior: semMovimento ? "auto" : "smooth" });
    }
  }

  function escolher(i) { $("q").value = linhas[i][col.texto]; classificar(linhas[i][col.texto], true); }

  function sortear() {
    var f = $("filtro").value, cand = [];
    linhas.forEach(function (l, i) {
      var ok = true;
      if (f === "ia_erra") ok = !certoRev(i, IA);
      else if (f === "classico_erra") ok = !certoRev(i, CL);
      else if (f === "juntos_erra") ok = JU ? !certoRev(i, JU) : false;
      else if (f === "revisto") ok = l[col.situacao] === "rotulo_errado" || l[col.situacao] === "ambiguo";
      if (ok) cand.push(i);
    });
    if (cand.length) escolher(cand[Math.floor(Math.random() * cand.length)]);
  }

  /* ---------------- textos que dependem dos números ---------------- */
  function d(R, k) { return R[k] || null; }
  function faixaD(x) { return x ? pts(x.original[0]) + (L === "pt" ? " a " : " to ") + pts(x.original[1]) : ""; }

  var NOTAS = {
    pt: {
      hortifruti: "É a categoria “sobra”: na base aparecem nela geleia, granola, farinha de coco e achocolatado.",
      alcoolicas: "Muita cerveja importada só tinha a tag “bebida alcoólica” e caiu aqui; também tem Skol Beats, que fica entre cerveja e drinque.",
      conservas: "Milho, ervilha e grão-de-bico em lata aparecem ora em conservas, ora em grãos, conforme quem cadastrou.",
      balas_doces: "Bombom e trufa ficam no limite com chocolates; Tic Tac e balas aparecem até em geleias.",
      geleias_mel: "Mistura geleia, doce de leite, pasta de amendoim e mel; na regra das tags, mel vai para açúcar, mas o nome da categoria diz mel.",
      pratos_prontos: "Fronteira com massas (lasanha, mac’n cheese) e com carnes (nuggets, empanados).",
      sorvetes: "O nome lembra outra coisa (Oreo, cookies, brownie): só a marca da sorveteria ou o “ml” dá a pista.",
      chocolates: "Muita barra com nome de fantasia (Charge, Suflair, Prestígio) e marca toda no teste.",
      castanhas: "Pasta de amendoim e paçoca ficam entre castanhas, geleias e doces.",
      sucos: "Leite fermentado e iogurte de frutas aparecem rotulados como suco.",
      bebidas_vegetais: "Leite zero lactose (de vaca) aparece rotulado como bebida vegetal.",
      frutas: "",
    },
    en: {
      hortifruti: "It is the “leftover” category: jam, granola, coconut flour and chocolate drink mix show up in it.",
      alcoolicas: "Many imported beers only had the “alcoholic beverage” tag and landed here; Skol Beats sits between beer and a mixed drink.",
      conservas: "Canned corn, peas and chickpeas show up either as canned food or as grains, depending on who entered them.",
      balas_doces: "Bonbons and truffles border on chocolates; Tic Tac and candies even show up as jams.",
      geleias_mel: "Mixes jam, dulce de leche, peanut butter and honey; by the tag rule honey goes to sugar, but the category name says honey.",
      pratos_prontos: "Borders on pasta (lasagna, mac’n cheese) and on meat (nuggets, breaded chicken).",
      sorvetes: "The name points elsewhere (Oreo, cookies, brownie): only the ice-cream brand or the “ml” gives it away.",
      chocolates: "Many bars with brand-only names (Charge, Suflair, Prestígio), and the whole brand is in the test set.",
      castanhas: "Peanut butter and paçoca sit between nuts, spreads and candy.",
      sucos: "Fermented milk and fruit yogurt show up labeled as juice.",
      bebidas_vegetais: "Lactose-free cow milk shows up labeled as a plant-based drink.",
    },
  };

  var DIN = {
    pt: {
      res_i: function (R) { return fmtInt(R.n_teste) + " produtos de " + R.categorias + " categorias, de marcas que não aparecem no treino. A barra é o acerto contra a categoria da base; o traço mostra a faixa de 95% de confiança. “Teste revisado” conta como certo quando a base estava errada e o modelo acertou o produto (veja a revisão abaixo)."; },
      res_rodape: function (R) { return "Tempos: GPU T4 do Kaggle (de 2018) para as IAs; CPU comum de 2 núcleos para o clássico. “Um por vez” = um produto chegando sozinho, como num cadastro feito na hora."; },
      custo_i: function (R, CL, IA) {
        var v1 = C("lora_1_5b"), c1 = C("tfidf");
        return "De manhã, a IA ajustada (LoRA) ganhava do clássico v1 por " + pts(v1.acuracia - c1.acuracia) + " pontos e levava " + fmtNum(v1.ms_um / c1.ms_um, 0) + " vezes mais tempo por produto, um por vez, numa GPU. Sozinha, não compensava, e agora compensa menos ainda: o clássico v2 chegou ao mesmo acerto sem GPU. O que a IA faz bem é dar uma segunda opinião. Tempos com o LoRA fundido nos pesos, como em produção:";
      },
      so_classico: "Só o clássico (nada vai para a GPU)", tudo_ia: "Os três juntos em tudo (100% na GPU)",
      cascata_rot: function (f, barata) { return (barata ? "Cascata barata (" : "Cascata (") + pct(f, 0) + " vão para a GPU)"; },
      cascata_t: "Acerto no teste, conforme quanto passa pela GPU:",
      k_cascata_sub: function (r) { return "só " + pct(r.fracao_gpu, 0) + " na GPU"; },
      quando: function (R, CL, IA) {
        var out = [], c = C(CL), ia = C(IA), v1 = C("lora_1_5b"), c1 = C("tfidf");
        out.push("<b>Não vale: o LoRA sozinho.</b> Ele acerta " + pct(ia.acuracia) + ", e o clássico v2, " + pct(c.acuracia) + " (empate). Mesmo fundido nos pesos, leva " + ms(ia.ms_um) + " por produto, um por vez, numa GPU; o clássico leva " + ms(c.ms_um) + " numa CPU comum e menos de 1 ms no navegador.");
        if (tem("qwen15_lora_q")) {
          var q = C("qwen15_lora_q");
          out.push("<b>Testamos uma IA mais rápida:</b> o mesmo modelo como classificador (uma passada, sem escrever) responde em " + ms(q.ms_um) + ", mas acertou menos no teste (" + pct(q.acuracia) + "). Escrever o nome da categoria aproveita o que o modelo já sabe dessas palavras; a cabeça de classificação começa do zero. Na validação parecia empate, por isso a medição no teste importa.");
        }
        if (tem("juntos")) {
          var j = C("juntos"), e = Math.round((j.acuracia - c.acuracia) * 1000);
          out.push("<b>Vale: como segunda opinião, em lote.</b> Juntos, clássico e IA tiram " + fmtInt(e) + " erros a mais a cada 1.000 produtos (faixa " + faixaD(R.juntos_menos_classico_v2) + " pontos). Se uma pessoa leva uns 30 segundos para achar e corrigir um produto na categoria errada (estimativa), são " + fmtInt(Math.round(e * 30 / 60)) + " minutos de trabalho poupados a cada 1.000.");
        }
        out.push("<b>O custo de verdade é a GPU ligada</b>, não o produto: uma máquina com GPU esperando cadastro custa o mês inteiro. Por isso a cascata manda para a IA só o que o clássico não tem certeza.");
        return out;
      },
      recomenda: function (R, CL, IA) {
        if (!tem("cascata_ia_v2")) return "";
        var b = C("cascata_ia_v2"), cas = C("cascata"), j = C("juntos");
        return "<b>Recomendação para produção: a cascata barata.</b><ol><li>O clássico v2 responde na hora, em CPU ou no navegador. Quando a confiança dele passa de " + pct(b.limite, 0) + " (" + pct(1 - b.fracao_gpu, 0) + " dos produtos), ele acerta " + pct(b.acuracia_quando_classico_seguro) + ".</li><li>O resto (" + pct(b.fracao_gpu, 0) + ") vai para a IA classificadora, em lote, com a GPU ligada só nessa hora.</li><li>Quando os dois discordam, o produto vai para uma pessoa conferir.</li></ol>" +
          "No teste: " + pct(b.acuracia) + " de acerto, " + ms(b.ms_um) + " por produto em média. A cascata com os três juntos dá " + pct(cas.acuracia) + " (diferença dentro da margem: " + faixaD(R.cascata_menos_cascata_barata) + " pontos) e custa " + fmtNum(cas.ms_um / b.ms_um, 0) + " vezes mais. Limites escolhidos na validação.";
      },
      achados: function (R, CL, IA) {
        var out = [], c = C(CL), c1 = C("tfidf");
        out.push({ cor: "var(--c-classico)", grande: "+" + pts(c.acuracia - c1.acuracia) + " pontos", texto: "O clássico melhorou sem GPU: outro modelo linear (LinearSVC), a quantidade em faixas e cada produto do treino repetido sem a marca (o lojista novo traz marca que o modelo nunca viu). Faixa da melhora: " + faixaD(R.classico_v2_menos_v1) + " pontos. Agora ele empata com a IA ajustada." });
        if (tem("juntos")) {
          var j = C("juntos");
          out.push({ cor: "var(--c-juntos)", grande: pct(j.acuracia), texto: "é o acerto do clássico e da IA juntos: " + pts(j.acuracia - C("lora_1_5b").acuracia) + " pontos acima do melhor da manhã (faixa " + faixaD(R.juntos_menos_lora_v1) + "). Eles erram coisas diferentes: o clássico lê palavras, a IA conhece marcas e o mundo. Quando concordam (" + pct(R.combinacao.concordam.cobertura, 0) + " dos produtos), acertam " + pct(R.combinacao.concordam.acuracia, 0) + "." });
        }
        var rv = R.revisao, e = C("lora_1_5b").erros;
        out.push({ cor: "var(--c-zero)", grande: fmtInt(e.aceitos_na_revisao) + " de " + fmtInt(e.total), texto: "erros da IA da manhã viram acerto depois da revisão: a categoria da base estava errada ou era ambígua e o modelo tinha razão. Revisamos " + fmtInt(rv.revistos) + " produtos do teste (" + fmtInt(rv.rotulo_errado || 0) + " rótulos errados, " + fmtInt(rv.ambiguo || 0) + " ambíguos). No teste revisado, os dois juntos acertam " + pct(C(tem("juntos") ? "juntos" : CL).acuracia_revisada) + "." });
        return out;
      },
      q_p1: "Ideia do Rafael: “Leite Nestlé 34 g” pode ser leite ou chocolate, mas não existe caixa de leite de 34 g. Então lemos a quantidade do texto, normalizamos (1 kg = 1.000 g, 1,5 L = 1.500 ml) e colocamos em faixas (20 a 45 g, 250 a 400 ml...). O clássico recebe a faixa como uma palavra a mais; as IAs recebem “| quantidade: 34 g” no fim do texto. Acerto no teste, sem e com:",
      q_sem: function (pt) { return pt + ", sem"; }, q_com: function (pt) { return pt + ", com"; },
      q_p2: function (R, i) {
        var q = R.quantidade || {}, s = [];
        if (q.classico) s.push("No clássico, a quantidade muda a resposta de " + fmtInt(q.classico.mudaram) + " produtos e o saldo é " + pts(q.classico.teste_com - q.classico.teste_sem) + " ponto no teste (+" + pts(q.classico.cv_com - q.classico.cv_sem) + " na validação cruzada, que foi onde escolhemos).");
        if (q.bertimbau) s.push("No BERTimbau, " + (q.bertimbau.teste_com >= q.bertimbau.teste_sem ? "+" : "") + pts(q.bertimbau.teste_com - q.bertimbau.teste_sem) + " ponto (faixa " + pts(q.bertimbau.com_menos_sem_ic95[0]) + " a " + pts(q.bertimbau.com_menos_sem_ic95[1]) + ").");
        s.push("Leitura honesta: ela ajuda a desempatar, mas pesa pouco no total, porque a maioria dos nomes já diz o que é o produto.");
        if (i != null && tem("juntos")) s.push("No “Leite Nestlé 34 g”: clássico v2 diz " + nomeCat(linhas[i][col[CL]]) + ", juntos dizem " + nomeCat(linhas[i][col.juntos]) + ".");
        return esc(s.join(" "));
      },
      original: "original", revisado: "revisado",
      rev_p1: function (rv) { return "A base é colaborativa e tem erro. Revisamos, produto por produto e olhando só o nome, os " + fmtInt(rv.revistos) + " produtos do teste em que algum modelo da manhã errou: " + fmtInt(rv.rotulo_errado || 0) + " estavam com a categoria errada (cerveja em “vinhos e destilados”, leite fermentado em “leite”, bala em “geleias”) e " + fmtInt(rv.ambiguo || 0) + " valem duas categorias (mel, nuggets, alfajor). Acerto original e revisado:"; },
      rev_p2: function (R) { return "O teste não foi mexido: os números principais são contra a base como veio. A revisão foi feita com ajuda de IA (Claude), antes de medir os modelos da tarde, e está em <code>reports/revisao_teste.csv</code> para qualquer um conferir. Ela favorece um pouco todos os modelos (só revimos onde algum errou), então o número a comparar é sempre o original."; },
      cat_i: function (n) { return "As 6 categorias mais fracas em “" + n + "”, com a confusão mais comum no teste:"; },
      cat_txt: function (top, n, w, a) { return (top ? "Mais confundida com " + top + " (" + n + (n === 1 ? " vez). " : " vezes). ") : "") + (w + a ? "Rótulos revistos: " + w + (w === 1 ? " errado e " : " errados e ") + a + (a === 1 ? " ambíguo." : " ambíguos.") : "Nenhum rótulo revisto."); },
      err_i: "✓ e ✕ contam como certo o que está certo depois da revisão do rótulo. Passe o mouse num selo para ver a resposta.",
      juntos_nota: function (e) { return "Pesos escolhidos na validação: " + e.modelos.map(function (m, i) { return nomeCurtoTab(m) + " " + fmtNum(e.pesos[i], 1); }).join(", ") + "."; },
    },
    en: {
      res_i: function (R) { return fmtInt(R.n_teste) + " products, " + R.categorias + " categories, brands not seen in training. The bar is accuracy against the database label; the whisker is the 95% confidence range. “Reviewed test” counts as right when the database was wrong and the model got the product right (see the review below)."; },
      res_rodape: function (R) { return "Timing: Kaggle T4 GPU (from 2018) for the AIs; a regular 2-core CPU for the classic model. “One at a time” = a single product arriving on its own, as in a live listing."; },
      custo_i: function (R, CL, IA) {
        var v1 = C("lora_1_5b"), c1 = C("tfidf");
        return "In the morning, the tuned AI (LoRA) beat classic v1 by " + pts(v1.acuracia - c1.acuracia) + " points and took " + fmtNum(v1.ms_um / c1.ms_um, 0) + " times longer per product, one at a time, on a GPU. On its own it was not worth it, and now even less so: classic v2 reached the same accuracy without a GPU. What the AI does well is give a second opinion. Timing with the LoRA merged into the weights, as in production:";
      },
      so_classico: "Classic only (nothing goes to the GPU)", tudo_ia: "All three together on everything (100% on GPU)",
      cascata_rot: function (f, barata) { return (barata ? "Cheap cascade (" : "Cascade (") + pct(f, 0) + " go to the GPU)"; },
      cascata_t: "Test accuracy, by how much goes through the GPU:",
      k_cascata_sub: function (r) { return "only " + pct(r.fracao_gpu, 0) + " on GPU"; },
      quando: function (R, CL, IA) {
        var out = [], c = C(CL), ia = C(IA);
        out.push("<b>Not worth it: LoRA on its own.</b> It gets " + pct(ia.acuracia) + ", and classic v2 gets " + pct(c.acuracia) + " (a tie). Even merged into the weights, it takes " + ms(ia.ms_um) + " per product, one at a time, on a GPU; the classic model takes " + ms(c.ms_um) + " on a regular CPU and under 1 ms in the browser.");
        if (tem("qwen15_lora_q")) {
          var q = C("qwen15_lora_q");
          out.push("<b>We tried a faster AI:</b> the same model as a classifier (one pass, no writing) answers in " + ms(q.ms_um) + ", but it was less accurate on the test (" + pct(q.acuracia) + "). Writing the category name uses what the model already knows about those words; a classification head starts from scratch. On validation it looked like a tie, which is why measuring on the test matters.");
        }
        if (tem("juntos")) {
          var j = C("juntos"), e = Math.round((j.acuracia - c.acuracia) * 1000);
          out.push("<b>Worth it: as a second opinion, in batch.</b> Together, the classic model and the AI remove " + fmtInt(e) + " more errors per 1,000 products (range " + faixaD(R.juntos_menos_classico_v2) + " points). If a person takes about 30 seconds to find and fix a product in the wrong category (an estimate), that is " + fmtInt(Math.round(e * 30 / 60)) + " minutes of work saved per 1,000.");
        }
        out.push("<b>The real cost is a GPU left on</b>, not the product: a GPU machine waiting for listings costs the whole month. That is why the cascade only sends what the classic model is unsure about.");
        return out;
      },
      recomenda: function (R, CL, IA) {
        if (!tem("cascata_ia_v2")) return "";
        var b = C("cascata_ia_v2"), cas = C("cascata");
        return "<b>Recommendation for production: the cheap cascade.</b><ol><li>Classic v2 answers live, on a CPU or in the browser. When its confidence is above " + pct(b.limite, 0) + " (" + pct(1 - b.fracao_gpu, 0) + " of products), it is right " + pct(b.acuracia_quando_classico_seguro) + " of the time.</li><li>The rest (" + pct(b.fracao_gpu, 0) + ") goes to the classifier AI, in batch, with the GPU on only then.</li><li>When the two disagree, a person checks it.</li></ol>" +
          "On the test: " + pct(b.acuracia) + " accuracy, " + ms(b.ms_um) + " per product on average. The cascade with all three together gets " + pct(cas.acuracia) + " (difference within the margin: " + faixaD(R.cascata_menos_cascata_barata) + " points) and costs " + fmtNum(cas.ms_um / b.ms_um, 0) + " times more. Thresholds picked on validation.";
      },
      achados: function (R, CL, IA) {
        var out = [], c = C(CL), c1 = C("tfidf");
        out.push({ cor: "var(--c-classico)", grande: "+" + pts(c.acuracia - c1.acuracia) + " points", texto: "The classic model improved with no GPU: a different linear model (LinearSVC), quantity ranges, and every training product repeated without its brand (a new store brings a brand the model never saw). Range of the gain: " + faixaD(R.classico_v2_menos_v1) + " points. It now ties the tuned AI." });
        if (tem("juntos")) {
          var j = C("juntos");
          out.push({ cor: "var(--c-juntos)", grande: pct(j.acuracia), texto: "is the accuracy of the classic model and the AI together: " + pts(j.acuracia - C("lora_1_5b").acuracia) + " points above the morning’s best (range " + faixaD(R.juntos_menos_lora_v1) + "). They make different mistakes: the classic model reads words, the AI knows brands and the world. When they agree (" + pct(R.combinacao.concordam.cobertura, 0) + " of products), they are right " + pct(R.combinacao.concordam.acuracia, 0) + " of the time." });
        }
        var rv = R.revisao, e = C("lora_1_5b").erros;
        out.push({ cor: "var(--c-zero)", grande: fmtInt(e.aceitos_na_revisao) + " of " + fmtInt(e.total), texto: "errors of the morning AI become correct after the review: the database category was wrong or ambiguous and the model was right. We reviewed " + fmtInt(rv.revistos) + " test products (" + fmtInt(rv.rotulo_errado || 0) + " wrong labels, " + fmtInt(rv.ambiguo || 0) + " ambiguous). On the reviewed test, both together get " + pct(C(tem("juntos") ? "juntos" : CL).acuracia_revisada) + "." });
        return out;
      },
      q_p1: "Rafael’s idea: “Leite Nestlé 34 g” could be milk or chocolate, but there is no 34 g carton of milk. So we read the quantity from the text, normalize it (1 kg = 1,000 g, 1.5 L = 1,500 ml) and bucket it (20 to 45 g, 250 to 400 ml...). The classic model gets the range as one extra word; the AIs get “| quantidade: 34 g” at the end of the text. Test accuracy, without and with:",
      q_sem: function (pt, en) { return en + ", without"; }, q_com: function (pt, en) { return en + ", with"; },
      q_p2: function (R, i) {
        var q = R.quantidade || {}, s = [];
        if (q.classico) s.push("In the classic model, the quantity changes the answer for " + fmtInt(q.classico.mudaram) + " products and the net effect is " + pts(q.classico.teste_com - q.classico.teste_sem) + " point on the test (+" + pts(q.classico.cv_com - q.classico.cv_sem) + " in cross-validation, where we made the choice).");
        if (q.bertimbau) s.push("In BERTimbau, " + (q.bertimbau.teste_com >= q.bertimbau.teste_sem ? "+" : "") + pts(q.bertimbau.teste_com - q.bertimbau.teste_sem) + " point (range " + pts(q.bertimbau.com_menos_sem_ic95[0]) + " to " + pts(q.bertimbau.com_menos_sem_ic95[1]) + ").");
        s.push("Honest reading: it helps break ties, but it weighs little overall, because most names already say what the product is.");
        if (i != null && tem("juntos")) s.push("For “Leite Nestlé 34 g”: classic v2 says " + nomeCat(linhas[i][col[CL]]) + ", together they say " + nomeCat(linhas[i][col.juntos]) + ".");
        return esc(s.join(" "));
      },
      original: "original", revisado: "reviewed",
      rev_p1: function (rv) { return "The database is crowdsourced and has errors. Product by product, looking only at the name, we reviewed the " + fmtInt(rv.revistos) + " test products where some morning model was wrong: " + fmtInt(rv.rotulo_errado || 0) + " had the wrong category (beer under “wine and spirits”, fermented milk under “milk”, candy under “jams”) and " + fmtInt(rv.ambiguo || 0) + " fit two categories (honey, nuggets, alfajor). Original vs reviewed accuracy:"; },
      rev_p2: function (R) { return "The test was not touched: the headline numbers are against the database as it came. The review was done with AI help (Claude), before measuring the afternoon models, and it is in <code>reports/revisao_teste.csv</code> for anyone to check. It slightly favors every model (we only reviewed where some model was wrong), so the number to compare is always the original one."; },
      cat_i: function (n) { return "The 6 weakest categories for “" + n + "”, with the most common confusion on the test:"; },
      cat_txt: function (top, n, w, a) { return (top ? "Most often confused with " + top + " (" + n + (n === 1 ? " time). " : " times). ") : "") + (w + a ? "Reviewed labels: " + w + " wrong and " + a + " ambiguous." : "No reviewed labels."); },
      err_i: "✓ and ✕ count as right what is right after the label review. Hover a badge to see the answer.",
      juntos_nota: function (e) { return "Weights picked on validation: " + e.modelos.map(function (m, i) { return nomeCurtoTab(m) + " " + fmtNum(e.pesos[i], 1); }).join(", ") + "."; },
    },
  };

  var COMO = {
    pt: function (R, d) {
      return [
        fmtInt(d.produtos_brasil_com_nome_e_categoria) + " produtos vendidos no Brasil com nome e categoria no Open Food Facts; " + fmtInt(d.depois_de_tirar_repetidos) + " depois de juntar as tags em " + d.categorias + " categorias de prateleira e tirar repetidos.",
        "Divisão por marca: treino " + fmtInt(d.treino) + ", validação " + fmtInt(d.validacao) + ", teste " + fmtInt(d.teste) + ". Nenhuma marca do teste aparece no treino, como um lojista novo cadastrando produtos.",
        "Todos os caminhos treinam só no treino. Tudo o que foi escolhido (configuração do clássico, época das IAs, pesos da combinação, limite da cascata) foi escolhido na validação ou em validação cruzada por marca dentro de treino + validação. O teste é o mesmo de manhã e foi usado uma vez por versão.",
        "Acerto com faixa de 95% (bootstrap, 2.000 sorteios) e F1 macro (média por categoria: a categoria pequena pesa igual à grande). Diferença entre caminhos com bootstrap pareado (os mesmos produtos nos dois).",
        "Uma decisão veio depois de olhar o teste, e fica registrada: a IA como classificador acertou menos que a da manhã, então a IA da manhã voltou para a combinação (respondendo de novo a validação, com confiança). Os pesos continuaram saindo da validação; a primeira combinação deu " + (tem("juntos_ia_v2") ? pct(C("juntos_ia_v2").acuracia) : "") + " no teste e está nos relatórios.",
        "Por que dividir por marca: o mesmo clássico v1 parece melhor quando o teste tem marcas que ele já viu.",
      ];
    },
    en: function (R, d) {
      return [
        fmtInt(d.produtos_brasil_com_nome_e_categoria) + " products sold in Brazil with a name and category in Open Food Facts; " + fmtInt(d.depois_de_tirar_repetidos) + " after mapping tags to " + d.categorias + " shelf categories and removing duplicates.",
        "Split by brand: train " + fmtInt(d.treino) + ", validation " + fmtInt(d.validacao) + ", test " + fmtInt(d.teste) + ". No test brand appears in training, like a new store listing its products.",
        "Every approach trains on the train set only. Everything that was chosen (classic settings, AI epoch, combination weights, cascade threshold) was chosen on validation or in brand-grouped cross-validation inside train + validation. The test set is the same as in the morning and was used once per version.",
        "Accuracy with a 95% range (bootstrap, 2,000 resamples) and macro F1 (average over categories: small categories weigh as much as big ones). Differences between approaches use a paired bootstrap (same products in both).",
        "One decision came after looking at the test, and it is on record: the classifier AI was less accurate than the morning one, so the morning AI came back into the combination (answering validation again, with confidence). Weights were still picked on validation; the first combination got " + (tem("juntos_ia_v2") ? pct(C("juntos_ia_v2").acuracia) : "") + " on the test and is in the reports.",
        "Why split by brand: the same classic v1 model looks better when the test set has brands it has already seen.",
      ];
    },
  };

  /* ---------------- início ---------------- */
  document.querySelectorAll(".idioma button").forEach(function (b) {
    b.addEventListener("click", function () { L = b.dataset.lang; try { localStorage.setItem("cm_lang", L); } catch (e) { /* ok */ } aplicarIdioma(); });
  });
  var timer = null;
  $("q").addEventListener("input", function () { clearTimeout(timer); var v = this.value; timer = setTimeout(function () { classificar(v); }, 90); });
  $("form").addEventListener("submit", function (e) {
    e.preventDefault(); clearTimeout(timer);
    if (window.matchMedia && window.matchMedia("(pointer: coarse)").matches) $("q").blur(); // no celular, fecha o teclado para a resposta aparecer
    classificar($("q").value, true);
  });
  $("sortear").addEventListener("click", sortear);

  carregar().then(function () {
    aplicarIdioma();
    var inicial = (R.chips && R.chips[0]) || "Leite Condensado Moça 395g";
    $("q").value = inicial; classificar(inicial);
  }).catch(function (e) {
    $("res3").innerHTML = '<p class="vazio">Erro ao carregar os dados: ' + esc(e.message) + "</p>";
  });
})();
