import fitz  # PyMuPDF
import os
from typing import Callable

# PyMuPDF field type integer → human label
_FIELD_LABELS = {
    0:  "Text",
    1:  "Button",
    2:  "CheckBox",
    3:  "RadioButton",
    4:  "ComboBox",
    5:  "ListBox",
    6:  "Text",       # multi-line text variant
    7:  "Signature",
}


class FormsService:

    @staticmethod
    def get_fields(pdf_path: str) -> list[dict]:
        """
        Read all AcroForm fields from a PDF.

        Returns list of dicts with keys:
            page (1-based int), page_index (0-based), name (str),
            type_label (str), value (str), field_type (int),
            choices (list[str]) — for combo/list boxes, else []
        """
        if not os.path.isfile(pdf_path):
            raise RuntimeError(f"File not found: {pdf_path}")

        doc = fitz.open(pdf_path)
        fields = []
        for page_num, page in enumerate(doc):
            for widget in page.widgets():
                field_type = widget.field_type
                value = widget.field_value
                if value is None:
                    value = ""
                # Normalise bool/checkbox values to a display string
                if isinstance(value, bool):
                    value = "Yes" if value else "No"
                elif not isinstance(value, str):
                    value = str(value)

                choices = []
                if field_type in (4, 5):  # combo / list
                    try:
                        choices = widget.choice_values or []
                    except Exception:
                        pass

                fields.append({
                    "page":       page_num + 1,
                    "page_index": page_num,
                    "name":       widget.field_name or f"field_{len(fields)}",
                    "type_label": _FIELD_LABELS.get(field_type, "Unknown"),
                    "field_type": field_type,
                    "value":      value,
                    "choices":    choices,
                })
        doc.close()
        return fields

    @staticmethod
    def fill_and_save(
        pdf_path: str,
        output_path: str,
        values: dict[str, str],
        progress_cb: Callable[[int], None] = None,
    ) -> int:
        """
        Write field values into the PDF and save.

        Args:
            values: {field_name: new_value_string}

        Returns:
            Number of fields updated.
        """
        if not os.path.isfile(pdf_path):
            raise RuntimeError(f"File not found: {pdf_path}")

        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        updated = 0

        for page_num, page in enumerate(doc):
            for widget in page.widgets():
                name = widget.field_name
                if name not in values:
                    continue
                new_val = values[name]
                field_type = widget.field_type

                # Checkbox: accept "yes"/"true"/"1" → "/Yes", anything else → "/Off"
                if field_type == 2:
                    if new_val.lower() in ("yes", "true", "1", "/yes", "/on"):
                        widget.field_value = True
                    else:
                        widget.field_value = False
                else:
                    widget.field_value = new_val

                widget.update()
                updated += 1

            if progress_cb:
                progress_cb(int((page_num + 1) / total_pages * 90))

        doc.save(output_path, incremental=True, encryption=fitz.PDF_ENCRYPT_KEEP)
        doc.close()

        if progress_cb:
            progress_cb(100)
        return updated

    @staticmethod
    def has_fields(pdf_path: str) -> bool:
        """Return True if the PDF has at least one AcroForm field."""
        if not os.path.isfile(pdf_path):
            return False
        doc = fitz.open(pdf_path)
        for page in doc:
            if any(True for _ in page.widgets()):
                doc.close()
                return True
        doc.close()
        return False
