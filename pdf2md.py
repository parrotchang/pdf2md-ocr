#!/usr/bin/env python3
"""
pdf2md-ocr: PDF 轉 Markdown，支援簡繁中文 OCR，大型 PDF 分批處理
Usage: python pdf2md.py input.pdf [options]
"""

import argparse
import io
import os
import sys
import time
from pathlib import Path

try:
    import fitz  # PyMuPDF
    import pytesseract
    from PIL import Image
    from tqdm import tqdm
except ImportError as e:
    print(f"[錯誤] 缺少依賴套件：{e}")
    print("請執行：pip install -r requirements.txt")
    sys.exit(1)


# ─────────────────────────────────────────
# 頁面處理函式
# ─────────────────────────────────────────

def page_has_text(page: fitz.Page, min_chars: int = 20) -> bool:
    """判斷頁面是否有可直接提取的文字（非掃描版）"""
    return len(page.get_text("text").strip()) >= min_chars


def extract_text(page: fitz.Page) -> str:
    """從 PDF 向量文字層直接提取文字"""
    return page.get_text("text")


def ocr_page(page: fitz.Page, dpi: int = 200, lang: str = "chi_sim+eng") -> str:
    """光柵化頁面後執行 Tesseract OCR，回傳識別文字"""
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    config = "--oem 3 --psm 6"
    return pytesseract.image_to_string(img, lang=lang, config=config)


def process_page(page: fitz.Page, dpi: int, lang: str, force_ocr: bool) -> tuple[str, str]:
    """
    處理單一頁面，自動選擇提取方式。
    回傳 (文字內容, 方法名稱)
    """
    if not force_ocr and page_has_text(page):
        return extract_text(page), "text"
    return ocr_page(page, dpi=dpi, lang=lang), "ocr"


# ─────────────────────────────────────────
# 文字後處理
# ─────────────────────────────────────────

def clean_text(text: str) -> str:
    """清理多餘空行，保留段落結構"""
    lines = text.splitlines()
    result, prev_empty = [], False
    for line in lines:
        stripped = line.rstrip()
        if stripped == "":
            if not prev_empty:
                result.append("")
            prev_empty = True
        else:
            result.append(stripped)
            prev_empty = False
    return "\n".join(result).strip() or "*（本頁無可識別文字）*"


def format_page(text: str, page_num: int) -> str:
    """格式化單頁為 Markdown，附加頁碼標記"""
    return f"<!-- page {page_num} -->\n\n{clean_text(text)}\n"


# ─────────────────────────────────────────
# 主轉換流程
# ─────────────────────────────────────────

def convert(
    pdf_path: str,
    output_path: str | None = None,
    dpi: int = 200,
    lang: str = "chi_sim+eng",
    chunk_size: int = 100,
    force_ocr: bool = False,
) -> str:
    """
    將 PDF 轉換為 Markdown。

    Args:
        pdf_path:    輸入 PDF 路徑
        output_path: 輸出 .md 路徑（None 則同目錄同名）
        dpi:         OCR 光柵化解析度
        lang:        Tesseract 語言字串
        chunk_size:  每批處理頁數
        force_ocr:   強制所有頁面 OCR

    Returns:
        輸出 .md 的絕對路徑
    """
    pdf_path = Path(pdf_path).resolve()
    if not pdf_path.exists():
        raise FileNotFoundError(f"找不到 PDF：{pdf_path}")

    if output_path is None:
        output_path = pdf_path.with_suffix(".md")
    output_path = Path(output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"📂 輸入：{pdf_path}  ({pdf_path.stat().st_size / 1e6:.1f} MB)")
    print(f"📝 輸出：{output_path}")

    doc = fitz.open(str(pdf_path))
    total = len(doc)
    chunks = [(s, min(s + chunk_size, total)) for s in range(0, total, chunk_size)]

    print(f"   總頁數：{total} 頁 | 分 {len(chunks)} 批（每批 {chunk_size} 頁）")
    print(f"   OCR 語言：{lang} | DPI：{dpi}\n")

    pages_data: list[tuple[int, str, str]] = []
    ocr_count = text_count = 0
    t0 = time.time()

    for ci, (start, end) in enumerate(chunks):
        label = f"Chunk {ci+1}/{len(chunks)}（p{start+1}–{end}）"
        for i in tqdm(range(start, end), desc=label, unit="p"):
            text, method = process_page(doc[i], dpi, lang, force_ocr)
            pages_data.append((i + 1, text, method))
            if method == "ocr":
                ocr_count += 1
            else:
                text_count += 1

    doc.close()
    elapsed = time.time() - t0

    # ── 組合 Markdown ──
    header = (
        f"# {pdf_path.stem}\n\n"
        f"> 來源檔案：`{pdf_path.name}`  \n"
        f"> 總頁數：{total} 頁  \n"
        f"> OCR 語言：`{lang}`  \n"
        f"> 直接提取：{text_count} 頁 ｜ OCR 識別：{ocr_count} 頁\n\n---\n"
    )
    body = "\n\n---\n\n".join(
        format_page(text, pn) for pn, text, _ in sorted(pages_data)
    )
    md_content = header + "\n" + body

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    size_kb = output_path.stat().st_size / 1024
    print(f"\n✅ 完成！耗時 {elapsed:.1f}s（{elapsed/60:.1f} 分鐘）")
    print(f"   輸出大小：{size_kb:.0f} KB | 字元數：{len(md_content):,}")
    print(f"   直接提取：{text_count} 頁 | OCR：{ocr_count} 頁")
    return str(output_path)


# ─────────────────────────────────────────
# CLI 入口
# ─────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="PDF 轉 Markdown（支援簡繁中文 OCR）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例：
  python pdf2md.py book.pdf
  python pdf2md.py book.pdf --lang chi_sim+chi_tra+eng --dpi 300
  python pdf2md.py book.pdf --output result.md --chunk 50
  python pdf2md.py book.pdf --force-ocr
        """,
    )
    p.add_argument("pdf", help="輸入 PDF 路徑")
    p.add_argument("-o", "--output", default=None, help="輸出 .md 路徑（預設同目錄）")
    p.add_argument("--lang", default="chi_sim+eng",
                   help="Tesseract 語言（預設：chi_sim+eng）")
    p.add_argument("--dpi", type=int, default=200,
                   help="OCR 影像解析度（預設：200）")
    p.add_argument("--chunk", type=int, default=100,
                   help="每批處理頁數（預設：100）")
    p.add_argument("--force-ocr", action="store_true",
                   help="強制所有頁面 OCR（忽略內嵌文字層）")
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    convert(
        pdf_path=args.pdf,
        output_path=args.output,
        dpi=args.dpi,
        lang=args.lang,
        chunk_size=args.chunk,
        force_ocr=args.force_ocr,
    )
