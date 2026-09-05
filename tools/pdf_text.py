#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pdf_text.py — 把 PDF 抽成文本,自动处理「文字版」与「扫描图片版(OCR)」。
用法: python pdf_text.py <in.pdf> <out.txt> [--resume]
- 文字版 PDF:直接 pypdf 抽取;
- 扫描版(文字极少):按页解出内嵌图片 → rapidocr-onnxruntime OCR → 拼接输出。
- --resume:断点续传——若 <out.txt> 已存在,仅 OCR 缺失页(大扫描件中断后补跑)。
依赖: pip install pypdf rapidocr-onnxruntime
"""
import os
import sys
import re


def _split_existing(path):
    """读已有输出,返回 {页码: 原始块文本}。"""
    blocks = {}
    with open(path, encoding="utf-8") as f:
        content = f.read()
    parts = re.split(r"(?m)^(=== 第 (\d+) 页\(共\d+页\) ===\n)", content)
    # parts: [pre, mark, pageno, body, mark, ...]
    i = 1
    while i + 2 < len(parts):
        try:
            pno = int(parts[i + 1])
        except ValueError:
            i += 3
            continue
        body = parts[i + 2]
        nxt = parts[i + 3] if i + 3 < len(parts) else ""
        blocks[pno] = parts[i] + body
        i += 3
    return blocks


def _write(dst, blocks, n):
    text = "\n\n".join(blocks[k] for k in sorted(blocks))
    with open(dst, "w", encoding="utf-8") as f:
        f.write(text)
    return len(text)


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    src, dst = sys.argv[1], sys.argv[2]
    resume = "--resume" in sys.argv
    f0 = int(sys.argv[sys.argv.index("--from") + 1]) if "--from" in sys.argv else 1
    to_ = int(sys.argv[sys.argv.index("--to") + 1]) if "--to" in sys.argv else 10 ** 9

    engine = _get_engine()
    import pypdf
    reader = pypdf.PdfReader(src)
    n = len(reader.pages)
    to_ = min(to_, n)

    blocks = {}
    if resume and os.path.isfile(dst):
        blocks = _split_existing(dst)
        print(f"[resume] 已有 {len(blocks)} 页, 本次范围 {f0}-{to_}", flush=True)

    scanned = 0
    for i in range(f0 - 1, to_):
        pno = i + 1
        if pno in blocks:
            continue
        page = reader.pages[i]
        try:
            t = page.extract_text() or ""
        except Exception:
            t = ""
        if len(t.strip()) < 5:
            scanned += 1
            t = _ocr_page(page, engine) or ""
        blocks[pno] = f"=== 第 {pno} 页(共{n}页) ===\n" + t
        if pno % 12 == 0:
            _write(dst, blocks, n)
            print(f"[progress] {pno}/{n} 页已写盘", flush=True)
        import gc
        gc.collect()

    ch = _write(dst, blocks, n)
    print(f"wrote: {dst}  (共 {n} 页, {ch} 字符, 本次 OCR {scanned} 页)")


_ENGINE = None


def _get_engine():
    global _ENGINE
    if _ENGINE is None:
        from rapidocr_onnxruntime import RapidOCR
        _ENGINE = RapidOCR()
    return _ENGINE


def _ocr_page(page, engine):
    """把 pypdf PageObject 的内嵌图片取出交给 RapidOCR(引擎复用)。"""
    try:
        imgs = page.images
    except Exception:
        return ""
    texts = []
    for im in imgs:
        data = im.data
        ext = (im.name or "").rsplit(".", 1)[-1].lower()
        try:
            texts.append(_ocr_bytes(data, ext, engine))
        except Exception as e:
            print(f"  [OCR 失败] {im.name}: {e}")
    return "\n".join(t for t in texts if t)


def _ocr_bytes(data, ext, engine):
    tmp = os.path.join(os.environ.get("TEMP", os.getcwd()), f"_ocr_img.{ext or 'png'}")
    with open(tmp, "wb") as f:
        f.write(data)
    result, _ = engine(tmp)
    if not result:
        return ""
    return "\n".join(item[1] for item in result)


if __name__ == "__main__":
    main()