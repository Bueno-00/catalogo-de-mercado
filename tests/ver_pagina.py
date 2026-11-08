"""Abre a página (docs/) num servidor local e tira prints em 1440 px e 390 px; confere rolagem lateral e erros.

Uso: python3 tests/ver_pagina.py <pasta-de-saida> [--en]
"""
import http.server
import socketserver
import sys
import threading
from functools import partial
from pathlib import Path

from playwright.sync_api import sync_playwright

DOCS = Path(__file__).resolve().parents[1] / "docs"
saida = Path(sys.argv[1]); saida.mkdir(parents=True, exist_ok=True)
lang = "en" if "--en" in sys.argv else "pt"

H = partial(http.server.SimpleHTTPRequestHandler, directory=str(DOCS))
H.log_message = lambda *a, **k: None
srv = socketserver.TCPServer(("127.0.0.1", 0), H)
porta = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
url = f"http://127.0.0.1:{porta}/" + ("?lang=en" if lang == "en" else "")
problemas = []
with sync_playwright() as p:
    import glob
    import os

    cand = sorted(glob.glob(os.path.expanduser("~/.cache/ms-playwright/chromium-*/chrome-linux*/chrome")))
    nav = p.chromium.launch(executable_path=os.environ.get("CHROMIUM_PATH") or (cand[-1] if cand else None))
    for nome, w, h in (("pc", 1440, 900), ("cel", 390, 844)):
        for tema in ("light", "dark"):
            pg = nav.new_page(viewport={"width": w, "height": h}, color_scheme=tema, device_scale_factor=1)
            erros = []
            pg.on("console", lambda m, erros=erros: erros.append(m.text) if m.type == "error" else None)
            pg.on("pageerror", lambda e, erros=erros: erros.append(str(e)))
            pg.goto(url, wait_until="networkidle")
            pg.wait_for_selector(".res .barras", timeout=15000)
            larg = pg.evaluate("document.documentElement.scrollWidth")
            if larg > w:
                problemas.append(f"{nome}/{tema}: rolagem lateral ({larg} > {w})")
            if erros:
                problemas.append(f"{nome}/{tema}: erros {erros}")
            if tema == "light":
                pg.screenshot(path=str(saida / f"{lang}-{nome}-topo.png"))
                pg.screenshot(path=str(saida / f"{lang}-{nome}-inteira.png"), full_page=True)
                # digita um produto que não está no teste e um que está
                pg.fill("#q", "Biscoito recheado chocolate 140g")
                pg.wait_for_timeout(400)
                pg.locator("#experimente").screenshot(path=str(saida / f"{lang}-{nome}-livre.png"))
                pg.select_option("#filtro", "ia_erra")
                pg.click("#sortear"); pg.wait_for_timeout(400)
                pg.locator("#experimente").screenshot(path=str(saida / f"{lang}-{nome}-sorteado.png"))
            else:
                pg.screenshot(path=str(saida / f"{lang}-{nome}-escuro.png"), full_page=True)
            pg.close()
    nav.close()
srv.shutdown()
print("problemas:", problemas or "nenhum")
