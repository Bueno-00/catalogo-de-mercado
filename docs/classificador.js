/* Classificador clássico rodando no navegador: TF-IDF (palavras + pedaços) + faixa da quantidade + modelo linear.
   Mesma conta de src/catalogo/web_modelo.py e src/catalogo/quantidade.py; tests/test_catalogo.py confere. */
(function (raiz) {
  "use strict";

  function norm(s) {
    s = String(s || "").normalize("NFKD").replace(/[^\x00-\x7f]/g, "").toLowerCase();
    s = s.replace(/[^a-z0-9]+/g, " ");
    s = s.replace(/([0-9])(?=[a-z])/g, "$1 ").replace(/([a-z])(?=[0-9])/g, "$1 ");
    return s.split(/\s+/).filter(Boolean).join(" ");
  }

  /* ---- quantidade: igual a src/catalogo/quantidade.py (ler + faixa_tokens) ---- */
  var UNIDADE = "kg|kgs|kilos?|quilos?|g|gr|grs|grama|gramas|mg|ml|mls|cl|l|lt|lts|litro|litros|oz" +
    "|un|und|unds|unid|unids|unidade|unidades|uni|cap|caps|capsula|capsulas|sache|saches|sachet|sachets";
  var MASSA = { kg: 1000, kgs: 1000, kilo: 1000, kilos: 1000, quilo: 1000, quilos: 1000, g: 1, gr: 1, grs: 1, grama: 1, gramas: 1, mg: 0.001, oz: 28.35 };
  var VOLUME = { ml: 1, mls: 1, cl: 10, l: 1000, lt: 1000, lts: 1000, litro: 1000, litros: 1000 };
  var FAIXAS = { massa: [20, 45, 90, 180, 350, 700, 1500], volume: [250, 400, 700, 1200, 2200], unid: [1, 6, 20] };
  var LETRA = { massa: "m", volume: "v", unid: "u" };

  function numero(txt, unidade) {
    if (/^\d+[.,]\d{3}$/.test(txt) && txt[0] !== "0" && ["g", "gr", "grs", "ml", "mg"].indexOf(unidade) >= 0) return parseFloat(txt.replace(/[.,]/g, ""));
    return parseFloat(txt.replace(/,/g, "."));
  }

  function lerQuantidade(texto) {
    var s = String(texto || "").normalize("NFKD").replace(/[^\x00-\x7f]/g, "").toLowerCase();
    var re = new RegExp("(?:(\\d{1,3})\\s*x\\s*)?(\\d+(?:[.,]\\d+)?)\\s*(" + UNIDADE + ")(?![a-z])", "g"), m, ult = null;
    while ((m = re.exec(s)) !== null) ult = m;
    if (!ult) return { tipo: "nenhum", valor: 0, faixa: -1 };
    var un = ult[3], v = numero(ult[2], un), tipo;
    if (MASSA[un] != null) { tipo = "massa"; v *= MASSA[un]; }
    else if (VOLUME[un] != null) { tipo = "volume"; v *= VOLUME[un]; }
    else tipo = "unid";
    var f = 0;
    FAIXAS[tipo].forEach(function (lim) { if (v > lim) f++; });
    return { tipo: tipo, valor: v, faixa: f };
  }

  function faixaTokens(texto) {
    var q = lerQuantidade(texto);
    if (q.tipo === "nenhum") return ["qt_nada"];
    var t = LETRA[q.tipo];
    return ["qt_" + t, "qf_" + t + q.faixa];
  }

  function ngramasPalavras(t) {
    var toks = t ? t.split(" ") : [], out = toks.slice();
    for (var i = 0; i + 1 < toks.length; i++) out.push(toks[i] + " " + toks[i + 1]);
    return out;
  }

  function ngramasPedacos(t) {
    var out = [];
    if (!t) return out;
    t.split(" ").forEach(function (w) {
      w = " " + w + " ";
      for (var n = 3; n <= 5; n++) {
        var off = 0;
        out.push(w.slice(off, off + n));
        while (off + n < w.length) { off++; out.push(w.slice(off, off + n)); }
        if (off === 0) break;
      }
    });
    return out;
  }

  function criar(m) {
    var iw = new Map(), ic = new Map(), iq = new Map();
    m.palavras.forEach(function (k, i) { iw.set(k, i); });
    m.pedacos.forEach(function (k, i) { ic.set(k, i); });
    (m.quantidade || []).forEach(function (k, i) { iq.set(k, i); });
    var pesoQ = m.peso_quantidade || 0, T = m.temperatura || 1;
    var bin = atob(m.pesos_int8_b64), n = m.n_atributos, K = m.classes.length;
    var W = new Float32Array(K * n);
    for (var c = 0; c < K; c++) {
      var esc = m.escala[c];
      for (var j = 0; j < n; j++) {
        var b = bin.charCodeAt(c * n + j);
        W[c * n + j] = (b > 127 ? b - 256 : b) * esc;
      }
    }
    var nw = m.palavras.length;

    function bloco(grams, idx, idf, desloc, x, peso) {
      var cont = new Map();
      grams.forEach(function (g) { if (idx.has(g)) cont.set(g, (cont.get(g) || 0) + 1); });
      if (!cont.size) return;
      var v = [], soma = 0;
      cont.forEach(function (c, g) {
        var i = idx.get(g), val = (1 + Math.log(c)) * idf[i];
        v.push([desloc + i, val]); soma += val * val;
      });
      var nr = Math.sqrt(soma);
      v.forEach(function (p) { x.push([p[0], (peso == null ? 1 : peso) * p[1] / nr]); });
    }

    function proba(texto) {
      var t = norm(texto), x = [];
      bloco(ngramasPalavras(t), iw, m.idf_palavras, 0, x);
      bloco(ngramasPedacos(t), ic, m.idf_pedacos, nw, x);
      var nTexto = x.length, qtd = null;
      if (pesoQ) { qtd = lerQuantidade(texto); bloco(faixaTokens(texto), iq, m.idf_quantidade, nw + m.pedacos.length, x, pesoQ); }
      var z = new Float64Array(K);
      for (var c = 0; c < K; c++) {
        var s = m.intercepto[c], base = c * n;
        for (var q = 0; q < x.length; q++) s += W[base + x[q][0]] * x[q][1];
        z[c] = T * s;
      }
      var mx = -Infinity;
      for (c = 0; c < K; c++) if (z[c] > mx) mx = z[c];
      var tot = 0;
      for (c = 0; c < K; c++) { z[c] = Math.exp(z[c] - mx); tot += z[c]; }
      for (c = 0; c < K; c++) z[c] /= tot;
      return { p: z, conhecidos: nTexto, quantidade: qtd };
    }

    function prever(texto, k) {
      var r = proba(texto), ordem = [];
      for (var c = 0; c < K; c++) ordem.push(c);
      ordem.sort(function (a, b) { return r.p[b] - r.p[a]; });
      return { top: ordem.slice(0, k || 3).map(function (c) {
        return { chave: m.classes[c], nome: m.nomes[c], p: r.p[c] };
      }), conhecidos: r.conhecidos, quantidade: r.quantidade };
    }

    return { prever: prever, proba: proba, classes: m.classes, nomes: m.nomes, temQuantidade: !!pesoQ };
  }

  var api = { norm: norm, criar: criar, ngramasPedacos: ngramasPedacos, lerQuantidade: lerQuantidade, faixaTokens: faixaTokens };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else raiz.Classificador = api;
})(typeof self !== "undefined" ? self : this);
