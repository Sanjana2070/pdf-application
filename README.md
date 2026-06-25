# PDF Tools

A native Windows desktop application for working with PDFs and images — compress,
convert, edit, merge/split, read, fill forms, and digitally sign. Built from
scratch in Python with a thin PySide6 (Qt) UI over a dedicated service layer.

Inspired by PDFGear and Adobe Acrobat, minus the notifications and bloat.

## Features

| Area | What it does |
|------|--------------|
| **Compress** | Shrink PDFs, images, and video (pikepdf / Ghostscript, Pillow, FFmpeg) |
| **Convert** | Images → PDF, PDF ↔ Word |
| **Edit** | Rotate pages, insert images, basic page operations |
| **Merge / Split** | Combine multiple PDFs or split into single pages |
| **Reader** | Render and view PDF pages |
| **Forms** | Read and fill PDF form fields |
| **Sign** | Digital signatures using `.pfx` certificates (endesive) |

## Architecture

The app keeps UI and processing logic strictly separated:

```
app.py                 # Entry point — boots QApplication, theme, MainWindow
ui/                    # Thin Qt UI (no processing logic)
  main_window.py       #   Window shell + sidebar + stacked panels
  sidebar.py
  theme.py
  panels/              #   One panel per tool (compress, convert, edit, ...)
services/              # Wraps third-party libraries; does the real work
  pdf_service.py
  image_service.py
  compress_service.py
  convert_service.py
  forms_service.py
  sign_service.py
workers/               # Background threads (Qt QThread) for long tasks
  worker.py
```

**Flow:** UI panel → service layer → library. Heavy operations run on background
workers so the UI stays responsive.

## Requirements

- **Python 3.10+**
- Windows (the app targets Windows desktop)
- Python packages (see [requirements.txt](requirements.txt)):
  - PySide6, PyMuPDF, Pillow, pikepdf, pdf2docx, endesive

### External tools (optional, for full functionality)

- **Ghostscript** — aggressive PDF compression
- **FFmpeg** — video compression
- **LibreOffice** — DOCX → PDF conversion

Install these separately and ensure they're available on your `PATH`.

## Getting started

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
python app.py
```

## Packaging (Windows)

Build a standalone executable with PyInstaller:

```bash
pyinstaller --onefile --windowed app.py
```

## Roadmap

- **Phase 1** — UI shell, Image → PDF, Merge/Split
- **Phase 2** — PDF editing basics, compression
- **Phase 3** — Reader, PDF ↔ Word
- **Phase 4** — Forms, digital signatures

## License

Not yet specified.
