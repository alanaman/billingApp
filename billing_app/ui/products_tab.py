"""Product management tab."""
from __future__ import annotations

from PyQt6.QtCore import QPoint, Qt, pyqtSlot
from PyQt6.QtGui import QDoubleValidator, QIntValidator, QAction
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from billing_app.core.database import DataBase
from billing_app.core.state import get_elevation


class ProductTable(QTableWidget):
    def __init__(self, db: DataBase, parent=None):
        super().__init__(parent)
        self.db = db
        self.setColumnCount(8)
        self.setHorizontalHeaderLabels(["ID", "Name", "HSN", "Price", "Stock", "unit", "tax percentage", "Description"])
        self.last_p_id = None

        if get_elevation() == "admin":
            self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            self.customContextMenuRequested.connect(self.showContextMenu)
            self.cellChanged.connect(self.updateProduct)
            self.cellDoubleClicked.connect(self.saveLastP_id)
        else:
            self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.loadProducts()

    def loadProducts(self):
        products = self.db.get_products()
        self.setRowCount(len(products))
        if get_elevation() == "admin":
            self.cellChanged.disconnect(self.updateProduct)
        for row_idx, product in enumerate(products):
            for col_idx, data in enumerate(product):
                self.setItem(row_idx, col_idx, QTableWidgetItem(str(data)))
        if get_elevation() == "admin":
            self.cellChanged.connect(self.updateProduct)

    @pyqtSlot(int, int)
    def updateProduct(self, row: int, column: int):
        new_value = self.item(row, column).text()
        self.db.update_product(self.last_p_id, column, new_value)
        self.loadProducts()

    @pyqtSlot(int, int)
    def saveLastP_id(self, row: int, column: int):
        self.last_p_id = self.item(row, 0).text()

    @pyqtSlot(QPoint)
    def showContextMenu(self, position: QPoint):
        menu = QMenu(self)
        delete_action = QAction("Delete Selected", self)
        delete_action.triggered.connect(self.confirmDelete)
        menu.addAction(delete_action)
        menu.exec(self.viewport().mapToGlobal(position))

    @pyqtSlot()
    def confirmDelete(self):
        selected_rows = set(index.row() for index in self.selectedIndexes())
        if not selected_rows:
            return
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            "Are you sure you want to delete the selected products?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            for row in sorted(selected_rows, reverse=True):
                product_id = self.item(row, 0).text()
                self.deleteProduct(product_id)

    def deleteProduct(self, product_id: str):
        self.db.delete_product(product_id)
        self.loadProducts()


class ProductForm(QWidget):
    def __init__(self, db: DataBase, parent=None):
        super().__init__(parent)
        self.db = db

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
        self.button.clicked.connect(self.add_product)

        input_layout = QHBoxLayout()
        for label, widget in [
            (self.id_label, self.p_id),
            (self.name_label, self.p_name),
            (self.hsn_label, self.p_hsn),
            (self.price_label, self.p_price),
            (self.stock_label, self.p_stock),
            (self.unit_label, self.p_unit),
            (self.tax_label, self.p_tax),
            (self.desc_label, self.p_desc),
        ]:
            col = QVBoxLayout()
            col.addWidget(label)
            col.addWidget(widget)
            input_layout.addLayout(col)
        input_layout.addWidget(self.button)

        self.setLayout(input_layout)

    @pyqtSlot()
    def add_product(self):
        self.db.add_product(
            self.p_id.text(),
            self.p_name.text(),
            self.p_hsn.text(),
            self.p_price.text(),
            self.p_stock.text(),
            self.p_unit.text(),
            self.p_tax.text(),
            self.p_desc.text(),
        )
        self.parent().refresh()  # type: ignore[call-arg]


class ProductTab(QWidget):
    def __init__(self, db: DataBase, parent=None):
        super().__init__(parent)
        self.db = db

        self.main_layout = QVBoxLayout()
        if get_elevation() == "admin":
            self.product_form = ProductForm(db, self)
            self.main_layout.addWidget(self.product_form)

        self.table = ProductTable(db=db)
        self.main_layout.addWidget(self.table)
        self.setLayout(self.main_layout)

    def refresh(self):
        self.table.loadProducts()
