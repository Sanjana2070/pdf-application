import os

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTabWidget,
    QWidget, QFileDialog, QRadioButton, QButtonGroup,
    QLineEdit, QDoubleSpinBox, QSpinBox, QFrame
)
from PySide6.QtCore import Qt

from ui.panels.base_panel import BasePanel
from workers.worker import Worker
from services.pdf_service import PdfService, _parse_page_range


class EditPanel(BasePanel):

    _accepted_extensions = {".pdf"}

    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker: Worker | None = None
        # paths for each tab
        self._rotate_path: str = ""
        self._addimg_pdf_path: str = ""
        self._addimg_img_path: str = ""
        self._rotate_page_count: int = 0
        self._addimg_page_count: int = 0
        self._build_ui()
        self._connect_signals()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(12)

        title = QLabel("Edit PDF")
        title.setObjectName("panelTitle")

        self._tabs = QTabWidget()
        self._tabs.addTab(self._build_rotate_tab(), "Rotate Pages")
        self._tabs.addTab(self._build_addimg_tab(), "Add Image")

        layout.addWidget(title)
        layout.addWidget(self._tabs, stretch=1)
        layout.addWidget(self._progress_bar)
        layout.addWidget(self._status_label)

    # ── Rotate tab ───────────────────────────────────────────────────────────

    def _build_rotate_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self._rot_drop_hint = QLabel("Drag & drop a PDF here, or use Select File")
        self._rot_drop_hint.setObjectName("dropHint")
        self._rot_drop_hint.setAlignment(Qt.AlignCenter)

        self._rot_file_label = QLabel("No file selected.")
        self._rot_file_label.setStyleSheet("color: #aaaaaa;")

        self._rot_btn_pick = QPushButton("Select PDF File")
        self._rot_page_info = QLabel("")
        self._rot_page_info.setStyleSheet("color: #888888; font-size: 11px;")

        # Page selection
        sel_layout = QHBoxLayout()
        self._rot_all_radio = QRadioButton("All pages")
        self._rot_sel_radio = QRadioButton("Specific pages:")
        self._rot_all_radio.setChecked(True)
        self._rot_page_group = QButtonGroup()
        self._rot_page_group.addButton(self._rot_all_radio)
        self._rot_page_group.addButton(self._rot_sel_radio)
        self._rot_pages_edit = QLineEdit()
        self._rot_pages_edit.setPlaceholderText("e.g. 1, 3, 5-7")
        self._rot_pages_edit.setEnabled(False)
        sel_layout.addWidget(self._rot_all_radio)
        sel_layout.addWidget(self._rot_sel_radio)
        sel_layout.addWidget(self._rot_pages_edit, stretch=1)

        # Rotation buttons
        rot_layout = QHBoxLayout()
        rot_layout.addWidget(QLabel("Rotate:"))
        self._rot_90cw  = QPushButton("90° Clockwise")
        self._rot_90ccw = QPushButton("90° Counter-CW")
        self._rot_180   = QPushButton("180°")
        rot_layout.addWidget(self._rot_90cw)
        rot_layout.addWidget(self._rot_90ccw)
        rot_layout.addWidget(self._rot_180)
        rot_layout.addStretch()

        self._rot_btn_run = QPushButton("Apply & Save")
        self._rot_btn_run.setObjectName("primaryButton")
        self._rot_btn_run.setEnabled(False)
        self._rot_angle: int = 90  # default, updated when a button is clicked

        layout.addWidget(self._rot_drop_hint)
        layout.addWidget(self._rot_file_label)
        layout.addWidget(self._rot_btn_pick)
        layout.addWidget(self._rot_page_info)
        layout.addLayout(sel_layout)
        layout.addLayout(rot_layout)
        layout.addStretch()
        layout.addWidget(self._rot_btn_run)
        return tab

    # ── Add Image tab ────────────────────────────────────────────────────────

    def _build_addimg_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # PDF selection
        pdf_row = QHBoxLayout()
        self._ai_pdf_label = QLabel("PDF: None")
        self._ai_pdf_label.setStyleSheet("color: #aaaaaa;")
        self._ai_btn_pdf = QPushButton("Select PDF")
        pdf_row.addWidget(self._ai_pdf_label, stretch=1)
        pdf_row.addWidget(self._ai_btn_pdf)

        # Image selection
        img_row = QHBoxLayout()
        self._ai_img_label = QLabel("Image: None")
        self._ai_img_label.setStyleSheet("color: #aaaaaa;")
        self._ai_btn_img = QPushButton("Select Image")
        img_row.addWidget(self._ai_img_label, stretch=1)
        img_row.addWidget(self._ai_btn_img)

        # Page selector
        page_row = QHBoxLayout()
        page_row.addWidget(QLabel("Insert on page:"))
        self._ai_page_spin = QSpinBox()
        self._ai_page_spin.setRange(1, 9999)
        self._ai_page_spin.setValue(1)
        self._ai_page_spin.setFixedWidth(80)
        self._ai_page_count_label = QLabel("")
        self._ai_page_count_label.setStyleSheet("color: #888888; font-size: 11px;")
        page_row.addWidget(self._ai_page_spin)
        page_row.addWidget(self._ai_page_count_label)
        page_row.addStretch()

        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("color: #3a3a3a;")

        pos_hint = QLabel("Position & size (PDF points; 72 pts = 1 inch)")
        pos_hint.setStyleSheet("color: #888888; font-size: 11px;")

        # X, Y row
        xy_row = QHBoxLayout()
        xy_row.addWidget(QLabel("X:"))
        self._ai_x = QDoubleSpinBox()
        self._ai_x.setRange(0, 5000); self._ai_x.setValue(50); self._ai_x.setFixedWidth(80)
        xy_row.addWidget(self._ai_x)
        xy_row.addWidget(QLabel("  Y:"))
        self._ai_y = QDoubleSpinBox()
        self._ai_y.setRange(0, 5000); self._ai_y.setValue(50); self._ai_y.setFixedWidth(80)
        xy_row.addWidget(self._ai_y)
        xy_row.addStretch()

        # Width, Height row
        wh_row = QHBoxLayout()
        wh_row.addWidget(QLabel("Width:"))
        self._ai_w = QDoubleSpinBox()
        self._ai_w.setRange(1, 5000); self._ai_w.setValue(150); self._ai_w.setFixedWidth(80)
        wh_row.addWidget(self._ai_w)
        wh_row.addWidget(QLabel("  Height:"))
        self._ai_h = QDoubleSpinBox()
        self._ai_h.setRange(1, 5000); self._ai_h.setValue(150); self._ai_h.setFixedWidth(80)
        wh_row.addWidget(self._ai_h)
        wh_row.addStretch()

        self._ai_btn_run = QPushButton("Add Image & Save")
        self._ai_btn_run.setObjectName("primaryButton")
        self._ai_btn_run.setEnabled(False)

        layout.addLayout(pdf_row)
        layout.addLayout(img_row)
        layout.addLayout(page_row)
        layout.addWidget(divider)
        layout.addWidget(pos_hint)
        layout.addLayout(xy_row)
        layout.addLayout(wh_row)
        layout.addStretch()
        layout.addWidget(self._ai_btn_run)
        return tab

    # ── Signals ──────────────────────────────────────────────────────────────

    def _connect_signals(self) -> None:
        # Rotate tab
        self._rot_btn_pick.clicked.connect(self._pick_rotate_pdf)
        self._rot_sel_radio.toggled.connect(self._rot_pages_edit.setEnabled)
        self._rot_90cw.clicked.connect(lambda: self._set_rotation(90))
        self._rot_90ccw.clicked.connect(lambda: self._set_rotation(270))
        self._rot_180.clicked.connect(lambda: self._set_rotation(180))
        self._rot_btn_run.clicked.connect(self._run_rotate)

        # Add Image tab
        self._ai_btn_pdf.clicked.connect(self._pick_ai_pdf)
        self._ai_btn_img.clicked.connect(self._pick_ai_img)
        self._ai_btn_run.clicked.connect(self._run_add_image)

    # ── Drag-and-drop ────────────────────────────────────────────────────────

    def handle_dropped_files(self, paths: list[str]) -> None:
        if not paths:
            return
        p = paths[0]
        if self._tabs.currentIndex() == 0:
            self._set_rotate_file(p)
        else:
            self._set_ai_pdf(p)

    # ── Rotate helpers ───────────────────────────────────────────────────────

    def _pick_rotate_pdf(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select PDF", "", "PDF Files (*.pdf)")
        if path:
            self._set_rotate_file(path)

    def _set_rotate_file(self, path: str) -> None:
        self._rotate_path = path
        name = path.replace("\\", "/").split("/")[-1]
        self._rot_file_label.setText(f"Selected: {name}")
        self._rot_file_label.setStyleSheet("color: #ffffff;")
        self._rot_drop_hint.hide()
        try:
            self._rotate_page_count = PdfService.page_count(path)
            self._rot_page_info.setText(f"{self._rotate_page_count} page(s)")
            self._ai_page_spin.setMaximum(self._rotate_page_count)
        except Exception:
            self._rotate_page_count = 0
        self._refresh_rot_run()

    def _set_rotation(self, angle: int) -> None:
        self._rot_angle = angle
        labels = {90: "90° CW", 270: "90° CCW", 180: "180°"}
        self._rot_90cw.setStyleSheet("")
        self._rot_90ccw.setStyleSheet("")
        self._rot_180.setStyleSheet("")
        btn_map = {90: self._rot_90cw, 270: self._rot_90ccw, 180: self._rot_180}
        btn_map[angle].setStyleSheet("background-color: #0078d4; color: #fff;")
        self._refresh_rot_run()

    def _refresh_rot_run(self) -> None:
        self._rot_btn_run.setEnabled(bool(self._rotate_path) and hasattr(self, "_rot_angle"))

    def _run_rotate(self) -> None:
        output, _ = QFileDialog.getSaveFileName(
            self, "Save Rotated PDF", "rotated.pdf", "PDF Files (*.pdf)"
        )
        if not output:
            return
        if not output.lower().endswith(".pdf"):
            output += ".pdf"

        page_indices = None
        if self._rot_sel_radio.isChecked():
            spec = self._rot_pages_edit.text().strip()
            if spec:
                page_indices = _parse_page_range(spec, self._rotate_page_count)
                if not page_indices:
                    self.show_status("No valid pages in the range you entered.", is_error=True)
                    return

        self._set_busy(True)
        self.show_status("")
        self._worker = Worker(
            fn=PdfService.rotate_pages,
            args=(self._rotate_path, output, self._rot_angle, page_indices)
        )
        self._worker.progress.connect(self.set_progress)
        self._worker.finished.connect(self._on_done)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    # ── Add Image helpers ────────────────────────────────────────────────────

    def _pick_ai_pdf(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select PDF", "", "PDF Files (*.pdf)")
        if path:
            self._set_ai_pdf(path)

    def _set_ai_pdf(self, path: str) -> None:
        self._addimg_pdf_path = path
        name = path.replace("\\", "/").split("/")[-1]
        self._ai_pdf_label.setText(f"PDF: {name}")
        self._ai_pdf_label.setStyleSheet("color: #ffffff;")
        try:
            count = PdfService.page_count(path)
            self._ai_page_spin.setMaximum(count)
            self._ai_page_count_label.setText(f"(of {count})")
        except Exception:
            pass
        self._refresh_ai_run()

    def _pick_ai_img(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.tiff *.tif *.webp)"
        )
        if path:
            self._set_ai_image(path)

    def _set_ai_image(self, path: str) -> None:
        self._addimg_img_path = path
        name = path.replace("\\", "/").split("/")[-1]
        self._ai_img_label.setText(f"Image: {name}")
        self._ai_img_label.setStyleSheet("color: #ffffff;")
        self._refresh_ai_run()

    def _refresh_ai_run(self) -> None:
        self._ai_btn_run.setEnabled(
            bool(self._addimg_pdf_path) and bool(self._addimg_img_path)
        )

    def _run_add_image(self) -> None:
        output, _ = QFileDialog.getSaveFileName(
            self, "Save Edited PDF", "edited.pdf", "PDF Files (*.pdf)"
        )
        if not output:
            return
        if not output.lower().endswith(".pdf"):
            output += ".pdf"

        self._set_busy(True)
        self.show_status("")
        self._worker = Worker(
            fn=PdfService.add_image_to_page,
            args=(
                self._addimg_pdf_path,
                output,
                self._addimg_img_path,
                self._ai_page_spin.value() - 1,  # convert to 0-based
                self._ai_x.value(),
                self._ai_y.value(),
                self._ai_w.value(),
                self._ai_h.value(),
            )
        )
        self._worker.progress.connect(self.set_progress)
        self._worker.finished.connect(self._on_done)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    # ── Shared ───────────────────────────────────────────────────────────────

    def _on_done(self, _) -> None:
        self._set_busy(False)
        self.show_status("Done! File saved successfully.")

    def _on_error(self, msg: str) -> None:
        self._set_busy(False)
        self.show_status(f"Error: {msg}", is_error=True)

    def _set_busy(self, busy: bool) -> None:
        for btn in (self._rot_btn_run, self._rot_btn_pick,
                    self._ai_btn_run, self._ai_btn_pdf, self._ai_btn_img):
            btn.setEnabled(not busy)
        if not busy:
            self._refresh_rot_run()
            self._refresh_ai_run()
        self.show_progress(busy)

    def _on_drag_enter_visual(self) -> None:
        self._rot_drop_hint.setStyleSheet(
            "color: #0078d4; border: 2px dashed #0078d4; border-radius: 8px; padding: 40px;"
        )

    def _on_drag_leave_visual(self) -> None:
        self._rot_drop_hint.setStyleSheet("")
