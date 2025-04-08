import sys
import sqlite3
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QTableWidget, QTableWidgetItem, QLabel
from PyQt6.QtWidgets import QListWidgetItem, QMenu, QMessageBox
from PyQt6.QtGui import QAction
from database import DataBase

from Printer import BillPrinter
from GlobalAccess import LogMsg, GetElevation

class BillTable(QWidget):
    def __init__(self, db: DataBase, parent=None):
        super().__init__()
        self.db: DataBase = db

        self.bill_table = QTableWidget()
        header_labels = [
                "ID",
                "Name",
                "HSN",
                "Price Per Unit",
                "Quantity",
                "Unit",
                "Price",
                "Tax%",
                "Tax Amt",
                "Total Amt"
            ]

        self.bill_table.setColumnCount(len(header_labels))
        self.bill_table.setHorizontalHeaderLabels(header_labels)
        self.grand_total = 0
        self.total_label = QLabel(f"Grand Total: {self.grand_total}")

        bill_layout = QVBoxLayout()
        bill_layout.addWidget(self.bill_table)
        bill_layout.addWidget(self.total_label)

        self.setLayout(bill_layout)

    def show_bill(self, bill):
        """Update the bill table with the latest data."""

        price_total = 0
        tax_total = 0
        # bill = self.db.getCurrentBill()
        self.bill_table.setRowCount(len(bill))
        for row_idx, item in enumerate(bill):
            id, name, HSN, unit_price, quantity, unit, tax_perc = item
            self.bill_table.setItem(row_idx, 0, QTableWidgetItem(str(id)))
            self.bill_table.setItem(row_idx, 1, QTableWidgetItem(str(name)))
            self.bill_table.setItem(row_idx, 2, QTableWidgetItem(str(HSN)))
            unit_price_no_tax = unit_price * (100 / (100 + tax_perc))

            self.bill_table.setItem(row_idx, 3, QTableWidgetItem(str(round(unit_price_no_tax, 2))))
            self.bill_table.setItem(row_idx, 4, QTableWidgetItem(str(quantity)))
            self.bill_table.setItem(row_idx, 5, QTableWidgetItem(str(unit)))
            price_no_tax = unit_price_no_tax * quantity
            self.bill_table.setItem(row_idx, 6, QTableWidgetItem(str(round(price_no_tax, 2))))
            self.bill_table.setItem(row_idx, 7, QTableWidgetItem(str(tax_perc)))
            tax_amt = price_no_tax*tax_perc/100
            self.bill_table.setItem(row_idx, 8, QTableWidgetItem(str(round(tax_amt, 2))))
            total_amt = unit_price*quantity; 
            self.bill_table.setItem(row_idx, 9, QTableWidgetItem(str(total_amt)))

            price_total += price_no_tax
            tax_total += tax_amt
        
        self.bill_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        # for row in range(self.bill_table.rowCount()):
        #     for col in range(self.bill_table.columnCount()):
        #         item = self.bill_table.item(row, col)
        #         item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

        grand_total = price_total + tax_total
        self.total_label.setText(
            f"Price total: {price_total:.2f}    " +
            f"Tax total: {tax_total:.2f}    " +
            f"Grand total: {grand_total:.2f}    "
        )
        self.total_label.setAlignment(Qt.AlignmentFlag.AlignRight)



class BillViewer(QWidget):
    def __init__(self, db: DataBase, parent=None):
        super().__init__()
        self.db: DataBase = db
        
        layout = QHBoxLayout()
        self.bill_list = QListWidget()
        self.bill_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.bill_list.customContextMenuRequested.connect(self.show_context_menu)
        self.bill_list.itemClicked.connect(self.load_bill_items)
        
        self.bill_table = BillTable(db)

        layout.addWidget(self.bill_list, 2)
        layout.addWidget(self.bill_table, 8)
        
        self.setLayout(layout)
        self.load_bills()
    
    def load_bills(self):
        bills = self.db.get_bills()

        self.bill_list.clear()
        
        for bill_id, username, timestamp in bills:
            item = QListWidgetItem(f"{bill_id} - {timestamp}")
            item.setData(Qt.ItemDataRole.UserRole, bill_id)
            self.bill_list.addItem(item)
    
    def load_bill_items(self, item: QListWidgetItem):
        bill_id = item.data(Qt.ItemDataRole.UserRole)
        items = self.db.get_bill_items(bill_id)
        
        self.bill_table.show_bill(items)
    
    def show_context_menu(self, position: QPoint):
        item = self.bill_list.itemAt(position)
        if item:
            menu = QMenu(self)
            print_action = menu.addAction("Print")
            delete_action = None
            if GetElevation() == 'admin':
                delete_action = menu.addAction("Delete")
            
            action = menu.exec(self.bill_list.mapToGlobal(position))
            if action == print_action:
                self.print_bill(item)
            elif action == delete_action and GetElevation() == 'admin':
                self.delete_bill(item)

    def print_bill(self, item: QListWidgetItem):
        invoice_no = item.data(Qt.ItemDataRole.UserRole)
        if invoice_no:
            bill = self.db.get_bill_items(invoice_no)
            BillPrinter(invoice_no, self.db.get_bill_date(invoice_no) ,bill).print_bill()


    def delete_bill(self, item: QListWidgetItem):
        bill_id = item.data(Qt.ItemDataRole.UserRole)
        
        reply = QMessageBox.question(
            self, "Delete Bill",
            f"Are you sure you want to delete Bill with invoice_no: {bill_id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.db.delete_bill(bill_id)
            self.load_bills()
            self.db.reset_invoice_no()
            LogMsg(f"Deleted Bill with invoice No: {bill_id} deleted successfully.")
