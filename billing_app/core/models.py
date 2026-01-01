"""SQLAlchemy ORM models for BillingApp."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Role(Base):
    __tablename__ = "roles"
    role_name = Column(String, primary_key=True)


class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    role_name = Column(String, ForeignKey("roles.role_name"), nullable=False)
    role = relationship("Role")


class Product(Base):
    __tablename__ = "product"
    p_id = Column(Integer, primary_key=True, autoincrement=True)
    p_name = Column(String, nullable=False)
    HSN = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    stock = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    tax_perc = Column(Float, nullable=False)
    description = Column("p_desc", Text, nullable=True, default="")


class CurrBill(Base):
    __tablename__ = "curr_bill"
    p_id = Column(Integer, primary_key=True)
    p_name = Column(String, nullable=False)
    HSN = Column(String, nullable=False)
    unit_price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    tax_perc = Column(Float, nullable=False)


class Bill(Base):
    __tablename__ = "bills"
    bill_id = Column(Integer, primary_key=True, autoincrement=True)
    creator = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.now)
    items = relationship("BillItem", back_populates="bill", cascade="all, delete-orphan")


class BillItem(Base):
    __tablename__ = "bill_items"
    bill_id = Column(Integer, ForeignKey("bills.bill_id", ondelete="CASCADE"), primary_key=True)
    p_id = Column(Integer, primary_key=True)
    p_name = Column(String, nullable=False)
    HSN = Column(String, nullable=False)
    unit_price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    tax_perc = Column(Float, nullable=False)

    bill = relationship("Bill", back_populates="items")
