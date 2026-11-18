#!/usr/bin/env python3
"""Genera il sito statico delle linee guida nella cartella _site/.

Uso:  python build.py
Fonti: site.json (dati del sito), chapters.json (ordine e titoli), content/*.html (testo dei capitoli).
Non servono librerie esterne.
"""
import json, re, shutil, html
from pathlib import Path

ROOT = Path(__file__).parent
OUT = ROOT / "_site"
site = json.loads((ROOT / "site.json").read_text(encoding="utf8"))
chapters = json.loads((ROOT / "chapters.json").read_text(encoding="utf8"))
esc = html.escape


def nav_html(current):
    out, group = [], None
    for c in chapters:
        if c["group"] != group:
            if group is not None:
                out.append("</ul></div>")
            group = c["group"]
            out.append(f'<div class="nav-group"><p class="nav-label">{esc(group)}</p><ul>')
        cur = ' aria-current="page"' if c["slug"] == current else ""
        num = f'<span class="nav-num">{esc(c["num"])}</span>' if c["num"] else '<span class="nav-num"></span>'
        out.append(f'<li><a href="{c["slug"]}.html"{cur}>{num}<span>{esc(c["title"])}</span></a></li>')
    out.append("</ul></div>")
    return "\n".join(out)


def toc_html(body):
    items = re.findall(r'<h2 id="([^"]+)">(.*?)</h2>', body)
    if len(items) < 2:
        return ""
    lis = "".join(f'<li><a href="#{i}">{t}</a></li>' for i, t in items)
    return f'<nav class="page-toc" aria-label="In questa pagina"><p>In questa pagina</p><ul>{lis}</ul></nav>'


def edit_links(c):
    repo = site.get("repo", "").rstrip("/")
    if not repo:
        return ""
    b = site.get("branch", "main")
    return (
        '<p class="page-actions">'
        f'<a href="{repo}/edit/{b}/content/{c["file"]}">Modifica questo capitolo su GitHub</a>'
        f'<a href="{repo}/issues/new?template=proposta-di-modifica.yml&amp;title={esc(c["title"])}">Proponi una modifica</a>'
        "</p>"
    )


def page(title, body, current, crumbs, extra_head=""):
    return f"""<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} · {esc(site["titolo"])} {esc(site["sottotitolo"])}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Titillium+Web:ital,wght@0,400;0,600;0,700;1,400&family=JetBrains+Mono:wght@400;500&display=swap">
<link rel="stylesheet" href="assets/style.css">
{extra_head}
</head>
<body>
<a class="skip" href="#contenuto">Vai al contenuto</a>
<header class="site-header">
  <div class="slim"><div class="wrap"><span>{esc(site["ente"])}</span></div></div>
  <div class="center"><div class="wrap center-in">
    <a class="brand" href="index.html"><span class="brand-name">{esc(site["titolo"])}</span><span class="brand-sub">{esc(site["sottotitolo"])} · versione {esc(site["versione"])}</span></a>
    <div class="search" role="search">
      <label for="q">Cerca nelle linee guida</label>
      <input id="q" type="search" placeholder="Per esempio: Pec, grassetto, CUP" autocomplete="off">
      <div id="results" class="results" hidden></div>
    </div>
  </div></div>
</header>
<div class="wrap layout">
  <aside class="sidebar" id="sidebar" aria-label="Capitoli">
    <button type="button" class="nav-toggle" id="nav-toggle" aria-expanded="false" aria-controls="nav">Capitoli</button>
    <nav id="nav" aria-label="Indice">
{nav_html(current)}
    </nav>
  </aside>
  <main id="contenuto" class="main">
    <nav class="crumbs" aria-label="Percorso"><ol>{crumbs}</ol></nav>
{body}
  </main>
</div>
<footer class="site-footer"><div class="wrap">{esc(site["ente"])} · {esc(site["titolo"])} {esc(site["sottotitolo"])} · versione {esc(site["versione"])}</div></footer>
<script src="assets/site.js"></script>
</body>
</html>
"""


def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "assets").mkdir(parents=True)
    for f in (ROOT / "assets").iterdir():
        shutil.copy(f, OUT / "assets" / f.name)
    (OUT / ".nojekyll").write_text("")

    index = []
    for n, c in enumerate(chapters):
        body = (ROOT / "content" / c["file"]).read_text(encoding="utf8").strip()
        text = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", body))).strip()
        index.append({"slug": c["slug"], "title": c["title"], "num": c["num"], "text": text})
        prev = chapters[n - 1] if n else None
        nxt = chapters[n + 1] if n + 1 < len(chapters) else None
        pn = ""
        if prev:
            pn += f'<a class="pn prev" href="{prev["slug"]}.html"><span>Precedente</span>{esc(prev["title"])}</a>'
        if nxt:
            pn += f'<a class="pn next" href="{nxt["slug"]}.html"><span>Successivo</span>{esc(nxt["title"])}</a>'
        article = (
            f'<article class="page">\n<header class="phead"><p class="kicker">{esc(c["kicker"])}</p><h1>{esc(c["title"])}</h1></header>\n'
            f'{toc_html(body)}\n<div class="prose">\n{body}\n</div>\n{edit_links(c)}\n<footer class="pnav">{pn}</footer>\n</article>'
        )
        crumbs = (
            '<li><a href="index.html">Home</a></li>'
            f'<li>{esc(c["group"])}</li><li aria-current="page">{esc(c["title"])}</li>'
        )
        (OUT / f'{c["slug"]}.html').write_text(page(c["title"], article, c["slug"], crumbs), encoding="utf8")

    cards, group, buf = [], None, []
    def flush():
        if group is not None:
            cards.append(f'<section class="card"><h2>{esc(group)}</h2><ul>{"".join(buf)}</ul></section>')
    for c in chapters:
        if c["group"] != group:
            flush(); group, buf = c["group"], []
        num = f'<span class="nav-num">{esc(c["num"])}</span>' if c["num"] else ""
        buf.append(f'<li><a href="{c["slug"]}.html">{num}{esc(c["title"])}</a></li>')
    flush()
    home = (
        f'<article class="page home"><header class="phead"><p class="kicker">{esc(site["ente"])}</p>'
        f'<h1>{esc(site["titolo"])} {esc(site["sottotitolo"])}</h1></header>\n'
        f'<p class="lead">{esc(site["descrizione"])}</p>\n<div class="cards">{"".join(cards)}</div></article>'
    )
    (OUT / "index.html").write_text(
        page("Home", home, "", '<li aria-current="page">Home</li>'), encoding="utf8"
    )
    (OUT / "assets" / "search-index.json").write_text(json.dumps(index, ensure_ascii=False), encoding="utf8")
    print(f"Sito generato in {OUT} ({len(chapters)} capitoli)")


if __name__ == "__main__":
    build()
