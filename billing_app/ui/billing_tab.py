"""Billing tab with product search and bill table."""
from __future__ import annotations

from typing import List, Tuple

from PyQt6.QtCore import QPoint, Qt, QAbstractListModel, QModelIndex
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListView,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from billing_app.core.database import DataBase
from billing_app.core.state import get_elevation, log_msg
from billing_app.printing.bill_printer import BillPrinter
from billing_app.ui.bills_tab import BillTable


class DropDownWindow(QListView):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.hide()

    def focusOutEvent(self, event):  # type: ignore[override]
        self.hide()
        return super().focusOutEvent(event)


class IndexedListModel(QAbstractListModel):
    def __init__(self, items: List[Tuple[int, str, float]] | None = None):
        super().__init__()
        self.items = items or []

    def rowCount(self, parent=None):  # noqa: N802 - Qt signature
        return len(self.items)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):  # noqa: N802
        if not index.isValid():
            return None
        p_id, name, price = self.items[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            return f"{p_id} - {name} - Rs. {price}/-"
        if role == Qt.ItemDataRole.UserRole:
            return p_id
        return None


class BillingTab(QWidget):
    def __init__(self, db: DataBase, parent: QWidget | None = None):
        super().__init__(parent)
        self.db = db
        self.product_data: List[Tuple[int, str, float]] = []
        self.last_added_product_id: int | None = None

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        search_label = QLabel("Search Product to Add to Bill:")
        self.product_search = QLineEdit()
        self.product_search.setPlaceholderText("Type to search...")

        self.invoice_id_label = QLabel("Invoice ID: ")
        self.override_invoice_id_toggle = QCheckBox("Override")
        self.override_id_input = QLineEdit()
        self.override_id_input.setPlaceholderText("Override Invoice ID")

        quantity_label = QLabel("Enter Quantity")
        self.quantity_input = QLineEdit()
        self.quantity_input.setPlaceholderText("Enter Quantity")

        self.list_widget = DropDownWindow(self)

        self.bill_table = BillTable(db)

        self.print_button = QPushButton("Print Bill")
        self.clear_button = QPushButton("New Bill")

        invoice_section = QHBoxLayout()
        invoice_section.addWidget(self.invoice_id_label)
        if get_elevation() == "admin":
            invoice_section.addWidget(self.override_invoice_id_toggle)
            invoice_section.addWidget(self.override_id_input)

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

        bill_layout = QVBoxLayout()
        bill_layout.addLayout(invoice_section)
        bill_layout.addLayout(entry_section)
        bill_layout.addWidget(self.bill_table)
        bill_layout.addLayout(button_section)

        self.setLayout(bill_layout)

        self.product_search.textChanged.connect(self.update_completer)
        self.product_search.returnPressed.connect(self.handle_search_enter_pressed)
        self.list_widget.clicked.connect(self.handle_search_popup_activated)
        self.quantity_input.returnPressed.connect(self.handle_quantity_enter_pressed)

        self.print_button.clicked.connect(self.print_bill)
        self.clear_button.clicked.connect(self.clear_bill)

        self.update_bill()

    def get_next_bill_id(self) -> int:
        return self.db.get_next_bill_id()

    def keyPressEvent(self, event: QKeyEvent) -> None:  # type: ignore[override]
        if event.key() == Qt.Key.Key_P and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.print_bill()
        if event.key() == Qt.Key.Key_N and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.clear_bill()

    def show_popup(self) -> None:
        self.list_widget.setMinimumWidth(self.product_search.width())
        pos = self.product_search.mapToGlobal(QPoint(0, self.product_search.height()))
        self.list_widget.move(pos)
        rows = min(self.list_widget.model().rowCount(), 10) if self.list_widget.model() else 0
        self.list_widget.resize(self.product_search.width(), rows * 20)
        self.list_widget.show()

    def hide_popup(self) -> None:
        if self.hasFocus():
            self.list_widget.hide()

    def update_completer(self) -> None:
        search_text = self.product_search.text()
        if not search_text:
            self.list_widget.hide()
            return

        products = self.db.search_products(search_text)
        if not products:
            self.product_data = []
            self.list_widget.hide()
            return

        self.product_data = [(p_id, name, price) for p_id, name, hsn, price, stock, unit, tax, desc in products]
        self.list_widget.setModel(IndexedListModel(self.product_data))
        self.show_popup()

    def add_product_to_bill(self, product_id: int, quantity: float, override: bool = True) -> None:
        self.db.add_item_to_bill(str(product_id), quantity, override)
        self.update_bill()
        self.last_added_product_id = product_id

    def update_bill(self) -> None:
        self.invoice_id_label.setText(f"Invoice ID: {self.get_next_bill_id()}")
        bill = self.db.get_current_bill()
        self.bill_table.show_bill(bill)

    def clear_bill(self) -> None:
        self.db.clear_current_bill()
        self.update_bill()

    def handle_search_enter_pressed(self) -> None:
        if not self.product_data:
            return
        p_id, _, _ = self.product_data[0]
        self.add_product_to_bill(product_id=p_id, quantity=1, override=False)
        self.quantity_input.setFocus()

    def handle_search_popup_activated(self, index: QModelIndex) -> None:
        p_id = self.list_widget.model().data(index, Qt.ItemDataRole.UserRole)
        if p_id is None:
            return
        self.product_search.setText(str(p_id))
        self.add_product_to_bill(product_id=p_id, quantity=1, override=False)
        self.list_widget.hide()
        self.quantity_input.setFocus()

    def handle_quantity_enter_pressed(self) -> None:
        if not self.product_data:
            return
        try:
            quantity = float(self.quantity_input.text())
        except Exception:  # pylint: disable=broad-except
            return

        if self.product_search.text() == "":
            if self.last_added_product_id is not None:
                self.add_product_to_bill(self.last_added_product_id, quantity)
            return

        first_item = self.product_data[0][0]
        self.add_product_to_bill(first_item, quantity)
        self.quantity_input.clear()
        self.product_search.clear()
        self.product_search.setFocus()

    def _save_bill(self) -> int | None:
        if not len(self.db.get_current_bill()):
            log_msg("No items in bill to save")
            return None

        if self.override_invoice_id_toggle.checkState() == Qt.CheckState.Unchecked:
            reply = QMessageBox.question(
                self,
                "Confirm Save",
                "Are you sure you want to save and print this bill?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                invoice_no = self.db.save_bill()
                self.update_bill()
                return invoice_no
        else:
            try:
                override_id = int(self.override_id_input.text())
            except Exception:  # pylint: disable=broad-except
                log_msg("Invalid Invoice No.")
                return None

            display_text = "Invoice Id already exists. Are you sure you want to override?" if self.db.does_invoice_id_exist(override_id) else "Are you sure you want to save and print this bill?"
            reply = QMessageBox.question(
                self,
                "Confirm Save",
                display_text,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                invoice_no = self.db.save_bill_override_id(override_id)
                self.update_bill()
                return invoice_no
        return None

    def print_bill(self) -> None:
        invoice_no = self._save_bill()
        if invoice_no:
            bill = self.db.get_bill_items(invoice_no)
            BillPrinter(invoice_no, self.db.get_bill_date(invoice_no), bill).print_bill()
