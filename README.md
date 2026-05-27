# 📄 pdf2md-ocr

> PDF 轉 Markdown 工具，支援簡體／繁體中文 OCR，專為大型 PDF（40MB+）設計。

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/YOUR_USERNAME/pdf2md-ocr/blob/main/pdf2md_ocr.ipynb)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)

---

## ✨ 功能

- 🔍 **自動偵測頁面類型** — 有文字層直接提取，掃描版自動 OCR，無需手動判斷
- 🀄 **中文 OCR** — 支援簡體（`chi_sim`）、繁體（`chi_tra`）或同時識別
- ✂️ **分批處理** — 每 100 頁切割，避免大檔記憶體溢出
- 🔗 **自動合併** — 所有批次結果依頁碼順序合併為單一 `.md` 檔案
- 📊 **進度顯示** — 顯示處理速度與預估剩餘時間
- 🔧 **進階重處理** — 可針對特定頁面用更高 DPI 單獨重跑

## 🚀 快速開始

### 方法一：Google Colab（推薦，免安裝）

1. 點擊上方 [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/YOUR_USERNAME/pdf2md-ocr/blob/main/pdf2md_ocr.ipynb) 徽章
2. 依序執行每個 cell
3. 上傳 PDF → 等待處理 → 下載 `.md` 檔案

### 方法二：本機執行

```bash
# 安裝系統依賴（Ubuntu / Debian）
sudo apt-get install tesseract-ocr tesseract-ocr-chi-sim tesseract-ocr-chi-tra poppler-utils

# 安裝 Python 套件
pip install -r requirements.txt

# 執行轉換
python pdf2md.py input.pdf --lang chi_sim+eng --dpi 200 --chunk 100
```

## ⚙️ 參數說明

| 參數 | 預設值 | 說明 |
|------|--------|------|
| `--lang` | `chi_sim+eng` | OCR 語言，可用值：`chi_sim` `chi_tra` `eng` 任意組合 |
| `--dpi` | `200` | 影像解析度，掃描版建議 200–300，速度優先可用 150 |
| `--chunk` | `100` | 每批處理頁數，記憶體不足可降至 50 |
| `--force-ocr` | `False` | 強制所有頁面 OCR（忽略內嵌文字層）|
| `--output` | 同輸入目錄 | 輸出 `.md` 路徑 |

## 📋 系統需求

- Python 3.8+
- Tesseract 4.0+（含 `chi_sim` 語言包）
- 建議 Colab GPU（T4）執行，約 10–20 分鐘處理 44MB PDF

## 🗂️ 輸出格式

每頁以 HTML 註解標記頁碼，方便後續解析：

```markdown
# 文件標題

> 來源檔案：`example.pdf`
> 總頁數：200 頁
> OCR 語言：`chi_sim+eng`

---

<!-- page 1 -->

第一頁的內容文字...

---

<!-- page 2 -->

第二頁的內容文字...
```

## 🐛 常見問題

**Q：OCR 速度太慢？**  
降低 `--dpi 150`，或縮小 `--chunk 50`。

**Q：簡繁混排識別差？**  
改用 `--lang chi_sim+chi_tra+eng`。

**Q：記憶體不足（Colab OOM）？**  
縮小 chunk size 至 30–50。

**Q：文字亂碼（PDF 有文字層但顯示錯誤）？**  
使用 `--force-ocr` 忽略內嵌文字層，強制 OCR。

## 📄 授權

MIT License — 詳見 [LICENSE](LICENSE)

## 🤝 貢獻

歡迎提交 Issue 或 Pull Request！
