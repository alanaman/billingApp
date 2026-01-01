"""Application entry point."""
from __future__ import annotations

import sys
from PyQt6.QtWidgets import QApplication

from billing_app.core.database import DataBase
from billing_app.core.paths import resource_path
from billing_app.ui.main_window import MainWindow


def run() -> int:
    db = DataBase(resource_path("database/sql.db"))
    app = QApplication([])
    app.setStyle("Fusion")
    window = MainWindow(db)
    window.show()
    try:
        app.exec()
        return 0
    except Exception as exc:  # pylint: disable=broad-except
        from billing_app.core.state import log_msg

        log_msg(f"Unexpected error: {exc}")
        raise


def main() -> None:
    sys.exit(run())


if __name__ == "__main__":
    main()
