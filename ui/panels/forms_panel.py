import os

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QFileDialog, QHeaderView,
    QAbstractItemView, QComboBox
)
from PySide6.QtCore import Qt

from ui.panels.base_panel import BasePanel
from workers.worker import Worker
from services.forms_service import FormsService


class FormsPanel(BasePanel):

    _accepted_extensions = {".pdf"}

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pdf_path: str = ""
        self._fields: list[dict] = []
        self._worker: Worker | None = None
        self._build_ui()
        self._connect_signals()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(12)

        title = QLabel("PDF Forms")
        title.setObjectName("panelTitle")

        # File selection row
        file_row = QHBoxLayout()
        self._drop_hint = QLabel("Drag & drop a PDF with form fields here, or use Select File")
        self._drop_hint.setObjectName("dropHint")
        self._drop_hint.setAlignment(Qt.AlignCenter)

        file_info_row = QHBoxLayout()
        self._file_label = QLabel("No file selected.")
        self._file_label.setStyleSheet("color: #aaaaaa;")
        self._btn_pick = QPushButton("Select PDF")
        self._btn_pick.setFixedWidth(110)
        self._btn_load = QPushButton("Load Fields")
        self._btn_load.setEnabled(False)
        self._btn_load.setFixedWidth(110)
        file_info_row.addWidget(self._file_label, stretch=1)
        file_info_row.addWidget(self._btn_pick)
        file_info_row.addWidget(self._btn_load)

        self._field_count_label = QLabel("")
        self._field_count_label.setStyleSheet("color: #888888; font-size: 11px;")

        # Fields table
        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(["Page", "Field Name", "Type", "Value"])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.SelectedClicked)
        self._table.setStyleSheet(
            "QTableWidget { border: 1px solid #3a3a3a; border-radius: 4px; }"
            "QTableWidget::item { padding: 4px; }"
            "QHeaderView::section { background-color: #2d2d2d; padding: 6px; border: none; border-bottom: 1px solid #3a3a3a; }"
        )

        self._empty_label = QLabel("Load a PDF to see its form fields here.")
        self._empty_label.setAlignment(Qt.AlignCenter)
        self._empty_label.setStyleSheet("color: #666666; font-size: 13px; padding: 40px;")

        # Save button
        btn_row = QHBoxLayout()
        self._btn_clear = QPushButton("Clear Values")
        self._btn_save = QPushButton("Save Filled PDF")
        self._btn_save.setObjectName("primaryButton")
        self._btn_save.setEnabled(False)
        btn_row.addStretch()
        btn_row.addWidget(self._btn_clear)
        btn_row.addWidget(self._btn_save)

        layout.addWidget(title)
        layout.addWidget(self._drop_hint)
        layout.addLayout(file_info_row)
        layout.addWidget(self._field_count_label)
        layout.addWidget(self._empty_label, stretch=1)
        layout.addWidget(self._table, stretch=1)
        layout.addLayout(btn_row)
        layout.addWidget(self._progress_bar)
        layout.addWidget(self._status_label)

        self._table.hide()

    def _connect_signals(self) -> None:
        self._btn_pick.clicked.connect(self._pick_file)
        self._btn_load.clicked.connect(self._load_fields)
        self._btn_save.clicked.connect(self._save_filled)
        self._btn_clear.clicked.connect(self._clear_values)

    # ── Drag-and-drop ─────────────────────────────────────────────────────────

    def handle_dropped_files(self, paths: list[str]) -> None:
        if paths:
            self._set_file(paths[0])
            self._load_fields()

    def _on_drag_enter_visual(self) -> None:
        self._drop_hint.setStyleSheet(
            "color: #0078d4; border: 2px dashed #0078d4; border-radius: 8px; padding: 40px;"
        )

    def _on_drag_leave_visual(self) -> None:
        self._drop_hint.setStyleSheet("")

    # ── File selection ────────────────────────────────────────────────────────

    def _pick_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select PDF", "", "PDF Files (*.pdf)")
        if path:
            self._set_file(path)

    def _set_file(self, path: str) -> None:
        self._pdf_path = path
        name = path.replace("\\", "/").split("/")[-1]
        self._file_label.setText(f"Selected: {name}")
        self._file_label.setStyleSheet("color: #ffffff;")
        self._drop_hint.hide()
        self._btn_load.setEnabled(True)
        self._fields = []
        self._table.setRowCount(0)
        self._table.hide()
        self._empty_label.show()
        self._field_count_label.setText("")
        self._btn_save.setEnabled(False)
        self.show_status("")

    # ── Load fields ───────────────────────────────────────────────────────────

    def _load_fields(self) -> None:
        if not self._pdf_path:
            return
        self._set_busy(True)
        self.show_status("")
        self._worker = Worker(fn=FormsService.get_fields, args=(self._pdf_path,))
        self._worker.finished.connect(self._on_fields_loaded)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_fields_loaded(self, fields: list) -> None:
        self._set_busy(False)
        self._fields = fields

        if not fields:
            self._table.hide()
            self._empty_label.setText("This PDF has no fillable form fields.")
            self._empty_label.show()
            self._field_count_label.setText("")
            self._btn_save.setEnabled(False)
            self.show_status("No form fields found in this PDF.", is_error=False)
            return

        self._populate_table(fields)

        sig_count = sum(1 for f in fields if f["field_type"] == 7)
        fillable = len(fields) - sig_count
        parts = []
        if fillable:
            parts.append(f"{fillable} fillable field(s)")
        if sig_count:
            parts.append(f"{sig_count} signature field(s)")
        self._field_count_label.setText(", ".join(parts))
        self._btn_save.setEnabled(fillable > 0)

    def _populate_table(self, fields: list[dict]) -> None:
        self._table.blockSignals(True)
        self._table.setRowCount(len(fields))

        for row, field in enumerate(fields):
            # Page — not editable
            page_item = QTableWidgetItem(str(field["page"]))
            page_item.setFlags(page_item.flags() & ~Qt.ItemIsEditable)
            page_item.setTextAlignment(Qt.AlignCenter)

            # Name — not editable
            name_item = QTableWidgetItem(field["name"])
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)

            # Type — not editable
            type_item = QTableWidgetItem(field["type_label"])
            type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
            type_item.setForeground(Qt.gray)

            # Value — editable (unless it's a signature field)
            if field["field_type"] == 7:
                val_item = QTableWidgetItem("(signature field)")
                val_item.setFlags(val_item.flags() & ~Qt.ItemIsEditable)
                val_item.setForeground(Qt.gray)
            elif field["field_type"] == 2:
                # Checkbox — show "Yes" or "No" and make editable
                val_item = QTableWidgetItem(field["value"] or "No")
                val_item.setToolTip('Enter "Yes" or "No"')
            elif field["choices"] and field["field_type"] in (4, 5):
                # Combo/List — still use text item; tooltip shows choices
                val_item = QTableWidgetItem(field["value"])
                val_item.setToolTip("Choices: " + ", ".join(field["choices"]))
            else:
                val_item = QTableWidgetItem(field["value"])

            self._table.setItem(row, 0, page_item)
            self._table.setItem(row, 1, name_item)
            self._table.setItem(row, 2, type_item)
            self._table.setItem(row, 3, val_item)

        self._table.blockSignals(False)
        self._empty_label.hide()
        self._table.show()

    # ── Clear / Save ──────────────────────────────────────────────────────────

    def _clear_values(self) -> None:
        for row in range(self._table.rowCount()):
            val_item = self._table.item(row, 3)
            if val_item and (val_item.flags() & Qt.ItemIsEditable):
                val_item.setText("")

    def _save_filled(self) -> None:
        output, _ = QFileDialog.getSaveFileName(
            self, "Save Filled PDF", "filled.pdf", "PDF Files (*.pdf)"
        )
        if not output:
            return
        if not output.lower().endswith(".pdf"):
            output += ".pdf"

        # Collect current table values
        values: dict[str, str] = {}
        for row in range(self._table.rowCount()):
            name_item = self._table.item(row, 1)
            val_item = self._table.item(row, 3)
            if name_item and val_item and (val_item.flags() & Qt.ItemIsEditable):
                values[name_item.text()] = val_item.text()

        self._set_busy(True)
        self.show_status("")
        self._worker = Worker(
            fn=FormsService.fill_and_save,
            args=(self._pdf_path, output, values)
        )
        self._worker.progress.connect(self.set_progress)
        self._worker.finished.connect(self._on_save_done)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_save_done(self, updated: int) -> None:
        self._set_busy(False)
        self.show_status(f"Saved successfully. {updated} field(s) filled.")

    # ── Shared ────────────────────────────────────────────────────────────────

    def _on_error(self, msg: str) -> None:
        self._set_busy(False)
        self.show_status(f"Error: {msg}", is_error=True)

    def _set_busy(self, busy: bool) -> None:
        self._btn_load.setEnabled(not busy and bool(self._pdf_path))
        self._btn_save.setEnabled(not busy and bool(self._fields))
        self._btn_pick.setEnabled(not busy)
        self.show_progress(busy)
