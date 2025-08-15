"""
Enhanced data models for the Curtain Quotation System.
Includes all entities: Products, Customers, Quotations, Employees, Assignments, Payments.
"""

import enum
from datetime import datetime, date, time
from decimal import Decimal
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Date, Time, Boolean,
    ForeignKey, UniqueConstraint, Enum
)
from sqlalchemy.types import DECIMAL as SQLDecimal
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


Base = declarative_base()


# Enums
class UnitType(enum.Enum):
    AREA = "area"
    WIDTH = "width" 
    LENGTH = "length"
    PCS = "pcs"


class DiscountType(enum.Enum):
    PERCENT = "percent"
    FIXED = "fixed"


class Currency(enum.Enum):
    SAR = "SAR"
    USD = "USD"


class CustomerType(enum.Enum):
    INDIVIDUAL = "individual"
    COMPANY = "company"


class QuotationStatus(enum.Enum):
    DRAFT = "draft"
    SENT = "sent"
    ACCEPTED = "accepted"
    LOST = "lost"


class AssignmentType(enum.Enum):
    DELIVERY = "delivery"
    INSTALLATION = "installation"


class AssignmentStatus(enum.Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"


class PaymentMethod(enum.Enum):
    CASH = "cash"
    CARD = "card"
    TRANSFER = "transfer"
    OTHER = "other"


# Models
class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    email = Column(String(100))
    phone = Column(String(20))
    address = Column(Text)
    
    # Enhanced fields
    type = Column(Enum(CustomerType), default=CustomerType.INDIVIDUAL, nullable=False)
    company_name = Column(String(200))
    company_vat = Column(String(50))
    company_address = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    quotations = relationship("Quotation", back_populates="customer")


class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    category = Column(String(100))
    
    # Enhanced pricing fields
    unit_type = Column(Enum(UnitType), default=UnitType.AREA, nullable=False)
    base_unit_price = Column(SQLDecimal(10, 2), nullable=False)
    
    currency = Column(Enum(Currency), default=Currency.SAR, nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    variations = relationship("ProductVariation", back_populates="product", cascade="all, delete-orphan")
    quote_items = relationship("QuoteItem", back_populates="product")
    
    # Self-referential many-to-many for linked products
    linked_products = relationship(
        "ProductLink",
        foreign_keys="ProductLink.product_id",
        back_populates="product"
    )


class ProductVariation(Base):
    __tablename__ = "product_variations"
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    name = Column(String(100), nullable=False)  # e.g., "Red", "Blue", "Large"
    unit_price_override = Column(SQLDecimal(10, 2))  # Optional price override
    sku = Column(String(50))
    image_path = Column(String(500))  # Relative path to image file
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    product = relationship("Product", back_populates="variations")
    quote_items = relationship("QuoteItem", back_populates="product_variation")


class ProductLink(Base):
    __tablename__ = "product_links"
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    linked_product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    link_type = Column(String(50))  # e.g., "accessory", "complement"
    note = Column(String(200))
    
    # Relationships
    product = relationship("Product", foreign_keys=[product_id], back_populates="linked_products")
    linked_product = relationship("Product", foreign_keys=[linked_product_id])


class Employee(Base):
    __tablename__ = "employees"
    
    id = Column(Integer, primary_key=True)
    full_name = Column(String(200), nullable=False)
    phone = Column(String(20))
    role = Column(String(100))
    active = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    assignments = relationship("Assignment", back_populates="assigned_employee")


class Quotation(Base):
    __tablename__ = "quotations"
    
    id = Column(Integer, primary_key=True)
    serial_number = Column(String(20), unique=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    
    # Status and workflow
    status = Column(Enum(QuotationStatus), default=QuotationStatus.DRAFT, nullable=False)
    
    # Discount and tax settings
    header_discount_type = Column(Enum(DiscountType), default=DiscountType.FIXED, nullable=False)
    header_discount_value = Column(SQLDecimal(10, 2), default=Decimal('0.00'), nullable=False)
    tax_rate = Column(SQLDecimal(5, 4), default=Decimal('0.15'), nullable=False)  # 15% default
    
    # Computed totals (stored for performance and audit trail)
    subtotal_ex_vat = Column(SQLDecimal(12, 2), default=Decimal('0.00'))
    discount_header = Column(SQLDecimal(12, 2), default=Decimal('0.00'))
    discounted_ex_vat = Column(SQLDecimal(12, 2), default=Decimal('0.00'))
    vat_amount = Column(SQLDecimal(12, 2), default=Decimal('0.00'))
    grand_total = Column(SQLDecimal(12, 2), default=Decimal('0.00'))
    
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    customer = relationship("Customer", back_populates="quotations")
    items = relationship("QuoteItem", back_populates="quotation", cascade="all, delete-orphan")
    assignments = relationship("Assignment", back_populates="quotation")
    payments = relationship("Payment", back_populates="quotation", cascade="all, delete-orphan")


class QuoteItem(Base):
    __tablename__ = "quote_items"
    
    id = Column(Integer, primary_key=True)
    quotation_id = Column(Integer, ForeignKey("quotations.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    product_variation_id = Column(Integer, ForeignKey("product_variations.id"))
    
    # Item specifications
    color_text = Column(String(100))  # Free text color if no variation selected
    width = Column(SQLDecimal(8, 4))  # meters, 4 decimal places
    height = Column(SQLDecimal(8, 4))  # meters, 4 decimal places
    area = Column(SQLDecimal(10, 4), nullable=False, default=Decimal('0.0000'))  # computed: width * height
    quantity = Column(Integer, default=1, nullable=False)
    total_area = Column(SQLDecimal(10, 4), nullable=False, default=Decimal('0.0000'))  # computed: area * quantity
    
    # Pricing
    unit_price = Column(SQLDecimal(10, 2), nullable=False)  # Effective price used
    discount_type = Column(Enum(DiscountType), default=DiscountType.FIXED, nullable=False)
    discount_value = Column(SQLDecimal(10, 2), default=Decimal('0.00'), nullable=False)
    
    # Computed line totals
    line_total_ex_vat = Column(SQLDecimal(12, 2), nullable=False, default=Decimal('0.00'))
    vat_amount = Column(SQLDecimal(12, 2), nullable=False, default=Decimal('0.00'))
    line_total_inc_vat = Column(SQLDecimal(12, 2), nullable=False, default=Decimal('0.00'))
    
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    quotation = relationship("Quotation", back_populates="items")
    product = relationship("Product", back_populates="quote_items")
    product_variation = relationship("ProductVariation", back_populates="quote_items")


class Assignment(Base):
    __tablename__ = "assignments"
    
    id = Column(Integer, primary_key=True)
    quotation_id = Column(Integer, ForeignKey("quotations.id"), nullable=False)
    type = Column(Enum(AssignmentType), nullable=False)
    
    # Scheduling
    scheduled_date = Column(Date, nullable=False)
    time_start = Column(Time)
    time_end = Column(Time)
    
    # Location and assignment
    location = Column(Text, nullable=False)
    assigned_employee_id = Column(Integer, ForeignKey("employees.id"))
    
    # Status and notes
    status = Column(Enum(AssignmentStatus), default=AssignmentStatus.PLANNED, nullable=False)
    notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    quotation = relationship("Quotation", back_populates="assignments")
    assigned_employee = relationship("Employee", back_populates="assignments")
    
    # Computed property for customer (via quotation)
    @property
    def customer(self):
        return self.quotation.customer if self.quotation else None


class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True)
    quotation_id = Column(Integer, ForeignKey("quotations.id"), nullable=False)
    
    date = Column(Date, nullable=False)
    amount = Column(SQLDecimal(12, 2), nullable=False)
    method = Column(Enum(PaymentMethod), nullable=False)
    reference = Column(String(100))  # Check number, transaction ID, etc.
    notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    quotation = relationship("Quotation", back_populates="payments")


class CompanySettings(Base):
    __tablename__ = "company_settings"
    
    id = Column(Integer, primary_key=True)
    company_name = Column(String(200), default="Adhlal")
    logo_path = Column(String(500))
    address = Column(Text)
    phone = Column(String(20))
    email = Column(String(100))
    website = Column(String(200))
    default_currency = Column(Enum(Currency), default=Currency.SAR)
    default_tax_rate = Column(SQLDecimal(5, 4), default=Decimal('0.15'))
    
    # Copy format for item copy button
    clipboard_copy_format = Column(String(200), default='"{ItemName} {Color} {W} {H}"')
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
