#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pdf_text.py — 把 PDF 抽成文本,自动处理「文字版」与「扫描图片版(OCR)」。
用法: python pdf_text.py <in.pdf> <out.txt>
- 文字版 PDF:直接 pypdf 抽取;
- 扫描版(文字极少):按页解出内嵌图片 → rapidocr-onnxruntime OCR → 拼接输出。
依赖: pip install pypdf rapidocr-onnxruntime
"""
import os
import sys
import io


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    src, dst = sys.argv[1], sys.argv[2]

    engine = _get_engine()
    import pypdf
    reader = pypdf.PdfReader(src)
    n = len(reader.pages)
    parts = []
    scanned = 0
    for i, page in enumerate(reader.pages):
        try:
            t = page.extract_text() or ""
        except Exception:
            t = ""
        if len(t.strip()) < 5:
            scanned += 1
            t = _ocr_page(page, engine) or ""
        parts.append(f"=== 第 {i+1} 页(共{n}页) ===\n" + t)
    text = "\n\n".join(parts)
    with open(dst, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"wrote: {dst}  ({n} 页, {len(text)} 字符, OCR 页 {scanned})")


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