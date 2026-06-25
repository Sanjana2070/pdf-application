import os
import shutil
import subprocess
from typing import Callable


def _find_libreoffice() -> str | None:
    lo = shutil.which("soffice")
    if lo:
        return lo
    candidates = [
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path
    return None


class ConvertService:

    @staticmethod
    def pdf_to_word(
        input_path: str,
        output_path: str,
        progress_cb: Callable[[int], None] = None
    ) -> None:
        """Convert PDF to DOCX using pdf2docx."""
        if not os.path.isfile(input_path):
            raise RuntimeError(f"File not found: {input_path}")

        from pdf2docx import Converter

        if progress_cb:
            progress_cb(5)

        cv = Converter(input_path)
        cv.convert(output_path, start=0, end=None)
        cv.close()

        if progress_cb:
            progress_cb(100)

    @staticmethod
    def word_to_pdf(
        input_path: str,
        output_path: str,
        progress_cb: Callable[[int], None] = None
    ) -> None:
        """
        Convert DOCX/DOC to PDF via LibreOffice headless CLI.
        LibreOffice names the output file based on the input stem and places it
        in the specified directory; we rename afterward if needed.
        """
        if not os.path.isfile(input_path):
            raise RuntimeError(f"File not found: {input_path}")

        soffice = _find_libreoffice()
        if not soffice:
            raise RuntimeError(
                "LibreOffice not found. Download from https://www.libreoffice.org/ "
                "and install it, then restart the app."
            )

        if progress_cb:
            progress_cb(5)

        output_dir = os.path.dirname(os.path.abspath(output_path))
        cmd = [
            soffice,
            "--headless",
            "--convert-to", "pdf",
            "--outdir", output_dir,
            input_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"LibreOffice error:\n{result.stderr[-400:]}")

        # LibreOffice writes {input_stem}.pdf in output_dir
        input_stem = os.path.splitext(os.path.basename(input_path))[0]
        lo_output = os.path.join(output_dir, f"{input_stem}.pdf")

        desired = os.path.abspath(output_path)
        if os.path.abspath(lo_output) != desired and os.path.isfile(lo_output):
            os.replace(lo_output, desired)

        if progress_cb:
            progress_cb(100)

    @staticmethod
    def libreoffice_available() -> bool:
        return _find_libreoffice() is not None


def render_page(
    pdf_path: str,
    page_index: int,
    zoom: float,
    progress_cb: Callable[[int], None] = None
) -> dict:
    """
    Render a single PDF page to raw RGB bytes.
    Runs in a worker thread (opens its own fitz document so it's thread-safe).

    Returns dict with: samples (bytes), width, height, stride.
    """
    import fitz
    doc = fitz.open(pdf_path)
    page = doc[page_index]
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    data = {
        "samples": bytes(pix.samples),
        "width": pix.width,
        "height": pix.height,
        "stride": pix.stride,
        "page_width_pts": page.rect.width,
        "page_height_pts": page.rect.height,
    }
    doc.close()
    if progress_cb:
        progress_cb(100)
    return data
