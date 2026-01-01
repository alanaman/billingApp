"""Application-wide state and logging helpers."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtCore import QDateTime

from .paths import app_root, ensure_dir, resource_path


class AppState(QObject):
    status_msg = pyqtSignal(str)

    _instance: Optional["AppState"] = None

    @classmethod
    def instance(cls) -> "AppState":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self) -> None:
        super().__init__()
        self.username: Optional[str] = None
        self.elevation: Optional[str] = None

        log_dir = ensure_dir(app_root())
        self.log_path: Path = log_dir / "log.txt"
        self.log_path.touch(exist_ok=True)

    def set_user(self, username: Optional[str], elevation: Optional[str]) -> None:
        self.username = username
        self.elevation = elevation

    def log(self, message: str) -> None:
        self.status_msg.emit(message)
        timestamp = QDateTime.currentDateTime().toString()
        with self.log_path.open("a", encoding="utf-8") as fh:
            fh.write(f"{timestamp} : {message}\n")


def log_msg(message: str) -> None:
    AppState.instance().log(message)


def get_elevation() -> Optional[str]:
    return AppState.instance().elevation


def get_user() -> Optional[str]:
    return AppState.instance().username


__all__ = ["AppState", "log_msg", "get_elevation", "get_user", "resource_path"]
