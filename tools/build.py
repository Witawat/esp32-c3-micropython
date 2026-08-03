#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build.py — สร้างเว็บ static HTML (แยกทุกหน้า) จาก docs/*.md

วิธีใช้:
    python tools/build.py              # สร้างเว็บทั้งหมด
    python tools/build.py wifi mqtt    # สร้างเฉพาะหน้าที่ระบุ (ชื่อ md โดยไม่มี .md)
"""

import os
import re
import sys
import html as _html
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
WEB = ROOT / "web"

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

SITE_NAME = "ESP32 MicroPython Tutorial"
SITE_TAGLINE = "คู่มือใช้งาน lib ครบทุกหมวด — การต่อวงจร แนวคิด และ API"

# ---------------------------------------------------------------- categories
# (cat_key, title, sub_link) — sub_link ใช้สำหรับหมวดที่รวมเป็นหน้าเดียว
CATEGORY_ORDER = [
    ("start",   "🚀 เริ่มต้นใช้งาน",      None),
    ("network", "🌐 Network & Communication", None),
    ("cloud",   "☁️ Cloud Platforms",      None),
    ("sensors", "🌡️ Sensors",             None),
    ("display", "🖥️ Display",             None),
    ("output",  "⚙️ Output / Actuator",    None),
    ("input",   "🎮 Input",               None),
    ("p10",     "📺 P10 LED Panel",        None),
    ("audio",   "🎵 Audio",               None),
    ("ioexp",   "🔌 I/O Expander",         None),
    ("io",      "🔧 I/O Abstraction",      None),
    ("storage", "💾 Storage",             None),
    ("system",  "🔋 System Utilities",     None),
    ("security", "🔐 Security",            None),
    ("crypto",  "🔑 Crypto",              None),
    ("repl",    "🛠️ REPL",               None),
]

CAT_TITLE = {k: t for k, t, _ in CATEGORY_ORDER}


# ---------------------------------------------------------------- markdown
def _inline(text):
    """แปลง inline markdown: code, bold, italic, link"""
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    return text


def md_to_html(src, from_web=None, page_map=None):
    """แปลง Markdown เป็น HTML (รองรับ heading, table, code, list, quote, hr)"""
    lines = src.split("\n")
    i, n = 0, len(lines)
    out = []
    in_code = False
    code_buf = []
    code_lang = ""
    pfx = {"from_web": from_web, "page_map": page_map or {}}

    def fix_links(html_text):
        if not pfx["page_map"] or pfx["from_web"] is None:
            return html_text

        def rep(m):
            name = m.group(1)
            target = pfx["page_map"].get(name)
            if target is None:
                return "@" + name
            rel = os.path.relpath(str(target), str(pfx["from_web"].parent))
            return rel.replace("\\", "/")

        return re.sub(r'href="@([a-zA-Z0-9_-]+)"', lambda m: 'href="' + rep(m) + '"', html_text)

    while i < n:
        line = lines[i]

        # --- code block
        if line.startswith("```"):
            if not in_code:
                in_code = True
                code_lang = line[3:].strip() or "python"
                code_buf = []
            else:
                in_code = False
                body = _html.escape("\n".join(code_buf))
                lang = _html.escape(code_lang)
                out.append(
                    '<div class="code-block">'
                    f'<div class="code-head"><span>{lang}</span>'
                    '<button class="copy-btn" type="button" onclick="copyCode(this)">คัดลอก</button></div>'
                    f'<pre><code class="lang-{lang}">{body}</code></pre></div>'
                )
            i += 1
            continue
        if in_code:
            code_buf.append(line)
            i += 1
            continue

        if not line.strip():
            i += 1
            continue

        # --- heading
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            lvl = len(m.group(1))
            out.append(f"<h{lvl}>{fix_links(_inline(m.group(2)))}</h{lvl}>")
            i += 1
            continue

        # --- table
        if line.lstrip().startswith("|") and i + 1 < n and re.match(r"^\s*\|[\s\-|:]+\|?\s*$", lines[i + 1]):
            header = [_inline(c.strip()) for c in line.strip().strip("|").split("|")]
            i += 2
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                rows.append([_inline(c.strip()) for c in lines[i].strip().strip("|").split("|")])
                i += 1
            th = "".join(f"<th>{c}</th>" for c in header)
            trs = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
            out.append(f'<div class="table-wrap"><table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table></div>')
            continue

        # --- horizontal rule
        if re.match(r"^\s*---+\s*$", line):
            out.append("<hr>")
            i += 1
            continue

        # --- blockquote
        if line.startswith(">"):
            buf = []
            while i < n and lines[i].startswith(">"):
                buf.append(lines[i][1:].strip())
                i += 1
            body = "<br>".join(_inline(b) for b in buf)
            out.append(f"<blockquote>{fix_links(body)}</blockquote>")
            continue

        # --- unordered list
        if re.match(r"^\s*[-*]\s+", line):
            items = []
            while i < n and re.match(r"^\s*[-*]\s+", lines[i]):
                items.append(_inline(re.sub(r"^\s*[-*]\s+", "", lines[i])))
                i += 1
            out.append("<ul>" + "".join(f"<li>{it}</li>" for it in items) + "</ul>")
            continue

        # --- ordered list
        if re.match(r"^\s*\d+\.\s+", line):
            items = []
            while i < n and re.match(r"^\s*\d+\.\s+", lines[i]):
                items.append(_inline(re.sub(r"^\s*\d+\.\s+", "", lines[i])))
                i += 1
            out.append("<ol>" + "".join(f"<li>{it}</li>" for it in items) + "</ol>")
            continue

        # --- paragraph (merge consecutive text lines)
        buf = [line.strip()]
        i += 1
        while (
            i < n
            and lines[i].strip()
            and not lines[i].startswith("#")
            and not lines[i].lstrip().startswith("|")
            and not lines[i].startswith("```")
            and not lines[i].startswith(">")
            and not re.match(r"^\s*[-*]\s+", lines[i])
            and not re.match(r"^\s*\d+\.\s+", lines[i])
            and not re.match(r"^\s*---+\s*$", lines[i])
        ):
            buf.append(lines[i].strip())
            i += 1
        out.append(f"<p>{fix_links(_inline(' '.join(buf)))}</p>")

    return "\n".join(out)


# ---------------------------------------------------------------- front matter
def parse_frontmatter(src):
    meta = {}
    body = src
    if src.startswith("---\n"):
        end = src.find("\n---", 4)
        if end != -1:
            for line in src[4:end].split("\n"):
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip()] = v.strip().strip('"').strip("'")
            body = src[end + 4:].lstrip("\n")
    return meta, body


# ---------------------------------------------------------------- pages
def web_path_for(md_path):
    """map ไฟล์ md → ตำแหน่งเว็บ"""
    rel = md_path.relative_to(DOCS)
    name = rel.stem
    if name == "README":
        return Path("index.html")
    if rel.parent == Path("."):
        base = re.sub(r"^\d+-", "", name)
        return Path(base + ".html")
    folder = re.sub(r"^\d+-", "", rel.parent.name)
    return Path(folder) / (name + ".html")


def collect_pages():
    pages = []
    for md in sorted(DOCS.rglob("*.md")):
        rel = md.relative_to(DOCS)
        meta, body = parse_frontmatter(md.read_text(encoding="utf-8"))
        if "title" not in meta:
            print(f"  ! ข้าม {rel}: ไม่มี title ใน front matter")
            continue
        is_index = rel.parent == Path(".") and rel.name == "README.md"
        name = "index" if is_index else re.sub(r"^\d+-", "", rel.stem)
        pages.append({
            "name": name,
            "title": meta["title"],
            "desc": meta.get("desc", ""),
            "icon": meta.get("icon", ""),
            "cat": meta.get("cat", "misc"),
            "order": int(meta.get("order", 99)),
            "type": meta.get("type", "page"),
            "keywords": meta.get("keywords", ""),
            "md": md,
            "web": WEB / web_path_for(md),
            "body": body,
        })
    pages.sort(key=lambda p: (p["order"], p["title"]))
    return pages


# ---------------------------------------------------------------- links
def rel_link(from_web, to_web):
    if to_web is None:
        return "#"
    return os.path.relpath(str(to_web), str(from_web.parent)).replace("\\", "/")


def root_prefix(from_web):
    rel = os.path.relpath(str(WEB), str(from_web.parent)).replace("\\", "/")
    return "" if rel == "." else rel + "/"


# ---------------------------------------------------------------- sidebar
def build_sidebar(from_web, pages):
    by_cat = {}
    for p in pages:
        by_cat.setdefault(p["cat"], []).append(p)

    items = []
    for cat_key, cat_title, _sub in CATEGORY_ORDER:
        cat_pages = by_cat.get(cat_key, [])
        if not cat_pages:
            continue
        items.append(f'<p class="nav-head">{_html.escape(cat_title)}</p>')
        for p in cat_pages:
            href = rel_link(from_web, p["web"])
            cls = "nav-link active" if p["web"] == from_web else "nav-link"
            label = _html.escape(p["icon"] + " " + p["title"])
            items.append(f'<a class="{cls}" href="{href}">{label}</a>')
    return "\n".join(items)


def build_cards(from_web, pages):
    by_cat = {}
    for p in pages:
        by_cat.setdefault(p["cat"], []).append(p)
    cards = []
    for cat_key, cat_title, _sub in CATEGORY_ORDER:
        cat_pages = by_cat.get(cat_key, [])
        if not cat_pages:
            continue
        first = cat_pages[0]
        icon = first["icon"] or "📦"
        href = rel_link(from_web, first["web"])
        count = f"{len(cat_pages)} หน้า" if len(cat_pages) > 1 else "1 หน้า"
        cards.append(
            f'<a class="card" href="{href}">'
            f'<div class="card-icon">{_html.escape(icon)}</div>'
            f'<div class="card-body"><h3>{_html.escape(cat_title)}</h3>'
            f'<p>{_html.escape(first["desc"])}</p>'
            f'<span class="card-meta">{count}</span></div></a>'
        )
    return "\n".join(cards)


# ---------------------------------------------------------------- templates
PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__ — ESP32 MicroPython Tutorial</title>
<meta name="description" content="__DESC__">
<link rel="stylesheet" href="__PREFIX__assets/css/style.css">
</head>
<body>
<a class="skip-link" href="#main">ข้ามไปเนื้อหา</a>
<header class="site-header">
  <div class="container header-inner">
    <a class="brand" href="__PREFIX__index.html">
      <span class="brand-logo">⚡</span>
      <span class="brand-text">
        <span class="brand-title">ESP32 MicroPython Tutorial</span>
        <span class="brand-sub">คู่มือใช้งาน lib แบบละเอียด</span>
      </span>
    </a>
    <div class="header-actions">
      <div class="search-box">
        <input id="site-search" type="search" placeholder="ค้นหาหมวด / คลาส / API…" autocomplete="off">
        <ul id="search-results" class="search-results" hidden></ul>
      </div>
      <button id="theme-toggle" class="theme-toggle" type="button" title="สลับธีม">🌙</button>
      <button id="nav-toggle" class="nav-toggle" type="button" aria-label="เมนู">☰</button>
    </div>
  </div>
</header>
<div class="layout container">
  <aside class="sidebar" id="sidebar">
    <nav class="side-nav">__SIDEBAR__</nav>
  </aside>
  <main class="content" id="main">
    <nav class="breadcrumb">__BREADCRUMB__</nav>
    <article class="prose">__CONTENT__</article>
    <footer class="page-footer">
      <p>อัปเดตตามโค้ดจริงใน <code>src/lib</code> — หากพบข้อมูลไม่ตรง กรุณาแจ้งได้ที่ Issue</p>
    </footer>
  </main>
</div>
<footer class="site-footer">
  <div class="container">
    <p>__FOOTER__</p>
  </div>
</footer>
<script>window.ROOT_PREFIX = "__PREFIX__";</script>
<script src="__PREFIX__assets/js/search-index.js"></script>
<script src="__PREFIX__assets/js/main.js"></script>
</body>
</html>
"""


# ---------------------------------------------------------------- render
def render_page(page, pages, is_index=False):
    from_web = page["web"]
    prefix = root_prefix(from_web)
    page_map = {p["name"]: p["web"] for p in pages}
    page_map["index"] = WEB / Path("index.html")

    content = md_to_html(page["body"], from_web=from_web, page_map=page_map)

    if is_index:
        hero = (
            '<section class="hero">'
            '<h1>⚡ ESP32 MicroPython Framework</h1>'
            f'<p>{SITE_TAGLINE}</p>'
            f'<p class="hero-sub">95+ โมดูล · 29 หมวดหมู่ · ใช้ร่วมกับตัวอย่างโค้ดจริงจาก <code>src/lib</code></p>'
            '</section>'
        )
        cards = build_cards(from_web, pages)
        content = hero + content + '<section class="category-grid">' + cards + "</section>"

    # breadcrumb
    if is_index:
        breadcrumb = '<a href="index.html">หน้าแรก</a>'
    else:
        cat_title = CAT_TITLE.get(page["cat"], "เอกสาร")
        breadcrumb = (
            f'<a href="{rel_link(from_web, page_map["index"])}">หน้าแรก</a>'
            f'<span>/</span><span>{_html.escape(cat_title)}</span>'
            f'<span>/</span><span>{_html.escape(page["title"])}</span>'
        )

    footer = f"{SITE_NAME} — สร้างจากโค้ดจริงใน <code>src/lib</code>"

    html = (
        PAGE_TEMPLATE
        .replace("__TITLE__", _html.escape(page["title"]))
        .replace("__DESC__", _html.escape(page["desc"]))
        .replace("__PREFIX__", prefix)
        .replace("__SIDEBAR__", build_sidebar(from_web, pages))
        .replace("__BREADCRUMB__", breadcrumb)
        .replace("__CONTENT__", content)
        .replace("__FOOTER__", footer)
    )
    return html


def build_search_index(pages):
    entries = []
    for p in pages:
        rel_web = p["web"].relative_to(WEB)
        entries.append({
            "t": p["title"],
            "h": str(rel_web).replace("\\", "/"),
            "c": CAT_TITLE.get(p["cat"], ""),
            "k": (p["keywords"] + " " + p["desc"]).strip(),
        })
    return "const SEARCH_INDEX = " + _html.escape(
        __import__("json").dumps(entries, ensure_ascii=False)
    ) + ";"


# ---------------------------------------------------------------- main
def main():
    only = {a.lower() for a in sys.argv[1:]}
    print("→ อ่าน docs จาก:", DOCS)
    pages = collect_pages()
    print(f"→ พบ {len(pages)} หน้า")

    # search index
    (WEB / "assets" / "js").mkdir(parents=True, exist_ok=True)
    (WEB / "assets" / "js" / "search-index.js").write_text(
        build_search_index(pages), encoding="utf-8"
    )
    print("→ สร้าง assets/js/search-index.js")

    built = 0
    for page in pages:
        name = page["name"]
        if only and name not in only and not any(o in name for o in only):
            continue
        is_index = page["type"] == "index"
        html = render_page(page, pages, is_index=is_index)
        out_path = WEB / page["web"]
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(html, encoding="utf-8")
        print(f"  ✓ {out_path.relative_to(WEB)}")
        built += 1

    print(f"→ สร้างเสร็จ {built} หน้า ที่ {WEB}")
    if not built:
        sys.exit(1)


if __name__ == "__main__":
    main()
