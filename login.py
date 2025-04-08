import sqlite3
import bcrypt
from PyQt6.QtCore import QObject, pyqtSignal as Signal, pyqtSlot as Slot, Qt, QPoint, QStringListModel
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout
from PyQt6.QtWidgets import QFrame
import sys
from database import DataBase

class LoginWindow(QWidget):
    def __init__(self, db):
        super().__init__()
        self.init_ui()
        self.db : DataBase = db

    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def verify_password(self, password:str, hashed_password:str):
        """Verify hashed password."""
        return bcrypt.checkpw(password.encode(), hashed_password.encode())

    def register_user(self, username, password):
        """Register a new user with hashed password."""
        hashed_password = self.hash_password(password)
        try:
            self.cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
            self.conn.commit()
        except sqlite3.IntegrityError:
            return False  # Username already exists
        return True

    def check_login(self, username, password):
        """Check login credentials."""
        pw, role = self.db.get_user_data(username) or (None, None)

        if pw is None:
            self.label_status.setText("User does not exist.")
        else:
            if self.verify_password(password, pw):
                return role
            else:
                self.label_status.setText("Invalid password.")
    
    def init_ui(self):
        """Initialize UI elements."""
        self.setWindowTitle("Login")
        self.setGeometry(100, 100, 300, 200)

        main_layout = QVBoxLayout()
        container = QFrame()
        container.setFixedSize(500, 400)
        layout = QVBoxLayout()


        self.label_username = QLabel("Username:")
        self.input_username = QLineEdit()
        layout.addWidget(self.label_username)
        layout.addWidget(self.input_username)

        self.label_password = QLabel("Password:")
        self.input_password = QLineEdit()
        self.input_password.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.label_password)
        layout.addWidget(self.input_password)

        self.button_login = QPushButton("Login")
        self.button_login.clicked.connect(self.handle_login)
        layout.addWidget(self.button_login)

        # self.button_register = QPushButton("Register")
        # self.button_register.clicked.connect(self.handle_register)
        # layout.addWidget(self.button_register)

        self.label_status = QLabel("")
        layout.addWidget(self.label_status)

        layout.addStretch()
        container.setLayout(layout)
        main_layout.addWidget(container, alignment=Qt.AlignmentFlag.AlignCenter)
        self.setLayout(main_layout)

    def handle_login(self):
        username = self.input_username.text()
        password = self.input_password.text()

        role = self.check_login(username, password)
        if role:
            self.parent().login(username, role)

    # def handle_register(self):
    #     username = self.input_username.text()
    #     password = self.input_password.text()

    #     if self.register_user(username, password):
    #         self.label_status.setText("User registered successfully!")
    #     else:
    #         self.label_status.setText("Username already exists.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec())
