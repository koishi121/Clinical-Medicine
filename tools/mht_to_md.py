# -*- coding: utf-8 -*-
"""MHT(OneNote 导出) → Markdown + 图片资产 拆图转换器(试点,stdlib only)。

用法:
    python mht_to_md.py <input.mht> <output_dir>

产物:
    <output_dir>/<stem>.md          主文档(带“旧笔记”颜色标记横幅)
    <output_dir>/assets/<basename>  内嵌图片(按 Content-Location 原始名)

表格策略:OneNote 导出表格为“每个表格/单元格自成 <table>”的碎片结构,
按一致性判断:列等宽且≥2 列 → 标准 MD 表格;否则每行转竖排列表,保证内容零丢失。
"""
import base64
import email
import os
import quopri
import re
import sys
from html.parser import HTMLParser

IMG_MAP = {}


def parse_mht(path):
    with open(path, "rb") as f:
        msg = email.message_from_bytes(f.read())
    html = None
    images = {}
    for part in msg.walk():
        ct = part.get_content_type()
        if ct == "text/html":
            raw = part.get_payload(decode=True) or b""
            ch = part.get_content_charset() or "utf-8"
            html = raw.decode(ch, "ignore")
        elif ct.startswith("image/"):
            payload = part.get_payload(decode=True)
            if payload is None:
                enc = (part.get("Content-Transfer-Encoding") or "").lower()
                payload = part.get_payload()
                if isinstance(payload, list):
                    payload = b"".join(
                        chunk.encode("latin1", "ignore") if isinstance(chunk, str) else chunk
                        for chunk in payload
                    )
                elif isinstance(payload, str):
                    payload = payload.encode("latin1", "ignore")
                if enc == "base64":
                    payload = base64.b64decode(payload)
                elif enc.startswith("quoted"):
                    payload = quopri.decodestring(payload)
            loc = part.get("Content-Location", "") or ""
            base = os.path.basename(loc.replace("\\", "/"))
            if not base:
                ext = ct.split("/")[-1]
                base = f"anon_{len(images) + 1}.{ext}"
            images[base] = payload
    return html, images


def _clean_cell(c):
    return c.replace("\n", " ").replace("\u00a0", " ").replace("&nbsp;", " ").strip()


class ToMarkdown(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []
        self.strong = 0
        self.em = 0
        self.in_li = False
        # 表格
        self.table_depth = 0
        self.td_nest = 0       # 当前在多少层 td/th 内(含嵌套)
        self.cell = ""
        self.row = []
        self.rows = []
        self.hlevel = None
        self.hbuf = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.hlevel = int(tag[1])
        elif tag in ("strong", "b"):
            self.strong += 1
        elif tag in ("em", "i"):
            self.em += 1
        elif tag == "li":
            self.in_li = True
        elif tag == "table":
            self.table_depth += 1
            if self.table_depth == 1:
                self.rows = []
        elif tag == "tr":
            if self.table_depth == 1:
                self.row = []
        elif tag in ("td", "th"):
            if self.table_depth >= 1:
                self.td_nest += 1
                if self.table_depth == 1:
                    self.cell = ""
        elif tag == "img":
            src = a.get("src", "")
            if self.td_nest > 0:
                self.cell += f"![图]({_resolve(src)}) "
            else:
                self.out.append(f"![]({_resolve(src)})")
        elif tag in ("div", "p", "br"):
            if self.td_nest > 0:
                self.cell += "\n"
            else:
                self.out.append("\n")

    def handle_endtag(self, tag):
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            txt = "".join(self.hbuf).strip()
            if txt:
                self.out.append("\n" + "#" * self.hlevel + " " + txt + "\n")
            self.hlevel = None
            self.hbuf = []
        elif tag in ("strong", "b"):
            self.strong = max(0, self.strong - 1)
        elif tag in ("em", "i"):
            self.em = max(0, self.em - 1)
        elif tag == "li":
            self.out.append("\n- ")
            self.in_li = False
        elif tag == "table":
            self.table_depth = max(0, self.table_depth - 1)
            if self.table_depth == 0:
                self._emit_table()
        elif tag in ("td", "th"):
            if self.td_nest > 0:
                self.td_nest -= 1
                if self.table_depth == 1 and self.td_nest == 0:
                    self.row.append(_clean_cell(self.cell))
                    self.cell = ""
        elif tag == "tr":
            if self.table_depth == 1 and self.row:
                self.rows.append(self.row)
                self.row = []
        elif tag in ("div", "p"):
            if self.td_nest > 0:
                self.cell += "\n"
            else:
                self.out.append("\n")

    def handle_data(self, data):
        if self.hlevel is not None:
            self.hbuf.append(data)
            return
        if self.td_nest > 0:
            self.cell += data
            return
        if self.strong:
            data = f"**{data}**"
        if self.em:
            data = f"*{data}*"
        self.out.append(data)

    def _emit_table(self):
        if not self.rows:
            return
        # OneNote 导出表格为碎片结构(每逻辑行/单元格各自成 table),
        # 一律转竖排列表,保证内容零丢失且排版不破。
        self.out.append("\n_表格内容:_\n")
        for r in self.rows:
            self.out.append("- " + " | ".join(r) + "\n")


def _resolve(src):
    base = os.path.basename(src.replace("\\", "/"))
    return IMG_MAP.get(base) or src


def build_banner(stem):
    return (
        '<div style="background:#fff7e0;border:1px solid #f0ad4e;border-left:5px solid #f0ad4e;'
        "border-radius:6px;padding:10px 14px;margin-bottom:12px;\">\n"
        '<b style="color:#a05a00;">📌 旧笔记</b> — 本页内容源自 OneNote《临床医学》导出 '
        f'(<span style=\"color:#a05a00;\">个人一手笔记,2024–2025</span>),非 AI 初稿。'
        f"原始文件:<code>MHT/{stem}.mht</code>\n</div>\n"
    )


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else ""
    outdir = sys.argv[2] if len(sys.argv) > 2 else ""
    if not src or not outdir:
        print(__doc__)
        sys.exit(1)
    stem = os.path.splitext(os.path.basename(src))[0]
    html, images = parse_mht(src)

    assets_dir = os.path.join(outdir, "assets")
    os.makedirs(assets_dir, exist_ok=True)
    for base, data in images.items():
        with open(os.path.join(assets_dir, base), "wb") as f:
            f.write(data)
        IMG_MAP[base] = f"assets/{base}"

    p = ToMarkdown()
    p.feed(html)
    body = "".join(p.out)
    body = re.sub(r"\n{3,}", "\n\n", body)
    body = re.sub(r"[ \t]+\n", "\n", body)
    body = re.sub(r"^(\*\*.+?\*\*)$", lambda m: "## " + m.group(1).strip("* "), body, flags=re.M)

    md = f"# {stem}\n\n" + build_banner(stem) + f"\n\n{body}\n"
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, f"{stem}.md"), "w", encoding="utf-8") as f:
        f.write(md)
    print(f"wrote: {outdir}\\{stem}.md")
    print(f"images written: {len(images)}")
    refs = set(re.findall(r"!\[[^\]]*\]\(([^)]+)\)", md))
    missing = sorted(r for r in refs if not r.startswith("assets/") and not r.startswith("http"))
    print("unresolved refs:", missing if missing else "none")


if __name__ == "__main__":
    main()