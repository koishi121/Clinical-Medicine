#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dir_index.py — 生成 Clinical Medicine 工作区的可搜索 HTML 快捷索引(索引.html)
用法:python dir_index.py [<工作区根目录>]   (默认 d:\\Clinical Medicine)
重跑即覆盖索引.html,全库新增内容后重跑一次即可保持最新。
"""
import os
import re
import sys
import html as _html
import urllib.parse

DEFAULT_ROOT = r"d:\Clinical Medicine"
SKIP_DIRS = {".git", "__pycache__", ".vs", ".vscode", "node_modules", "assets"}
SKIP_FILES = {".gitignore", "索引.html", "index.html"}


def esc(s: str) -> str:
    return _html.escape(s, quote=True)


def rel(root: str, path: str) -> str:
    return os.path.relpath(path, root).replace("\\", "/")


def href_from(root: str, path: str) -> str:
    return urllib.parse.quote(rel(root, path))


def it(root: str, path: str, label: str) -> str:
    """一个可搜索条目;label 为显示名,sub 为相对路径小字。"""
    r = rel(root, path)
    h = href_from(root, path)
    plain = re.sub(r"\.(md|html|py)$", "", label)
    return (f'<a class="it" href="{h}" data-t="{esc(plain + " " + r)}">'
            f'<span class="nm">{esc(plain)}</span>'
            f'<span class="sub">{esc(r)}</span></a>')


def group(title_html: str, items: list) -> str:
    if not items:
        return ""
    body = "".join(items)
    return (f'<div class="grp"><h3 class="h3">{title_html}'
            f'<span class="cnt">{len(items)}</span></h3>'
            f'<div class="items">{body}</div></div>')


def h3_link(root: str, path: str, label: str) -> str:
    h = href_from(root, path)
    return f'<a href="{h}">{esc(label)}</a>'


def sections(root: str) -> str:
    exam = os.path.join(root, "考试")
    gp = os.path.join(root, "规培")
    zl = os.path.join(root, "资料")
    docs = os.path.join(root, "docs")
    tools = os.path.join(root, "tools")

    # ---------- 快捷直达 ----------
    quick = [
        ("正库总索引(14 系统病种卡)", "考试/03_临床医学综合/README.md"),
        ("规培·内科总索引(10 科室)", "规培/内科/README.md"),
        ("旧笔记·考试×规培映射页", "资料/旧笔记/index.html"),
        ("工作区总览 README", "README.md"),
        ("术语表 CONTEXT", "CONTEXT.md"),
        ("教材/题库准备", "资料/README.md"),
        ("备考大纲与计划", "考试/00_大纲与计划/README.md"),
        ("实践技能(查体/判读)", "考试/05_实践技能/README.md"),
    ]
    quick_html = "".join(
        f'<a class="chip" href="{href_from(root, os.path.join(root, *p.split("/")))}">{esc(t)}</a>'
        for t, p in quick
    )

    # ---------- 考试 ----------
    exam_groups = []
    if os.path.isdir(exam):
        for unit in sorted(os.listdir(exam)):
            uroot = os.path.join(exam, unit)
            if not os.path.isdir(uroot):
                continue
            unit_name = unit  # 如 03_临床医学综合
            unit_readme = os.path.join(uroot, "README.md")
            if unit == "03_临床医学综合":
                inner = []
                for sysname in sorted(os.listdir(uroot)):
                    sroot = os.path.join(uroot, sysname)
                    if not os.path.isdir(sroot):
                        continue
                    s_readme = os.path.join(sroot, "README.md")
                    items = []
                    head_txt = (h3_link(root, s_readme, f"💾 {sysname}")
                                if os.path.isfile(s_readme) else esc(sysname))
                    if os.path.isdir(sroot):
                        for f in sorted(os.listdir(sroot)):
                            fp = os.path.join(sroot, f)
                            if os.path.isfile(fp) and f.endswith(".md") and f.lower() != "readme.md":
                                items.append(it(root, fp, f))
                    inner.append(group(f"<span class='gn'>{head_txt}</span>", items))
                exam_groups.append(
                    f"<h3 class='h3 big'>{esc(unit_name)} · 14 系统病种卡" 
                    f"<span class='cnt'>{len(inner)}</span></h3>" + "".join(inner))
            else:
                items = []
                readme = unit_readme if os.path.isfile(unit_readme) else None
                for f in sorted(os.listdir(uroot)):
                    fp = os.path.join(uroot, f)
                    if os.path.isfile(fp) and f.endswith(".md"):
                        if readme and os.path.abspath(fp) == os.path.abspath(readme):
                            continue
                        items.append(it(root, fp, f))
                head = (h3_link(root, readme, f"📘 {unit_name}") if readme else esc(unit_name))
                allitems = []
                if readme:
                    allitems.append(it(root, readme, f"📘 {unit_name} · 总览"))
                allitems += items
                exam_groups.append(group(f"<span class='gn'>{head}</span>", allitems))

    # ---------- 规培 ----------
    gp_groups = []
    if os.path.isdir(gp):
        for dept in sorted(os.listdir(gp)):
            droot = os.path.join(gp, dept)
            if not os.path.isdir(droot):
                continue
            for sub in sorted(os.listdir(droot)):
                sroot = os.path.join(droot, sub)
                if not os.path.isdir(sroot):
                    continue
                readme = os.path.join(sroot, "README.md")
                items = []
                if os.path.isfile(readme):
                    items.append(it(root, readme, f"🏥 {sub} · 科室首页"))
                for f in sorted(os.listdir(sroot)):
                    fp = os.path.join(sroot, f)
                    if os.path.isfile(fp) and f.endswith(".md") and f.lower() != "readme.md":
                        items.append(it(root, fp, f))
                head = (h3_link(root, readme, f"🏥 {sub}")
                        if os.path.isfile(readme) else esc(sub))
                gp_groups.append(group(f"<span class='gn'>{head}</span>", items))

    # ---------- 资料 ----------
    zl_groups = []
    if os.path.isdir(zl):
        zl_readme = os.path.join(zl, "README.md")
        zl_items = [it(root, zl_readme, "📂 资料 · 教材/题库指南")] if os.path.isfile(zl_readme) else []
        zl_groups.append(group(f"<span class='gn'>📂 资料总览</span>", zl_items))

        old = os.path.join(zl, "旧笔记")
        if os.path.isdir(old):
            items = [it(root, os.path.join(old, "index.html"), "🗺️ 旧笔记 · 考试×规培映射页"),
                     it(root, os.path.join(old, "README.md"), "📋 旧笔记 · 登记表"),
                     it(root, os.path.join(old, "拆图方案评估.md"), "🧾 旧笔记 · 拆图方案评估")]
            for f in sorted(os.listdir(old)):
                fp = os.path.join(old, f)
                if os.path.isfile(fp) and f.endswith(".md") and f not in ("README.md", "拆图方案评估.md"):
                    items.append(it(root, fp, f))
            old_html_dir = os.path.join(old, "html")
            if os.path.isdir(old_html_dir):
                htmls = []
                for d in sorted(os.listdir(old_html_dir)):
                    dp = os.path.join(old_html_dir, d)
                    fp = os.path.join(dp, f"{d}.html")
                    if os.path.isdir(dp) and os.path.isfile(fp):
                        htmls.append(it(root, fp, f"📄 {d}"))
                items += htmls
            zl_groups.append(group(f"<span class='gn'>📌 旧笔记(一手笔记,HTML 唯一正本)</span>", items))

    # ---------- 文档·决策 ----------
    doc_groups = []
    for path, label in (("CONTEXT.md", "📖 术语表 CONTEXT.md"),
                        ("README.md", "🏠 工作区总览 README")):
        fp = os.path.join(root, path)
        if os.path.isfile(fp):
            doc_groups.append(group(f"<span class='gn'>{esc(label)}</span>",
                                    [it(root, fp, label)]))
    adr_dir = os.path.join(docs, "adr")
    if os.path.isdir(adr_dir):
        adr_items = []
        for f in sorted(os.listdir(adr_dir)):
            fp = os.path.join(adr_dir, f)
            if f.endswith(".md"):
                adr_items.append(it(root, fp, f"📐 ADR · {f[:-3]}"))
        doc_groups.append(group("<span class='gn'>📐 架构决策(ADR)</span>", adr_items))

    # ---------- 工具 ----------
    tool_items = []
    if os.path.isdir(tools):
        for f in sorted(os.listdir(tools)):
            fp = os.path.join(tools, f)
            if f.endswith(".py"):
                tool_items.append(it(root, fp, f"🛠 {f}"))
    tool_groups = group("<span class='gn'>🛠 工具脚本</span>", tool_items)

    s = ""
    s += f'<section id="q"><h2 class="sec">🚀 快捷直达</h2><div class="chips">{quick_html}</div></section>'
    s += f'<section id="exam"><h2 class="sec">📚 考试·备考<span class="scnt"></span></h2>{"".join(exam_groups)}</section>'
    s += f'<section id="gp"><h2 class="sec">🏥 规培·内科轮转<span class="scnt"></span></h2>{"".join(gp_groups)}</section>'
    s += f'<section id="zl"><h2 class="sec">📂 资料<span class="scnt"></span></h2>{"".join(zl_groups)}</section>'
    s += f'<section id="doc"><h2 class="sec">📄 文档·决策<span class="scnt"></span></h2>{"".join(doc_groups)}</section>'
    s += f'<section id="tool"><h2 class="sec">🛠 工具<span class="scnt"></span></h2>{tool_groups}</section>'
    return s


def build(root: str) -> str:
    body = sections(root)
    count = body.count('class="it"')
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>🏠 Clinical Medicine · 快捷索引</title>
<style>
html,body{{background:#faf6ee;color:#3f3f3f;
 font-family:"Microsoft YaHei UI","Microsoft YaHei","PingFang SC",system-ui,-apple-system,"Segoe UI",sans-serif;
 font-size:16px;line-height:1.9;}}
body{{max-width:1080px;margin:0 auto;padding:26px 36px 80px;}}
h1{{color:#7a5224;font-size:26px;margin:0 0 4px;}}
.lead{{color:#8a887f;font-size:14px;margin:0 0 16px;}}
.banner-note{{background:#fdf3e3;border:1px solid #ead9b8;border-left:6px solid #e0a84e;
 border-radius:8px;padding:12px 16px;margin:0 0 20px;color:#7a4a00;line-height:1.6;}}
.banner-note b{{color:#9c6b1f;}}
.search{{position:sticky;top:0;z-index:5;background:#faf6ee;padding:10px 0 14px;display:flex;gap:10px;align-items:center;flex-wrap:wrap;}}
.search input{{flex:1;min-width:240px;font:inherit;font-size:16px;padding:10px 14px;border:1px solid #d9cbb0;border-radius:8px;background:#fffdf8;color:#3f3f3f;}}
.search input:focus{{outline:2px solid #e0c88f;}}
#res{{font-size:13px;color:#9a937f;}}
button{{font:inherit;font-size:14px;padding:8px 14px;border:1px solid #d9cbb0;border-radius:8px;background:#fffdf8;color:#6b4a1f;cursor:pointer;}}
button:hover{{background:#f7eed7;}}
.toc{{margin:0 0 8px;font-size:14px;}}
.toc a{{margin-right:14px;text-decoration:none;color:#8a5a2b;}}
.toc a:hover{{text-decoration:underline;}}
section{{margin:26px 0 6px;}}
.sec{{color:#7a5224;font-size:20px;border-bottom:2px solid #e8dfcf;padding-bottom:6px;margin:0 0 12px;}}
.scnt::before{{content:" · ";}}
.scnt{{font-size:13px;color:#9a937f;font-weight:normal;}}
.grp{{margin:0 0 14px;}}
.h3{{color:#5f4a26;font-size:16px;margin:10px 0 4px;font-weight:600;}}
.h3.big{{font-size:17px;color:#7a5224;margin-top:16px;}}
.h3 a{{color:#5f4a26;text-decoration:none;}}
.h3 a:hover{{color:#d09c4c;text-decoration:underline;}}
.cnt{{display:inline-block;min-width:22px;text-align:center;font-size:12px;color:#fff;background:#d6bd87;border-radius:999px;padding:0 7px;margin-left:8px;line-height:19px;}}
.chips{{display:flex;flex-wrap:wrap;gap:8px;padding:4px 0 2px;}}
.chip{{display:inline-block;padding:5px 13px;border-radius:999px;background:#f1e6d0;border:1px solid #e0d4ba;color:#6b4a1f;text-decoration:none;font-size:14px;}}
.chip:hover{{background:#e7d6b2;}}
.items{{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:6px 14px;}}
.it{{display:block;text-decoration:none;color:#3f3f3f;background:#fffdf8;border:1px solid #ece2cb;border-radius:7px;padding:6px 11px;line-height:1.5;}}
.it:hover{{border-color:#d6bd87;background:#fcf6e7;}}
.it .nm{{display:block;color:#5f4a26;font-size:15px;}}
.it .sub{{display:block;font-size:12px;color:#9a937f;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}}
.hide{{display:none !important;}}
.foot{{margin-top:34px;font-size:13px;color:#9a937f;border-top:1px solid #e8dfcf;padding-top:12px;}}
</style>
</head>
<body>

<div class="banner-note"><b>🏠 Clinical Medicine · 快捷索引</b>
— 全库目录一键检索:上方搜索框按<b>病种 / 科室 / 科目 / 文件名</b>实时过滤;区域直达
<a href="#exam">📚考试</a> <a href="#gp">🏥规培</a> <a href="#zl">📂资料</a> <a href="#doc">📄文档</a> <a href="#tool">🛠工具</a>。
本页由 <code>tools/dir_index.py</code> 自动生成,全库更新后重跑一次即可。</div>

<h1>Clinical Medicine · 快捷索引</h1>
<div class="lead">执医考备考 + 规培内科轮转 · 双用途工作区 · 更新于 {esc(__import__("datetime").date.today().isoformat())}</div>

<div class="search">
<input id="q" type="text" placeholder="🔍 输入病种/科室/科目/文件名…(如: 肺炎、呼吸、影像学)" autofocus>
<button id="clr" type="button">清除</button>
<div id="res">共 {count} 个条目</div>
</div>

{body}

<script>
const inp=document.getElementById('q');
const btn=document.getElementById('clr');
const res=document.getElementById('res');
const items=[...document.querySelectorAll('.it')];
const total=items.length;
function go(){{
  const q=inp.value.trim().toLowerCase();
  let shown=0;
  items.forEach(a=>{{
    const ok=!q || (a.dataset.t||'').toLowerCase().includes(q);
    a.classList.toggle('hide',!ok);
    if(ok) shown++;
  }});
  document.querySelectorAll('.grp').forEach(g=>{{
    const vis=[...g.querySelectorAll('.it')].filter(a=>!a.classList.contains('hide')).length;
    const c=g.querySelector('.cnt'); if(c) c.textContent=vis;
    g.classList.toggle('hide',vis===0);
  }});
  document.querySelectorAll('section').forEach(s=>{{
    const vis=[...s.querySelectorAll('.it')].filter(a=>!a.classList.contains('hide')).length;
    const sc=s.querySelector('.scnt'); if(sc) sc.textContent=vis;
    s.classList.toggle('hide', vis===0 && !!q);
  }});
  res.textContent = q? `匹配 ${{shown}} / ${{total}} 项` : `共 ${{total}} 个条目`;
}}
inp.addEventListener('input',go);
btn.addEventListener('click',()=>{{inp.value='';go();inp.focus();}});
go();
</script>

<div class="foot">正库病种卡 218 · 规培科室 10 · 旧笔记 HTML 20 科 · ADR 2 · 工具脚本若干。档案源:MHT 已删,旧笔记 HTML 为唯一正本。</div>
</body>
</html>
"""


def main():
    root = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.abspath(DEFAULT_ROOT)
    out = os.path.join(root, "索引.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(build(root))
    n = build(root).count('class="it"')
    print(f"wrote: {out}")
    print(f"items: {n}")


if __name__ == "__main__":
    main()