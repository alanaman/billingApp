from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot as Slot, Qt, QPoint, QStringListModel, QModelIndex, QAbstractListModel
from PyQt6.QtWidgets import QApplication, QMenu, QTableWidget, QTabWidget, QTableWidgetItem, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QDialog, QLineEdit
from PyQt6.QtWidgets import QMessageBox, QCompleter, QListWidget, QListWidgetItem, QListView
from PyQt6.QtGui import QIntValidator, QDoubleValidator, QAction, QKeyEvent
from database import DataBase

from Printer import BillPrinter
from GlobalAccess import LogMsg
from Bills import BillTable

class DropDownWindow(QListView):
    def __init__(self, parent=None):
        super(DropDownWindow, self).__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)  # Floating, non-blocking
        # self.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # Prevent stealing focus
        self.hide()
    
    def focusOutEvent(self, e):
        self.hide()
        return super().focusOutEvent(e)


class IndexedListModel(QAbstractListModel):
    def __init__(self, items=None):
        super().__init__()
        self.items = items  # Store index with text

    def rowCount(self, parent=None):
        return len(self.items)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        # print(self.items)
        id, name, price = self.items[index.row()]
        
        if role == Qt.ItemDataRole.DisplayRole:  # Display text
            return f"{id} - {name} - Rs. {price}/-"
        
        if role == Qt.ItemDataRole.UserRole:  # Custom role to retrieve index
            return id

        return None
    
class MyLineEdit(QLineEdit):
    LostFocusSignal = pyqtSignal()
    GainFocusSignal = pyqtSignal()
    def __init__(self, parent=None):
        super(MyLineEdit, self).__init__(parent)

    def focusOutEvent(self, event):
        QLineEdit.focusOutEvent(self, event)
        self.LostFocusSignal.emit()
    
    def focusInEvent(self, event):
        QLineEdit.focusInEvent(self, event)
        self.GainFocusSignal.emit()

class BillingTab(QWidget):
    def __init__(self, db: DataBase, parent=None):
        super(BillingTab, self).__init__(parent)
        self.db : DataBase = db

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        search_label = QLabel("Search Product to Add to Bill:")
        self.product_search = MyLineEdit()
        self.product_search.setPlaceholderText("Type to search...")

        self.invoice_id_label = QLabel("Invoice ID: ")


        quantity_label = QLabel("Enter Quantity")
        self.quantity_input = QLineEdit()
        self.quantity_input.setPlaceholderText("Enter Quantity")

        self.list_widget = DropDownWindow(self)

        self.bill_table = BillTable(db)

        self.print_button = QPushButton("Print Bill")
        # self.save_button = QPushButton("Save Bill")
        self.clear_button = QPushButton("New Bill")
        
        search_section = QVBoxLayout()
        search_section.addWidget(search_label)
        search_section.addWidget(self.product_search)

        quantity_section = QVBoxLayout()
        quantity_section.addWidget(quantity_label)
        quantity_section.addWidget(self.quantity_input)

        entry_section = QHBoxLayout()
        entry_section.addLayout(search_section)
        entry_section.addLayout(quantity_section)

        button_section = QHBoxLayout()
        button_section.addWidget(self.clear_button)
        button_section.addWidget(self.print_button)
        # button_section.addWidget(self.save_button)

        bill_layout = QVBoxLayout()
        bill_layout.addWidget(self.invoice_id_label)
        bill_layout.addLayout(entry_section)
        bill_layout.addWidget(self.bill_table)
        bill_layout.addLayout(button_section)
        
        
        self.setLayout(bill_layout)

        # Data storage for dropdown selection
        self.product_data = {}
        self.last_added_product_id = None

        # Connect signals
        self.product_search.textChanged.connect(self.update_completer)
        self.product_search.GainFocusSignal.connect(self.update_completer)
        self.product_search.LostFocusSignal.connect(self.hide_popup)

        self.product_search.returnPressed.connect(self.handle_search_enter_pressed)
        self.list_widget.clicked.connect(self.handle_search_popup_activated)
        self.quantity_input.returnPressed.connect(self.handle_quantity_enter_pressed)

        self.print_button.clicked.connect(self.print_bill)
        # self.save_button.clicked.connect(self.save_bill)
        self.clear_button.clicked.connect(self.clear_bill)

        self.update_bill()

    def get_next_bill_id(self):
        return self.db.getNextBillId()
        
    
    def keyPressEvent(self, event: QKeyEvent):
        # Ensure key events only affect the active tab
        if event.key() == Qt.Key.Key_S and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.save_bill()
        if event.key() == Qt.Key.Key_P and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.print_bill()
        if event.key() == Qt.Key.Key_N and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.clear_bill()
        

    def show_popup(self):
        """ Position the popup below the search bar """
        self.list_widget.setMinimumWidth(self.product_search.width())  # Match width of search bar
        
        # Get global position of search bar and position the list below it
        pos = self.product_search.mapToGlobal(QPoint(0, self.product_search.height()))
        self.list_widget.move(pos)
        self.list_widget.resize(self.product_search.width(), min(self.list_widget.model().rowCount(), 10) * 20)
        self.list_widget.show()
    
    def hide_popup(self):
        # hide if mouse is not over the list_widget
        if self.hasFocus():
            self.list_widget.hide()

    def update_completer(self):
        """Fetch matching products from the database and update completer."""
        search_text = self.product_search.text()
        if not search_text:
            self.list_widget.hide()
            return

        # Fetch product details (id, name, price) from the database
        products = self.db.searchProducts(search_text)  # Returns list of tuples [(id, name, price), ...]

        if not products:
            self.product_data = []
            self.list_widget.hide()
            return

        self.product_data = [(id, name,price) for id, name, hsn, price, stock, unit, tax, desc in products]

        # Update completer model
        # self.list_widget.setModel(QStringListModel(list(f"{id} - {name} - Rs. {price}/-" for id, name, price, _, _ in products)))
        self.list_widget.setModel(IndexedListModel(self.product_data))
        # self.list_widget.clear()
        # self.list_widget.addItems(list(f"{id} - {name} - Rs. {price}/-" for id, name, price in self.product_data))
        self.show_popup()

    def add_product_to_bill(self, product_id, quantity, override=True):
        """Add the selected product to the bill when Enter is pressed or dropdown is clicked."""
        # Insert into the bill table
        self.db.addItemToBill(product_id, quantity, override)
        self.update_bill()
        self.last_added_product_id = product_id


    def update_bill(self):
        """Update the bill table with the latest data."""

        self.invoice_id_label.setText(f"Invoice ID: {self.get_next_bill_id()}")

        bill = self.db.getCurrentBill()
        self.bill_table.show_bill(bill)

    def clear_bill(self):
        self.db.clearCurrentBill()
        self.update_bill()

    def handle_search_enter_pressed(self):
        """Handles pressing Enter on the search field, adding the first dropdown item if available."""
        if not self.product_data:
            return  # No items in dropdown, do nothing

        # Get the first item in the dropdown
        id, product_name, price = self.product_data[0]
        self.add_product_to_bill(product_id=id, quantity=1, override=False)
        self.quantity_input.setFocus()

    def handle_search_popup_activated(self, index: QModelIndex):
        """Handles selecting an item from the dropdown popup."""
        # id = item.data(Qt.ItemDataRole.UserRole)
        id = self.list_widget.model().data(index, Qt.ItemDataRole.UserRole)
        self.product_search.setText(str(id))
        self.add_product_to_bill(product_id=id, quantity=1, override=False)
        self.list_widget.hide()
        self.quantity_input.setFocus()

    def handle_quantity_enter_pressed(self):
        if not self.product_data:
            return
        
        quantity = float(self.quantity_input.text())

        if(self.product_search.text() == ""):
            if(self.last_added_product_id):
                self.add_product_to_bill(self.last_added_product_id, quantity)
            return
        else:
            if(self.product_data):
                first_item = self.product_data[0][0]
                self.add_product_to_bill(first_item, quantity)

        self.quantity_input.clear()
        self.product_search.clear()
        self.product_search.setFocus()
    
    def save_bill(self):
        if not len(self.db.getCurrentBill()):
            LogMsg("No items in bill to save")
            return

        reply = QMessageBox.question(
            self, "Confirm Save", "Are you sure you want to save and print this bill?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            invoice_no = self.db.save_bill()
            self.update_bill()
            return invoice_no
        
    def print_bill(self):
        invoice_no = self.save_bill()
        if invoice_no:
            bill = self.db.getCurrentBill()
            BillPrinter(invoice_no, self.db.get_bill_date(invoice_no) ,bill).print_bill()
            # BillPrinter().print_bill(bill)

        
if __name__ == "__main__":
    db = DataBase('database/sql.db')
    app = QApplication([])
    billing_tab = BillingTab(db)
    
    billing_tab.print_bill()
