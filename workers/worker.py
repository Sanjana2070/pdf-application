from PySide6.QtCore import QThread, Signal
from typing import Callable, Any


class Worker(QThread):
    progress = Signal(int)
    finished = Signal(object)
    error = Signal(str)

    def __init__(self, fn: Callable, args: tuple = (), kwargs: dict = None, parent=None):
        super().__init__(parent)
        self._fn = fn
        self._args = args
        self._kwargs = kwargs or {}
        self.finished.connect(lambda _: self.deleteLater())
        self.error.connect(lambda _: self.deleteLater())

    def run(self) -> None:
        try:
            result = self._fn(*self._args, **self._kwargs, progress_cb=self._emit_progress)
            self.finished.emit(result)
        except TypeError:
            try:
                result = self._fn(*self._args, **self._kwargs)
                self.finished.emit(result)
            except Exception as e:
                self.error.emit(str(e))
        except Exception as e:
            self.error.emit(str(e))

    def _emit_progress(self, value: int) -> None:
        self.progress.emit(max(0, min(100, value)))
