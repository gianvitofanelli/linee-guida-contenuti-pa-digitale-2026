#!/usr/bin/env python3
"""Genera il sito statico delle linee guida nella cartella _site/.

Uso:  python build.py
Fonti: site.json (dati del sito), chapters.json (ordine e titoli), content/*.html (testo dei capitoli).
Non servono librerie esterne.
"""
import json, re, shutil, html, zipfile
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).parent
OUT = ROOT / "_site"
site = json.loads((ROOT / "site.json").read_text(encoding="utf8"))
chapters = json.loads((ROOT / "chapters.json").read_text(encoding="utf8"))
esc = html.escape
export = json.loads((ROOT / "esportazioni.json").read_text(encoding="utf8"))


# ---- Esportazione in Markdown (HTML dei capitoli -> .md) ----
VOID = {"br", "hr", "img", "meta", "link", "input"}


class Node:
    def __init__(self, tag, attrs=None):
        self.tag, self.attrs, self.kids = tag, dict(attrs or []), []


class Tree(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("root")
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        n = Node(tag, attrs)
        self.stack[-1].kids.append(n)
        if tag not in VOID:
            self.stack.append(n)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        self.stack[-1].kids.append(data)


def inline(node, table=False):
    out = ""
    for k in node.kids:
        if isinstance(k, str):
            out += re.sub(r"\s+", " ", k)
            continue
        t, inner = k.tag, inline(k, table)
        if t in ("strong", "b"):
            out += f"**{inner.strip()}**" if inner.strip() else ""
        elif t in ("em", "i"):
            out += f"*{inner.strip()}*" if inner.strip() else ""
        elif t == "code":
            out += f"`{inner}`"
        elif t == "a":
            out += f"[{inner.strip()}]({k.attrs.get('href', '')})"
        elif t == "span" and "btn" in k.attrs.get("class", ""):
            out += f"[{inner.strip()}]"
        elif t == "br":
            out += " " if table else "  \n"
        elif t in ("ul", "ol", "p"):
            out += " " + inner + " "
        else:
            out += inner
    return out.replace("|", "\\|") if table else out


def list_md(node, depth=0):
    lines, n = [], 0
    for li in [k for k in node.kids if not isinstance(k, str) and k.tag == "li"]:
        n += 1
        mark = f"{n}." if node.tag == "ol" else "-"
        pad = "  " * depth
        text, subs = "", []
        for k in li.kids:
            if not isinstance(k, str) and k.tag in ("ul", "ol"):
                subs.append(k)
            elif not isinstance(k, str) and k.tag == "p":
                text += inline(k).strip() + " "
            else:
                text += re.sub(r"\s+", " ", k) if isinstance(k, str) else inline(Wrap(k))
        lines.append(f"{pad}{mark} {text.strip()}")
        for sub in subs:
            lines.extend(list_md(sub, depth + 1))
    return lines


class Wrap(Node):
    def __init__(self, child):
        super().__init__("x")
        self.kids = [child]


def table_md(node):
    rows = []
    def collect(n):
        for k in n.kids:
            if isinstance(k, str):
                continue
            if k.tag == "tr":
                rows.append([inline(c, True).strip() for c in k.kids if not isinstance(c, str) and c.tag in ("th", "td")])
            else:
                collect(k)
    collect(node)
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    out = ["| " + " | ".join(rows[0]) + " |", "| " + " | ".join("---" for _ in range(width)) + " |"]
    out += ["| " + " | ".join(r) + " |" for r in rows[1:]]
    return "\n".join(out)


def blocks(node):
    out = []
    for k in node.kids:
        if isinstance(k, str):
            if k.strip():
                out.append(re.sub(r"\s+", " ", k).strip())
            continue
        t = k.tag
        if t == "p":
            out.append(inline(k).strip())
        elif t in ("h2", "h3", "h4"):
            out.append("#" * int(t[1]) + " " + inline(k).strip())
        elif t in ("ul", "ol"):
            out.append("\n".join(list_md(k)))
        elif t == "table":
            out.append(table_md(k))
        elif t == "pre":
            txt = "".join(x if isinstance(x, str) else inline(x) for x in k.kids)
            out.append("```\n" + txt.strip("\n") + "\n```")
        elif t == "blockquote":
            inner = "\n\n".join(b for b in blocks(k) if b)
            out.append("\n".join(("> " + l).rstrip() for l in inner.split("\n")))
        else:
            out.extend(blocks(k))
    return [b for b in out if b]


def to_md(fragment):
    tree = Tree()
    tree.feed(fragment)
    return "\n\n".join(blocks(tree.root)) + "\n"


def chapter_md(c, body):
    m = re.match(r"(Capitolo|Appendice) (\w+)", c["kicker"])
    head = f"{m.group(2)}. {c['title']}" if m and m.group(1) == "Capitolo" else (
        f"Appendice {m.group(2)}. {c['title']}" if m else c["title"])
    return f"# {head}\n\n" + to_md(body)


def kb(n):
    return f"{max(1, round(n / 1024))} kB"


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
    body = re.sub(r"<th>", '<th scope="col">', body)
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
    <div class="header-tools">
      <button type="button" class="tool-btn" id="search-toggle" aria-expanded="false" aria-controls="search-box"><svg aria-hidden="true" focusable="false" viewBox="0 0 24 24" width="20" height="20"><path fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" d="M10.5 18a7.5 7.5 0 1 1 0-15 7.5 7.5 0 0 1 0 15zm5.5-2 5 5"/></svg><span>Cerca</span></button>
      <button type="button" class="tool-btn" id="nav-toggle" aria-expanded="false" aria-controls="nav"><svg aria-hidden="true" focusable="false" viewBox="0 0 24 24" width="20" height="20"><path fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" d="M4 6h16M4 12h16M4 18h16"/></svg><span>Capitoli</span></button>
    </div>
    <div class="search" role="search" id="search-box">
      <label for="q">Cerca nelle linee guida</label>
      <input id="q" type="search" placeholder="Per esempio: Pec, grassetto, CUP" autocomplete="off" aria-controls="results" aria-describedby="q-status">
      <div id="results" class="results" hidden></div>
      <p id="q-status" class="sr" role="status" aria-live="polite"></p>
    </div>
  </div></div>
</header>
<div class="wrap layout">
  <div class="nav-backdrop" id="nav-backdrop" hidden></div>
  <aside class="sidebar" id="sidebar">
    <nav id="nav" aria-label="Capitoli">
      <div class="nav-head"><span>Capitoli</span><button type="button" class="tool-btn tool-close" id="nav-close"><svg aria-hidden="true" focusable="false" viewBox="0 0 24 24" width="20" height="20"><path fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" d="M5 5l14 14M19 5L5 19"/></svg><span>Chiudi</span></button></div>
{nav_html(current)}
    </nav>
  </aside>
  <main id="contenuto" class="main" tabindex="-1">
    <nav class="crumbs" aria-label="Percorso"><ol>{crumbs}</ol></nav>
{body}
  </main>
</div>
<footer class="site-footer"><div class="wrap">{esc(site["ente"])} · {esc(site["titolo"])} {esc(site["sottotitolo"])} · versione {esc(site["versione"])}</div></footer>
<button type="button" class="back-to-top" id="back-to-top" aria-label="Torna all’inizio della pagina"><svg aria-hidden="true" focusable="false" viewBox="0 0 24 24" width="24" height="24"><path fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" d="M5 15l7-7 7 7"/></svg></button>
<script src="assets/site.js"></script>
</body>
</html>
"""


def write_exports(bodies):
    """Scrive i file .md e lo zip in _site/download/ e restituisce la tabella dei download."""
    dl = OUT / "download"
    dl.mkdir()
    by_slug = {c["slug"]: c for c in chapters}
    md = {slug: chapter_md(by_slug[slug], bodies[slug]) for slug in bodies if slug != "intelligenza-artificiale"}
    files = {}
    for f in export["file"]:
        text = ""
        if f.get("intro"):
            text += "# Linee guida di content design – PA digitale 2026\n\n" + f["intro"] + "\n\n"
        text += "\n".join(md[s] for s in f["capitoli"])
        files[f["file"]] = text
    comp = export["completo"]
    files[comp["file"]] = (
        f"# {comp['titolo']} (versione {site['versione']})\n\n"
        + "\n".join(md[c["slug"]] for c in chapters if c["slug"] in md and c["slug"] != "fonti")
    )
    for name, text in files.items():
        (dl / name).write_text(text, encoding="utf8")
    with zipfile.ZipFile(dl / export["zip"], "w", zipfile.ZIP_DEFLATED) as z:
        for name in files:
            z.write(dl / name, name)

    def row(name, desc):
        size = kb((dl / name).stat().st_size)
        return (
            f'<tr><td><code>{esc(name)}</code></td><td>{esc(desc)}</td>'
            f'<td><a class="dl" href="download/{esc(name)}" download>Scarica<span class="sr"> {esc(name)}</span> (MD, {size})</a></td></tr>'
        )

    rows = "".join(row(f["file"], f["descrizione"]) for f in export["file"])
    rows += row(comp["file"], comp["descrizione"])
    zrow = (
        f'<p><a class="dl dl-main" href="download/{esc(export["zip"])}" download>Scarica tutti i file '
        f'(ZIP, {kb((dl / export["zip"]).stat().st_size)})</a></p>'
    )
    return (
        zrow + '<div class="tbl"><table class="plain"><thead><tr><th>File</th><th>Contenuto</th><th>Download</th></tr></thead>'
        f"<tbody>{rows}</tbody></table></div>"
    )


def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "assets").mkdir(parents=True)
    for f in (ROOT / "assets").iterdir():
        shutil.copy(f, OUT / "assets" / f.name)
    (OUT / ".nojekyll").write_text("")

    bodies = {c["slug"]: (ROOT / "content" / c["file"]).read_text(encoding="utf8").strip() for c in chapters}
    download_html = write_exports(bodies)

    index = []
    for n, c in enumerate(chapters):
        body = bodies[c["slug"]].replace("{{DOWNLOAD}}", download_html)
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
