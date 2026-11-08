/* Página do Catálogo de mercado: demonstração + resultados. Sem servidor: tudo vem de arquivos estáticos. */
(function () {
  "use strict";

  var T = {
    pt: {
      marca: "Catálogo de mercado", nav_demo: "Experimente", nav_res: "Resultados", nav_como: "Como foi medido",
      selo: "Projeto de estudo · Rafael Bueno", titulo: "Qual é a categoria deste produto?",
      lead: "Lojista cadastra “LEITE COND MOÇA 395G” e o sistema precisa saber que é leite condensado, para a busca e as vitrines acharem o produto. Aqui, três jeitos de responder, medidos no mesmo teste, com marcas que nenhum modelo viu no treino.",
      demo_t: "Experimente",
      demo_i: "Digite um produto como ele apareceria num catálogo. O modelo clássico responde na hora, aqui no seu navegador. As respostas das duas IAs foram calculadas na GPU gratuita do Kaggle para os produtos do teste (não há servidor ligado): escolha um produto do teste para ver as três lado a lado.",
      rotulo_q: "Produto", btn_ok: "Classificar", exemplos: "Exemplos:", btn_sortear: "Sortear",
      f_todos: "Qualquer produto do teste", f_lora: "Onde a IA ajustada errou", f_tfidf: "Onde o clássico errou", f_disc: "Onde os três discordam",
      sug_t: "Produtos parecidos no teste (com a resposta das três):",
      aviso: "Categoria “certa” = a do Open Food Facts, base colaborativa: às vezes ela mesma está errada (veja os erros comentados abaixo).",
      res_t: "Resultados no teste", ach_t: "O que isso quer dizer",
      imp_t: "Por que isso importa",
      imp_p1: "Em marketplace de comida e de mercado, quem cadastra o produto é o lojista, com texto curto, abreviado e sem padrão. Categoria errada some da busca, aparece na vitrine errada e atrapalha a recomendação. O time de catálogo do iFood descreve exatamente esse problema: classificar ofertas numa taxonomia e usar LLM para rotular dados e vigiar os classificadores.",
      imp_p2: "Este projeto é um recorte pequeno e público desse problema, feito para medir com honestidade quando vale treinar uma IA e quando o clássico resolve.",
      ref1: "Castro e Menezes (iFood), workshop WAMLM no KDD 2024", ref2: "Robotoff, o robô de categorias do próprio Open Food Facts",
      como_t: "Como foi medido", err_t: "Erros comentados", f1_t: "Acerto por categoria (F1)",
      rod1: "Dados: Open Food Facts (world.openfoodfacts.org), base aberta sob a licença ODbL. O recorte usado aqui também é ODbL. Código sob licença MIT.",
      rod2: "Modelos abertos: Qwen2.5-1.5B-Instruct e Qwen2.5-7B-Instruct (Apache 2.0). Nenhuma API paga foi usada.",
      k_tfidf: "Clássico", k_zero: "IA sem treino", k_lora: "IA com LoRA",
      c_tfidf: "Clássico (TF-IDF)", c_zero: "IA sem treino", c_zero7: "IA maior sem treino (7 B)", c_lora: "IA ajustada (LoRA)",
      o_tfidf: "Palavras e pedaços de palavra + regressão logística. Roda no seu navegador.",
      o_zero: "Qwen2.5-1.5B recebe a lista de categorias, sem treino. GPU do Kaggle.",
      o_zero7: "Qwen2.5-7B em 4 bits, sem treino. GPU do Kaggle.",
      o_lora: "O mesmo Qwen2.5-1.5B com um adapter LoRA treinado. GPU do Kaggle.",
      acerto: "acerto", certo: "Categoria certa (Open Food Facts):", acertou: "Acertou", errou: "Errou",
      so_teste: "Esta resposta foi calculada só para os produtos do teste. Escolha um parecido abaixo ou sorteie.",
      digite: "Digite um produto acima.", desconhecido: "Nenhuma palavra conhecida: o modelo está chutando a categoria mais comum.",
      respondeu: "O modelo respondeu: ", fora: " (fora da lista; ligado à categoria mais parecida)",
      th_c: "Caminho", th_a: "Acerto (faixa de 95%)", th_f: "F1 macro", th_t: "Tempo por produto", th_o: "Onde roda",
      lote: "em lote", um: "um por vez", cpu: "CPU comum ou navegador, sem GPU", gpu: "GPU T4 (grátis no Kaggle)",
      res_i: function (r) { return fmtInt(r.n_teste) + " produtos de " + r.categorias + " categorias, de marcas que não aparecem no treino. A barra é o acerto; o traço mostra a faixa de 95% de confiança."; },
      sete_b: "Modelo 7 B sem treino: ",
      treino_lora: function (t) { return "Treino do LoRA: " + fmtNum(t.min, 1) + " min na T4, " + fmtInt(t.exemplos) + " exemplos, " + t.epocas + " épocas; " + fmtNum(100 * t.parametros_treinaveis / t.parametros_total, 2) + "% dos pesos treinados."; },
    },
    en: {
      marca: "Grocery catalog", nav_demo: "Try it", nav_res: "Results", nav_como: "How it was measured",
      selo: "Study project · Rafael Bueno", titulo: "Which category is this product?",
      lead: "A store types “LEITE COND MOÇA 395G” and the system has to know it is condensed milk, so search and shelves can find it. Here are three ways to answer, measured on the same test, with brands no model saw in training.",
      demo_t: "Try it",
      demo_i: "Type a product the way it would show up in a catalog (products are Brazilian, in Portuguese). The classic model answers instantly, right in your browser. The two AI answers were computed on Kaggle’s free GPU for the test products (no server running): pick a test product to see all three side by side.",
      rotulo_q: "Product", btn_ok: "Classify", exemplos: "Examples:", btn_sortear: "Random",
      f_todos: "Any test product", f_lora: "Where the tuned AI was wrong", f_tfidf: "Where the classic model was wrong", f_disc: "Where all three disagree",
      sug_t: "Similar products in the test set (with all three answers):",
      aviso: "“Correct” category = the one in Open Food Facts, a crowdsourced database: sometimes it is wrong itself (see the commented errors below).",
      res_t: "Test results", ach_t: "What it means",
      imp_t: "Why it matters",
      imp_p1: "In food and grocery marketplaces, the store types the product, in short, abbreviated, inconsistent text. A wrong category drops out of search, lands on the wrong shelf and hurts recommendations. iFood’s catalog team describes exactly this problem: classifying offers into a taxonomy and using LLMs to label data and monitor classifiers.",
      imp_p2: "This project is a small, public slice of that problem, built to measure honestly when training an AI is worth it and when the classic model is enough.",
      ref1: "Castro and Menezes (iFood), WAMLM workshop at KDD 2024", ref2: "Robotoff, Open Food Facts’ own category robot",
      como_t: "How it was measured", err_t: "Commented errors", f1_t: "Per-category F1",
      rod1: "Data: Open Food Facts (world.openfoodfacts.org), open database under the ODbL. The subset used here is ODbL too. Code under the MIT license.",
      rod2: "Open models: Qwen2.5-1.5B-Instruct and Qwen2.5-7B-Instruct (Apache 2.0). No paid API was used.",
      k_tfidf: "Classic", k_zero: "AI, no training", k_lora: "AI + LoRA",
      c_tfidf: "Classic (TF-IDF)", c_zero: "AI, no training", c_zero7: "Bigger AI, no training (7B)", c_lora: "Tuned AI (LoRA)",
      o_tfidf: "Words and word pieces + logistic regression. Runs in your browser.",
      o_zero: "Qwen2.5-1.5B gets the category list, no training. Kaggle GPU.",
      o_zero7: "Qwen2.5-7B in 4-bit, no training. Kaggle GPU.",
      o_lora: "The same Qwen2.5-1.5B with a trained LoRA adapter. Kaggle GPU.",
      acerto: "accuracy", certo: "Correct category (Open Food Facts):", acertou: "Right", errou: "Wrong",
      so_teste: "This answer was computed only for test products. Pick a similar one below or draw one at random.",
      digite: "Type a product above.", desconhecido: "No known word: the model is guessing the most common category.",
      respondeu: "The model answered: ", fora: " (not in the list; mapped to the closest category)",
      th_c: "Approach", th_a: "Accuracy (95% range)", th_f: "Macro F1", th_t: "Time per product", th_o: "Runs on",
      lote: "batched", um: "one at a time", cpu: "Regular CPU or browser, no GPU", gpu: "T4 GPU (free on Kaggle)",
      res_i: function (r) { return fmtInt(r.n_teste) + " products, " + r.categorias + " categories, brands not seen in training. The bar is accuracy; the whisker is the 95% confidence range."; },
      sete_b: "7B model, no training: ",
      treino_lora: function (t) { return "LoRA training: " + fmtNum(t.min, 1) + " min on the T4, " + fmtInt(t.exemplos) + " examples, " + t.epocas + " epochs; " + fmtNum(100 * t.parametros_treinaveis / t.parametros_total, 2) + "% of the weights trained."; },
    },
  };

  var L = "pt";
  try { if ((localStorage.getItem("cm_lang") || "") === "en") L = "en"; } catch (e) { /* sem armazenamento */ }
  if (/[?&]lang=en\b/.test(location.search)) L = "en";
  function t(k) { return T[L][k]; }
  function fmtNum(x, d) { return Number(x).toLocaleString(L === "pt" ? "pt-BR" : "en-US", { minimumFractionDigits: d, maximumFractionDigits: d }); }
  function fmtInt(x) { return Number(x).toLocaleString(L === "pt" ? "pt-BR" : "en-US"); }
  function pct(x, d) { return fmtNum(100 * x, d == null ? 1 : d) + "%"; }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function $(id) { return document.getElementById(id); }

  var COR = { tfidf: "var(--c-classico)", zero_shot_1_5b: "var(--c-zero)", zero_shot_7b_4bit: "var(--c-zero7)", lora_1_5b: "var(--c-lora)" };
  var NOME = { tfidf: "c_tfidf", zero_shot_1_5b: "c_zero", zero_shot_7b_4bit: "c_zero7", lora_1_5b: "c_lora" };
  var ONDE = { tfidf: "o_tfidf", zero_shot_1_5b: "o_zero", zero_shot_7b_4bit: "o_zero7", lora_1_5b: "o_lora" };
  var ORDEM_DEMO = ["tfidf", "zero_shot_1_5b", "lora_1_5b"];

  var clf = null, R = null, EX = null, idx = new Map(), df = new Map(), linhas = [], col = {}, erros = [];
  var atual = { texto: "", linha: null };

  function nomeCat(chave) { return (L === "pt" ? R.nomes : R.nomes_en)[chave] || chave; }

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
    });
  }

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

  /* ---------------- cabeçalho e placar ---------------- */
  function montarPlacar() {
    $("placar").innerHTML = ORDEM_DEMO.filter(function (c) { return R.caminhos[c]; }).map(function (c) {
      var r = R.caminhos[c];
      return '<div class="kpi"><div class="rot"><span class="ponto" style="background:' + COR[c] + '"></span>' + esc(t({ tfidf: "k_tfidf", zero_shot_1_5b: "k_zero", lora_1_5b: "k_lora" }[c])) +
        '</div><div class="val num">' + pct(r.acuracia) + '</div><div class="sub">' + esc(t("acerto")) + "</div></div>";
    }).join("");
  }

  function montarTabela() {
    $("res_i").textContent = t("res_i")(R);
    var cs = ["zero_shot_1_5b", "zero_shot_7b_4bit", "tfidf", "lora_1_5b"].filter(function (c) { return R.caminhos[c]; });
    var melhor = cs.reduce(function (a, b) { return R.caminhos[b].acuracia > R.caminhos[a].acuracia ? b : a; }, cs[0]);
    var h = "<thead><tr><th>" + t("th_c") + "</th><th>" + t("th_a") + "</th><th>" + t("th_f") + "</th><th>" + t("th_t") + "</th><th>" + t("th_o") + "</th></tr></thead><tbody>";
    cs.forEach(function (c) {
      var r = R.caminhos[c], ic = r.acuracia_ic95, tempo, onde;
      if (c === "tfidf") { tempo = fmtNum(r.ms_por_item_lote_cpu, 1) + " ms " + t("lote") + "<br><span class='ic-txt'>" + fmtNum(r.ms_um_a_um_cpu, 0) + " ms " + t("um") + "</span>"; onde = t("cpu"); }
      else { tempo = fmtNum(r.ms_por_item_lote_gpu, 0) + " ms " + t("lote") + "<br><span class='ic-txt'>" + fmtNum(r.ms_um_a_um_gpu, 0) + " ms " + t("um") + "</span>"; onde = t("gpu"); }
      h += '<tr class="' + (c === melhor ? "lider" : "") + '"><td><div class="nome-c"><span class="ponto" style="background:' + COR[c] + '"></span><div>' + esc(t(NOME[c])) + "<small>" + esc(t(ONDE[c])) + "</small></div></div></td>" +
        '<td data-r="' + esc(t("th_a")) + '"><div style="display:flex;align-items:center;gap:12px"><span class="v-acerto num">' + pct(r.acuracia) + '</span><div class="escala" style="flex:1"><div class="fundo"></div><div class="fill" style="width:' + (100 * r.acuracia) + "%;background:" + COR[c] + '"></div><div class="ic" style="left:' + (100 * ic[0]) + "%;width:" + (100 * (ic[1] - ic[0])) + '%"></div></div></div><span class="ic-txt num">' + pct(ic[0]) + " – " + pct(ic[1]) + "</span></td>" +
        '<td class="num" data-r="' + esc(t("th_f")) + '">' + pct(r.f1_macro) + "</td>" +
        '<td class="num" data-r="' + esc(t("th_t")) + '">' + tempo + "</td>" +
        '<td data-r="' + esc(t("th_o")) + '">' + esc(onde) + "</td></tr>";
    });
    $("tabela").innerHTML = h + "</tbody>";
  }

  function montarAchados() {
    var c = R.caminhos, cards = [];
    var A = ACHADOS[L](R);
    cards = A.map(function (a) { return '<div class="cartao achado"><div class="grande num" style="color:' + a.cor + '">' + a.grande + "</div><p>" + a.texto + "</p></div>"; });
    $("achados").innerHTML = cards.join("");
  }

  function montarComo() {
    var d = R.dados, it = COMO[L](R, d);
    $("como_l").innerHTML = it.map(function (x) { return "<li>" + x + "</li>"; }).join("");
    if (R.split_aleatorio_tfidf) {
      var a = R.split_aleatorio_tfidf.acuracia, b = R.caminhos.tfidf.acuracia;
      var rot = L === "pt" ? ["Split aleatório", "Split por marca"] : ["Random split", "Brand split"];
      $("vaz").innerHTML = [[rot[0], a, "var(--muted)"], [rot[1], b, "var(--c-classico)"]].map(function (x) {
        return '<div class="l"><span>' + x[0] + '</span><div class="barra"><div class="trilho" style="height:10px"><div class="enche" style="width:' + (100 * x[1]) + "%;background:" + x[2] + '"></div></div></div><b class="num">' + pct(x[1]) + "</b></div>";
      }).join("");
    }
  }

  function montarErros() {
    var tipos = { rotulo: L === "pt" ? "rótulo errado" : "wrong label", modelo: L === "pt" ? "erro do modelo" : "model error", ambiguo: L === "pt" ? "ambíguo" : "ambiguous" };
    $("erros").innerHTML = erros.map(function (e) {
      return '<div class="erro"><div class="prod">' + esc(e.texto) + '</div><div class="rot"><span class="tag ' + e.tipo + '">' + tipos[e.tipo] + "</span>" +
        esc((L === "pt" ? "Base: " : "Label: ") + nomeCat(e.certo) + " · " + t(NOME[e.caminho]) + ": " + nomeCat(e.previsto)) + "</div><p>" + esc(e[L]) + "</p></div>";
    }).join("");
  }

  function montarF1() {
    var cs = ["zero_shot_1_5b", "zero_shot_7b_4bit", "tfidf", "lora_1_5b"].filter(function (c) { return R.caminhos[c]; });
    var pc = R.caminhos.tfidf.por_categoria;
    var cats = Object.keys(pc).sort(function (a, b) { return pc[b].n - pc[a].n; });
    var h = "<thead><tr><th>" + (L === "pt" ? "Categoria" : "Category") + "</th><th>n</th>" + cs.map(function (c) { return "<th>" + esc(t(NOME[c])) + "</th>"; }).join("") + "</tr></thead><tbody>";
    cats.forEach(function (k) {
      h += "<tr><td>" + esc(nomeCat(k)) + '</td><td class="num">' + pc[k].n + "</td>" + cs.map(function (c) {
        var f = R.caminhos[c].por_categoria[k].f1;
        var bg = "color-mix(in srgb, var(--ok) " + Math.round(f * 38) + "%, color-mix(in srgb, var(--erro) " + Math.round((1 - f) * 30) + "%, transparent))";
        return '<td><span class="calor" style="background:' + bg + '">' + pct(f, 0) + "</span></td>";
      }).join("") + "</tr>";
    });
    $("f1t").innerHTML = h + "</tbody>";
  }

  function montarChips() {
    var quer = [];
    var preferidos = (R.chips || []).filter(function (s) { return idx.has(Classificador.norm(s)); });
    quer = quer.concat(preferidos.slice(0, 4));
    $("chips").innerHTML = quer.map(function (s) { return '<button type="button" class="chip">' + esc(s) + "</button>"; }).join(" ");
    $("chips").querySelectorAll("button").forEach(function (b) { b.addEventListener("click", function () { $("q").value = b.textContent; classificar(b.textContent); }); });
  }

  function montarTudo() { montarPlacar(); montarTabela(); montarAchados(); montarComo(); montarErros(); montarF1(); montarChips(); }

  /* ---------------- demonstração ---------------- */
  function cardClassico(texto) {
    if (!texto.trim()) return '<p class="vazio">' + t("digite") + "</p>";
    var r = clf.prever(texto, 3), h = '<div class="barras">';
    r.top.forEach(function (x, i) {
      h += '<div class="barra' + (i === 0 ? " prim" : "") + '"><div class="topo-b"><span>' + esc(nomeCat(x.chave)) + '</span><span class="num">' + (x.p < 0.005 ? "<1%" : pct(x.p, 0)) + '</span></div><div class="trilho"><div class="enche" style="width:' + (100 * x.p) + "%;background:var(--c-classico);opacity:" + (i === 0 ? 1 : 0.45) + '"></div></div></div>';
    });
    h += "</div>";
    if (!r.conhecidos) h += '<p class="aviso">' + t("desconhecido") + "</p>";
    if (atual.linha != null) h += marca(r.top[0].chave === linhas[atual.linha][col.certo]);
    return h;
  }

  function marca(ok) { return ok ? '<span class="marca-ok">✓ ' + t("acertou") + "</span>" : '<span class="marca-erro">✕ ' + t("errou") + "</span>"; }

  function cardIA(c) {
    if (atual.linha == null) return '<p class="vazio">' + (atual.texto.trim() ? t("so_teste") : t("digite")) + "</p>";
    var l = linhas[atual.linha], p = l[col[c]], h = '<div class="resposta">' + esc(nomeCat(p)) + "</div>";
    var crua = col[c + "_resposta"] != null ? l[col[c + "_resposta"]] : null;
    if (crua != null) {
      var nomeP = (R.nomes[p] || "").toLowerCase(), cr = String(crua).trim();
      var crl = cr.toLowerCase().replace(/[.\s]+$/, "");
      var fora = crl !== nomeP && !(crl.length >= 12 && nomeP.indexOf(crl) === 0);
      h += '<div class="crua">' + esc(t("respondeu") + "“" + cr.slice(0, 60) + "”") + (fora ? esc(t("fora")) : "") + "</div>";
    }
    if (c === "zero_shot_1_5b" && col.zero_shot_7b_4bit != null) {
      var p7 = l[col.zero_shot_7b_4bit];
      h += '<div class="crua" style="margin-top:8px">' + esc(t("sete_b") + nomeCat(p7)) + " " + (p7 === l[col.certo] ? "✓" : "✕") + "</div>";
    }
    if (c === "lora_1_5b" && R.caminhos.lora_1_5b && R.caminhos.lora_1_5b.treino) {
      h += '<div class="crua" style="margin-top:8px">' + esc(t("treino_lora")(R.caminhos.lora_1_5b.treino)) + "</div>";
    }
    return h + marca(p === l[col.certo]);
  }

  function render() {
    if (!R) return;
    $("res3").innerHTML = ORDEM_DEMO.filter(function (c) { return c === "tfidf" || col[c] != null; }).map(function (c) {
      return '<article class="res"><header><span class="ponto" style="background:' + COR[c] + '"></span>' + esc(t(NOME[c])) + '</header><div class="onde">' + esc(t(ONDE[c])) + "</div>" +
        (c === "tfidf" ? cardClassico(atual.texto) : cardIA(c)) + "</article>";
    }).join("");
    var certo = $("certo");
    if (atual.linha != null) { certo.innerHTML = esc(t("certo")) + " <b>" + esc(nomeCat(linhas[atual.linha][col.certo])) + "</b>"; certo.classList.add("on"); }
    else certo.classList.remove("on");
    var sug = $("sug");
    if (atual.linha == null && atual.texto.trim().length >= 3) {
      var ps = parecidos(atual.texto, 6);
      if (ps.length) {
        $("sugl").innerHTML = ps.map(function (i) { return '<li><button type="button" data-i="' + i + '">' + esc(linhas[i][col.texto]) + "</button></li>"; }).join("");
        $("sugl").querySelectorAll("button").forEach(function (b) { b.addEventListener("click", function () { escolher(+b.dataset.i); }); });
        sug.classList.add("on");
      } else sug.classList.remove("on");
    } else sug.classList.remove("on");
  }

  function classificar(texto) {
    atual.texto = texto;
    var i = idx.get(Classificador.norm(texto));
    atual.linha = i == null ? null : i;
    render();
  }

  function escolher(i) { $("q").value = linhas[i][col.texto]; classificar(linhas[i][col.texto]); }

  function sortear() {
    var f = $("filtro").value, cand = [];
    linhas.forEach(function (l, i) {
      var ok = true, certo = l[col.certo];
      if (f === "lora_erra") ok = col.lora_1_5b != null && l[col.lora_1_5b] !== certo;
      else if (f === "tfidf_erra") ok = l[col.tfidf] !== certo;
      else if (f === "discordam") ok = col.lora_1_5b != null && col.zero_shot_1_5b != null && new Set([l[col.tfidf], l[col.lora_1_5b], l[col.zero_shot_1_5b]]).size === 3;
      if (ok) cand.push(i);
    });
    if (cand.length) escolher(cand[Math.floor(Math.random() * cand.length)]);
  }

  /* ---------------- textos que dependem dos números ---------------- */
  var ACHADOS = {
    pt: function (R) {
      var c = R.caminhos, out = [];
      if (c.lora_1_5b && c.zero_shot_1_5b) out.push({ cor: "var(--c-lora)", grande: "+" + fmtNum(100 * (c.lora_1_5b.acuracia - c.zero_shot_1_5b.acuracia), 0) + " pontos",
        texto: "O treino é o que faz a IA servir. A mesma IA de 1,5 bilhão de parâmetros sai de " + pct(c.zero_shot_1_5b.acuracia, 0) + " sem treino para " + pct(c.lora_1_5b.acuracia, 0) + " com LoRA" + (c.zero_shot_7b_4bit && c.zero_shot_7b_4bit.acuracia ? ", e uma IA 5 vezes maior sem treino fica em " + pct(c.zero_shot_7b_4bit.acuracia, 0) : "") + ". Sem exemplos, ela não conhece a régua desta loja (o que é “barra” e o que é “chocolate”)." });
      if (c.lora_1_5b && c.tfidf && R.lora_menos_tfidf_ic95) {
        var d = c.lora_1_5b.acuracia - c.tfidf.acuracia, ic = R.lora_menos_tfidf_ic95, vale = ic[0] > 0;
        out.push({ cor: "var(--c-classico)", grande: (vale ? "+" + fmtNum(100 * d, 1) + " pontos" : "Empate"),
          texto: vale ? "A IA ajustada passa o clássico por " + fmtNum(100 * d, 1) + " pontos (faixa de " + fmtNum(100 * ic[0], 1) + " a " + fmtNum(100 * ic[1], 1) + "), mas custa GPU: " + fmtNum(c.lora_1_5b.ms_por_item_lote_gpu, 0) + " ms por produto contra " + fmtNum(c.tfidf.ms_por_item_lote_cpu, 1) + " ms do clássico em CPU."
                      : "A diferença entre a IA ajustada e o clássico (" + fmtNum(100 * d, 1) + " pontos) cabe na margem de erro (" + fmtNum(100 * ic[0], 1) + " a " + fmtNum(100 * ic[1], 1) + "). Com estes dados, o clássico, que roda de graça em CPU, resolve igual." });
      }
      if (R.quando_concordam) {
        var q = R.quando_concordam;
        out.push({ cor: "var(--ok)", grande: pct(q.acuracia, 0), texto: "é o acerto quando o clássico e a IA ajustada dão a mesma resposta, o que acontece em " + pct(q.cobertura, 0) + " dos produtos. Na prática: aprovar esses sozinho e mandar só o resto para uma pessoa conferir." });
      }
      return out;
    },
    en: function (R) {
      var c = R.caminhos, out = [];
      if (c.lora_1_5b && c.zero_shot_1_5b) out.push({ cor: "var(--c-lora)", grande: "+" + fmtNum(100 * (c.lora_1_5b.acuracia - c.zero_shot_1_5b.acuracia), 0) + " points",
        texto: "Training is what makes the AI useful. The same 1.5-billion-parameter model goes from " + pct(c.zero_shot_1_5b.acuracia, 0) + " with no training to " + pct(c.lora_1_5b.acuracia, 0) + " with LoRA" + (c.zero_shot_7b_4bit && c.zero_shot_7b_4bit.acuracia ? ", and a 5x bigger model with no training reaches " + pct(c.zero_shot_7b_4bit.acuracia, 0) : "") + ". Without examples it does not know this store’s rules (what counts as a “bar” vs a “chocolate”)." });
      if (c.lora_1_5b && c.tfidf && R.lora_menos_tfidf_ic95) {
        var d = c.lora_1_5b.acuracia - c.tfidf.acuracia, ic = R.lora_menos_tfidf_ic95, vale = ic[0] > 0;
        out.push({ cor: "var(--c-classico)", grande: (vale ? "+" + fmtNum(100 * d, 1) + " points" : "A tie"),
          texto: vale ? "The tuned AI beats the classic model by " + fmtNum(100 * d, 1) + " points (range " + fmtNum(100 * ic[0], 1) + " to " + fmtNum(100 * ic[1], 1) + "), but it needs a GPU: " + fmtNum(c.lora_1_5b.ms_por_item_lote_gpu, 0) + " ms per product vs " + fmtNum(c.tfidf.ms_por_item_lote_cpu, 1) + " ms for the classic model on CPU."
                      : "The gap between the tuned AI and the classic model (" + fmtNum(100 * d, 1) + " points) is within the margin of error (" + fmtNum(100 * ic[0], 1) + " to " + fmtNum(100 * ic[1], 1) + "). With this data, the classic model, free on a CPU, does just as well." });
      }
      if (R.quando_concordam) {
        var q = R.quando_concordam;
        out.push({ cor: "var(--ok)", grande: pct(q.acuracia, 0), texto: "is the accuracy when the classic model and the tuned AI agree, which happens for " + pct(q.cobertura, 0) + " of products. In practice: auto-approve those and send only the rest to a person." });
      }
      return out;
    },
  };

  var COMO = {
    pt: function (R, d) {
      return [
        fmtInt(d.produtos_brasil_com_nome_e_categoria) + " produtos vendidos no Brasil com nome e categoria no Open Food Facts; " + fmtInt(d.depois_de_tirar_repetidos) + " depois de juntar as tags em " + d.categorias + " categorias de prateleira e tirar repetidos.",
        "Divisão por marca: treino " + fmtInt(d.treino) + ", validação " + fmtInt(d.validacao) + ", teste " + fmtInt(d.teste) + ". Nenhuma marca do teste aparece no treino, como um lojista novo cadastrando produtos.",
        "Os três caminhos treinam (quando treinam) só no treino. A configuração do clássico foi escolhida na validação; o teste foi usado uma vez, no fim.",
        "Acerto com faixa de 95% (bootstrap, 2.000 sorteios) e F1 macro (média por categoria: a categoria pequena pesa igual à grande).",
        "Por que dividir por marca: o mesmo modelo clássico parece melhor quando o teste tem marcas que ele já viu.",
      ];
    },
    en: function (R, d) {
      return [
        fmtInt(d.produtos_brasil_com_nome_e_categoria) + " products sold in Brazil with a name and category in Open Food Facts; " + fmtInt(d.depois_de_tirar_repetidos) + " after mapping tags to " + d.categorias + " shelf categories and removing duplicates.",
        "Split by brand: train " + fmtInt(d.treino) + ", validation " + fmtInt(d.validacao) + ", test " + fmtInt(d.teste) + ". No test brand appears in training, like a new store listing its products.",
        "All three approaches train (when they train) on the train set only. The classic model’s settings were picked on validation; the test set was used once, at the end.",
        "Accuracy with a 95% range (bootstrap, 2,000 resamples) and macro F1 (average over categories: small categories weigh as much as big ones).",
        "Why split by brand: the same classic model looks better when the test set has brands it has already seen.",
      ];
    },
  };

  /* ---------------- início ---------------- */
  document.querySelectorAll(".idioma button").forEach(function (b) {
    b.addEventListener("click", function () { L = b.dataset.lang; try { localStorage.setItem("cm_lang", L); } catch (e) { /* ok */ } aplicarIdioma(); });
  });
  var timer = null;
  $("q").addEventListener("input", function () { clearTimeout(timer); var v = this.value; timer = setTimeout(function () { classificar(v); }, 90); });
  $("form").addEventListener("submit", function (e) { e.preventDefault(); classificar($("q").value); });
  $("sortear").addEventListener("click", sortear);

  carregar().then(function () {
    aplicarIdioma();
    var inicial = (R.chips && R.chips[0]) || "Leite Condensado Moça 395g";
    $("q").value = inicial; classificar(inicial);
  }).catch(function (e) {
    $("res3").innerHTML = '<p class="vazio">Erro ao carregar os dados: ' + esc(e.message) + "</p>";
  });
})();
