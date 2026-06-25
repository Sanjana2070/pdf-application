import os
import shutil
import subprocess
from typing import Callable

import pikepdf
from PIL import Image


class CompressService:

    # ── PDF ──────────────────────────────────────────────────────────────────

    @staticmethod
    def compress_pdf(
        input_path: str,
        output_path: str,
        level: str = "medium",
        progress_cb: Callable[[int], None] = None
    ) -> dict:
        """
        Compress a PDF file.

        Args:
            level: "low" | "medium" | "high"
                   "high" uses Ghostscript if available, falls back to medium.

        Returns:
            dict with "input_size" and "output_size" in bytes.
        """
        if not os.path.isfile(input_path):
            raise RuntimeError(f"File not found: {input_path}")

        if progress_cb:
            progress_cb(10)

        if level == "high":
            gs = (
                shutil.which("gswin64c")
                or shutil.which("gswin32c")
                or shutil.which("gs")
            )
            if gs:
                CompressService._ghostscript_compress(gs, input_path, output_path, "screen")
                if progress_cb:
                    progress_cb(100)
                return CompressService._size_result(input_path, output_path)

        # pikepdf for low / medium (and high fallback)
        with pikepdf.open(input_path) as pdf:
            if level == "low":
                pdf.save(output_path, optimize_streams=True)
            else:
                # medium or high-fallback: recompress + remove unreferenced objects
                pdf.save(
                    output_path,
                    optimize_streams=True,
                    compress_streams=True,
                    object_stream_mode=pikepdf.ObjectStreamMode.generate,
                )

        if progress_cb:
            progress_cb(100)
        return CompressService._size_result(input_path, output_path)

    @staticmethod
    def _ghostscript_compress(gs: str, input_path: str, output_path: str, quality: str) -> None:
        """quality: 'screen' | 'ebook' | 'printer' | 'prepress'"""
        cmd = [
            gs,
            "-sDEVICE=pdfwrite",
            "-dCompatibilityLevel=1.4",
            f"-dPDFSETTINGS=/{quality}",
            "-dNOPAUSE",
            "-dQUIET",
            "-dBATCH",
            f"-sOutputFile={output_path}",
            input_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Ghostscript error: {result.stderr.strip()}")

    # ── Image ────────────────────────────────────────────────────────────────

    @staticmethod
    def compress_image(
        input_path: str,
        output_path: str,
        quality: int = 75,
        progress_cb: Callable[[int], None] = None
    ) -> dict:
        """
        Compress a single image.

        Args:
            quality: 1–95. For JPEG this is the JPEG quality value.
                     For PNG, quality controls the zlib compression effort (0–9 mapped).

        Returns:
            dict with "input_size" and "output_size" in bytes.
        """
        if not os.path.isfile(input_path):
            raise RuntimeError(f"File not found: {input_path}")

        img = Image.open(input_path)
        ext = os.path.splitext(output_path)[1].lower()

        if ext in (".jpg", ".jpeg"):
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.save(output_path, "JPEG", optimize=True, quality=quality)
        elif ext == ".png":
            img.save(output_path, "PNG", optimize=True)
        elif ext == ".webp":
            img.save(output_path, "WEBP", quality=quality, method=6)
        else:
            # Default: save in original format with quality
            save_kwargs = {"optimize": True}
            if img.format in ("JPEG", "WEBP"):
                save_kwargs["quality"] = quality
            img.save(output_path, **save_kwargs)

        if progress_cb:
            progress_cb(100)
        return CompressService._size_result(input_path, output_path)

    # ── Video ────────────────────────────────────────────────────────────────

    @staticmethod
    def compress_video(
        input_path: str,
        output_path: str,
        crf: int = 28,
        progress_cb: Callable[[int], None] = None
    ) -> dict:
        """
        Compress a video using FFmpeg (H.264, libx264).

        Args:
            crf: Constant Rate Factor, 18 (near-lossless) – 51 (worst). Default 28.

        Raises:
            RuntimeError: If FFmpeg is not found on PATH.
        """
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            raise RuntimeError(
                "FFmpeg not found. Download it from https://ffmpeg.org/download.html "
                "and add it to your system PATH."
            )
        if not os.path.isfile(input_path):
            raise RuntimeError(f"File not found: {input_path}")

        if progress_cb:
            progress_cb(5)

        cmd = [
            ffmpeg, "-i", input_path,
            "-vcodec", "libx264",
            "-crf", str(crf),
            "-preset", "medium",
            "-acodec", "aac",
            "-y",
            output_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg error:\n{result.stderr[-500:]}")

        if progress_cb:
            progress_cb(100)
        return CompressService._size_result(input_path, output_path)

    # ── Helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _size_result(input_path: str, output_path: str) -> dict:
        in_size = os.path.getsize(input_path)
        out_size = os.path.getsize(output_path)
        return {"input_size": in_size, "output_size": out_size}

    @staticmethod
    def ffmpeg_available() -> bool:
        return bool(
            shutil.which("ffmpeg")
        )

    @staticmethod
    def ghostscript_available() -> bool:
        return bool(
            shutil.which("gswin64c")
            or shutil.which("gswin32c")
            or shutil.which("gs")
        )
