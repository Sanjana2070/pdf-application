I want to create an pdf and image application, for windows desktop (not web). i want to build most of this from scratch in python. that application should be similar to PDFGear and Adobe Acrobat (without the notifications and useless features).


Stack
UI: PySide6 (Qt for Python) or Tkinter (simpler, less polished)
Core services (separate modules):
pdf_service.py
image_service.py
video_service.py
convert_service.py
Workers: background threads or processes (Qt QThread)

Design
Thin UI → calls service layer
Service layer → wraps libraries
Avoid mixing UI + processing logic

A. Compress (PDF, image, video)
PDF
Use:
pikepdf (best for rewriting/optimizing)
Ghostscript (strong compression)
import pikepdf

def compress_pdf(input_path, output_path):
    with pikepdf.open(input_path) as pdf:
        pdf.save(output_path, optimize_streams=True)

For aggressive compression, call Ghostscript via subprocess.

Image
Use:
Pillow
from PIL import Image

def compress_image(inp, out, quality=60):
    img = Image.open(inp)
    img.save(out, optimize=True, quality=quality)
Video
Use:
FFmpeg
ffmpeg -i input.mp4 -vcodec libx264 -crf 28 output.mp4


B. Images → PDF
from PIL import Image

def images_to_pdf(image_paths, output):
    imgs = [Image.open(p).convert("RGB") for p in image_paths]
    imgs[0].save(output, save_all=True, append_images=imgs[1:])


C. Edit PDF (rotate, add image, etc.)

Use:

PyMuPDF
import fitz  # PyMuPDF

doc = fitz.open("input.pdf")
page = doc[0]
page.set_rotation(90)
doc.save("out.pdf")

Add image:

rect = fitz.Rect(50, 50, 200, 200)
page.insert_image(rect, filename="img.png")
D. Merge / Split
import fitz

def merge_pdfs(files, out):
    doc = fitz.open()
    for f in files:
        doc.insert_pdf(fitz.open(f))
    doc.save(out)

Split:

def split_pdf(file):
    doc = fitz.open(file)
    for i, page in enumerate(doc):
        new = fitz.open()
        new.insert_pdf(doc, from_page=i, to_page=i)
        new.save(f"page_{i}.pdf")


E. PDF ↔ Word
Use:
pdf2docx
python-docx
from pdf2docx import Converter

cv = Converter("input.pdf")
cv.convert("out.docx")
cv.close()

Reverse:
Generate DOCX → convert via LibreOffice CLI

F. PDF Reader
Use:
PyMuPDF for rendering pages as images
pix = page.get_pixmap()
pix.save("page.png")

Display inside Qt widget.

G. Forms + Digital Signature
Forms
PyMuPDF supports reading/writing fields (limited)

For robust forms:
consider pdfrw
Digital signature

Options:
Wrap:
OpenSSL
or use endesive Python library

You must handle:
certificates (.pfx)
hashing
embedding signature in PDF structure


3) UI design (minimal but clean)
Main window:
Sidebar:
Compress
Convert
Edit
Merge/Split
Reader
Central panel: dynamic tool UI
Drag-and-drop support


4) Packaging (Windows)

Use:
PyInstaller
pyinstaller --onefile --windowed app.py


5) What you should NOT build from scratch

Avoid reinventing:

PDF rendering engine
Video codecs
Cryptographic signing primitives

You will lose months and still get worse results.

6) Realistic roadmap

Phase 1
UI shell
Image → PDF
Merge/Split

Phase 2
PDF editing basics
Compression

Phase 3
Reader
PDF ↔ Word

Phase 4 (advanced)
Forms
Digital signatures