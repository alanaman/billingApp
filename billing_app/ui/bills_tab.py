"""Tabs for viewing bills and bill table display."""
from __future__ import annotations

from typing import Any, Dict, Tuple

from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QDateTimeEdit,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from billing_app.core.database import DataBase
from billing_app.core.state import get_elevation, log_msg
from billing_app.printing.bill_printer import BillPrinter


class BillTable(QWidget):
    def __init__(self, db: DataBase, parent: QWidget | None = None):
        super().__init__(parent)
        self.db = db

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
            "Total Amt",
        ]
        self.bill_table.setColumnCount(len(header_labels))
        self.bill_table.setHorizontalHeaderLabels(header_labels)
        self.total_label = QLabel("Grand Total: 0")

        bill_layout = QVBoxLayout()
        bill_layout.addWidget(self.bill_table)
        bill_layout.addWidget(self.total_label)
        self.total_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.setLayout(bill_layout)

    def show_bill(self, bill) -> None:
        price_total = 0.0
        tax_total = 0.0
        self.bill_table.setRowCount(len(bill))
        for row_idx, item in enumerate(bill):
            p_id, name, hsn, unit_price, quantity, unit, tax_perc = item
            self.bill_table.setItem(row_idx, 0, QTableWidgetItem(str(p_id)))
            self.bill_table.setItem(row_idx, 1, QTableWidgetItem(str(name)))
            self.bill_table.setItem(row_idx, 2, QTableWidgetItem(str(hsn)))
            unit_price_no_tax = unit_price * (100 / (100 + tax_perc)) if tax_perc else unit_price
            self.bill_table.setItem(row_idx, 3, QTableWidgetItem(str(round(unit_price_no_tax, 2))))
            self.bill_table.setItem(row_idx, 4, QTableWidgetItem(str(quantity)))
            self.bill_table.setItem(row_idx, 5, QTableWidgetItem(str(unit)))
            price_no_tax = unit_price_no_tax * quantity
            self.bill_table.setItem(row_idx, 6, QTableWidgetItem(str(round(price_no_tax, 2))))
            self.bill_table.setItem(row_idx, 7, QTableWidgetItem(str(tax_perc)))
            tax_amt = price_no_tax * tax_perc / 100
            self.bill_table.setItem(row_idx, 8, QTableWidgetItem(str(round(tax_amt, 2))))
            total_amt = unit_price * quantity
            self.bill_table.setItem(row_idx, 9, QTableWidgetItem(str(total_amt)))
            price_total += price_no_tax
            tax_total += tax_amt

        self.bill_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        grand_total = price_total + tax_total
        self.total_label.setText(
            f"Price total: {price_total:.2f}    Tax total: {tax_total:.2f}    Grand total: {grand_total:.2f}    "
        )
        self.total_label.setAlignment(Qt.AlignmentFlag.AlignRight)


class BillViewer(QWidget):
    def __init__(self, db: DataBase, parent: QWidget | None = None):
        super().__init__(parent)
        self.db = db

        layout = QHBoxLayout()
        self.list_filter_layout = QVBoxLayout()

        self.filter_toggle = QCheckBox("Filter")
        self.list_filter_layout.addWidget(self.filter_toggle)
        self.filter_toggle.stateChanged.connect(self.on_filter_changed)

        start_layout = QHBoxLayout()
        start_layout.addWidget(QLabel("StartTime:"))
        self.startDate = QDateTimeEdit()
        start_layout.addWidget(self.startDate)
        self.list_filter_layout.addLayout(start_layout)
        self.startDate.dateTimeChanged.connect(self.on_filter_changed)

        end_layout = QHBoxLayout()
        end_layout.addWidget(QLabel("EndTime:"))
        self.endDate = QDateTimeEdit()
        end_layout.addWidget(self.endDate)
        self.list_filter_layout.addLayout(end_layout)
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
        self.summary_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.summary_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.summary_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.list_filter_layout.addWidget(self.summary_table)

        self.bill_table = BillTable(db)

        layout.addLayout(self.list_filter_layout, 4)
        layout.addWidget(self.bill_table, 6)

        self.setLayout(layout)
        self.load_bills()

    def on_filter_changed(self) -> None:
        self.load_bills()

    def load_bills(self) -> None:
        if self.filter_toggle.checkState() == Qt.CheckState.Checked:
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

    def update_summary_label(self, summary: Dict[str, Any]) -> None:
        text = f"<b>Total Sales:</b> ₹{summary['total_price']:.2f}<br><br><b>Products Sold:</b><br>"
        self.summary_label.setText(text)
        product_summary = summary["product_summary"]
        self.summary_table.setRowCount(len(product_summary))
        for row, ((_, p_name), data) in enumerate(product_summary.items()):
            self.summary_table.setItem(row, 0, QTableWidgetItem(p_name))
            self.summary_table.setItem(row, 1, QTableWidgetItem(str(data["total_quantity"])))

    def load_bill_items(self, item: QListWidgetItem) -> None:
        bill_id = item.data(Qt.ItemDataRole.UserRole)
        items = self.db.get_bill_items(bill_id)
        self.bill_table.show_bill(items)

    def show_context_menu(self, position: QPoint) -> None:
        item = self.bill_list.itemAt(position)
        if not item:
            return
        menu = QMenu(self)
        print_action = menu.addAction("Print")
        delete_action = None
        if get_elevation() == "admin":
            delete_action = menu.addAction("Delete")

        action = menu.exec(self.bill_list.mapToGlobal(position))
        if action == print_action:
            self.print_bill(item)
        elif action == delete_action and get_elevation() == "admin":
            self.delete_bill(item)

    def print_bill(self, item: QListWidgetItem) -> None:
        invoice_no = item.data(Qt.ItemDataRole.UserRole)
        if invoice_no:
            bill = self.db.get_bill_items(invoice_no)
            BillPrinter(invoice_no, self.db.get_bill_date(invoice_no), bill).print_bill()

    def delete_bill(self, item: QListWidgetItem) -> None:
        bill_id = item.data(Qt.ItemDataRole.UserRole)
        reply = QMessageBox.question(
            self,
            "Delete Bill",
            f"Are you sure you want to delete Bill with invoice_no: {bill_id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.db.delete_bill(bill_id)
            self.load_bills()
            log_msg(f"Deleted Bill with invoice No: {bill_id} deleted successfully.")
