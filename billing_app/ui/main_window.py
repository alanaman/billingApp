"""Main window wiring all tabs together."""
from __future__ import annotations

from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication, QLabel, QMainWindow, QTabWidget, QVBoxLayout, QWidget

from billing_app.core.database import DataBase
from billing_app.core.state import AppState, get_elevation
from billing_app.ui.billing_tab import BillingTab
from billing_app.ui.bills_tab import BillViewer
from billing_app.ui.login import LoginWindow
from billing_app.ui.products_tab import ProductTab
from billing_app.ui.users_tab import UserManagement


class MainWindow(QMainWindow):
    def __init__(self, db: DataBase):
        super().__init__()
        self.db = db
        self.widget: QWidget | None = None
        self.setCentralWidget(LoginWindow(db, self.login))
        self.elevation = None
        self.username = None

    def login(self, username: str, elevation: str) -> None:
        self.elevation = elevation
        AppState.instance().set_user(username, elevation)
        self.username = username
        self.widget = MainApp(self.db)
        self.setCentralWidget(self.widget)
        self.show()

    def logout(self) -> None:
        self.widget = LoginWindow(self.db, self.login)
        self.setCentralWidget(self.widget)
        self.elevation = None
        AppState.instance().set_user(None, None)
        self.username = None
        self.show()


class MainApp(QWidget):
    def __init__(self, db: DataBase):
        super().__init__()
        self.db = db
        self.tabs = QTabWidget()
        self.status_message = QLabel()

        self.billing_tab = BillingTab(db)
        self.tabs.addTab(self.billing_tab, "Billing")

        self.products_tab = ProductTab(db, self)
        self.tabs.addTab(self.products_tab, "Products")

        self.bills = BillViewer(db)
        self.tabs.addTab(self.bills, "Past Bills")

        if get_elevation() == "admin":
            self.users = UserManagement(db)
            self.tabs.addTab(self.users, "User Management")

        self.vlayout = QVBoxLayout()
        self.vlayout.addWidget(self.tabs)
        self.vlayout.addWidget(self.status_message)
        self.setLayout(self.vlayout)

        self.tabs.currentChanged.connect(self.on_tab_change)
        AppState.instance().status_msg.connect(self.show_status)

    def on_tab_change(self, index: int) -> None:
        if index == 0:
            self.billing_tab.update_bill()
        if index == 1:
            self.products_tab.table.loadProducts()
        if index == 2:
            self.bills.load_bills()
        if index == 3 and get_elevation() == "admin":
            self.users.load_users()

    def show_status(self, message: str) -> None:
        self.status_message.setText(message)


def set_light_mode(app: QApplication) -> None:
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(0, 0, 0))
    palette.setColor(QPalette.ColorRole.Base, QColor(240, 240, 240))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 220))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(0, 0, 0))
    palette.setColor(QPalette.ColorRole.Text, QColor(0, 0, 0))
    palette.setColor(QPalette.ColorRole.Button, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(0, 0, 0))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 120, 215))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    app.setPalette(palette)
