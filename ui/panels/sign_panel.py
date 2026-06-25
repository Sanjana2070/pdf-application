import os

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTabWidget,
    QWidget, QFileDialog, QLineEdit, QTextEdit, QFormLayout, QFrame
)
from PySide6.QtCore import Qt

from ui.panels.base_panel import BasePanel
from workers.worker import Worker
from services.sign_service import SignService


class SignPanel(BasePanel):

    _accepted_extensions = {".pdf", ".pfx", ".p12"}

    def __init__(self, parent=None):
        super().__init__(parent)
        self._sign_pdf_path: str = ""
        self._pfx_path: str = ""
        self._verify_path: str = ""
        self._worker: Worker | None = None
        self._build_ui()
        self._connect_signals()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(12)

        title = QLabel("Digital Signatures")
        title.setObjectName("panelTitle")

        self._tabs = QTabWidget()
        self._tabs.addTab(self._build_sign_tab(), "Sign PDF")
        self._tabs.addTab(self._build_verify_tab(), "Inspect Signatures")
        self._tabs.addTab(self._build_cert_tab(), "Generate Test Certificate")

        layout.addWidget(title)
        layout.addWidget(self._tabs, stretch=1)
        layout.addWidget(self._progress_bar)
        layout.addWidget(self._status_label)

    # ── Sign tab ──────────────────────────────────────────────────────────────

    def _build_sign_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        self._sign_drop_hint = QLabel("Drag & drop a PDF here, or use Select File")
        self._sign_drop_hint.setObjectName("dropHint")
        self._sign_drop_hint.setAlignment(Qt.AlignCenter)

        # PDF row
        pdf_row = QHBoxLayout()
        self._sign_pdf_label = QLabel("PDF: None")
        self._sign_pdf_label.setStyleSheet("color: #aaaaaa;")
        self._sign_btn_pdf = QPushButton("Select PDF")
        self._sign_btn_pdf.setFixedWidth(110)
        pdf_row.addWidget(self._sign_pdf_label, stretch=1)
        pdf_row.addWidget(self._sign_btn_pdf)

        # PFX row
        pfx_row = QHBoxLayout()
        self._pfx_label = QLabel("Certificate (.pfx): None")
        self._pfx_label.setStyleSheet("color: #aaaaaa;")
        self._btn_pfx = QPushButton("Select .pfx")
        self._btn_pfx.setFixedWidth(110)
        pfx_row.addWidget(self._pfx_label, stretch=1)
        pfx_row.addWidget(self._btn_pfx)

        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("color: #3a3a3a;")

        # Signature metadata form
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setSpacing(8)

        self._pw_edit = QLineEdit()
        self._pw_edit.setPlaceholderText("Certificate password (leave blank if none)")
        self._pw_edit.setEchoMode(QLineEdit.Password)

        self._reason_edit = QLineEdit()
        self._reason_edit.setPlaceholderText("e.g. I approve this document")

        self._location_edit = QLineEdit()
        self._location_edit.setPlaceholderText("e.g. New York, USA")

        self._contact_edit = QLineEdit()
        self._contact_edit.setPlaceholderText("e.g. name@example.com")

        form.addRow("Password:", self._pw_edit)
        form.addRow("Reason:", self._reason_edit)
        form.addRow("Location:", self._location_edit)
        form.addRow("Contact:", self._contact_edit)

        note = QLabel(
            "The signature is embedded invisibly as an incremental update — "
            "the original content is preserved."
        )
        note.setStyleSheet("color: #888888; font-size: 11px;")
        note.setWordWrap(True)

        self._sign_btn_run = QPushButton("Sign & Save PDF")
        self._sign_btn_run.setObjectName("primaryButton")
        self._sign_btn_run.setEnabled(False)

        layout.addWidget(self._sign_drop_hint)
        layout.addLayout(pdf_row)
        layout.addLayout(pfx_row)
        layout.addWidget(divider)
        layout.addLayout(form)
        layout.addWidget(note)
        layout.addStretch()
        layout.addWidget(self._sign_btn_run)
        return tab

    # ── Verify tab ────────────────────────────────────────────────────────────

    def _build_verify_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        self._ver_drop_hint = QLabel("Drag & drop a PDF here, or use Select File")
        self._ver_drop_hint.setObjectName("dropHint")
        self._ver_drop_hint.setAlignment(Qt.AlignCenter)

        ver_row = QHBoxLayout()
        self._ver_label = QLabel("PDF: None")
        self._ver_label.setStyleSheet("color: #aaaaaa;")
        self._ver_btn_pdf = QPushButton("Select PDF")
        self._ver_btn_pdf.setFixedWidth(110)
        self._ver_btn_run = QPushButton("Inspect")
        self._ver_btn_run.setEnabled(False)
        ver_row.addWidget(self._ver_label, stretch=1)
        ver_row.addWidget(self._ver_btn_pdf)
        ver_row.addWidget(self._ver_btn_run)

        self._ver_output = QTextEdit()
        self._ver_output.setReadOnly(True)
        self._ver_output.setPlaceholderText("Signature information will appear here.")
        self._ver_output.setStyleSheet(
            "QTextEdit { background-color: #1e1e1e; border: 1px solid #3a3a3a; "
            "border-radius: 4px; padding: 8px; color: #cccccc; font-family: 'Consolas'; }"
        )

        layout.addWidget(self._ver_drop_hint)
        layout.addLayout(ver_row)
        layout.addWidget(self._ver_output, stretch=1)
        return tab

    # ── Generate certificate tab ──────────────────────────────────────────────

    def _build_cert_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        info = QLabel(
            "Generate a self-signed certificate for testing the Sign workflow.\n"
            "Self-signed certificates are NOT trusted by Adobe Reader or browsers.\n"
            "For production use, obtain a certificate from a trusted Certificate Authority."
        )
        info.setStyleSheet("color: #aaaaaa; padding: 8px;")
        info.setWordWrap(True)

        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("color: #3a3a3a;")

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setSpacing(8)

        self._cert_name_edit = QLineEdit("PDF Tools Test Signer")
        self._cert_pw_edit = QLineEdit()
        self._cert_pw_edit.setPlaceholderText("Optional — leave blank for no password")
        self._cert_pw_edit.setEchoMode(QLineEdit.Password)
        self._cert_pw_confirm = QLineEdit()
        self._cert_pw_confirm.setPlaceholderText("Confirm password")
        self._cert_pw_confirm.setEchoMode(QLineEdit.Password)

        form.addRow("Name / CN:", self._cert_name_edit)
        form.addRow("Password:", self._cert_pw_edit)
        form.addRow("Confirm:", self._cert_pw_confirm)

        self._cert_btn_gen = QPushButton("Generate & Save .pfx")
        self._cert_btn_gen.setObjectName("primaryButton")

        layout.addWidget(info)
        layout.addWidget(divider)
        layout.addLayout(form)
        layout.addStretch()
        layout.addWidget(self._cert_btn_gen)
        return tab

    # ── Signals ───────────────────────────────────────────────────────────────

    def _connect_signals(self) -> None:
        self._sign_btn_pdf.clicked.connect(self._pick_sign_pdf)
        self._btn_pfx.clicked.connect(self._pick_pfx)
        self._sign_btn_run.clicked.connect(self._run_sign)

        self._ver_btn_pdf.clicked.connect(self._pick_verify_pdf)
        self._ver_btn_run.clicked.connect(self._run_verify)

        self._cert_btn_gen.clicked.connect(self._run_generate_cert)

    # ── Drag-and-drop routing ──────────────────────────────────────────────────

    def handle_dropped_files(self, paths: list[str]) -> None:
        if not paths:
            return
        ext = os.path.splitext(paths[0])[1].lower()
        if ext in (".pfx", ".p12"):
            self._tabs.setCurrentIndex(0)
            self._set_pfx(paths[0])
        elif ext == ".pdf":
            idx = self._tabs.currentIndex()
            if idx == 1:
                self._set_verify_pdf(paths[0])
            else:
                self._tabs.setCurrentIndex(0)
                self._set_sign_pdf(paths[0])

    def _on_drag_enter_visual(self) -> None:
        self._sign_drop_hint.setStyleSheet(
            "color: #0078d4; border: 2px dashed #0078d4; border-radius: 8px; padding: 40px;"
        )

    def _on_drag_leave_visual(self) -> None:
        self._sign_drop_hint.setStyleSheet("")

    # ── Sign helpers ──────────────────────────────────────────────────────────

    def _pick_sign_pdf(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select PDF to Sign", "", "PDF Files (*.pdf)")
        if path:
            self._set_sign_pdf(path)

    def _set_sign_pdf(self, path: str) -> None:
        self._sign_pdf_path = path
        name = path.replace("\\", "/").split("/")[-1]
        self._sign_pdf_label.setText(f"PDF: {name}")
        self._sign_pdf_label.setStyleSheet("color: #ffffff;")
        self._sign_drop_hint.hide()
        self._refresh_sign_btn()

    def _pick_pfx(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Certificate", "",
            "Certificate Files (*.pfx *.p12)"
        )
        if path:
            self._set_pfx(path)

    def _set_pfx(self, path: str) -> None:
        self._pfx_path = path
        name = path.replace("\\", "/").split("/")[-1]
        self._pfx_label.setText(f"Certificate: {name}")
        self._pfx_label.setStyleSheet("color: #ffffff;")
        self._refresh_sign_btn()

    def _refresh_sign_btn(self) -> None:
        self._sign_btn_run.setEnabled(
            bool(self._sign_pdf_path) and bool(self._pfx_path)
        )

    def _run_sign(self) -> None:
        base = os.path.splitext(os.path.basename(self._sign_pdf_path))[0]
        output, _ = QFileDialog.getSaveFileName(
            self, "Save Signed PDF", f"{base}_signed.pdf", "PDF Files (*.pdf)"
        )
        if not output:
            return
        if not output.lower().endswith(".pdf"):
            output += ".pdf"

        self._set_busy(True)
        self.show_status("")

        self._worker = Worker(
            fn=SignService.sign_pdf,
            args=(
                self._sign_pdf_path,
                output,
                self._pfx_path,
                self._pw_edit.text(),
                self._reason_edit.text(),
                self._location_edit.text(),
                self._contact_edit.text(),
            )
        )
        self._worker.progress.connect(self.set_progress)
        self._worker.finished.connect(self._on_sign_done)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_sign_done(self, _) -> None:
        self._set_busy(False)
        self.show_status("PDF signed and saved successfully.")

    # ── Verify helpers ────────────────────────────────────────────────────────

    def _pick_verify_pdf(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select PDF", "", "PDF Files (*.pdf)")
        if path:
            self._set_verify_pdf(path)

    def _set_verify_pdf(self, path: str) -> None:
        self._verify_path = path
        name = path.replace("\\", "/").split("/")[-1]
        self._ver_label.setText(f"PDF: {name}")
        self._ver_label.setStyleSheet("color: #ffffff;")
        self._ver_drop_hint.hide()
        self._ver_btn_run.setEnabled(True)

    def _run_verify(self) -> None:
        self._set_busy(True)
        self.show_status("")
        self._worker = Worker(fn=SignService.list_signatures, args=(self._verify_path,))
        self._worker.finished.connect(self._on_verify_done)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_verify_done(self, sigs: list) -> None:
        self._set_busy(False)
        if not sigs:
            self._ver_output.setPlainText("No signature fields found in this PDF.")
            self.show_status("No signatures detected.")
            return

        lines = [f"Found {len(sigs)} signature field(s):\n"]
        for i, s in enumerate(sigs, 1):
            status = "Signed" if s["signed"] else "Empty (unsigned field)"
            lines.append(f"  [{i}] Page {s['page']}  ·  Field: {s['name']}  ·  {status}")
        lines.append(
            "\nNote: This tool detects signature fields but does not perform "
            "cryptographic chain-of-trust verification."
        )
        self._ver_output.setPlainText("\n".join(lines))
        signed_count = sum(1 for s in sigs if s["signed"])
        self.show_status(f"{signed_count} of {len(sigs)} field(s) contain a signature.")

    # ── Generate certificate helpers ──────────────────────────────────────────

    def _run_generate_cert(self) -> None:
        pw = self._cert_pw_edit.text()
        pw_confirm = self._cert_pw_confirm.text()
        if pw != pw_confirm:
            self.show_status("Passwords do not match.", is_error=True)
            return

        cn = self._cert_name_edit.text().strip() or "PDF Tools Test Signer"
        output, _ = QFileDialog.getSaveFileName(
            self, "Save Certificate As", f"{cn}.pfx",
            "Certificate Files (*.pfx)"
        )
        if not output:
            return
        if not output.lower().endswith((".pfx", ".p12")):
            output += ".pfx"

        self._set_busy(True)
        self.show_status("Generating RSA key and certificate…")

        self._worker = Worker(
            fn=SignService.generate_test_certificate,
            args=(output, cn, pw)
        )
        self._worker.progress.connect(self.set_progress)
        self._worker.finished.connect(self._on_cert_done)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_cert_done(self, _) -> None:
        self._set_busy(False)
        self.show_status(
            "Certificate generated. You can now use it in the Sign PDF tab. "
            "Note: this is a self-signed certificate for testing only."
        )

    # ── Shared ────────────────────────────────────────────────────────────────

    def _on_error(self, msg: str) -> None:
        self._set_busy(False)
        self.show_status(f"Error: {msg}", is_error=True)

    def _set_busy(self, busy: bool) -> None:
        for btn in (self._sign_btn_run, self._sign_btn_pdf, self._btn_pfx,
                    self._ver_btn_run, self._ver_btn_pdf, self._cert_btn_gen):
            btn.setEnabled(not busy)
        if not busy:
            self._refresh_sign_btn()
            self._ver_btn_run.setEnabled(bool(self._verify_path))
        self.show_progress(busy)
