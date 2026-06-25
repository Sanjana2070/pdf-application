import os

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTabWidget,
    QWidget, QFileDialog, QComboBox, QSlider, QSpinBox
)
from PySide6.QtCore import Qt

from ui.panels.base_panel import BasePanel
from workers.worker import Worker
from services.compress_service import CompressService


def _fmt_size(size_bytes: int) -> str:
    if size_bytes >= 1_048_576:
        return f"{size_bytes / 1_048_576:.1f} MB"
    return f"{size_bytes / 1024:.1f} KB"


class CompressPanel(BasePanel):

    _accepted_extensions = {
        ".pdf", ".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp",
        ".mp4", ".avi", ".mov", ".mkv", ".wmv"
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker: Worker | None = None
        self._build_ui()
        self._connect_signals()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(12)

        title = QLabel("Compress")
        title.setObjectName("panelTitle")

        self._tabs = QTabWidget()
        self._tabs.addTab(self._build_pdf_tab(), "PDF")
        self._tabs.addTab(self._build_image_tab(), "Image")
        self._tabs.addTab(self._build_video_tab(), "Video")

        layout.addWidget(title)
        layout.addWidget(self._tabs, stretch=1)
        layout.addWidget(self._progress_bar)
        layout.addWidget(self._status_label)

    # ── PDF tab ──────────────────────────────────────────────────────────────

    def _build_pdf_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self._pdf_drop_hint = QLabel("Drag & drop a PDF here, or use Select File")
        self._pdf_drop_hint.setObjectName("dropHint")
        self._pdf_drop_hint.setAlignment(Qt.AlignCenter)

        self._pdf_file_label = QLabel("No file selected.")
        self._pdf_file_label.setStyleSheet("color: #aaaaaa;")

        self._pdf_btn_pick = QPushButton("Select PDF File")

        level_row = QHBoxLayout()
        level_row.addWidget(QLabel("Compression level:"))
        self._pdf_level = QComboBox()
        self._pdf_level.addItems(["Low (fast, slight reduction)", "Medium (balanced)", "High (Ghostscript, max compression)"])
        self._pdf_level.setCurrentIndex(1)
        level_row.addWidget(self._pdf_level, stretch=1)

        self._pdf_gs_note = QLabel("")
        self._pdf_gs_note.setStyleSheet("color: #aaaaaa; font-size: 11px;")
        self._pdf_gs_note.setWordWrap(True)
        if not CompressService.ghostscript_available():
            self._pdf_gs_note.setText(
                "Ghostscript not found — High level will fall back to Medium. "
                "Install Ghostscript to enable maximum compression."
            )

        self._pdf_btn_run = QPushButton("Compress PDF")
        self._pdf_btn_run.setObjectName("primaryButton")
        self._pdf_btn_run.setEnabled(False)

        layout.addWidget(self._pdf_drop_hint)
        layout.addWidget(self._pdf_file_label)
        layout.addWidget(self._pdf_btn_pick)
        layout.addLayout(level_row)
        layout.addWidget(self._pdf_gs_note)
        layout.addStretch()
        layout.addWidget(self._pdf_btn_run)
        return tab

    # ── Image tab ────────────────────────────────────────────────────────────

    def _build_image_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self._img_drop_hint = QLabel("Drag & drop an image here, or use Select File")
        self._img_drop_hint.setObjectName("dropHint")
        self._img_drop_hint.setAlignment(Qt.AlignCenter)

        self._img_file_label = QLabel("No file selected.")
        self._img_file_label.setStyleSheet("color: #aaaaaa;")

        self._img_btn_pick = QPushButton("Select Image File")

        quality_row = QHBoxLayout()
        quality_row.addWidget(QLabel("Quality:"))
        self._img_quality_slider = QSlider(Qt.Horizontal)
        self._img_quality_slider.setRange(1, 95)
        self._img_quality_slider.setValue(75)
        self._img_quality_val = QLabel("75")
        self._img_quality_val.setFixedWidth(30)
        quality_row.addWidget(self._img_quality_slider, stretch=1)
        quality_row.addWidget(self._img_quality_val)

        format_row = QHBoxLayout()
        format_row.addWidget(QLabel("Output format:"))
        self._img_format = QComboBox()
        self._img_format.addItems(["Same as input", "JPEG", "PNG", "WebP"])
        format_row.addWidget(self._img_format, stretch=1)

        self._img_btn_run = QPushButton("Compress Image")
        self._img_btn_run.setObjectName("primaryButton")
        self._img_btn_run.setEnabled(False)

        layout.addWidget(self._img_drop_hint)
        layout.addWidget(self._img_file_label)
        layout.addWidget(self._img_btn_pick)
        layout.addLayout(quality_row)
        layout.addLayout(format_row)
        layout.addStretch()
        layout.addWidget(self._img_btn_run)
        return tab

    # ── Video tab ────────────────────────────────────────────────────────────

    def _build_video_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        if not CompressService.ffmpeg_available():
            note = QLabel(
                "FFmpeg is not installed or not on PATH.\n\n"
                "Download from https://ffmpeg.org/download.html and add to system PATH, "
                "then restart the app."
            )
            note.setStyleSheet("color: #e07050; padding: 16px;")
            note.setWordWrap(True)
            layout.addWidget(note)
            layout.addStretch()
            self._vid_drop_hint = QLabel()
            self._vid_file_label = QLabel()
            self._vid_btn_pick = QPushButton()
            self._vid_crf_slider = QSlider()
            self._vid_crf_val = QLabel()
            self._vid_btn_run = QPushButton()
            return tab

        self._vid_drop_hint = QLabel("Drag & drop a video here, or use Select File")
        self._vid_drop_hint.setObjectName("dropHint")
        self._vid_drop_hint.setAlignment(Qt.AlignCenter)

        self._vid_file_label = QLabel("No file selected.")
        self._vid_file_label.setStyleSheet("color: #aaaaaa;")

        self._vid_btn_pick = QPushButton("Select Video File")

        crf_row = QHBoxLayout()
        crf_row.addWidget(QLabel("Quality (CRF):"))
        self._vid_crf_slider = QSlider(Qt.Horizontal)
        self._vid_crf_slider.setRange(18, 51)
        self._vid_crf_slider.setValue(28)
        self._vid_crf_val = QLabel("28")
        self._vid_crf_val.setFixedWidth(30)
        crf_row.addWidget(self._vid_crf_slider, stretch=1)
        crf_row.addWidget(self._vid_crf_val)

        crf_hint = QLabel("18 = near-lossless (large file)  ·  28 = balanced  ·  51 = smallest file (low quality)")
        crf_hint.setStyleSheet("color: #888888; font-size: 11px;")

        self._vid_btn_run = QPushButton("Compress Video")
        self._vid_btn_run.setObjectName("primaryButton")
        self._vid_btn_run.setEnabled(False)

        layout.addWidget(self._vid_drop_hint)
        layout.addWidget(self._vid_file_label)
        layout.addWidget(self._vid_btn_pick)
        layout.addLayout(crf_row)
        layout.addWidget(crf_hint)
        layout.addStretch()
        layout.addWidget(self._vid_btn_run)
        return tab

    # ── Signal wiring ────────────────────────────────────────────────────────

    def _connect_signals(self) -> None:
        self._pdf_btn_pick.clicked.connect(self._pick_pdf)
        self._pdf_btn_run.clicked.connect(self._run_pdf)

        self._img_btn_pick.clicked.connect(self._pick_image)
        self._img_quality_slider.valueChanged.connect(
            lambda v: self._img_quality_val.setText(str(v))
        )
        self._img_btn_run.clicked.connect(self._run_image)

        self._vid_btn_pick.clicked.connect(self._pick_video)
        if CompressService.ffmpeg_available():
            self._vid_crf_slider.valueChanged.connect(
                lambda v: self._vid_crf_val.setText(str(v))
            )
            self._vid_btn_run.clicked.connect(self._run_video)

    # ── Drag-and-drop routing ────────────────────────────────────────────────

    def handle_dropped_files(self, paths: list[str]) -> None:
        if not paths:
            return
        p = paths[0]
        ext = os.path.splitext(p)[1].lower()
        if ext == ".pdf":
            self._tabs.setCurrentIndex(0)
            self._set_pdf_file(p)
        elif ext in {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp"}:
            self._tabs.setCurrentIndex(1)
            self._set_image_file(p)
        else:
            self._tabs.setCurrentIndex(2)
            self._set_video_file(p)

    # ── PDF helpers ──────────────────────────────────────────────────────────

    def _pick_pdf(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select PDF", "", "PDF Files (*.pdf)")
        if path:
            self._set_pdf_file(path)

    def _set_pdf_file(self, path: str) -> None:
        self._pdf_path = path
        name = path.replace("\\", "/").split("/")[-1]
        self._pdf_file_label.setText(f"Selected: {name}")
        self._pdf_file_label.setStyleSheet("color: #ffffff;")
        self._pdf_drop_hint.hide()
        self._pdf_btn_run.setEnabled(True)

    def _run_pdf(self) -> None:
        output, _ = QFileDialog.getSaveFileName(
            self, "Save Compressed PDF", "compressed.pdf", "PDF Files (*.pdf)"
        )
        if not output:
            return
        if not output.lower().endswith(".pdf"):
            output += ".pdf"

        level_map = {0: "low", 1: "medium", 2: "high"}
        level = level_map[self._pdf_level.currentIndex()]

        self._set_busy(True)
        self.show_status("")
        self._worker = Worker(
            fn=CompressService.compress_pdf,
            args=(self._pdf_path, output, level)
        )
        self._worker.progress.connect(self.set_progress)
        self._worker.finished.connect(self._on_pdf_done)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_pdf_done(self, result: dict) -> None:
        self._set_busy(False)
        saved = result["input_size"] - result["output_size"]
        pct = saved / result["input_size"] * 100 if result["input_size"] else 0
        self.show_status(
            f"Done. {_fmt_size(result['input_size'])} → {_fmt_size(result['output_size'])} "
            f"({pct:.1f}% reduction)"
        )

    # ── Image helpers ────────────────────────────────────────────────────────

    def _pick_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.tiff *.tif *.webp)"
        )
        if path:
            self._set_image_file(path)

    def _set_image_file(self, path: str) -> None:
        self._img_path = path
        name = path.replace("\\", "/").split("/")[-1]
        self._img_file_label.setText(f"Selected: {name}")
        self._img_file_label.setStyleSheet("color: #ffffff;")
        self._img_drop_hint.hide()
        self._img_btn_run.setEnabled(True)

    def _run_image(self) -> None:
        fmt_map = {0: None, 1: ".jpg", 2: ".png", 3: ".webp"}
        chosen_ext = fmt_map[self._img_format.currentIndex()]

        src_ext = os.path.splitext(self._img_path)[1].lower()
        out_ext = chosen_ext or src_ext
        filter_str = f"Image (*{out_ext})"
        base = os.path.splitext(os.path.basename(self._img_path))[0]

        output, _ = QFileDialog.getSaveFileName(
            self, "Save Compressed Image", f"{base}_compressed{out_ext}", filter_str
        )
        if not output:
            return

        self._set_busy(True)
        self.show_status("")
        self._worker = Worker(
            fn=CompressService.compress_image,
            args=(self._img_path, output, self._img_quality_slider.value())
        )
        self._worker.progress.connect(self.set_progress)
        self._worker.finished.connect(self._on_img_done)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_img_done(self, result: dict) -> None:
        self._set_busy(False)
        saved = result["input_size"] - result["output_size"]
        pct = saved / result["input_size"] * 100 if result["input_size"] else 0
        self.show_status(
            f"Done. {_fmt_size(result['input_size'])} → {_fmt_size(result['output_size'])} "
            f"({pct:.1f}% reduction)"
        )

    # ── Video helpers ────────────────────────────────────────────────────────

    def _pick_video(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Video", "",
            "Videos (*.mp4 *.avi *.mov *.mkv *.wmv)"
        )
        if path:
            self._set_video_file(path)

    def _set_video_file(self, path: str) -> None:
        self._vid_path = path
        name = path.replace("\\", "/").split("/")[-1]
        self._vid_file_label.setText(f"Selected: {name}")
        self._vid_file_label.setStyleSheet("color: #ffffff;")
        self._vid_drop_hint.hide()
        self._vid_btn_run.setEnabled(True)

    def _run_video(self) -> None:
        base = os.path.splitext(os.path.basename(self._vid_path))[0]
        output, _ = QFileDialog.getSaveFileName(
            self, "Save Compressed Video", f"{base}_compressed.mp4", "MP4 (*.mp4)"
        )
        if not output:
            return

        self._set_busy(True)
        self.show_status("Compressing video — this may take a while...")
        self._worker = Worker(
            fn=CompressService.compress_video,
            args=(self._vid_path, output, self._vid_crf_slider.value())
        )
        self._worker.progress.connect(self.set_progress)
        self._worker.finished.connect(self._on_vid_done)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_vid_done(self, result: dict) -> None:
        self._set_busy(False)
        saved = result["input_size"] - result["output_size"]
        pct = saved / result["input_size"] * 100 if result["input_size"] else 0
        self.show_status(
            f"Done. {_fmt_size(result['input_size'])} → {_fmt_size(result['output_size'])} "
            f"({pct:.1f}% reduction)"
        )

    # ── Shared helpers ───────────────────────────────────────────────────────

    def _on_error(self, msg: str) -> None:
        self._set_busy(False)
        self.show_status(f"Error: {msg}", is_error=True)

    def _set_busy(self, busy: bool) -> None:
        for btn in (self._pdf_btn_run, self._img_btn_run, self._vid_btn_run,
                    self._pdf_btn_pick, self._img_btn_pick, self._vid_btn_pick):
            btn.setEnabled(not busy)
        if not busy:
            # re-enable run buttons only if a file is selected
            self._pdf_btn_run.setEnabled(hasattr(self, "_pdf_path"))
            self._img_btn_run.setEnabled(hasattr(self, "_img_path"))
            self._vid_btn_run.setEnabled(hasattr(self, "_vid_path"))
        self.show_progress(busy)

    def _on_drag_enter_visual(self) -> None:
        tab = self._tabs.currentIndex()
        hints = [self._pdf_drop_hint, self._img_drop_hint, self._vid_drop_hint]
        hints[tab].setStyleSheet(
            "color: #0078d4; border: 2px dashed #0078d4; border-radius: 8px; padding: 40px;"
        )

    def _on_drag_leave_visual(self) -> None:
        for h in (self._pdf_drop_hint, self._img_drop_hint, self._vid_drop_hint):
            h.setStyleSheet("")
