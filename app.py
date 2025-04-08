from PyQt6.QtCore import QObject, pyqtSignal as Signal, pyqtSlot as Slot, Qt, QPoint, QStringListModel
from PyQt6.QtWidgets import QApplication, QMenu, QTableWidget, QTabWidget, QTableWidgetItem, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QDialog, QLineEdit
from PyQt6.QtWidgets import QMessageBox, QCompleter, QMainWindow, QStyleFactory
from PyQt6.QtGui import QIntValidator, QDoubleValidator, QAction, QKeyEvent, QPalette, QColor
import sys

from database import DataBase
from ProductTable import ProductTab
from Billing import BillingTab
from Bills import BillViewer
from GlobalAccess import GlobalData, resource_path, LogMsg
from login import LoginWindow
from users import UserManagement

from GlobalAccess import GetElevation


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.widget = LoginWindow(db)
        self.setCentralWidget(self.widget)
        self.elevation = None
        self.username = None

    def login(self, username, elevation):
        self.elevation = elevation
        GlobalData.I().SetUser(username, elevation)
        self.username = username
        self.widget = MainApp()
        self.setCentralWidget(self.widget)
        self.show()
    
    def logout(self):
        self.widget = LoginWindow()
        self.setCentralWidget(self.widget)
        self.elevation = None
        GlobalData.I().SetUser(None, None)
        self.username = None
        self.show()


class MainApp(QWidget):
    def __init__(self):
        super(MainApp, self).__init__()
        
        self.tabs = QTabWidget()
        self.status_message = QLabel()

        self.billing_tab = BillingTab(db)
        self.tabs.addTab(self.billing_tab, "Billing")
        
        self.products_tab = ProductTab(db, self)
        self.tabs.addTab(self.products_tab, "Products")
        
        self.bills = BillViewer(db)
        self.tabs.addTab(self.bills, "Past Bills")

        if GetElevation() == 'admin':
            self.users = UserManagement(db)
            self.tabs.addTab(self.users, "User Management")


        self.vlayout = QVBoxLayout()
        self.vlayout.addWidget(self.tabs)
        self.vlayout.addWidget(self.status_message)
        self.setLayout(self.vlayout)

        self.tabs.currentChanged.connect(self.on_tab_change)

        GlobalData.I().status_msg.connect(self.show_status)

    def on_tab_change(self, index):
        if index == 0:
            self.billing_tab.update_bill()
        if index == 1:
            self.products_tab.table.loadProducts()
        if index == 2:
            self.bills.load_bills()
        if index == 3:
            self.users.load_users()


    def show_status(self, message):
        self.status_message.setText(message)

def set_light_mode(app: QApplication):
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(255, 255, 255))  # Background color
    palette.setColor(QPalette.ColorRole.WindowText, QColor(0, 0, 0))    # Text color
    palette.setColor(QPalette.ColorRole.Base, QColor(240, 240, 240))    # Input fields
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 220))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(0, 0, 0))
    palette.setColor(QPalette.ColorRole.Text, QColor(0, 0, 0))
    palette.setColor(QPalette.ColorRole.Button, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(0, 0, 0))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 120, 215))  # Selection color
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))

    app.setPalette(palette)

if __name__ == '__main__':
    # import os
    # os.environ["QT_QPA_PLATFORM"] = "windows:darkmode=0"
    
    db = DataBase(resource_path('database/sql.db')) 
    
    app = QApplication([])
    # set_light_mode(app)
    app.setStyle("Fusion")
    # Create and show the form
    window = MainWindow()
    window.show()
    # Run the main Qt loop
    try:
        app.exec()
        sys.exit(0)
    except Exception as e:
        LogMsg(f"Unexpected error: {str(e)}")
        raise  # Ensure the program still exits properly
    except BaseException as e:
        LogMsg(f"Critical error: {str(e)}")
        raise  # Re-raise SystemExit and other critical exceptions
