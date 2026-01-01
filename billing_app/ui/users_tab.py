"""User management tab for admins."""
from __future__ import annotations

import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QHeaderView,
    QHBoxLayout,
    QLineEdit,
    QMenu,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from PyQt6.QtGui import QAction

from billing_app.core.database import DataBase
from billing_app.core.state import log_msg


class UserManagement(QWidget):
    def __init__(self, db: DataBase):
        super().__init__()
        self.db = db
        self.setWindowTitle("User Management")
        self.setGeometry(100, 100, 600, 400)
        self._init_ui()
        self.load_users()

    def _init_ui(self) -> None:
        layout = QVBoxLayout()

        form_layout = QHBoxLayout()
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.conf_password_input = QLineEdit()
        self.conf_password_input.setPlaceholderText("Confirm Password")
        self.conf_password_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.role_input = QComboBox()
        self.role_input.addItems(["admin", "user"])

        self.add_button = QPushButton("Add User")
        self.add_button.clicked.connect(self.add_user)

        for widget in [
            self.username_input,
            self.password_input,
            self.conf_password_input,
            self.role_input,
            self.add_button,
        ]:
            form_layout.addWidget(widget)
        layout.addLayout(form_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["User ID", "Username", "Role"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.table)
        self.setLayout(layout)

    def load_users(self) -> None:
        self.table.setRowCount(0)
        users = self.db.get_users()
        for row_number, user in enumerate(users):
            user_id, name, _pw_hash, role = user
            self.table.insertRow(row_number)
            self.table.setItem(row_number, 0, QTableWidgetItem(str(user_id)))
            self.table.setItem(row_number, 1, QTableWidgetItem(str(name)))
            self.table.setItem(row_number, 2, QTableWidgetItem(str(role)))

    def add_user(self) -> None:
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        role = self.role_input.currentText()

        if not username or not password:
            return
        if password != self.conf_password_input.text().strip():
            log_msg("Passwords do not match")
            return

        self.db.add_user(username, password, role)
        self.load_users()
        self.username_input.clear()
        self.password_input.clear()
        self.conf_password_input.clear()

    def show_context_menu(self, pos) -> None:
        menu = QMenu(self)
        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(self.delete_user)
        menu.addAction(delete_action)
        menu.exec(self.table.viewport().mapToGlobal(pos))

    def delete_user(self) -> None:
        selected_row = self.table.currentRow()
        if selected_row < 0:
            return
        user_id = self.table.item(selected_row, 0).text()
        self.db.delete_user(user_id)
        self.load_users()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    db = DataBase("database/sql.db")
    window = UserManagement(db)
    window.show()
    sys.exit(app.exec())
