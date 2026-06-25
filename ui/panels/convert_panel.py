import os

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTabWidget,
    QListWidget, QListWidgetItem, QFileDialog, QAbstractItemView, QWidget
)
from PySide6.QtCore import Qt

from ui.panels.base_panel import BasePanel
from workers.worker import Worker
from services.image_service import ImageService
from services.convert_service import ConvertService


class ConvertPanel(BasePanel):

    _accepted_extensions = {
        ".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp",
        ".pdf", ".docx", ".doc"
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._img_paths: list[str] = []
        self._worker: Worker | None = None
        self._build_ui()
        self._connect_signals()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(12)

        title = QLabel("Convert")
        title.setObjectName("panelTitle")

        self._tabs = QTabWidget()
        self._tabs.addTab(self._build_img_tab(), "Images → PDF")
        self._tabs.addTab(self._build_pdf_word_tab(), "PDF → Word")
        self._tabs.addTab(self._build_word_pdf_tab(), "Word → PDF")

        layout.addWidget(title)
        layout.addWidget(self._tabs, stretch=1)
        layout.addWidget(self._progress_bar)
        layout.addWidget(self._status_label)

    # ── Images → PDF tab ─────────────────────────────────────────────────────

    def _build_img_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        self._drop_hint = QLabel("Drag & drop images here, or use Add Files")
        self._drop_hint.setObjectName("dropHint")
        self._drop_hint.setAlignment(Qt.AlignCenter)

        self._file_list = QListWidget()
        self._file_list.setDragDropMode(QAbstractItemView.InternalMove)
        self._file_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self._file_list.hide()

        btn_row = QHBoxLayout()
        self._btn_add = QPushButton("Add Files")
        self._btn_remove = QPushButton("Remove Selected")
        self._btn_clear = QPushButton("Clear All")
        btn_row.addWidget(self._btn_add)
        btn_row.addWidget(self._btn_remove)
        btn_row.addWidget(self._btn_clear)
        btn_row.addStretch()

        self._btn_convert = QPushButton("Convert to PDF")
        self._btn_convert.setObjectName("primaryButton")
        self._btn_convert.setEnabled(False)

        layout.addWidget(self._drop_hint)
        layout.addWidget(self._file_list, stretch=1)
        layout.addLayout(btn_row)
        layout.addWidget(self._btn_convert)
        return tab

    # ── PDF → Word tab ────────────────────────────────────────────────────────

    def _build_pdf_word_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self._pw_drop_hint = QLabel("Drag & drop a PDF here, or use Select File")
        self._pw_drop_hint.setObjectName("dropHint")
        self._pw_drop_hint.setAlignment(Qt.AlignCenter)

        self._pw_file_label = QLabel("No file selected.")
        self._pw_file_label.setStyleSheet("color: #aaaaaa;")

        self._pw_btn_pick = QPushButton("Select PDF File")

        note = QLabel("Converts PDF text and layout to an editable .docx file.")
        note.setStyleSheet("color: #888888; font-size: 11px;")
        note.setWordWrap(True)

        self._pw_btn_run = QPushButton("Convert to Word")
        self._pw_btn_run.setObjectName("primaryButton")
        self._pw_btn_run.setEnabled(False)

        layout.addWidget(self._pw_drop_hint)
        layout.addWidget(self._pw_file_label)
        layout.addWidget(self._pw_btn_pick)
        layout.addWidget(note)
        layout.addStretch()
        layout.addWidget(self._pw_btn_run)
        return tab

    # ── Word → PDF tab ────────────────────────────────────────────────────────

    def _build_word_pdf_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        if not ConvertService.libreoffice_available():
            msg = QLabel(
                "LibreOffice is not installed.\n\n"
                "Download from https://www.libreoffice.org/ and install it, "
                "then restart the app to enable Word → PDF conversion."
            )
            msg.setStyleSheet("color: #e07050; padding: 16px;")
            msg.setWordWrap(True)
            layout.addWidget(msg)
            layout.addStretch()
            self._wp_drop_hint = QLabel()
            self._wp_file_label = QLabel()
            self._wp_btn_pick = QPushButton()
            self._wp_btn_run = QPushButton()
            return tab

        self._wp_drop_hint = QLabel("Drag & drop a .docx / .doc file here, or use Select File")
        self._wp_drop_hint.setObjectName("dropHint")
        self._wp_drop_hint.setAlignment(Qt.AlignCenter)

        self._wp_file_label = QLabel("No file selected.")
        self._wp_file_label.setStyleSheet("color: #aaaaaa;")

        self._wp_btn_pick = QPushButton("Select Word File")

        note = QLabel("Uses LibreOffice to produce a faithful PDF from your .docx / .doc.")
        note.setStyleSheet("color: #888888; font-size: 11px;")
        note.setWordWrap(True)

        self._wp_btn_run = QPushButton("Convert to PDF")
        self._wp_btn_run.setObjectName("primaryButton")
        self._wp_btn_run.setEnabled(False)

        layout.addWidget(self._wp_drop_hint)
        layout.addWidget(self._wp_file_label)
        layout.addWidget(self._wp_btn_pick)
        layout.addWidget(note)
        layout.addStretch()
        layout.addWidget(self._wp_btn_run)
        return tab

    # ── Signals ───────────────────────────────────────────────────────────────

    def _connect_signals(self) -> None:
        # Images → PDF
        self._btn_add.clicked.connect(self._pick_files)
        self._btn_remove.clicked.connect(self._remove_selected)
        self._btn_clear.clicked.connect(self._clear_files)
        self._btn_convert.clicked.connect(self._start_img_convert)
        self._file_list.model().rowsMoved.connect(self._sync_paths_from_list)

        # PDF → Word
        self._pw_btn_pick.clicked.connect(self._pick_pdf)
        self._pw_btn_run.clicked.connect(self._run_pdf_to_word)

        # Word → PDF
        self._wp_btn_pick.clicked.connect(self._pick_word)
        self._wp_btn_run.clicked.connect(self._run_word_to_pdf)

    # ── Drag-and-drop routing ──────────────────────────────────────────────────

    def handle_dropped_files(self, paths: list[str]) -> None:
        if not paths:
            return
        ext = os.path.splitext(paths[0])[1].lower()
        if ext == ".pdf":
            self._tabs.setCurrentIndex(1)
            self._set_pw_file(paths[0])
        elif ext in {".docx", ".doc"}:
            self._tabs.setCurrentIndex(2)
            self._set_wp_file(paths[0])
        else:
            self._tabs.setCurrentIndex(0)
            self._add_files(paths)

    # ── Images → PDF helpers ──────────────────────────────────────────────────

    def _pick_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Select Images", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.tiff *.tif *.webp)"
        )
        if paths:
            self._add_files(paths)

    def _add_files(self, paths: list[str]) -> None:
        for p in paths:
            if p not in self._img_paths:
                self._img_paths.append(p)
                name = p.replace("\\", "/").split("/")[-1]
                item = QListWidgetItem(name)
                item.setData(Qt.UserRole, p)
                self._file_list.addItem(item)
        self._refresh_img_state()

    def _remove_selected(self) -> None:
        for item in reversed(self._file_list.selectedItems()):
            self._file_list.takeItem(self._file_list.row(item))
        self._sync_paths_from_list()

    def _clear_files(self) -> None:
        self._file_list.clear()
        self._img_paths.clear()
        self._refresh_img_state()

    def _sync_paths_from_list(self) -> None:
        self._img_paths = [
            self._file_list.item(i).data(Qt.UserRole)
            for i in range(self._file_list.count())
        ]
        self._refresh_img_state()

    def _refresh_img_state(self) -> None:
        has = bool(self._img_paths)
        self._drop_hint.setVisible(not has)
        self._file_list.setVisible(has)
        self._btn_convert.setEnabled(has)

    def _start_img_convert(self) -> None:
        output, _ = QFileDialog.getSaveFileName(
            self, "Save PDF As", "output.pdf", "PDF Files (*.pdf)"
        )
        if not output:
            return
        if not output.lower().endswith(".pdf"):
            output += ".pdf"
        self._set_busy(True)
        self.show_status("")
        self._worker = Worker(ImageService.images_to_pdf, args=(list(self._img_paths), output))
        self._worker.progress.connect(self.set_progress)
        self._worker.finished.connect(lambda _: (self._set_busy(False), self.show_status("PDF created successfully.")))
        self._worker.error.connect(self._on_error)
        self._worker.start()

    # ── PDF → Word helpers ────────────────────────────────────────────────────

    def _pick_pdf(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select PDF", "", "PDF Files (*.pdf)")
        if path:
            self._set_pw_file(path)

    def _set_pw_file(self, path: str) -> None:
        self._pw_path = path
        name = path.replace("\\", "/").split("/")[-1]
        self._pw_file_label.setText(f"Selected: {name}")
        self._pw_file_label.setStyleSheet("color: #ffffff;")
        self._pw_drop_hint.hide()
        self._pw_btn_run.setEnabled(True)

    def _run_pdf_to_word(self) -> None:
        base = os.path.splitext(os.path.basename(self._pw_path))[0]
        output, _ = QFileDialog.getSaveFileName(
            self, "Save Word File As", f"{base}.docx", "Word Document (*.docx)"
        )
        if not output:
            return
        if not output.lower().endswith(".docx"):
            output += ".docx"
        self._set_busy(True)
        self.show_status("Converting — this may take a moment for large PDFs…")
        self._worker = Worker(ConvertService.pdf_to_word, args=(self._pw_path, output))
        self._worker.progress.connect(self.set_progress)
        self._worker.finished.connect(lambda _: (self._set_busy(False), self.show_status("Word document saved.")))
        self._worker.error.connect(self._on_error)
        self._worker.start()

    # ── Word → PDF helpers ────────────────────────────────────────────────────

    def _pick_word(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Word File", "", "Word Documents (*.docx *.doc)"
        )
        if path:
            self._set_wp_file(path)

    def _set_wp_file(self, path: str) -> None:
        self._wp_path = path
        name = path.replace("\\", "/").split("/")[-1]
        self._wp_file_label.setText(f"Selected: {name}")
        self._wp_file_label.setStyleSheet("color: #ffffff;")
        self._wp_drop_hint.hide()
        self._wp_btn_run.setEnabled(True)

    def _run_word_to_pdf(self) -> None:
        base = os.path.splitext(os.path.basename(self._wp_path))[0]
        output, _ = QFileDialog.getSaveFileName(
            self, "Save PDF As", f"{base}.pdf", "PDF Files (*.pdf)"
        )
        if not output:
            return
        if not output.lower().endswith(".pdf"):
            output += ".pdf"
        self._set_busy(True)
        self.show_status("Converting via LibreOffice…")
        self._worker = Worker(ConvertService.word_to_pdf, args=(self._wp_path, output))
        self._worker.progress.connect(self.set_progress)
        self._worker.finished.connect(lambda _: (self._set_busy(False), self.show_status("PDF saved.")))
        self._worker.error.connect(self._on_error)
        self._worker.start()

    # ── Shared ────────────────────────────────────────────────────────────────

    def _on_error(self, msg: str) -> None:
        self._set_busy(False)
        self.show_status(f"Error: {msg}", is_error=True)

    def _set_busy(self, busy: bool) -> None:
        for btn in (self._btn_convert, self._btn_add, self._pw_btn_run,
                    self._pw_btn_pick, self._wp_btn_run, self._wp_btn_pick):
            btn.setEnabled(not busy)
        if not busy:
            self._btn_convert.setEnabled(bool(self._img_paths))
            self._pw_btn_run.setEnabled(hasattr(self, "_pw_path"))
            self._wp_btn_run.setEnabled(hasattr(self, "_wp_path"))
        self.show_progress(busy)

    def _on_drag_enter_visual(self) -> None:
        self._drop_hint.setStyleSheet(
            "color: #0078d4; border: 2px dashed #0078d4; border-radius: 8px; padding: 40px;"
        )

    def _on_drag_leave_visual(self) -> None:
        self._drop_hint.setStyleSheet("")
