/* Classificador clássico (TF-IDF + regressão logística) rodando no navegador.
   Mesma conta de src/catalogo/web_modelo.py; tests/test_web.py confere as duas. */
(function (raiz) {
  "use strict";

  function norm(s) {
    s = String(s || "").normalize("NFKD").replace(/[^\x00-\x7f]/g, "").toLowerCase();
    s = s.replace(/[^a-z0-9]+/g, " ");
    s = s.replace(/([0-9])(?=[a-z])/g, "$1 ").replace(/([a-z])(?=[0-9])/g, "$1 ");
    return s.split(/\s+/).filter(Boolean).join(" ");
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
    var iw = new Map(), ic = new Map();
    m.palavras.forEach(function (k, i) { iw.set(k, i); });
    m.pedacos.forEach(function (k, i) { ic.set(k, i); });
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

    function bloco(grams, idx, idf, desloc, x) {
      var cont = new Map();
      grams.forEach(function (g) { if (idx.has(g)) cont.set(g, (cont.get(g) || 0) + 1); });
      if (!cont.size) return;
      var v = [], soma = 0;
      cont.forEach(function (c, g) {
        var i = idx.get(g), val = (1 + Math.log(c)) * idf[i];
        v.push([desloc + i, val]); soma += val * val;
      });
      var nr = Math.sqrt(soma);
      v.forEach(function (p) { x.push([p[0], p[1] / nr]); });
    }

    function proba(texto) {
      var t = norm(texto), x = [];
      bloco(ngramasPalavras(t), iw, m.idf_palavras, 0, x);
      bloco(ngramasPedacos(t), ic, m.idf_pedacos, nw, x);
      var z = new Float64Array(K);
      for (var c = 0; c < K; c++) {
        var s = m.intercepto[c], base = c * n;
        for (var q = 0; q < x.length; q++) s += W[base + x[q][0]] * x[q][1];
        z[c] = s;
      }
      var mx = -Infinity;
      for (c = 0; c < K; c++) if (z[c] > mx) mx = z[c];
      var tot = 0;
      for (c = 0; c < K; c++) { z[c] = Math.exp(z[c] - mx); tot += z[c]; }
      for (c = 0; c < K; c++) z[c] /= tot;
      return { p: z, conhecidos: x.length };
    }

    function prever(texto, k) {
      var r = proba(texto), ordem = [];
      for (var c = 0; c < K; c++) ordem.push(c);
      ordem.sort(function (a, b) { return r.p[b] - r.p[a]; });
      return { top: ordem.slice(0, k || 3).map(function (c) {
        return { chave: m.classes[c], nome: m.nomes[c], p: r.p[c] };
      }), conhecidos: r.conhecidos };
    }

    return { prever: prever, proba: proba, classes: m.classes, nomes: m.nomes };
  }

  var api = { norm: norm, criar: criar, ngramasPedacos: ngramasPedacos };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else raiz.Classificador = api;
})(typeof self !== "undefined" ? self : this);
