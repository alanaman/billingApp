"""SQLite database helpers backed by SQLAlchemy ORM."""
from __future__ import annotations

import os
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import bcrypt
from PyQt6.QtCore import QDateTime
from sqlalchemy import String, cast, create_engine, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from .models import Base, Bill, BillItem, CurrBill, Product, Role, User
from .paths import resource_path
from .state import get_user, log_msg


class DataBase:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

        self.engine = create_engine(f"sqlite+pysqlite:///{db_path}", echo=False, future=True)
        self.SessionLocal = sessionmaker(bind=self.engine, autoflush=False, expire_on_commit=False, future=True)

        self._ensure_schema()
        self.product_columns = ["p_id", "p_name", "HSN", "price", "stock", "unit", "tax_perc", "p_desc"]

    @contextmanager
    def session_scope(self) -> Iterable[Session]:
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def _ensure_schema(self) -> None:
        Base.metadata.create_all(self.engine)

        with self.session_scope() as session:
            for role_name in ("admin", "user"):
                if not session.scalar(select(Role).where(Role.role_name == role_name)):
                    session.add(Role(role_name=role_name))

            if not session.scalar(select(User).where(User.username == "admin")):
                hashed_pw = bcrypt.hashpw("admin".encode(), bcrypt.gensalt()).decode()
                session.add(User(username="admin", password=hashed_pw, role_name="admin"))

    def get_user_data(self, username: str) -> Optional[Tuple[str, str]]:
        with self.session_scope() as session:
            user = session.scalar(select(User).where(User.username == username))
            return (user.password, user.role_name) if user else None

    def get_users(self) -> List[Tuple[Any, ...]]:
        with self.session_scope() as session:
            rows = session.scalars(select(User)).all()
            return [(u.user_id, u.username, u.password, u.role_name) for u in rows]

    def add_user(self, username: str, password: str, role: str) -> None:
        hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        try:
            with self.session_scope() as session:
                session.add(User(username=username, password=hashed_pw, role_name=role))
                log_msg("User added successfully")
        except SQLAlchemyError as exc:
            log_msg(f"Error adding user: {exc}")

    def delete_user(self, user_id: int | str) -> None:
        try:
            with self.session_scope() as session:
                user = session.get(User, int(user_id))
                if user:
                    session.delete(user)
                    log_msg("User deleted successfully")
        except SQLAlchemyError as exc:
            log_msg(f"Error deleting user: {exc}")

    def add_product(self, product_id: str, name: str, hsn: str, price: str, stock: str, unit: str, tax_perc: str, desc: str) -> Optional[str]:
        try:
            price_val = float(price)
            stock_val = float(stock)
            tax_val = float(tax_perc)
        except Exception:  # pylint: disable=broad-except
            return log_msg("Invalid numeric value provided for product")

        with self.session_scope() as session:
            if product_id and session.get(Product, int(product_id)):
                return log_msg("Product ID already exists")

            product = Product(
                p_id=int(product_id) if product_id else None,
                p_name=name,
                HSN=hsn,
                price=price_val,
                stock=stock_val,
                unit=unit,
                tax_perc=tax_val,
                description=desc,
            )
            session.add(product)
            log_msg("Product added successfully")
        return None

    def get_products(self) -> List[Tuple[Any, ...]]:
        with self.session_scope() as session:
            rows = session.scalars(select(Product)).all()
            return [
                (
                    p.p_id,
                    p.p_name,
                    p.HSN,
                    p.price,
                    p.stock,
                    p.unit,
                    p.tax_perc,
                    p.description or "",
                )
                for p in rows
            ]

    def update_product(self, product_id: str, column_idx: int, new_value: str) -> None:
        attr_map = {
            0: "p_id",
            1: "p_name",
            2: "HSN",
            3: "price",
            4: "stock",
            5: "unit",
            6: "tax_perc",
            7: "description",
        }
        attr = attr_map.get(column_idx)
        if attr is None:
            return

        with self.session_scope() as session:
            product = session.get(Product, int(product_id))
            if not product:
                return
            if attr == "p_id":
                product.p_id = int(new_value)
            elif attr in {"price", "stock", "tax_perc"}:
                try:
                    setattr(product, attr, float(new_value))
                except Exception:  # pylint: disable=broad-except
                    log_msg("Invalid numeric value")
                    return
            else:
                setattr(product, attr, new_value)
            log_msg("Product updated successfully")

    def delete_product(self, product_id: str) -> None:
        with self.session_scope() as session:
            product = session.get(Product, int(product_id))
            if product:
                session.delete(product)
                log_msg("Product(s) deleted successfully")

    def search_products(self, search_query: str) -> List[Tuple[Any, ...]]:
        with self.session_scope() as session:
            like_val = f"%{search_query}%"
            rows = session.scalars(
                select(Product).where((Product.p_name.like(like_val)) | (cast(Product.p_id, String).like(like_val)))
            ).all()
            return [
                (
                    p.p_id,
                    p.p_name,
                    p.HSN,
                    p.price,
                    p.stock,
                    p.unit,
                    p.tax_perc,
                    p.description or "",
                )
                for p in rows
            ]

    def get_current_bill(self) -> List[Tuple[Any, ...]]:
        with self.session_scope() as session:
            rows = session.scalars(select(CurrBill)).all()
            return [
                (
                    b.p_id,
                    b.p_name,
                    b.HSN,
                    b.unit_price,
                    b.quantity,
                    b.unit,
                    b.tax_perc,
                )
                for b in rows
            ]

    def clear_current_bill(self) -> None:
        with self.session_scope() as session:
            session.query(CurrBill).delete()
            log_msg("Bill cleared")

    def add_item_to_bill(self, product_id: str, quantity: float, override: bool = True) -> None:
        with self.session_scope() as session:
            product = session.get(Product, int(product_id))
            if not product:
                log_msg("Product not found")
                return

            existing = session.get(CurrBill, int(product_id))
            if override:
                if quantity == 0:
                    if existing:
                        session.delete(existing)
                        log_msg(f"Product {product_id} removed from bill")
                    return
                if existing:
                    existing.quantity = quantity
                else:
                    session.add(
                        CurrBill(
                            p_id=product.p_id,
                            p_name=product.p_name,
                            HSN=product.HSN,
                            unit_price=product.price,
                            quantity=quantity,
                            unit=product.unit,
                            tax_perc=product.tax_perc,
                        )
                    )
                log_msg(f"Product {product_id} quantity set to: {quantity}")
            else:
                if not existing:
                    session.add(
                        CurrBill(
                            p_id=product.p_id,
                            p_name=product.p_name,
                            HSN=product.HSN,
                            unit_price=product.price,
                            quantity=quantity,
                            unit=product.unit,
                            tax_perc=product.tax_perc,
                        )
                    )
                    log_msg(f"Product {product_id} added to bill. Enter quantity")

    def remove_item_from_bill(self, product_id: str) -> None:
        with self.session_scope() as session:
            existing = session.get(CurrBill, int(product_id))
            if existing:
                session.delete(existing)
                log_msg(f"Product {product_id} removed from bill")

    def get_next_bill_id(self) -> int:
        with self.session_scope() as session:
            max_id = session.scalar(select(func.coalesce(func.max(Bill.bill_id), 0)))
            return int(max_id) + 1

    def save_bill(self) -> Optional[int]:
        with self.session_scope() as session:
            curr_items = session.scalars(select(CurrBill)).all()
            if not curr_items:
                log_msg("No items in bill to save")
                return None

            bill = Bill(creator=get_user() or "unknown")
            session.add(bill)
            session.flush()

            for item in curr_items:
                session.add(
                    BillItem(
                        bill_id=bill.bill_id,
                        p_id=item.p_id,
                        p_name=item.p_name,
                        HSN=item.HSN,
                        unit_price=item.unit_price,
                        quantity=item.quantity,
                        unit=item.unit,
                        tax_perc=item.tax_perc,
                    )
                )
                product = session.get(Product, item.p_id)
                if product:
                    product.stock -= item.quantity

            session.query(CurrBill).delete()
            log_msg("Bill saved to database. Stock updated")
            return bill.bill_id

    def save_bill_override_id(self, bill_id: int) -> Optional[int]:
        with self.session_scope() as session:
            curr_items = session.scalars(select(CurrBill)).all()
            if not curr_items:
                log_msg("No items in bill to save")
                return None

            existing = session.get(Bill, bill_id)
            if existing:
                for item in existing.items:
                    product = session.get(Product, item.p_id)
                    if product:
                        product.stock += item.quantity
                session.delete(existing)
                session.flush()

            bill = Bill(bill_id=bill_id, creator=get_user() or "unknown")
            session.add(bill)
            session.flush()

            for item in curr_items:
                session.add(
                    BillItem(
                        bill_id=bill.bill_id,
                        p_id=item.p_id,
                        p_name=item.p_name,
                        HSN=item.HSN,
                        unit_price=item.unit_price,
                        quantity=item.quantity,
                        unit=item.unit,
                        tax_perc=item.tax_perc,
                    )
                )
                product = session.get(Product, item.p_id)
                if product:
                    product.stock -= item.quantity

            session.query(CurrBill).delete()
            log_msg("Bill saved to database. Stock updated")
            return bill.bill_id

    def does_invoice_id_exist(self, bill_id: int) -> bool:
        with self.session_scope() as session:
            return bool(session.get(Bill, bill_id))

    def get_bill_date(self, bill_id: int) -> datetime:
        with self.session_scope() as session:
            bill = session.get(Bill, bill_id)
            return bill.timestamp if bill else datetime(1970, 1, 1)

    def get_bills(self, start_datetime: Optional[QDateTime] = None, end_datetime: Optional[QDateTime] = None) -> List[Tuple[Any, ...]]:
        if start_datetime is None:
            start_datetime = QDateTime.fromString("1970-01-01 00:00:00", "yyyy-MM-dd HH:mm:ss")
        if end_datetime is None:
            end_datetime = QDateTime.fromString("9999-12-31 23:59:59", "yyyy-MM-dd HH:mm:ss")

        start_dt = start_datetime.toPyDateTime()
        end_dt = end_datetime.toPyDateTime()

        with self.session_scope() as session:
            rows = session.scalars(
                select(Bill).where(Bill.timestamp.between(start_dt, end_dt)).order_by(Bill.timestamp.desc())
            ).all()
            return [(b.bill_id, b.creator, b.timestamp) for b in rows]

    def get_bill_summary(self, start_datetime: Optional[QDateTime] = None, end_datetime: Optional[QDateTime] = None) -> Dict[str, Any]:
        if start_datetime is None:
            start_datetime = QDateTime.fromString("1970-01-01 00:00:00", "yyyy-MM-dd HH:mm:ss")
        if end_datetime is None:
            end_datetime = QDateTime.fromString("9999-12-31 23:59:59", "yyyy-MM-dd HH:mm:ss")

        start_dt = start_datetime.toPyDateTime()
        end_dt = end_datetime.toPyDateTime()

        with self.session_scope() as session:
            rows = session.execute(
                select(
                    BillItem.p_id,
                    BillItem.p_name,
                    func.sum(BillItem.quantity),
                    func.sum(BillItem.quantity * BillItem.unit_price),
                )
                .join(Bill, Bill.bill_id == BillItem.bill_id)
                .where(Bill.timestamp.between(start_dt, end_dt))
                .group_by(BillItem.p_id, BillItem.p_name)
            ).all()

            total_price = 0.0
            product_summary: Dict[Tuple[int, str], Dict[str, float]] = {}
            for p_id, p_name, total_quantity, total_price_per_product in rows:
                product_summary[(p_id, p_name)] = {
                    "total_quantity": float(total_quantity),
                    "total_price": float(total_price_per_product),
                }
                total_price += float(total_price_per_product)

            return {"total_price": total_price, "product_summary": product_summary}

    def get_bill_items(self, bill_id: int) -> List[Tuple[Any, ...]]:
        with self.session_scope() as session:
            rows = session.scalars(select(BillItem).where(BillItem.bill_id == bill_id)).all()
            return [
                (
                    bi.p_id,
                    bi.p_name,
                    bi.HSN,
                    bi.unit_price,
                    bi.quantity,
                    bi.unit,
                    bi.tax_perc,
                )
                for bi in rows
            ]

    def delete_bill(self, bill_id: int) -> bool:
        try:
            with self.session_scope() as session:
                bill = session.get(Bill, bill_id)
                if not bill:
                    return False

                for item in bill.items:
                    product = session.get(Product, item.p_id)
                    if product:
                        product.stock += item.quantity

                session.delete(bill)
                log_msg("Bill deleted from database. Stock updated")
                return True
        except SQLAlchemyError as exc:
            log_msg(f"Failed to delete bill from database: {exc}")
            return False
