# -*- coding: utf-8 -*-
"""MHT(OneNote 导出) → 单文件夹 HTML(保留原始表格/标题/样式,加旧笔记配色横幅)。

用法:
    python mht_to_html.py <input.mht> <output_dir> [--embed]

产物:
    <output_dir>/<stem>.html           完整 HTML(UTF-8),顶部橙色「📌 旧笔记」横幅
    <output_dir>/assets/<basename>     内嵌图片(默认外链相对路径;--embed 改为 base64 内嵌)

说明:
- 提取 MHT 中 text/html 原文,保留 OneNote 原生结构(表格/标题/样式无损)。
- 图片 src 重写为 assets 相对路径或 data URI。
"""
import base64
import email
import os
import quopri
import re
import sys

BANNER_CSS = """
.banner-note{background:#fff7e0;border:1px solid #f0ad4e;border-left:6px solid #f0ad4e;
 border-radius:6px;padding:12px 16px;margin:0 0 16px 0;font-family:system-ui,-apple-system,sans-serif;
 color:#7a4a00;}
.banner-note b{color:#a05a00;}
.banner-note code{background:#ffe9c7;padding:1px 4px;border-radius:3px;}
"""


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
            ext = ct.split("/")[-1]
            if not base:
                base = f"anon_{len(images) + 1}.{ext if ext else 'png'}"
            images[base] = (payload, "image/" + ext)
    return html, images


def build_banner(stem):
    return (
        '<div class="banner-note"><b>📌 旧笔记</b> — 本页内容源自 OneNote《临床医学》导出 '
        f'(<span style="color:#a05a00">个人一手笔记,2024–2025</span>),非 AI 初稿。'
        f'原始文件:<code>MHT/{stem}.mht</code></div>'
    )


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else ""
    outdir = sys.argv[2] if len(sys.argv) > 2 else ""
    embed = "--embed" in sys.argv
    if not src or not outdir:
        print(__doc__)
        sys.exit(1)
    stem = os.path.splitext(os.path.basename(src))[0]
    html, images = parse_mht(src)

    assets_dir = os.path.join(outdir, "assets")
    os.makedirs(assets_dir, exist_ok=True)

    imgmap = {}
    label = ""
    if embed:
        for base, (data, mime) in images.items():
            imgmap[base] = f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"
        label = "embed"
    else:
        for base, (data, _mime) in images.items():
            with open(os.path.join(assets_dir, base), "wb") as f:
                f.write(data)
            imgmap[base] = f"assets/{base}"
        label = "external"

    # 重写图片引用:file:/// C:/... file7919.files/xxx.png -> assets/xxx.png 或 data URI
    def _rewrite(m):
        token = m.group(3)
        base = os.path.basename(token.replace("\\", "/"))
        return m.group(1) + m.group(2) + (imgmap.get(base) or token) + m.group(4)

    html = re.sub(r'(<img[^>]*\bsrc=)(["\'])([^"\']+)(["\'])', _rewrite, html, flags=re.I)

    # 抽取 <body> 内容(如无则视为 body)
    body = html
    m = re.search(r"<body[^>]*>(.*)</body>\s*</html>", html, flags=re.I | re.S)
    head = html
    if m:
        body = m.group(1)
        head = html[: m.start()]

    banner = build_banner(stem)
    document = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>📌 旧笔记 · {stem}</title>
<style>{BANNER_CSS}</style>
</head>
<body>
{banner}
{body}
</body>
</html>
"""
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, f"{stem}.html"), "w", encoding="utf-8") as f:
        f.write(document)
    print(f"wrote: {outdir}\\{stem}.html  [mode={label}]")
    print(f"images: {len(images)}")


if __name__ == "__main__":
    main()