import fitz  # PyMuPDF
import os
from typing import Callable


def _parse_page_range(spec: str, total: int) -> list[int]:
    """
    Parse a page range string like "1,3,5-7" into a sorted list of 0-based indices.
    Page numbers in the spec are 1-based. Invalid entries are silently skipped.
    """
    indices = set()
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            a, _, b = part.partition("-")
            try:
                lo = max(1, int(a.strip()))
                hi = min(total, int(b.strip()))
                indices.update(range(lo - 1, hi))
            except ValueError:
                pass
        else:
            try:
                n = int(part)
                if 1 <= n <= total:
                    indices.add(n - 1)
            except ValueError:
                pass
    return sorted(indices)


class PdfService:

    @staticmethod
    def merge_pdfs(
        input_paths: list[str],
        output_path: str,
        progress_cb: Callable[[int], None] = None
    ) -> None:
        if len(input_paths) < 2:
            raise ValueError("Merge requires at least 2 PDF files.")

        merged = fitz.open()
        total = len(input_paths)

        for i, path in enumerate(input_paths):
            if not os.path.isfile(path):
                raise RuntimeError(f"File not found: {path}")
            src = fitz.open(path)
            merged.insert_pdf(src)
            src.close()
            if progress_cb:
                progress_cb(int((i + 1) / total * 90))

        merged.save(output_path, garbage=4, deflate=True)
        merged.close()

        if progress_cb:
            progress_cb(100)

    @staticmethod
    def split_pdf(
        input_path: str,
        output_dir: str,
        pages_per_file: int = 1,
        progress_cb: Callable[[int], None] = None
    ) -> None:
        if not os.path.isfile(input_path):
            raise RuntimeError(f"File not found: {input_path}")

        src = fitz.open(input_path)
        total_pages = len(src)
        base_name = os.path.splitext(os.path.basename(input_path))[0]

        chunks = []
        for start in range(0, total_pages, pages_per_file):
            end = min(start + pages_per_file - 1, total_pages - 1)
            chunks.append((start, end))

        for i, (from_p, to_p) in enumerate(chunks):
            chunk = fitz.open()
            chunk.insert_pdf(src, from_page=from_p, to_page=to_p)
            out_path = os.path.join(output_dir, f"{base_name}_{i + 1:03d}.pdf")
            chunk.save(out_path, garbage=4, deflate=True)
            chunk.close()
            if progress_cb:
                progress_cb(int((i + 1) / len(chunks) * 100))

        src.close()

    @staticmethod
    def rotate_pages(
        input_path: str,
        output_path: str,
        rotation: int,
        page_indices: list[int] | None = None,
        progress_cb: Callable[[int], None] = None
    ) -> None:
        """
        Rotate pages in a PDF.

        Args:
            rotation: Degrees to rotate clockwise (90, 180, 270).
            page_indices: 0-based list of pages to rotate. None = all pages.
        """
        if not os.path.isfile(input_path):
            raise RuntimeError(f"File not found: {input_path}")

        doc = fitz.open(input_path)
        pages = page_indices if page_indices is not None else list(range(len(doc)))

        if not pages:
            doc.close()
            raise ValueError("No pages selected.")

        total = len(pages)
        for i, idx in enumerate(pages):
            page = doc[idx]
            page.set_rotation((page.rotation + rotation) % 360)
            if progress_cb:
                progress_cb(int((i + 1) / total * 90))

        doc.save(output_path, garbage=4, deflate=True)
        doc.close()

        if progress_cb:
            progress_cb(100)

    @staticmethod
    def add_image_to_page(
        input_path: str,
        output_path: str,
        image_path: str,
        page_index: int,
        x: float,
        y: float,
        width: float,
        height: float,
        progress_cb: Callable[[int], None] = None
    ) -> None:
        """
        Overlay an image onto a specific page of a PDF.

        Args:
            page_index: 0-based page index.
            x, y, width, height: Position and size in PDF points (72 pts = 1 inch).
        """
        if not os.path.isfile(input_path):
            raise RuntimeError(f"File not found: {input_path}")
        if not os.path.isfile(image_path):
            raise RuntimeError(f"Image not found: {image_path}")

        doc = fitz.open(input_path)
        if page_index < 0 or page_index >= len(doc):
            doc.close()
            raise ValueError(f"Page {page_index + 1} does not exist (document has {len(doc)} pages).")

        page = doc[page_index]
        rect = fitz.Rect(x, y, x + width, y + height)
        page.insert_image(rect, filename=image_path)

        if progress_cb:
            progress_cb(80)

        doc.save(output_path, garbage=4, deflate=True)
        doc.close()

        if progress_cb:
            progress_cb(100)

    @staticmethod
    def page_count(input_path: str) -> int:
        doc = fitz.open(input_path)
        count = len(doc)
        doc.close()
        return count
