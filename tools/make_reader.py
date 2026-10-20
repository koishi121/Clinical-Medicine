#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_reader.py — 生成全库「离线阅读器」索引.html
单文件内嵌所有 Markdown 内容:点击条目 = 页内切换阅读(零文件跳转),
因此即使在 VS Code 内置简易浏览器(file+vscode-resource 虚拟协议)
里也不会出现本地文件跳转 404。同时兼容 Chrome/Edge 双击打开。

用法: python make_reader.py [<根目录>]      (默认 d:\\Clinical Medicine)
重跑即覆盖索引.html,内容更新后重跑一次保持最新。
"""
import os
import re
import sys
import html as _h
import posixpath
from urllib.parse import unquote, urlsplit

DEFAULT_ROOT = r"d:\Clinical Medicine"
SKIP_DIRS = {".git", "__pycache__", ".vs", ".vscode", "node_modules", "assets", "MHT"}
OUT_NAME = "索引.html"


def esc(s: str) -> str:
    return _h.escape(s, quote=True)


def rel(root: str, path: str) -> str:
    return os.path.relpath(path, root).replace("\\", "/")


def norm(url: str) -> str:
    u = url.replace("\\", "/").strip()
    while u.startswith(("./", "/")):
        u = u[2:] if u.startswith("./") else u[1:]
    return u


# ---------------- Markdown -> HTML(轻量) ----------------
_CODE_RE = re.compile(r"`([^`]+)`")
_BOLD_RE = re.compile(r"\*\*([^*\n]+)\*\*")
_ITAL_RE = re.compile(r"(?<!\*)\*([^*\n]+)\*(?!\*)")
_CB_RE = re.compile(r"\[([ xX])\]\s*")
_IMG_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_MATERIAL_PATH_RE = re.compile(
    r"(?:[A-Za-z]:[\\/][^`<>\"'\r\n]*?资料[\\/][^`<>\"'\r\n]*|资料[\\/][^`<>\"'\r\n]*)"
)


def redact_material_paths(src: str) -> str:
    """Hide references to local source materials in the generated reader."""
    return _MATERIAL_PATH_RE.sub("[本地资料路径已省略]", src)


def _mk_link(text, url, idmap, source_path):
    u = url.strip()
    low = u.lower()
    if low.startswith(("http://", "https://", "mailto:")):
        return f'<a class="ext" href="{esc(u)}" target="_blank" rel="noopener">{esc(text)}</a>'
    if low.startswith("#"):
        return esc(text)
    parsed = urlsplit(u)
    if parsed.scheme or parsed.netloc or not parsed.path:
        return esc(text)
    target = unquote(parsed.path)
    key = norm(posixpath.normpath(posixpath.join(posixpath.dirname(source_path), target)))
    if key in idmap:
        return f'<a href="#" data-id="{idmap[key]}">{esc(text)}</a>'
    return f'<span class="muted-link">{esc(text)}</span>'


def inline(s, idmap, source_path):
    s = esc(s)
    s = _IMG_RE.sub(lambda m: f'<span class="img-note">🖼 {esc(m.group(1)) or "图"}</span>', s)
    s = _CODE_RE.sub(r"<code>\1</code>", s)
    s = _BOLD_RE.sub(r"<strong>\1</strong>", s)
    s = _ITAL_RE.sub(r"<em>\1</em>", s)
    s = _CB_RE.sub(lambda m: '<span class="cb' +
                   (' done" role="img" aria-label="已完成">✓' if m.group(1).lower() == 'x'
                    else '" role="img" aria-label="未完成">') + '</span>', s)
    s = _LINK_RE.sub(lambda m: _mk_link(m.group(1), m.group(2), idmap, source_path), s)
    return s


def _cells(row):
    r = row.strip()
    if r.startswith("|"):
        r = r[1:]
    if r.endswith("|"):
        r = r[:-1]
    return [c.strip() for c in r.split("|")]


def _render_table(rows, idmap, source_path):
    head = _cells(rows[0])
    out = ['<table><thead><tr>' + ''.join(f'<th>{inline(c, idmap, source_path)}</th>' for c in head) + '</tr></thead><tbody>']
    for r in rows[2:]:
        out.append('<tr>' + ''.join(f'<td>{inline(c, idmap, source_path)}</td>' for c in _cells(r)) + '</tr>')
    out.append('</tbody></table>')
    return ('<div class="table-wrap" role="region" aria-label="可横向滚动的数据表" tabindex="0">'
            + "".join(out) + "</div>")


def md_to_html(src, idmap, source_path):
    lines = src.split("\n")
    out = []
    buf = []
    i = 0

    def flush():
        if buf:
            out.append(f'<p>{"<br>".join(inline(x, idmap, source_path) for x in buf)}</p>')
            buf.clear()

    while i < len(lines):
        ln = lines[i]
        st = ln.strip()
        # 表格(与分隔行成块)
        if "|" in ln:
            j = i
            tl = []
            while j < len(lines) and "|" in lines[j] and not lines[j].strip().startswith("```"):
                tl.append(lines[j])
                j += 1
            if len(tl) >= 2 and re.match(r"^\s*\|?[\s:|-]+\|[\s:|-]*\|?\s*$", tl[1]):
                flush()
                out.append(_render_table(tl, idmap, source_path))
                i = j
                continue
        if not st:
            flush()
            i += 1
            continue
        if st.startswith("```"):
            flush()
            code = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code.append(lines[i])
                i += 1
            i += 1
            out.append("<pre>" + _h.escape("\n".join(code)) + "</pre>")
            continue
        if st.startswith("#### "):
            flush(); out.append(f'<h4>{inline(st[5:], idmap, source_path)}</h4>'); i += 1; continue
        if st.startswith("### "):
            flush(); out.append(f'<h3>{inline(st[4:], idmap, source_path)}</h3>'); i += 1; continue
        if st.startswith("## "):
            flush(); out.append(f'<h2>{inline(st[3:], idmap, source_path)}</h2>'); i += 1; continue
        if st.startswith("# "):
            flush(); out.append(f'<h1>{inline(st[2:], idmap, source_path)}</h1>'); i += 1; continue
        if st.startswith("> "):
            flush()
            q = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                q.append(lines[i].strip()[1:].strip())
                i += 1
            out.append(f'<blockquote><p>{"<br>".join(inline(x, idmap, source_path) for x in q)}</p></blockquote>')
            continue
        if re.match(r"^[-*]\s+", st):
            flush()
            items = []
            while i < len(lines) and re.match(r"^\s*[-*]\s+", lines[i]):
                items.append(re.sub(r"^\s*[-*]\s+", "", lines[i]))
                i += 1
            out.append("<ul>" + "".join(f"<li>{inline(x, idmap, source_path)}</li>" for x in items) + "</ul>")
            continue
        if re.match(r"^\s*\d+\.\s+", st):
            flush()
            items = []
            while i < len(lines) and re.match(r"^\s*\d+\.\s+", lines[i]):
                items.append(re.sub(r"^\s*\d+\.\s+", "", lines[i]))
                i += 1
            out.append("<ol>" + "".join(f"<li>{inline(x, idmap, source_path)}</li>" for x in items) + "</ol>")
            continue
        if st == "---":
            flush(); out.append("<hr>"); i += 1; continue
        buf.append(ln)
        i += 1
    flush()
    return "\n".join(out)


# ---------------- 收集条目 ----------------
class Entry:
    __slots__ = ("id", "title", "path", "suffix", "body_html", "level")

    def __init__(self, eid, title, path, suffix, body_html, level=""):
        self.id = eid
        self.title = title
        self.path = path
        self.suffix = suffix
        self.body_html = body_html
        self.level = level


def collect(root, idmap):
    """返回 {relpath: eid} idmap 与 entries 列表。"""
    entries = []
    counter = [0]
    ordered_paths = []
    for filename in ("README.md", "CONTEXT.md", "大纲导航.md"):
        path = os.path.join(root, filename)
        if os.path.isfile(path):
            ordered_paths.append(path)
    for section in ("考试", "规培"):
        base = os.path.join(root, section)
        if os.path.isdir(base):
            for current, dirs, files in os.walk(base):
                dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
                ordered_paths.extend(os.path.join(current, f) for f in sorted(files)
                                     if f.lower().endswith(".md"))
    adr = os.path.join(root, "docs", "adr")
    if os.path.isdir(adr):
        ordered_paths.extend(os.path.join(adr, f) for f in sorted(os.listdir(adr))
                             if f.lower().endswith(".md"))
    tools = os.path.join(root, "tools")
    if os.path.isdir(tools):
        ordered_paths.extend(os.path.join(tools, f) for f in sorted(os.listdir(tools))
                             if f.lower().endswith((".py", ".md")))
    for eid, path in enumerate(ordered_paths, start=1):
        idmap[norm(rel(root, path))] = eid

    def add(title, path, body_html, level=""):
        counter[0] += 1
        r = rel(root, path)
        e = Entry(counter[0], title, r, os.path.splitext(path)[1].lower(), body_html, level)
        entries.append(e)
        idmap[norm(r)] = e.id
        return e

    def add_md(path, title=None):
        try:
            with open(path, encoding="utf-8") as f:
                src = redact_material_paths(f.read())
        except (OSError, UnicodeDecodeError):
            return None
        t = title or os.path.splitext(os.path.basename(path))[0]
        m = re.search(r">\s*大纲要求\s*:([^\n]*)", src)
        lv = (m.group(1).strip() if m else "") or ""
        return add(t, path, md_to_html(src, idmap, norm(rel(root, path))), lv)

    def add_file(path, title=None):
        with open(path, encoding="utf-8") as f:
            src = redact_material_paths(f.read())
        t = title or os.path.splitext(os.path.basename(path))[0]
        return add(t, path, "<pre>" + _h.escape(src) + "</pre>")

    def add_external(path, title=None, hint=""):
        t = title or os.path.splitext(os.path.basename(path))[0]
        ap = os.path.abspath(path).replace("\\", "/")
        uri = "file:///" + urllib_quote(ap)
        body = (
            '<div class="extern">'
            f"<h3>📄 {esc(t)}</h3><p>这是<b>独立 HTML 单文件</b>(大文件不内嵌):</p>"
            f"<p class=\"p\">{esc(rel(root, path))}</p>"
            '<div class="btns">'
            f'<a class="btn" href="{uri}" target="_blank">在系统浏览器打开</a>'
            f'<button class="btn" data-copy="{esc(rel(root, path))}">复制路径</button>'
            "</div>"
            f"<p class=\"hint\">{hint or '在文件资源管理器中双击该文件也可打开;影像学等 25MB 大图建议系统浏览器打开。'}</p>"
            "</div>"
        )
        return add(t, path, body)

    # 根目录
    rp = os.path.join(root, "README.md")
    if os.path.isfile(rp):
        add_md(rp, "🏠 工作区总览 README")
    cp = os.path.join(root, "CONTEXT.md")
    if os.path.isfile(cp):
        add_md(cp, "📖 术语表 CONTEXT")
    dp = os.path.join(root, "大纲导航.md")
    if os.path.isfile(dp):
        add_md(dp, "🧭 大纲导航(2026)")

    # 考试与规培：递归收集 Markdown，保留各层 README 作为导航内容。
    for section in ("考试", "规培"):
        base = os.path.join(root, section)
        if not os.path.isdir(base):
            continue
        for current, dirs, files in os.walk(base):
            dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
            for filename in sorted(files):
                if filename.lower().endswith(".md"):
                    add_md(os.path.join(current, filename))

    # 文档 ADR
    adr = os.path.join(root, "docs", "adr")
    if os.path.isdir(adr):
        for f in sorted(os.listdir(adr)):
            fp = os.path.join(adr, f)
            if f.lower().endswith(".md"):
                add_md(fp, f"📐 ADR · {f[:-3]}")

    # 工具
    tools = os.path.join(root, "tools")
    if os.path.isdir(tools):
        for f in sorted(os.listdir(tools)):
            fp = os.path.join(tools, f)
            if f.lower().endswith((".py", ".md")):
                if f.lower().endswith(".py"):
                    add_file(fp, f"🛠 {f}")
                else:
                    add_md(fp)

    return entries


def urllib_quote(p):
    from urllib.parse import quote
    return quote(p, safe="/:")


# ---------------- 页面骨架 ----------------
ASSET_DIR = os.path.dirname(__file__)
with open(os.path.join(ASSET_DIR, "reader_styles.css"), encoding="utf-8") as file:
    CSS = file.read()
with open(os.path.join(ASSET_DIR, "reader_app.js"), encoding="utf-8") as file:
    JS = file.read()

def build(root):
    idmap = {}
    entries = collect(root, idmap)
    by_id = {e.id: e for e in entries}

    # 以源文件相对路径形成稳定的考试单元/系统和规培科室分组。
    exam_map = {}
    gp_map = {}
    for entry in entries:
        parts = entry.path.replace("\\", "/").split("/")
        if parts[0] == "考试" and len(parts) >= 2:
            key = tuple(parts[1:3]) if len(parts) >= 4 else (parts[1],)
            if len(parts) == 2:
                key = (parts[1], "总览")
            exam_map.setdefault(key, []).append(entry.id)
        elif parts[0] == "规培" and len(parts) >= 2:
            key = tuple(parts[1:3]) if len(parts) >= 4 else (parts[1], "总览")
            gp_map.setdefault(key, []).append(entry.id)

    exam_groups = [("📘 " + " · ".join(key), gids)
                   for key, gids in sorted(exam_map.items())]
    gp_groups = [("🏥 " + " · ".join(key), gids)
                 for key, gids in sorted(gp_map.items())]
    for key, gids in exam_map.items():
        if key[0] == "03_临床医学综合":
            gids.sort(key=lambda eid: (
                0 if by_id[eid].level.startswith("🔷") else
                1 if by_id[eid].level.startswith("◽") else 2,
                by_id[eid].title,
            ))

    # 文档
    doc_groups = [
        ("📖 术语表 / 🏠 总览",
         [e.id for e in entries if e.path.replace("\\", "/") in
          ("CONTEXT.md", "README.md", "大纲导航.md")]),
        ("📐 架构决策 ADR",
         [e.id for e in entries if e.path.replace("\\", "/").startswith("docs/adr/")]),
    ]
    # 工具
    tool_gids = [e.id for e in entries if e.path.replace("\\", "/").startswith("tools/")]
    nav_groups = exam_groups + gp_groups + doc_groups + [("工具脚本", tool_gids)]
    first_nav_id = next(
        (entry.id for entry in entries if entry.path == "规培/内科/消化内科/README.md"),
        next((gids[0] for _, gids in nav_groups if gids), None),
    )

    # ---- 组装导航 ----
    def lv_emoji(e):
        if e.level.startswith("🔷"):
            return "🔷"
        if e.level.startswith("◽"):
            return "◽"
        return ""

    def group_html(title, gids):
        if not gids:
            return ""
        items = []
        for gid in gids:
            e = by_id[gid]
            nm = (lv_emoji(e) + " " + e.title).strip() if lv_emoji(e) else e.title
            current = ' aria-current="page"' if e.id == first_nav_id else ""
            items.append(f'<a class="it" data-id="{e.id}" href="#d-{e.id}" data-t="{esc(e.title + " " + e.path)}"{current}>'
                         f'<span class="nm">{esc(nm)}</span>'
                         f'<span class="sub">{esc(e.path)}</span></a>')
        expanded = " open" if first_nav_id in gids else ""
        return (f'<details class="grp"{expanded}><summary><span class="h3">{esc(title)}</span>'
                f'<span class="cnt">{len(gids)}</span></summary>'
                f'<div class="items">{"".join(items)}</div></details>')

    sections_html = []
    def add_section(title, groups):
        groups = [(group_title, gids) for group_title, gids in groups if gids]
        if not groups:
            return
        sections_html.append(
            f'<div class="secbox"><h2 class="sec">{esc(title)}<span class="sc"></span></h2>'
            + "".join(group_html(group_title, gids) for group_title, gids in groups)
            + "</div>")

    add_section("📚 考试·备考", exam_groups)
    add_section("🏥 规培·内科轮转", gp_groups)
    add_section("📄 文档·决策", doc_groups)
    add_section("🛠 工具", [("工具脚本", tool_gids)] if tool_gids else [])

    # 文档内容
    docs_html = ['<div id="ph" hidden>← 从左侧选择一个条目开始阅读</div>']
    for e in entries:
        meta = (f'<div class="meta"><span class="p">{esc(e.path)}</span>'
                f'<button class="btn" data-copy="{esc(e.path)}">复制路径</button></div>')
        docs_html.append(f'<article class="doc" id="d-{e.id}" data-id="{e.id}" hidden>{meta}{e.body_html}</article>')

    return ("<!DOCTYPE html>\n<html lang=\"zh-CN\">\n<head>\n<meta charset=\"utf-8\">\n"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
            "<title>Clinical Medicine · 临床口袋手册</title>\n"
            "<style>" + CSS + "</style>\n</head>\n<body>\n"
            '<a class="skip-link" href="#viewer">跳转到正文</a>\n'
            '<header id="topbar">'
            '<button class="tool-button" id="menuToggle" aria-controls="nav" aria-expanded="false" aria-label="打开目录">☰</button>'
            '<div class="brand"><span class="brand-mark" aria-hidden="true">CM</span>'
            '<span><strong>Clinical Medicine</strong><small>临床学习 · 离线阅读</small></span></div>'
            '<div class="top-current"><span class="eyebrow">正在阅读</span>'
            '<span id="currentTitle">选择条目开始阅读</span></div>'
            '<div class="top-actions"><button class="tool-button" id="fontDec" aria-label="缩小正文字号">A−</button>'
            '<button class="tool-button" id="fontInc" aria-label="放大正文字号">A＋</button></div>'
            '</header>\n<div id="workspace">'
            "<nav id=\"nav\" aria-label=\"章节导航\">"
            '<div id="navH"><div class="nav-heading"><h2>内容目录</h2>'
            '<button class="tool-button" id="navClose" aria-label="关闭目录">×</button></div>'
            '<p class="nav-intro">考试备考 · 内科规培 · 项目资料</p>'
            '<div class="search"><input id="q" aria-label="搜索考试和规培条目" placeholder="搜索病种、科室、文件…">'
            '<button id="clr">清除</button></div><div id="res" role="status" aria-live="polite" aria-atomic="true"></div></div>'
            "<div id=\"tree\">" + "".join(sections_html) + "</div></nav>\n"
            '<button id="shade" aria-label="关闭目录" tabindex="-1"></button>'
            f"<main id=\"viewer\" tabindex=\"-1\">{''.join(docs_html)}</main>\n"
            '</div><button id="backTop" aria-label="回到正文顶部">↑ 顶部</button>\n'
            "<script>" + JS + "</script>\n</body>\n</html>")


def main():
    root = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.abspath(DEFAULT_ROOT)
    page = build(root)
    out = os.path.join(root, OUT_NAME)
    with open(out, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"wrote: {out}  ({os.path.getsize(out) / 1024 / 1024:.2f} MiB, {page.count('<article class=\"doc\"')} 条目)")


if __name__ == "__main__":
    main()
