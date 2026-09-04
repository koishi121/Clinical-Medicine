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
from datetime import date

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


def _mk_link(text, url, idmap):
    u = url.strip()
    low = u.lower()
    if low.startswith(("http://", "https://", "mailto:")):
        return f'<a class="ext" href="{esc(u)}" target="_blank" rel="noopener">{esc(text)}</a>'
    if low.startswith("#"):
        return esc(text)
    key = norm(u)
    for k, pid in idmap.items():
        if k == key or os.path.basename(k) == os.path.basename(key):
            return f'<a href="#" data-id="{pid}">{esc(text)}</a>'
    return f'<span class="muted-link">{esc(text)}</span>'


def inline(s, idmap):
    s = esc(s)
    s = _IMG_RE.sub(lambda m: f'<span class="img-note">🖼 {esc(m.group(1)) or "图"}</span>', s)
    s = _CODE_RE.sub(r"<code>\1</code>", s)
    s = _BOLD_RE.sub(r"<strong>\1</strong>", s)
    s = _ITAL_RE.sub(r"<em>\1</em>", s)
    s = _CB_RE.sub(lambda m: '<span class="cb' + (' done">✓' if m.group(1).lower() == 'x' else '">') + '</span>', s)
    s = _LINK_RE.sub(lambda m: _mk_link(m.group(1), m.group(2), idmap), s)
    return s


def _cells(row):
    r = row.strip()
    if r.startswith("|"):
        r = r[1:]
    if r.endswith("|"):
        r = r[:-1]
    return [c.strip() for c in r.split("|")]


def _render_table(rows, idmap):
    head = _cells(rows[0])
    out = ['<table><thead><tr>' + ''.join(f'<th>{inline(c, idmap)}</th>' for c in head) + '</tr></thead><tbody>']
    for r in rows[2:]:
        out.append('<tr>' + ''.join(f'<td>{inline(c, idmap)}</td>' for c in _cells(r)) + '</tr>')
    out.append('</tbody></table>')
    return "".join(out)


def md_to_html(src, idmap):
    lines = src.split("\n")
    out = []
    buf = []
    i = 0

    def flush():
        if buf:
            out.append(f'<p>{"<br>".join(inline(x, idmap) for x in buf)}</p>')
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
                out.append(_render_table(tl, idmap))
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
            flush(); out.append(f'<h4>{inline(st[5:], idmap)}</h4>'); i += 1; continue
        if st.startswith("### "):
            flush(); out.append(f'<h3>{inline(st[4:], idmap)}</h3>'); i += 1; continue
        if st.startswith("## "):
            flush(); out.append(f'<h2>{inline(st[3:], idmap)}</h2>'); i += 1; continue
        if st.startswith("# "):
            flush(); out.append(f'<h1>{inline(st[2:], idmap)}</h1>'); i += 1; continue
        if st.startswith("> "):
            flush()
            q = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                q.append(lines[i].strip()[1:].strip())
                i += 1
            out.append(f'<blockquote><p>{"<br>".join(inline(x, idmap) for x in q)}</p></blockquote>')
            continue
        if re.match(r"^[-*]\s+", st):
            flush()
            items = []
            while i < len(lines) and re.match(r"^\s*[-*]\s+", lines[i]):
                items.append(re.sub(r"^\s*[-*]\s+", "", lines[i]))
                i += 1
            out.append("<ul>" + "".join(f"<li>{inline(x, idmap)}</li>" for x in items) + "</ul>")
            continue
        if re.match(r"^\s*\d+\.\s+", st):
            flush()
            items = []
            while i < len(lines) and re.match(r"^\s*\d+\.\s+", lines[i]):
                items.append(re.sub(r"^\s*\d+\.\s+", "", lines[i]))
                i += 1
            out.append("<ol>" + "".join(f"<li>{inline(x, idmap)}</li>" for x in items) + "</ol>")
            continue
        if st == "---":
            flush(); out.append("<hr>"); i += 1; continue
        buf.append(ln)
        i += 1
    flush()
    return "\n".join(out)


# ---------------- 收集条目 ----------------
class Entry:
    __slots__ = ("id", "title", "path", "suffix", "body_html")

    def __init__(self, eid, title, path, suffix, body_html):
        self.id = eid
        self.title = title
        self.path = path
        self.suffix = suffix
        self.body_html = body_html


def collect(root, idmap):
    """返回 {relpath: eid} idmap 与 entries 列表。"""
    entries = []
    counter = [0]
    idmap.update({})  # ensure

    def add(title, path, body_html):
        counter[0] += 1
        r = rel(root, path)
        e = Entry(counter[0], title, r, os.path.splitext(path)[1].lower(), body_html)
        entries.append(e)
        idmap[norm(r)] = e.id
        return e

    def add_md(path, title=None):
        try:
            with open(path, encoding="utf-8") as f:
                src = f.read()
        except (OSError, UnicodeDecodeError):
            return None
        t = title or os.path.splitext(os.path.basename(path))[0]
        return add(t, path, md_to_html(src, idmap))

    def add_file(path, title=None):
        with open(path, encoding="utf-8") as f:
            src = f.read()
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

    # 考试
    exam = os.path.join(root, "考试")
    if os.path.isdir(exam):
        for unit in sorted(os.listdir(exam)):
            ur = os.path.join(exam, unit)
            if not os.path.isdir(ur):
                continue
            if unit == "03_临床医学综合":
                for sysname in sorted(os.listdir(ur)):
                    sr = os.path.join(ur, sysname)
                    if not os.path.isdir(sr):
                        continue
                    srm = os.path.join(sr, "README.md")
                    if os.path.isfile(srm):
                        add_md(srm, f"💾 {sysname}")
                    for f in sorted(os.listdir(sr)):
                        fp = os.path.join(sr, f)
                        if os.path.isfile(fp) and f.lower().endswith(".md") and f.lower() != "readme.md":
                            add_md(fp)
            else:
                urm = os.path.join(ur, "README.md")
                if os.path.isfile(urm):
                    add_md(urm, f"📘 {unit}")
                for f in sorted(os.listdir(ur)):
                    fp = os.path.join(ur, f)
                    if os.path.isfile(fp) and f.lower().endswith(".md") and f.lower() != "readme.md":
                        add_md(fp)

    # 规培
    gp = os.path.join(root, "规培")
    if os.path.isdir(gp):
        for dept in sorted(os.listdir(gp)):
            dr = os.path.join(gp, dept)
            if not os.path.isdir(dr):
                continue
            for sub in sorted(os.listdir(dr)):
                sr = os.path.join(dr, sub)
                if not os.path.isdir(sr):
                    continue
                srm = os.path.join(sr, "README.md")
                if os.path.isfile(srm):
                    add_md(srm, f"🏥 {sub}")
                for f in sorted(os.listdir(sr)):
                    fp = os.path.join(sr, f)
                    if os.path.isfile(fp) and f.lower().endswith(".md") and f.lower() != "readme.md":
                        add_md(fp)

    # 资料
    zl = os.path.join(root, "资料")
    if os.path.isdir(zl):
        zrm = os.path.join(zl, "README.md")
        if os.path.isfile(zrm):
            add_md(zrm, "📂 资料 · 教材/题库指南")
        old = os.path.join(zl, "旧笔记")
        if os.path.isdir(old):
            for f in ("index.html", "README.md", "拆图方案评估.md"):
                fp = os.path.join(old, f)
                if os.path.isfile(fp):
                    if f.endswith(".md"):
                        add_md(fp, {"README.md": "📋 旧笔记 · 登记表",
                                    "拆图方案评估.md": "🧾 旧笔记 · 拆图方案评估"}[f])
                    else:
                        add_external(fp, "🗺️ 旧笔记 · 考试×规培映射页")
            hdir = os.path.join(old, "html")
            if os.path.isdir(hdir):
                for d in sorted(os.listdir(hdir)):
                    fp = os.path.join(hdir, d, f"{d}.html")
                    if os.path.isfile(fp):
                        add_external(fp, f"📄 {d}", "超大图库(如 医学影像学 25MB/201 图)建议系统浏览器打开并放大查看。")

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
CSS = """
html,body{background:#faf6ee;color:#3f3f3f;height:100%;
 font-family:"Microsoft YaHei UI","Microsoft YaHei","PingFang SC",system-ui,-apple-system,"Segoe UI",sans-serif;
 font-size:15px;line-height:1.85;}
body{display:flex;height:100vh;overflow:hidden;margin:0;}
*{box-sizing:border-box;}
#nav{width:400px;flex:0 0 400px;border-right:1px solid #e6dcc4;background:#fcf7ec;overflow:hidden;
 display:flex;flex-direction:column;}
#navH{padding:14px 16px 10px;border-bottom:1px solid #e6dcc4;flex:0 0 auto;}
#navH h1{font-size:18px;color:#7a5224;margin:0 0 8px;}
.search{display:flex;gap:8px;align-items:center;flex-wrap:wrap;}
.search input{flex:1;min-width:150px;font:inherit;font-size:14px;padding:8px 12px;
 border:1px solid #d9cbb0;border-radius:8px;background:#fffdf8;color:#3f3f3f;}
.search input:focus{outline:2px solid #e0c88f;}
button{font:inherit;font-size:13px;padding:6px 12px;border:1px solid #d9cbb0;border-radius:8px;
 background:#fffdf8;color:#6b4a1f;cursor:pointer;}
button:hover{background:#f7eed7;}
#res{font-size:12px;color:#9a937f;margin-top:4px;}
#tree{overflow-y:auto;flex:1;padding:8px 10px 40px;}
.sec{color:#7a5224;font-size:15px;font-weight:700;margin:14px 4px 6px;padding-bottom:4px;
 border-bottom:1px dashed #e0d4ba;}
.grp{margin:6px 0 10px;}
.h3{color:#6b4a1f;font-size:13.5px;font-weight:600;margin:8px 4px 3px;}
.h3 .cnt{display:inline-block;min-width:20px;text-align:center;font-size:11px;color:#fff;
 background:#d6bd87;border-radius:999px;padding:0 6px;margin-left:6px;line-height:17px;}
.items{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:4px;}
.it{display:block;text-decoration:none;color:#3f3f3f;background:#fffdf8;border:1px solid #ece2cb;
 border-radius:7px;padding:5px 9px;line-height:1.5;font-size:13.5px;cursor:pointer;overflow:hidden;}
.it .nm{display:block;color:#5f4a26;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.it .sub{display:block;font-size:11px;color:#b0a784;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.it:hover{border-color:#d6bd87;background:#fcf6e7;}
.it.active{border-color:#d09c4c;background:#f6ead0;}
.hide{display:none !important;}

#viewer{flex:1;min-width:0;overflow-y:auto;background:#fdfbf4;}
#ph{display:flex;align-items:center;height:100%;justify-content:center;color:#b0a784;font-size:15px;}
.doc{max-width:880px;margin:0 auto;padding:24px 34px 60px;}
.doc h1{color:#7a5224;font-size:24px;margin:6px 0 2px;}
.doc h2{color:#7a5224;font-size:19px;margin:1.3em 0 .4em;border-bottom:1px solid #eee0c4;padding-bottom:4px;}
.doc h3{color:#6b4a1f;font-size:16px;margin:1em 0 .3em;}
.doc h4{color:#6b4a1f;font-size:14.5px;margin:.8em 0 .2em;}
.doc p{margin:.45em 0;}
.doc ul,.doc ol{margin:.3em 0 .6em;padding-left:1.6em;}
.doc li{margin:.15em 0;}
.doc table{border-collapse:collapse;max-width:100%;margin:.6em 0;font-size:14px;}
.doc th,.doc td{border:1px solid #e0d4ba;padding:6px 11px;background:#fffdf8;}
.doc th{background:#f1e6d0;color:#6b4a1f;}
.doc blockquote{background:#f6efdd;border-left:5px solid #dcc28a;border-radius:6px;
 padding:8px 14px;margin:.6em 0;color:#7a5a20;}
.doc code{background:#f5e7cf;padding:1px 5px;border-radius:4px;font-size:13px;color:#7a4a1f;}
.doc pre{background:#f5edd8;border:1px solid #e6d8b4;border-radius:8px;padding:12px 16px;
 overflow-x:auto;font-size:13px;line-height:1.6;}
.doc hr{border:none;border-top:1px solid #e8dfcf;margin:1.2em 0;}
.doc img{max-width:100%;height:auto;}
.cb{display:inline-block;width:15px;height:15px;border:1.5px solid #b8a87e;border-radius:4px;
 vertical-align:-2px;margin-right:3px;}
.cb.done{background:#8fb56a;color:#fff;font-size:11px;line-height:13px;text-align:center;border-color:#8fb56a;}
.img-note{display:inline-block;background:#f2ecda;border:1px dashed #dcc28a;border-radius:6px;
 padding:2px 8px;color:#8a6a2a;font-size:13px;}
.muted-link{color:#b0a784;}
.ext{color:#8a5a2b;}
.doc a.ext{color:#7a9b6d;}
.meta{font-size:12px;color:#9a937f;margin:0 0 14px;border-bottom:1px solid #eee0c4;padding-bottom:10px;}
.meta .p{font-family:Consolas,monospace;color:#a08c5a;}
.btns{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0;}
.btn{display:inline-block;text-decoration:none;font:inherit;font-size:13px;padding:7px 14px;
 border:1px solid #d9cbb0;border-radius:8px;background:#f7eed7;color:#6b4a1f;cursor:pointer;}
.btn:hover{background:#eeddae;}
.extern h3{color:#7a5224;}
.extern .hint{color:#9a937f;font-size:13px;}
#backTop{position:fixed;right:26px;bottom:26px;padding:8px 14px;}
@media (max-width:860px){
 body{flex-direction:column;}
 #nav{width:100%;flex:none;height:45vh;border-right:none;border-bottom:1px solid #e6dcc4;}
 #viewer{height:55vh;}
}
"""

JS = """
function ready(){
  var VIEWER=document.getElementById('viewer');
  var DEAD=document.getElementById('ph');
  var docs={};
  document.querySelectorAll('.doc').forEach(function(d){docs[d.dataset.id]=d;});
  function show(id){
    document.querySelectorAll('.it').forEach(function(x){x.classList.remove('active');});
    var a=document.querySelector('[data-id="'+id+'"]');
    if(a){a.classList.add('active');}
    document.querySelectorAll('.doc').forEach(function(d){d.hidden=true;});
    var d=docs[id];
    VIEWER.scrollTop=0;
    if(d){d.hidden=false;} else {DEAD.hidden=false;}
  }
  document.querySelectorAll('[data-id]').forEach(function(a){
    a.addEventListener('click',function(e){e.preventDefault(); show(a.dataset.id);});
  });
  document.addEventListener('click',function(e){
    var b=e.target.closest('[data-copy]'); if(!b)return;
    var r=b.dataset.copy;
    var ta=document.createElement('textarea'); ta.value=r; document.body.appendChild(ta);
    ta.select();
    try{document.execCommand('copy'); b.textContent='✓ 已复制';}catch(err){}
    document.body.removeChild(ta);
    setTimeout(function(){b.textContent='复制路径';},1500);
  });
  var inp=document.getElementById('q'), res=document.getElementById('res');
  var items=[].slice.call(document.querySelectorAll('.it'));
  var total=items.length, shownAll=0;
  function go(){
    var q=inp.value.trim().toLowerCase(), shown=0;
    items.forEach(function(a){
      var ok=!q || (a.dataset.t||'').toLowerCase().indexOf(q)>=0;
      a.classList.toggle('hide',!ok); if(ok)shown++;
    });
    document.querySelectorAll('.grp').forEach(function(g){
      var vis=[].slice.call(g.querySelectorAll('.it')).filter(function(a){return !a.classList.contains('hide');}).length;
      var c=g.querySelector('.cnt'); if(c)c.textContent=vis;
      g.classList.toggle('hide',vis===0);
    });
    document.querySelectorAll('.secbox').forEach(function(s){
      var vis=[].slice.call(s.querySelectorAll('.it')).filter(function(a){return !a.classList.contains('hide');}).length;
      var c=s.querySelector('.sc'); if(c)c.textContent=vis;
      s.classList.toggle('hide', vis===0 && !!q);
    });
    if(!q && !document.getElementById('firstShown')){
      // 首次展示时自动打开第一项
    }
    res.textContent = q ? ('匹配 '+shown+' / '+total+' 项') : ('共 '+total+' 项');
  }
  inp.addEventListener('input',go);
  document.getElementById('clr').addEventListener('click',function(){inp.value='';go();inp.focus();});
  document.getElementById('backTop').addEventListener('click',function(){VIEWER.scrollTop=0;});
  go();
  var first=document.querySelector('.it'); if(first){show(first.dataset.id);}
}
if (document.readyState==='loading'){document.addEventListener('DOMContentLoaded',ready);} else {ready();}
"""


def build(root):
    idmap = {}
    entries = collect(root, idmap)
    by_id = {e.id: e for e in entries}

    ex = os.path.join(root, "考试")
    gp = os.path.join(root, "规培")
    zl = os.path.join(root, "资料")

    # 03 临床医学综合:14 系统各一组
    groups03 = []
    if os.path.isdir(ex):
        for unit in sorted(os.listdir(ex)):
            ur = os.path.join(ex, unit)
            if not os.path.isdir(ur):
                continue
            if unit == "03_临床医学综合":
                for sysname in sorted(os.listdir(ur)):
                    sr = os.path.join(ur, sysname)
                    if not os.path.isdir(sr):
                        continue
                    prefix = "考试/03_临床医学综合/" + sysname + "/"
                    gids = [e.id for e in entries if e.path.replace("\\", "/").startswith(prefix)]
                    groups03.append((f"💾 {sysname}", gids))

    # 规培:内科科室各一组
    gp_groups = []
    if os.path.isdir(gp):
        for dept in sorted(os.listdir(gp)):
            dr = os.path.join(gp, dept)
            if not os.path.isdir(dr):
                continue
            for sub in sorted(os.listdir(dr)):
                sr = os.path.join(dr, sub)
                if not os.path.isdir(sr):
                    continue
                gids = [e.id for e in entries
                        if e.path.replace("\\", "/").startswith("规培/" + dept + "/" + sub + "/")]
                gp_groups.append((f"🏥 {sub}", gids))

    # 资料
    zl_groups = []
    zl_groups.append(("📂 资料 · 教材/题库指南",
                      [e.id for e in entries if e.path.replace("\\", "/") == "资料/README.md"]))
    old_base = "资料/旧笔记/"
    zl_groups.append(("📌 旧笔记 · 登记/映射/方案",
                      [e.id for e in entries if e.path.replace("\\", "/").startswith(old_base)
                       and "/html/" not in e.path.replace("\\", "/")]))
    zl_groups.append(("📄 旧笔记 · HTML 单文件(20 科,独立大文件)",
                      [e.id for e in entries if "/html/" in e.path.replace("\\", "/")]))

    # 文档
    doc_groups = [
        ("📖 术语表 / 🏠 总览",
         [e.id for e in entries if e.path.replace("\\", "/") in ("CONTEXT.md", "README.md")]),
        ("📐 架构决策 ADR",
         [e.id for e in entries if e.path.replace("\\", "/").startswith("docs/adr/")]),
    ]
    # 工具
    tool_gids = [e.id for e in entries if e.path.replace("\\", "/").startswith("tools/")]

    # ---- 组装导航 ----
    def group_html(title, gids):
        if not gids:
            return ""
        items = []
        for gid in gids:
            e = by_id[gid]
            items.append(f'<a class="it" data-id="{e.id}" data-t="{esc(e.title + " " + e.path)}">'
                         f'<span class="nm">{esc(e.title)}</span>'
                         f'<span class="sub">{esc(e.path)}</span></a>')
        return (f'<div class="grp"><h3 class="h3">{esc(title)}'
                f'<span class="cnt">{len(gids)}</span></h3>'
                f'<div class="items">{"".join(items)}</div></div>')

    sections_html = []
    # 考试
    exam_groups = list(groups03)
    for unit in ["00_大纲与计划", "01_基础医学综合", "02_医学人文综合", "04_预防医学综合", "05_实践技能"]:
        gids = [e.id for e in entries if e.path.replace("\\", "/").startswith("考试/" + unit + "/")]
        if gids:
            exam_groups.append((f"📘 {unit}", gids))
    sections_html.append(
        f'<div class="secbox"><h2 class="sec">📚 考试·备考<span class="sc"></span></h2>'
        + "".join(group_html(t, g) for t, g in exam_groups)
        + "</div>")
    sections_html.append(
        '<div class="secbox"><h2 class="sec">🏥 规培·内科轮转<span class="sc"></span></h2>'
        + "".join(group_html(t, g) for t, g in gp_groups) + "</div>")
    sections_html.append(
        '<div class="secbox"><h2 class="sec">📂 资料<span class="sc"></span></h2>'
        + "".join(group_html(t, g) for t, g in zl_groups) + "</div>")
    sections_html.append(
        '<div class="secbox"><h2 class="sec">📄 文档·决策<span class="sc"></span></h2>'
        + "".join(group_html(t, g) for t, g in doc_groups) + "</div>")
    sections_html.append(
        '<div class="secbox"><h2 class="sec">🛠 工具<span class="sc"></span></h2>'
        + group_html("工具脚本", tool_gids) + "</div>")

    # 文档内容
    docs_html = ['<div id="ph" hidden>← 从左侧选择一个条目开始阅读</div>']
    for e in entries:
        meta = (f'<div class="meta">📁 <span class="p">{esc(e.path)}</span>'
                f'<div class="btns">'
                f'<button class="btn" data-copy="{esc(e.path)}">复制路径</button>'
                f'</div></div>')
        docs_html.append(f'<article class="doc" id="d-{e.id}" data-id="{e.id}" hidden>{meta}{e.body_html}</article>')

    today = date.today().isoformat()
    return ("<!DOCTYPE html>\n<html lang=\"zh-CN\">\n<head>\n<meta charset=\"utf-8\">\n"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
            "<title>🏠 Clinical Medicine · 离线阅读器</title>\n"
            "<style>" + CSS + "</style>\n</head>\n<body>\n"
            "<nav id=\"nav\">"
            "<div id=\"navH\"><h1>🏠 Clinical Medicine</h1>"
            "<div class=\"search\"><input id=\"q\" placeholder=\"🔍 病种/科室/科目/文件名…\" autofocus>"
            "<button id=\"clr\">清除</button></div><div id=\"res\"></div></div>"
            "<div id=\"tree\">" + "".join(sections_html) + "</div></nav>\n"
            f"<main id=\"viewer\">{''.join(docs_html)}</main>\n"
            '<button id="backTop">▲ 回顶</button>\n'
            "<script>" + JS + "</script>\n</body>\n</html>")


def main():
    root = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.abspath(DEFAULT_ROOT)
    page = build(root)
    out = os.path.join(root, OUT_NAME)
    with open(out, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"wrote: {out}  ({len(page) / 1024 / 1024:.2f} MB, {page.count('data-id=\"')} 条目)")


if __name__ == "__main__":
    main()