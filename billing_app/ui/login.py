"""Login form."""
from __future__ import annotations

from typing import Callable

import bcrypt
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QFrame, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

from billing_app.core.database import DataBase


class LoginWindow(QWidget):
    def __init__(self, db: DataBase, on_login: Callable[[str, str], None]):
        super().__init__()
        self.db = db
        self.on_login = on_login
        self._init_ui()

    @staticmethod
    def _verify_password(password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(password.encode(), hashed_password.encode())

    def _check_login(self, username: str, password: str) -> str | None:
        result = self.db.get_user_data(username)
        if not result:
            self.status_label.setText("User does not exist.")
            return None

        stored_pw, role = result
        if self._verify_password(password, stored_pw):
            return role
        self.status_label.setText("Invalid password.")
        return None

    def _init_ui(self) -> None:
        self.setWindowTitle("Login")
        self.setGeometry(100, 100, 300, 200)

        main_layout = QVBoxLayout()
        container = QFrame()
        container.setFixedSize(500, 400)
        layout = QVBoxLayout()

        self.username_label = QLabel("Username:")
        self.username_input = QLineEdit()
        layout.addWidget(self.username_label)
        layout.addWidget(self.username_input)

        self.password_label = QLabel("Password:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_input)

        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self._handle_login)
        layout.addWidget(self.login_button)

        self.username_input.returnPressed.connect(self._focus_password)
        self.password_input.returnPressed.connect(self._handle_login)

        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        layout.addStretch()
        container.setLayout(layout)
        main_layout.addWidget(container, alignment=Qt.AlignmentFlag.AlignCenter)
        self.setLayout(main_layout)

    def _focus_password(self) -> None:
        self.password_input.setFocus()

    def _handle_login(self) -> None:
        username = self.username_input.text()
        password = self.password_input.text()
        role = self._check_login(username, password)
        if role:
            self.on_login(username, role)


if __name__ == "__main__":
    from billing_app.core.database import DataBase

    app = QApplication([])
    db = DataBase("database/sql.db")
    window = LoginWindow(db, lambda *_: None)
    window.show()
    app.exec()
