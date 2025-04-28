import sys
import sqlite3
from PyQt6.QtCore import Qt, QPoint, QDateTime, QTime
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QTableWidget, QTableWidgetItem, QLabel
from PyQt6.QtWidgets import QListWidgetItem, QMenu, QMessageBox, QCheckBox, QDateTimeEdit
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
        self.total_label.setAlignment(Qt.AlignmentFlag.AlignRight)


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

        self.list_filter_layout = QVBoxLayout()

        self.filter_toggle = QCheckBox("Filter")
        self.list_filter_layout.addWidget(self.filter_toggle)
        self.filter_toggle.stateChanged.connect(self.on_filter_changed)

        strtTime = QHBoxLayout()
        strtTime.addWidget(QLabel("StartTime:"))
        curDate = QDateTime.currentDateTime()
        curDate.setTime(QTime(0,0,0,0))
        self.startDate = QDateTimeEdit(curDate)
        strtTime.addWidget(self.startDate)
        self.list_filter_layout.addLayout(strtTime)
        self.startDate.dateTimeChanged.connect(self.on_filter_changed)

        endTime = QHBoxLayout()
        endTime.addWidget(QLabel("EndTime:"))
        self.endDate = QDateTimeEdit(curDate.addDays(1))
        endTime.addWidget(self.endDate)
        self.list_filter_layout.addLayout(endTime)
        self.endDate.dateTimeChanged.connect(self.on_filter_changed)

        self.bill_list = QListWidget()
        self.bill_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.bill_list.customContextMenuRequested.connect(self.show_context_menu)
        self.bill_list.itemClicked.connect(self.load_bill_items)
        self.list_filter_layout.addWidget(self.bill_list)

        self.summary_label = QLabel()
        self.list_filter_layout.addWidget(self.summary_label)
        self.summary_table = QTableWidget()
        self.summary_table.setColumnCount(2)
        self.summary_table.setHorizontalHeaderLabels(["Product Name", "Quantity Sold"])
        self.summary_table.horizontalHeader().setStretchLastSection(True)
        self.summary_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)  # Make it readonly
        self.summary_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)    # No selection
        self.summary_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.list_filter_layout.addWidget(self.summary_table)
        
        self.bill_table = BillTable(db)

        layout.addLayout(self.list_filter_layout, 4)
        layout.addWidget(self.bill_table, 6)
        
        self.setLayout(layout)
        self.load_bills()

    def on_filter_changed(self):
        self.load_bills()
    
    def load_bills(self):
        if(self.filter_toggle.checkState() == Qt.CheckState.Checked):
            bills = self.db.get_bills(self.startDate.dateTime(), self.endDate.dateTime())
            summary = self.db.get_bill_summary(self.startDate.dateTime(), self.endDate.dateTime())
        else:
            bills = self.db.get_bills()
            summary = self.db.get_bill_summary()

        self.bill_list.clear()
        
        for bill_id, username, timestamp in bills:
            item = QListWidgetItem(f"{bill_id} - {timestamp}")
            item.setData(Qt.ItemDataRole.UserRole, bill_id)
            self.bill_list.addItem(item)

        self.update_summary_label(summary)
    
    def update_summary_label(self, summary):
        text = f"<b>Total Sales:</b> ₹{summary['total_price']:.2f}<br><br><b>Products Sold:</b><br>"
        self.summary_label.setText(text)
        product_summary = summary['product_summary']
        self.summary_table.setRowCount(len(product_summary))

        # Fill product rows
        for row, ((p_id, p_name), data) in enumerate(product_summary.items()):
            self.summary_table.setItem(row, 0, QTableWidgetItem(p_name))
            self.summary_table.setItem(row, 1, QTableWidgetItem(str(data['total_quantity'])))

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
