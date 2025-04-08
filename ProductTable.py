from PyQt6.QtCore import QObject, pyqtSignal as Signal, pyqtSlot as Slot, Qt, QPoint, QStringListModel
from PyQt6.QtWidgets import QApplication, QMenu, QTableWidget, QTabWidget, QTableWidgetItem, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QDialog, QLineEdit
from PyQt6.QtWidgets import QMessageBox, QCompleter
from PyQt6.QtGui import QIntValidator, QDoubleValidator, QAction
import sys

from database import DataBase
from GlobalAccess import GetElevation

class ProductTable(QTableWidget):
    def __init__(self, db, parent = None):
        super(ProductTable, self).__init__(parent)
        self.db : DataBase = db
        self.setColumnCount(8)
        self.setHorizontalHeaderLabels(["ID", "Name", "HSN", "Price", "Stock", "unit", "tax percentage", "Description"])

        self.last_p_id = None

        if GetElevation() == 'admin':
            self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            self.customContextMenuRequested.connect(self.showContextMenu)

            self.cellChanged.connect(self.updateProduct)
            self.cellDoubleClicked.connect(self.saveLastP_id)
            self.loadProducts()
    
    def loadProducts(self):
        products = self.db.getProducts()  # Assuming db.getProducts() returns a list of tuples
        self.setRowCount(len(products))
        if GetElevation() == 'admin' : self.cellChanged.disconnect(self.updateProduct)
        for row_idx, product in enumerate(products):
            for col_idx, data in enumerate(product):
                self.setItem(row_idx, col_idx, QTableWidgetItem(str(data)))
        if GetElevation() == 'admin': self.cellChanged.connect(self.updateProduct)

        if GetElevation() != 'admin':
            self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    
    @Slot(int, int)
    def updateProduct(self, row, column):
        new_value = self.item(row, column).text()

        self.db.updateProduct(self.last_p_id, column, new_value)

        self.loadProducts()

    @Slot(int, int)
    def saveLastP_id(self, row, column):
        self.last_p_id = self.item(row, 0).text()

    @Slot(QPoint)
    def showContextMenu(self, position):
        menu = QMenu(self)
        delete_action = QAction("Delete Selected", self)
        delete_action.triggered.connect(self.confirmDelete)
        menu.addAction(delete_action)
        menu.exec(self.viewport().mapToGlobal(position))

    @Slot()
    def confirmDelete(self):
        selected_rows = set(index.row() for index in self.selectedIndexes())
        if not selected_rows:
            return
        
        reply = QMessageBox.question(
            self, "Confirm Deletion", "Are you sure you want to delete the selected products?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            for row in sorted(selected_rows, reverse=True):
                product_id = self.item(row, 0).text()
                self.deleteProduct(product_id)

    def deleteProduct(self, product_id):
        self.db.deleteProduct(product_id)
        self.loadProducts()

class ProductForm(QWidget):
    def __init__(self, db, parent=None):
        super(ProductForm, self).__init__(parent)
        
        self.db : DataBase = db

        # Create widgets with labels
        self.id_label = QLabel("Product ID:")
        self.p_id = QLineEdit()
        self.p_id.setValidator(QIntValidator())
        
        self.name_label = QLabel("Product Name:")
        self.p_name = QLineEdit()

        self.hsn_label = QLabel("HSN:")
        self.p_hsn = QLineEdit()
        
        self.price_label = QLabel("Price per unit:")
        self.p_price = QLineEdit()
        self.p_price.setValidator(QDoubleValidator(decimals=2))
        
        self.stock_label = QLabel("Product Stock:")
        self.p_stock = QLineEdit()
        self.p_stock.setValidator(QDoubleValidator(decimals=2))
        
        self.unit_label = QLabel("Unit:")
        self.p_unit = QLineEdit()

        self.tax_label = QLabel("Tax Percentage:")
        self.p_tax = QLineEdit()
        self.p_tax.setValidator(QDoubleValidator(decimals=2))

        self.desc_label = QLabel("Description:")
        self.p_desc = QLineEdit()
        
        self.button = QPushButton("Add Product")
        self.button.clicked.connect(self.AddProduct)
        
        # Create horizontal layout for input fields
        input_layout = QHBoxLayout()
        id_layout = QVBoxLayout()
        id_layout.addWidget(self.id_label)
        id_layout.addWidget(self.p_id)

        name_layout = QVBoxLayout()
        name_layout.addWidget(self.name_label)
        name_layout.addWidget(self.p_name)
        
        hsn_layout = QVBoxLayout()
        hsn_layout.addWidget(self.hsn_label)
        hsn_layout.addWidget(self.p_hsn)

        price_layout = QVBoxLayout()
        price_layout.addWidget(self.price_label)
        price_layout.addWidget(self.p_price)

        stock_layout = QVBoxLayout()
        stock_layout.addWidget(self.stock_label)
        stock_layout.addWidget(self.p_stock)

        unit_layout = QVBoxLayout()
        unit_layout.addWidget(self.unit_label)
        unit_layout.addWidget(self.p_unit)

        tax_layout = QVBoxLayout()
        tax_layout.addWidget(self.tax_label)
        tax_layout.addWidget(self.p_tax)

        desc_layout = QVBoxLayout()
        desc_layout.addWidget(self.desc_label)
        desc_layout.addWidget(self.p_desc)

        input_layout.addLayout(id_layout)
        input_layout.addLayout(name_layout)
        input_layout.addLayout(hsn_layout)
        input_layout.addLayout(price_layout)
        input_layout.addLayout(stock_layout)
        input_layout.addLayout(unit_layout)
        input_layout.addLayout(tax_layout)
        input_layout.addLayout(desc_layout)
        input_layout.addWidget(self.button)
        
        self.setLayout(input_layout)


    @Slot()
    def AddProduct(self):
        self.db.addProduct(
            self.p_id.text(), 
            self.p_name.text(), 
            self.p_hsn.text(),
            self.p_price.text(), 
            self.p_stock.text(),
            self.p_unit.text(), 
            self.p_tax.text(),
            self.p_desc.text()
        )

        self.parent().refresh()

class ProductTab(QWidget):
    def __init__(self, db, parent=None):
        super(ProductTab, self).__init__(parent)
        self.db = db

        self.main_layout = QVBoxLayout()
        if(GetElevation() == 'admin'):
            self.product_form = ProductForm(db, self)
            self.main_layout.addWidget(self.product_form)

        self.table = ProductTable(db=db)
        self.main_layout.addWidget(self.table)
        
        self.setLayout(self.main_layout)\
    
    def refresh(self):
        self.table.loadProducts()

        