import sys
import sqlite3
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QHBoxLayout, QComboBox, QHeaderView, QMenu
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from bcrypt import hashpw, gensalt
from database import DataBase

from GlobalAccess import LogMsg

class UserManagement(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db:DataBase = db
        self.setWindowTitle("User Management")
        self.setGeometry(100, 100, 600, 400)
        
        self.initUI()
        self.load_users()

    def initUI(self):
        layout = QVBoxLayout()

        # Form Layout
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
        
        form_layout.addWidget(self.username_input)
        form_layout.addWidget(self.password_input)
        form_layout.addWidget(self.conf_password_input)
        form_layout.addWidget(self.role_input)
        form_layout.addWidget(self.add_button)
        
        layout.addLayout(form_layout)
        
        # Table Widget
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["User ID", "Username", "Role"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        
        layout.addWidget(self.table)
        
        self.setLayout(layout)

    def load_users(self):
        self.table.setRowCount(0)
        users = self.db.get_users()
        for row_number, user in enumerate(users):
            id, name, pwhash, role = user
            self.table.insertRow(row_number)
            self.table.setItem(row_number, 0, QTableWidgetItem(str(id)))
            self.table.setItem(row_number, 1, QTableWidgetItem(str(name)))
            self.table.setItem(row_number, 2, QTableWidgetItem(str(role)))
    
    def add_user(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        role = self.role_input.currentText()

        if not username or not password:
            return  # Don't add empty users
        if password != self.conf_password_input.text().strip():
            LogMsg("Passwords do not match")
            return
        
        self.db.add_user(username, password, role)
        
        self.load_users()
        self.username_input.clear()
        self.password_input.clear()
        self.conf_password_input.clear()
    
    def show_context_menu(self, pos):
        menu = QMenu(self)
        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(self.delete_user)
        menu.addAction(delete_action)
        menu.exec(self.table.viewport().mapToGlobal(pos))
    
    def delete_user(self):
        selected_row = self.table.currentRow()
        if selected_row < 0:
            return
        
        user_id = self.table.item(selected_row, 0).text()
        
        self.db.delete_user(user_id)
        
        self.load_users()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = UserManagement()
    window.show()
    sys.exit(app.exec())
