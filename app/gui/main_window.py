"""
Main window for the Curtain Quotation System v3.0.
Enhanced with rich quotation workflow, logistics, and payments.
"""

import sys
from decimal import Decimal
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QFrame, QGroupBox, QFormLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QLineEdit, QTextEdit, QComboBox, QSpinBox,
    QDateEdit, QTimeEdit, QMessageBox, QDialog, QDialogButtonBox,
    QFileDialog, QSplitter, QScrollArea, QGridLayout, QStackedWidget,
    QRadioButton, QListWidget, QListWidgetItem, QCheckBox, QAbstractItemView
)
from PySide6.QtCore import Qt, QTimer, QDate, QTime
from PySide6.QtGui import QFont, QColor, QAction, QPixmap

# Import our modules
from core.database import get_db_session
from core.models import (
    Customer, Product, ProductVariation, Employee, Quotation, QuoteItem,
    Assignment, Payment, CompanySettings, CustomerType, UnitType,
    QuotationStatus, AssignmentType, PaymentMethod, DiscountType
)
from core.services import (
    CustomerService, ProductService, EmployeeService, QuotationService,
    PaymentService, AssignmentService, CompanyService
)
from core.calculations import calc_line_totals
from core.paths import app_paths
from gui.widgets import ModernButton, DashboardCard, EditableTable, DecimalSpinBox, StyledComboBox
from gui.quotation_form import QuotationForm


class CustomerDialog(QDialog):
    """Enhanced customer dialog with company fields and customer types."""
    
    def __init__(self, parent=None, customer=None):
        super().__init__(parent)
        self.customer = customer
        self.is_edit_mode = customer is not None
        
        self.setWindowTitle("Edit Customer" if self.is_edit_mode else "Add New Customer")
        self.setModal(True)
        self.setMinimumSize(600, 500)
        self.setup_ui()
        
        if self.is_edit_mode:
            self.load_customer_data()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Customer type selection
        type_group = QGroupBox("Customer Type")
        type_layout = QHBoxLayout(type_group)
        
        self.individual_radio = QRadioButton("Individual")
        self.company_radio = QRadioButton("Company")
        self.individual_radio.setChecked(True)
        
        self.individual_radio.toggled.connect(self.on_type_changed)
        self.company_radio.toggled.connect(self.on_type_changed)
        
        type_layout.addWidget(self.individual_radio)
        type_layout.addWidget(self.company_radio)
        layout.addWidget(type_group)
        
        # Basic information
        basic_group = QGroupBox("Basic Information")
        basic_layout = QFormLayout(basic_group)
        
        self.name_edit = QLineEdit()
        self.email_edit = QLineEdit()
        self.phone_edit = QLineEdit()
        self.address_edit = QTextEdit()
        self.address_edit.setMaximumHeight(80)
        
        basic_layout.addRow("Name:", self.name_edit)
        basic_layout.addRow("Email:", self.email_edit)
        basic_layout.addRow("Phone:", self.phone_edit)
        basic_layout.addRow("Address:", self.address_edit)
        
        layout.addWidget(basic_group)
        
        # Company information (initially hidden)
        self.company_group = QGroupBox("Company Information")
        company_layout = QFormLayout(self.company_group)
        
        self.company_name_edit = QLineEdit()
        self.company_vat_edit = QLineEdit()
        self.company_address_edit = QTextEdit()
        self.company_address_edit.setMaximumHeight(80)
        
        company_layout.addRow("Company Name:", self.company_name_edit)
        company_layout.addRow("VAT Number:", self.company_vat_edit)
        company_layout.addRow("Company Address:", self.company_address_edit)
        
        self.company_group.setVisible(False)
        layout.addWidget(self.company_group)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.save_customer)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # No custom styling - using default Qt appearance
    
    def on_type_changed(self):
        """Handle customer type change."""
        is_company = self.company_radio.isChecked()
        self.company_group.setVisible(is_company)
    
    def load_customer_data(self):
        """Load existing customer data for editing."""
        if not self.customer:
            return
        
        self.name_edit.setText(self.customer.name or "")
        self.email_edit.setText(self.customer.email or "")
        self.phone_edit.setText(self.customer.phone or "")
        self.address_edit.setPlainText(self.customer.address or "")
        
        # Set customer type
        if self.customer.type == CustomerType.COMPANY:
            self.company_radio.setChecked(True)
            self.company_name_edit.setText(self.customer.company_name or "")
            self.company_vat_edit.setText(self.customer.company_vat or "")
            self.company_address_edit.setPlainText(self.customer.company_address or "")
        else:
            self.individual_radio.setChecked(True)
    
    def save_customer(self):
        """Save the customer."""
        try:
            name = self.name_edit.text().strip()
            if not name:
                QMessageBox.warning(self, "Validation Error", "Customer name is required.")
                return
            
            email = self.email_edit.text().strip()
            phone = self.phone_edit.text().strip()
            address = self.address_edit.toPlainText().strip()
            
            customer_type = CustomerType.COMPANY if self.company_radio.isChecked() else CustomerType.INDIVIDUAL
            company_name = self.company_name_edit.text().strip() if self.company_radio.isChecked() else ""
            company_vat = self.company_vat_edit.text().strip() if self.company_radio.isChecked() else ""
            company_address = self.company_address_edit.toPlainText().strip() if self.company_radio.isChecked() else ""
            
            if self.is_edit_mode:
                # Update existing customer
                CustomerService.update_customer(
                    self.customer.id,
                    name=name,
                    email=email,
                    phone=phone,
                    address=address,
                    customer_type=customer_type,
                    company_name=company_name,
                    company_vat=company_vat,
                    company_address=company_address
                )
                QMessageBox.information(self, "Success", f"Customer '{name}' updated successfully!")
            else:
                # Create new customer
                CustomerService.create_customer(
                    name=name,
                    email=email,
                    phone=phone,
                    address=address,
                    customer_type=customer_type,
                    company_name=company_name,
                    company_vat=company_vat,
                    company_address=company_address
                )
                QMessageBox.information(self, "Success", f"Customer '{name}' created successfully!")
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save customer: {str(e)}")


class ProductDialog(QDialog):
    """Enhanced product dialog with variations, pricing units, images, and linked items."""
    
    def __init__(self, parent=None, product=None):
        super().__init__(parent)
        self.product = product
        self.is_edit_mode = product is not None
        
        self.setWindowTitle("Edit Product" if self.is_edit_mode else "Add New Product")
        self.setModal(True)
        self.setMinimumSize(800, 600)
        self.setup_ui()
        
        if self.is_edit_mode:
            self.load_product_data()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Basic information
        basic_group = QGroupBox("Basic Information")
        basic_layout = QFormLayout(basic_group)
        
        self.name_edit = QLineEdit()
        self.category_edit = QLineEdit()
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(60)
        
        # Unit type selector
        self.unit_type_combo = QComboBox()
        self.unit_type_combo.addItems(["Area (sqm)", "Width (m)", "Length (m)", "Pieces"])
        
        # Base unit price
        self.base_price_spin = DecimalSpinBox()
        self.base_price_spin.setRange(0, 999999)
        self.base_price_spin.setDecimals(2)
        self.base_price_spin.setSuffix(" SAR")
        
        basic_layout.addRow("Product Name:", self.name_edit)
        basic_layout.addRow("Category:", self.category_edit)
        basic_layout.addRow("Unit Type:", self.unit_type_combo)
        basic_layout.addRow("Base Unit Price:", self.base_price_spin)
        basic_layout.addRow("Notes:", self.notes_edit)
        
        layout.addWidget(basic_group)
        
        # Variations section
        variations_group = QGroupBox("Product Variations")
        variations_layout = QVBoxLayout(variations_group)
        
        # Variations controls
        variations_controls = QHBoxLayout()
        add_variation_btn = ModernButton("Add Variation", "primary", "small")
        add_variation_btn.clicked.connect(self.add_variation)
        variations_controls.addWidget(add_variation_btn)
        variations_controls.addStretch()
        variations_layout.addLayout(variations_controls)
        
        # Variations table
        self.variations_table = QTableWidget(0, 4)
        self.variations_table.setHorizontalHeaderLabels(["Name/Color", "Unit Price Override", "SKU", "Actions"])
        self.variations_table.horizontalHeader().setStretchLastSection(True)
        self.variations_table.setMaximumHeight(150)
        variations_layout.addWidget(self.variations_table)
        
        layout.addWidget(variations_group)
        
        # Linked items section
        linked_group = QGroupBox("Linked Items")
        linked_layout = QVBoxLayout(linked_group)
        
        linked_label = QLabel("Select products that are commonly sold together with this product:")
        linked_label.setStyleSheet("color: #cccccc; margin-bottom: 5px;")
        linked_layout.addWidget(linked_label)
        
        self.linked_list = QListWidget()
        self.linked_list.setMaximumHeight(120)
        self.linked_list.setSelectionMode(QAbstractItemView.MultiSelection)
        linked_layout.addWidget(self.linked_list)
        
        layout.addWidget(linked_group)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.save_product)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # No custom styling - using default Qt appearance
        
        # Load linked products
        self.load_linked_products()
    
    def load_linked_products(self):
        """Load available products for linking."""
        try:
            products = ProductService.get_all_products()
            self.linked_list.clear()
            
            for product in products:
                if not self.product or product.id != self.product.id:  # Don't include self
                    item = QListWidgetItem(product.name)
                    item.setData(Qt.UserRole, product.id)
                    self.linked_list.addItem(item)
        except Exception as e:
            print(f"Error loading products for linking: {e}")
    
    def add_variation(self):
        """Add a new variation row."""
        row = self.variations_table.rowCount()
        self.variations_table.insertRow(row)
        
        # Name/Color
        name_item = QTableWidgetItem("")
        self.variations_table.setItem(row, 0, name_item)
        
        # Unit Price Override
        price_item = QTableWidgetItem("")
        self.variations_table.setItem(row, 1, price_item)
        
        # SKU
        sku_item = QTableWidgetItem("")
        self.variations_table.setItem(row, 2, sku_item)
        
        # Actions
        actions_widget = QWidget()
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(5, 2, 5, 2)
        
        delete_btn = QPushButton("×")
        delete_btn.setMaximumSize(24, 24)
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336; color: white; border: none; border-radius: 4px;
                font-weight: bold; font-size: 12px;
            }
            QPushButton:hover { background-color: #d32f2f; }
        """)
        delete_btn.clicked.connect(lambda: self.delete_variation(row))
        
        actions_layout.addWidget(delete_btn)
        actions_layout.addStretch()
        
        self.variations_table.setCellWidget(row, 3, actions_widget)
    
    def delete_variation(self, row):
        """Delete a variation row."""
        self.variations_table.removeRow(row)
    
    def load_product_data(self):
        """Load existing product data for editing."""
        if not self.product:
            return
        
        self.name_edit.setText(self.product.name or "")
        self.category_edit.setText(self.product.category or "")
        self.notes_edit.setPlainText(self.product.notes or "")
        
        # Set unit type
        unit_type_map = {
            UnitType.AREA: 0,
            UnitType.WIDTH: 1, 
            UnitType.LENGTH: 2,
            UnitType.PCS: 3
        }
        self.unit_type_combo.setCurrentIndex(unit_type_map.get(self.product.unit_type, 0))
        
        # Set base price
        if self.product.base_unit_price:
            self.base_price_spin.setValue(float(self.product.base_unit_price))
        
        # Load variations
        try:
            variations = ProductService.get_product_variations(self.product.id)
            for variation in variations:
                row = self.variations_table.rowCount()
                self.variations_table.insertRow(row)
                
                self.variations_table.setItem(row, 0, QTableWidgetItem(variation.name or ""))
                price_override = str(float(variation.unit_price_override)) if variation.unit_price_override else ""
                self.variations_table.setItem(row, 1, QTableWidgetItem(price_override))
                self.variations_table.setItem(row, 2, QTableWidgetItem(variation.sku or ""))
                
                # Add delete button
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(5, 2, 5, 2)
                
                delete_btn = QPushButton("×")
                delete_btn.setMaximumSize(24, 24)
                delete_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #f44336; color: white; border: none; border-radius: 4px;
                        font-weight: bold; font-size: 12px;
                    }
                    QPushButton:hover { background-color: #d32f2f; }
                """)
                delete_btn.clicked.connect(lambda checked, r=row: self.delete_variation(r))
                
                actions_layout.addWidget(delete_btn)
                actions_layout.addStretch()
                
                self.variations_table.setCellWidget(row, 3, actions_widget)
        except Exception as e:
            print(f"Error loading variations: {e}")
        
        # Load linked products
        try:
            linked_products = ProductService.get_linked_products(self.product.id)
            for i in range(self.linked_list.count()):
                item = self.linked_list.item(i)
                product_id = item.data(Qt.UserRole)
                if any(link.linked_product_id == product_id for link in linked_products):
                    item.setSelected(True)
        except Exception as e:
            print(f"Error loading linked products: {e}")
    
    def save_product(self):
        """Save the product."""
        try:
            name = self.name_edit.text().strip()
            if not name:
                QMessageBox.warning(self, "Validation Error", "Product name is required.")
                return
            
            category = self.category_edit.text().strip()
            notes = self.notes_edit.toPlainText().strip()
            
            # Map unit type
            unit_type_map = [UnitType.AREA, UnitType.WIDTH, UnitType.LENGTH, UnitType.PCS]
            unit_type = unit_type_map[self.unit_type_combo.currentIndex()]
            
            base_price = Decimal(str(self.base_price_spin.value()))
            
            if self.is_edit_mode:
                # Update existing product
                ProductService.update_product(
                    self.product.id,
                    name=name,
                    category=category,
                    unit_type=unit_type,
                    base_unit_price=base_price,
                    notes=notes
                )
                product_id = self.product.id
                QMessageBox.information(self, "Success", f"Product '{name}' updated successfully!")
            else:
                # Create new product
                product = ProductService.create_product(
                    name=name,
                    category=category,
                    unit_type=unit_type,
                    base_unit_price=base_price,
                    notes=notes
                )
                product_id = product.id
                QMessageBox.information(self, "Success", f"Product '{name}' created successfully!")
            
            # Save variations
            self.save_variations(product_id)
            
            # Save linked products
            self.save_linked_products(product_id)
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save product: {str(e)}")
    
    def save_variations(self, product_id):
        """Save product variations."""
        try:
            # Clear existing variations if editing
            if self.is_edit_mode:
                ProductService.clear_product_variations(product_id)
            
            # Save new variations
            for row in range(self.variations_table.rowCount()):
                name = self.variations_table.item(row, 0).text().strip()
                price_text = self.variations_table.item(row, 1).text().strip()
                sku = self.variations_table.item(row, 2).text().strip()
                
                if name:  # Only save if name is provided
                    price_override = Decimal(price_text) if price_text else None
                    ProductService.create_product_variation(
                        product_id=product_id,
                        name=name,
                        unit_price_override=price_override,
                        sku=sku or None
                    )
        except Exception as e:
            print(f"Error saving variations: {e}")
            raise
    
    def save_linked_products(self, product_id):
        """Save linked products."""
        try:
            # Clear existing links if editing
            if self.is_edit_mode:
                ProductService.clear_product_links(product_id)
            
            # Save new links
            for i in range(self.linked_list.count()):
                item = self.linked_list.item(i)
                if item.isSelected():
                    linked_product_id = item.data(Qt.UserRole)
                    ProductService.create_product_link(
                        product_id=product_id,
                        linked_product_id=linked_product_id,
                        link_type="suggested"
                    )
        except Exception as e:
            print(f"Error saving linked products: {e}")
            raise


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.current_quotation_id = None
        self.current_quotation_items = []
        
        self.setWindowTitle("Adhlal - Curtain Business Management System v3.0")
        self.setMinimumSize(1400, 900)
        
        # Set up the UI
        self.setup_ui()
        self.setup_menu()
        self.setup_styles()
        
        # Load initial data
        QTimer.singleShot(100, self.load_initial_data)
    
    def setup_ui(self):
        """Set up the main UI structure."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        self.setup_header(main_layout)
        
        # Navigation tabs
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)
        main_layout.addWidget(self.tab_widget)
        
        # Set up pages
        self.setup_dashboard_page()
        self.setup_quotations_page()
        self.setup_customers_page()
        self.setup_products_page()
        self.setup_logistics_page()
        
        # Connect tab changes
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
    
    def setup_header(self, layout):
        """Set up the application header."""
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                            stop: 0 #4CAF50, stop: 1 #2E7D32);
                border: none;
                padding: 15px;
            }
        """)
        header_frame.setFixedHeight(80)
        
        header_layout = QHBoxLayout(header_frame)
        
        # Company logo and name
        logo_label = QLabel("🏢")
        logo_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 28px;
                margin-right: 15px;
                background: transparent;
            }
        """)
        header_layout.addWidget(logo_label)
        
        company_label = QLabel("أظلال")  # Adhlal in Arabic
        company_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 32px;
                font-weight: bold;
                background: transparent;
            }
        """)
        header_layout.addWidget(company_label)
        
        company_subtitle = QLabel("ADHLAL")
        company_subtitle.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.8);
                font-size: 14px;
                font-weight: normal;
                background: transparent;
                margin-left: 10px;
            }
        """)
        header_layout.addWidget(company_subtitle)
        
        header_layout.addStretch()
        
        # Quick stats (will be populated later)
        self.stats_layout = QHBoxLayout()
        header_layout.addLayout(self.stats_layout)
        
        layout.addWidget(header_frame)
    
    def setup_dashboard_page(self):
        """Set up the dashboard/home page."""
        dashboard_widget = QWidget()
        layout = QVBoxLayout(dashboard_widget)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(30)
        
        # Welcome section
        welcome_frame = QFrame()
        welcome_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                                            stop: 0 #2d2d2d, stop: 1 #1e1e1e);
                border: 1px solid #404040;
                border-radius: 12px;
                padding: 30px;
            }
        """)
        welcome_layout = QVBoxLayout(welcome_frame)
        
        welcome_title = QLabel("Welcome to Adhlal Management System")
        welcome_title.setStyleSheet("color: #4CAF50; font-size: 24px; font-weight: bold;")
        welcome_layout.addWidget(welcome_title)
        
        welcome_subtitle = QLabel("Manage your curtain business with ease")
        welcome_subtitle.setStyleSheet("color: #cccccc; font-size: 16px; margin-top: 10px;")
        welcome_layout.addWidget(welcome_subtitle)
        
        layout.addWidget(welcome_frame)
        
        # Dashboard cards
        cards_frame = QFrame()
        cards_layout = QGridLayout(cards_frame)
        cards_layout.setSpacing(20)
        
        self.customers_card = DashboardCard("Total Customers", "Loading...", "Registered clients", "👥")
        self.products_card = DashboardCard("Total Products", "Loading...", "Available products", "📦")
        self.quotations_card = DashboardCard("Total Quotations", "Loading...", "All quotations", "📋")
        self.revenue_card = DashboardCard("Monthly Revenue", "Loading...", "This month", "💰")
        
        cards_layout.addWidget(self.customers_card, 0, 0)
        cards_layout.addWidget(self.products_card, 0, 1)
        cards_layout.addWidget(self.quotations_card, 1, 0)
        cards_layout.addWidget(self.revenue_card, 1, 1)
        
        layout.addWidget(cards_frame)
        
        # Quick actions
        actions_frame = QFrame()
        actions_layout = QHBoxLayout(actions_frame)
        
        new_quote_btn = ModernButton("📋 Create New Quotation", "primary", "large")
        new_quote_btn.clicked.connect(lambda: self.tab_widget.setCurrentIndex(1))
        
        manage_customers_btn = ModernButton("👥 Manage Customers", "secondary", "large")
        manage_customers_btn.clicked.connect(lambda: self.tab_widget.setCurrentIndex(2))
        
        manage_products_btn = ModernButton("📦 Manage Products", "secondary", "large")
        manage_products_btn.clicked.connect(lambda: self.tab_widget.setCurrentIndex(3))
        
        actions_layout.addWidget(new_quote_btn)
        actions_layout.addWidget(manage_customers_btn)
        actions_layout.addWidget(manage_products_btn)
        actions_layout.addStretch()
        
        layout.addWidget(actions_frame)
        layout.addStretch()
        
        self.tab_widget.addTab(dashboard_widget, "🏠 Dashboard")
    
    def setup_quotations_page(self):
        """Set up the quotations management page with stacked widget for form."""
        quotations_widget = QWidget()
        layout = QVBoxLayout(quotations_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Use stacked widget to switch between list and form
        self.quotations_stack = QStackedWidget()
        
        # Page 0: Quotations list
        list_widget = QWidget()
        list_layout = QVBoxLayout(list_widget)
        list_layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Quotations Management")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #4CAF50;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        create_new_btn = ModernButton("Create New Quotation", "primary")
        create_new_btn.clicked.connect(self.create_new_quotation)
        header_layout.addWidget(create_new_btn)
        
        list_layout.addLayout(header_layout)
        
        # Filters
        filters_frame = QGroupBox("Filters")
        filters_layout = QFormLayout(filters_frame)
        
        self.phone_filter = QLineEdit()
        self.phone_filter.setPlaceholderText("Customer phone contains...")
        filters_layout.addRow("Phone:", self.phone_filter)
        
        self.status_filter = StyledComboBox()
        self.status_filter.addItem("All Statuses", "")
        for status in QuotationStatus:
            self.status_filter.addItem(status.value.title(), status.value)
        filters_layout.addRow("Status:", self.status_filter)
        
        filter_btn = ModernButton("Apply Filters", "secondary")
        filter_btn.clicked.connect(self.apply_quotation_filters)
        filters_layout.addRow("", filter_btn)
        
        list_layout.addWidget(filters_frame)
        
        # Quotations table
        self.quotations_table = EditableTable([
            "Serial", "Customer", "Phone", "Total Amount", "Status", "Created", "Actions"
        ])
        self.quotations_table.verticalHeader().setDefaultSectionSize(45)
        list_layout.addWidget(self.quotations_table)
        
        self.quotations_stack.addWidget(list_widget)
        
        # Page 1: Quotation form
        self.quotation_form = QuotationForm()
        self.quotation_form.back_requested.connect(lambda: self.quotations_stack.setCurrentIndex(0))
        self.quotations_stack.addWidget(self.quotation_form)
        
        layout.addWidget(self.quotations_stack)
        self.tab_widget.addTab(quotations_widget, "📋 Quotations")
    
    def setup_customers_page(self):
        """Set up the customers page."""
        customers_widget = QWidget()
        layout = QVBoxLayout(customers_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Customers Management")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #4CAF50;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        add_customer_btn = ModernButton("Add New Customer", "primary")
        add_customer_btn.clicked.connect(self.add_new_customer)
        header_layout.addWidget(add_customer_btn)
        
        layout.addLayout(header_layout)
        
        # Customers table
        self.customers_table = EditableTable([
            "Name", "Type", "Phone", "Email", "Company", "Actions"
        ])
        self.customers_table.verticalHeader().setDefaultSectionSize(40)
        layout.addWidget(self.customers_table)
        
        self.tab_widget.addTab(customers_widget, "👥 Customers")
    
    def setup_products_page(self):
        """Set up the products page."""
        products_widget = QWidget()
        layout = QVBoxLayout(products_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Products Management")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #4CAF50;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        add_product_btn = ModernButton("Add New Product", "primary")
        add_product_btn.clicked.connect(self.add_new_product)
        header_layout.addWidget(add_product_btn)
        
        layout.addLayout(header_layout)
        
        # Products table
        self.products_table = EditableTable([
            "Name", "Category", "Unit Type", "Base Price", "Variations", "Actions"
        ])
        self.products_table.verticalHeader().setDefaultSectionSize(40)
        layout.addWidget(self.products_table)
        
        self.tab_widget.addTab(products_widget, "📦 Products")
    
    def setup_logistics_page(self):
        """Set up the logistics page."""
        logistics_widget = QWidget()
        layout = QVBoxLayout(logistics_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Logistics Management")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #4CAF50;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        new_assignment_btn = ModernButton("New Assignment", "primary")
        new_assignment_btn.clicked.connect(self.create_new_assignment)
        header_layout.addWidget(new_assignment_btn)
        
        layout.addLayout(header_layout)
        
        # Assignments table
        self.assignments_table = EditableTable([
            "Type", "Quotation", "Customer", "Date", "Time", "Employee", "Status", "Actions"
        ])
        self.assignments_table.verticalHeader().setDefaultSectionSize(40)
        layout.addWidget(self.assignments_table)
        
        self.tab_widget.addTab(logistics_widget, "🚚 Logistics")
    
    def setup_menu(self):
        """Set up the application menu."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        export_action = QAction("Export to PDF", self)
        export_action.triggered.connect(self.export_current_quotation)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Company menu
        company_menu = menubar.addMenu("Company")
        
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.show_company_settings)
        company_menu.addAction(settings_action)
    
    def setup_styles(self):
        """Set up application styles."""
        # No custom styling - using default Qt appearance
        pass
    
    def on_tab_changed(self, index):
        """Handle tab change events."""
        if index == 0:  # Dashboard
            self.update_dashboard_stats()
        elif index == 1:  # Quotations
            self.refresh_quotations_table()
        elif index == 2:  # Customers
            self.refresh_customers_table()
        elif index == 3:  # Products
            self.refresh_products_table()
        elif index == 4:  # Logistics
            self.refresh_assignments_table()
    
    def load_initial_data(self):
        """Load initial application data."""
        try:
            # Use a timer to delay dashboard update until UI is fully rendered
            QTimer.singleShot(100, self.update_dashboard_stats)
            self.refresh_quotations_table()
            print("Initial data loaded successfully")
        except Exception as e:
            print(f"Error loading initial data: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load initial data:\n{str(e)}")
    
    def update_dashboard_stats(self):
        """Update dashboard statistics cards."""
        try:
            customers = CustomerService.get_all_customers()
            products = ProductService.get_all_products()
            quotations = QuotationService.get_all_quotations()
            
            print(f"Dashboard: {len(customers)} customers, {len(products)} products, {len(quotations)} quotations")
            
            # Update cards with explicit values
            self.customers_card.update_value(str(len(customers)))
            self.products_card.update_value(str(len(products)))
            self.quotations_card.update_value(str(len(quotations)))
            
            # Calculate monthly revenue
            current_month = datetime.now().month
            current_year = datetime.now().year
            monthly_revenue = sum(
                q.grand_total for q in quotations 
                if q.created_at.month == current_month and q.created_at.year == current_year
            )
            self.revenue_card.update_value(f"{monthly_revenue:.2f} SAR")
            
            # Force UI refresh
            self.customers_card.repaint()
            self.products_card.repaint()
            self.quotations_card.repaint()
            self.revenue_card.repaint()
            
        except Exception as e:
            print(f"Error updating dashboard stats: {e}")
            self.customers_card.update_value("Error")
            self.products_card.update_value("Error")
            self.quotations_card.update_value("Error")
            self.revenue_card.update_value("Error")
    
    def refresh_quotations_table(self):
        """Refresh the quotations table."""
        try:
            quotations = QuotationService.get_all_quotations()
            self.quotations_table.setRowCount(len(quotations))
            
            for row, quotation in enumerate(quotations):
                # Serial
                self.quotations_table.setItem(row, 0, QTableWidgetItem(quotation.serial_number))
                
                # Customer
                self.quotations_table.setItem(row, 1, QTableWidgetItem(quotation.customer.name))
                
                # Phone
                phone = quotation.customer.phone or ""
                self.quotations_table.setItem(row, 2, QTableWidgetItem(phone))
                
                # Total Amount
                total_item = QTableWidgetItem(f"{quotation.grand_total:.2f} SAR")
                total_item.setForeground(QColor("#4CAF50"))
                self.quotations_table.setItem(row, 3, total_item)
                
                # Status
                status_item = QTableWidgetItem(quotation.status.value.title())
                if quotation.status == QuotationStatus.ACCEPTED:
                    status_item.setForeground(QColor("#4CAF50"))
                elif quotation.status == QuotationStatus.LOST:
                    status_item.setForeground(QColor("#f44336"))
                self.quotations_table.setItem(row, 4, status_item)
                
                # Created date
                date_str = quotation.created_at.strftime("%Y-%m-%d")
                self.quotations_table.setItem(row, 5, QTableWidgetItem(date_str))
                
                # Actions - placeholder for now
                self.quotations_table.setItem(row, 6, QTableWidgetItem("View | Edit"))
                
        except Exception as e:
            print(f"Error refreshing quotations table: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load quotations:\n{str(e)}")
    
    def refresh_customers_table(self):
        """Refresh the customers table."""
        try:
            customers = CustomerService.get_all_customers()
            self.customers_table.setRowCount(len(customers))
            
            for row, customer in enumerate(customers):
                # Name
                self.customers_table.setItem(row, 0, QTableWidgetItem(customer.name or ""))
                
                # Type
                customer_type = "Company" if customer.type == CustomerType.COMPANY else "Individual"
                self.customers_table.setItem(row, 1, QTableWidgetItem(customer_type))
                
                # Phone
                self.customers_table.setItem(row, 2, QTableWidgetItem(customer.phone or ""))
                
                # Email
                self.customers_table.setItem(row, 3, QTableWidgetItem(customer.email or ""))
                
                # Company
                company_info = customer.company_name if customer.type == CustomerType.COMPANY else "-"
                self.customers_table.setItem(row, 4, QTableWidgetItem(company_info or "-"))
                
                # Actions
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(5, 2, 5, 2)
                
                edit_btn = QPushButton("✎")
                edit_btn.setMaximumSize(30, 24)
                edit_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #2196F3; color: white; border: none; border-radius: 4px;
                        font-weight: bold; font-size: 12px;
                    }
                    QPushButton:hover { background-color: #1976D2; }
                """)
                edit_btn.clicked.connect(lambda checked, c=customer: self.edit_customer(c))
                
                delete_btn = QPushButton("×")
                delete_btn.setMaximumSize(30, 24)
                delete_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #f44336; color: white; border: none; border-radius: 4px;
                        font-weight: bold; font-size: 12px;
                    }
                    QPushButton:hover { background-color: #d32f2f; }
                """)
                delete_btn.clicked.connect(lambda checked, c=customer: self.delete_customer(c))
                
                actions_layout.addWidget(edit_btn)
                actions_layout.addWidget(delete_btn)
                actions_layout.addStretch()
                
                self.customers_table.setCellWidget(row, 5, actions_widget)
            
            print(f"Debug: Loaded {len(customers)} customers")
            
        except Exception as e:
            print(f"Error loading customers: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load customers:\n{str(e)}")
    
    def refresh_products_table(self):
        """Refresh the products table."""
        try:
            products = ProductService.get_all_products()
            self.products_table.setRowCount(len(products))
            
            for row, product in enumerate(products):
                # Name
                self.products_table.setItem(row, 0, QTableWidgetItem(product.name or ""))
                
                # Category
                self.products_table.setItem(row, 1, QTableWidgetItem(product.category or "-"))
                
                # Unit Type
                unit_type_display = {
                    UnitType.AREA: "Area (sqm)",
                    UnitType.WIDTH: "Width (m)",
                    UnitType.LENGTH: "Length (m)",
                    UnitType.PCS: "Pieces"
                }.get(product.unit_type, "Area")
                self.products_table.setItem(row, 2, QTableWidgetItem(unit_type_display))
                
                # Base Price
                price_text = f"{float(product.base_unit_price):.2f} SAR" if product.base_unit_price else "0.00 SAR"
                self.products_table.setItem(row, 3, QTableWidgetItem(price_text))
                
                # Variations Count
                try:
                    variations = ProductService.get_product_variations(product.id)
                    variations_count = len(variations)
                    self.products_table.setItem(row, 4, QTableWidgetItem(str(variations_count)))
                except:
                    self.products_table.setItem(row, 4, QTableWidgetItem("0"))
                
                # Actions
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(5, 2, 5, 2)
                
                edit_btn = QPushButton("✎")
                edit_btn.setMaximumSize(30, 24)
                edit_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #2196F3; color: white; border: none; border-radius: 4px;
                        font-weight: bold; font-size: 12px;
                    }
                    QPushButton:hover { background-color: #1976D2; }
                """)
                edit_btn.clicked.connect(lambda checked, p=product: self.edit_product(p))
                
                delete_btn = QPushButton("×")
                delete_btn.setMaximumSize(30, 24)
                delete_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #f44336; color: white; border: none; border-radius: 4px;
                        font-weight: bold; font-size: 12px;
                    }
                    QPushButton:hover { background-color: #d32f2f; }
                """)
                delete_btn.clicked.connect(lambda checked, p=product: self.delete_product(p))
                
                actions_layout.addWidget(edit_btn)
                actions_layout.addWidget(delete_btn)
                actions_layout.addStretch()
                
                self.products_table.setCellWidget(row, 5, actions_widget)
            
            print(f"Debug: Loaded {len(products)} products")
            
        except Exception as e:
            print(f"Error loading products: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load products:\n{str(e)}")
    
    def refresh_assignments_table(self):
        """Refresh the assignments table."""
        try:
            assignments = AssignmentService.get_all_assignments()
            self.assignments_table.setRowCount(len(assignments))
            
            for row, assignment in enumerate(assignments):
                # Type
                assignment_type = assignment.type.value if assignment.type else "delivery"
                self.assignments_table.setItem(row, 0, QTableWidgetItem(assignment_type.title()))
                
                # Quotation
                quotation_info = f"Q-{assignment.quotation.serial}" if assignment.quotation else "-"
                self.assignments_table.setItem(row, 1, QTableWidgetItem(quotation_info))
                
                # Customer
                customer_name = assignment.quotation.customer.name if assignment.quotation and assignment.quotation.customer else "-"
                self.assignments_table.setItem(row, 2, QTableWidgetItem(customer_name))
                
                # Date
                date_str = assignment.scheduled_date.strftime("%Y-%m-%d") if assignment.scheduled_date else "-"
                self.assignments_table.setItem(row, 3, QTableWidgetItem(date_str))
                
                # Time
                time_str = ""
                if assignment.time_start and assignment.time_end:
                    time_str = f"{assignment.time_start.strftime('%H:%M')}-{assignment.time_end.strftime('%H:%M')}"
                elif assignment.time_start:
                    time_str = assignment.time_start.strftime('%H:%M')
                self.assignments_table.setItem(row, 4, QTableWidgetItem(time_str or "-"))
                
                # Employee
                employee_name = assignment.assigned_employee.full_name if assignment.assigned_employee else "Unassigned"
                self.assignments_table.setItem(row, 5, QTableWidgetItem(employee_name))
                
                # Status
                status = assignment.status.value if assignment.status else "planned"
                self.assignments_table.setItem(row, 6, QTableWidgetItem(status.title()))
                
                # Actions
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(5, 2, 5, 2)
                
                edit_btn = QPushButton("✎")
                edit_btn.setMaximumSize(30, 24)
                edit_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #2196F3; color: white; border: none; border-radius: 4px;
                        font-weight: bold; font-size: 12px;
                    }
                    QPushButton:hover { background-color: #1976D2; }
                """)
                edit_btn.clicked.connect(lambda checked, a=assignment: self.edit_assignment(a))
                
                done_btn = QPushButton("✓")
                done_btn.setMaximumSize(30, 24)
                done_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #4CAF50; color: white; border: none; border-radius: 4px;
                        font-weight: bold; font-size: 12px;
                    }
                    QPushButton:hover { background-color: #388E3C; }
                """)
                done_btn.clicked.connect(lambda checked, a=assignment: self.mark_assignment_done(a))
                
                delete_btn = QPushButton("×")
                delete_btn.setMaximumSize(30, 24)
                delete_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #f44336; color: white; border: none; border-radius: 4px;
                        font-weight: bold; font-size: 12px;
                    }
                    QPushButton:hover { background-color: #d32f2f; }
                """)
                delete_btn.clicked.connect(lambda checked, a=assignment: self.delete_assignment(a))
                
                actions_layout.addWidget(edit_btn)
                actions_layout.addWidget(done_btn)
                actions_layout.addWidget(delete_btn)
                actions_layout.addStretch()
                
                self.assignments_table.setCellWidget(row, 7, actions_widget)
            
            print(f"Debug: Loaded {len(assignments)} assignments")
            
        except Exception as e:
            print(f"Error loading assignments: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load assignments:\n{str(e)}")
    
    # Navigation methods
    def create_new_quotation(self):
        """Switch to the quotation form."""
        self.quotations_stack.setCurrentIndex(1)  # Show form
    
    def apply_quotation_filters(self):
        """Apply filters to quotations list (basic implementation)."""
        # Get filter values
        phone_filter = self.phone_filter_edit.text().strip() if hasattr(self, 'phone_filter_edit') else ""
        
        try:
            quotations = QuotationService.get_all_quotations()
            
            # Apply phone filter if provided
            if phone_filter:
                filtered_quotations = []
                for quotation in quotations:
                    if quotation.customer and quotation.customer.phone and phone_filter.lower() in quotation.customer.phone.lower():
                        filtered_quotations.append(quotation)
                quotations = filtered_quotations
            
            # Update table with filtered results
            self.quotations_table.setRowCount(len(quotations))
            
            for row, quotation in enumerate(quotations):
                # Serial
                self.quotations_table.setItem(row, 0, QTableWidgetItem(quotation.serial or f"Q-{quotation.id}"))
                
                # Customer
                customer_name = quotation.customer.name if quotation.customer else "Unknown"
                self.quotations_table.setItem(row, 1, QTableWidgetItem(customer_name))
                
                # Phone
                phone = quotation.customer.phone if quotation.customer else "-"
                self.quotations_table.setItem(row, 2, QTableWidgetItem(phone or "-"))
                
                # Total Amount
                total_text = f"{float(quotation.grand_total):.2f} SAR" if quotation.grand_total else "0.00 SAR"
                self.quotations_table.setItem(row, 3, QTableWidgetItem(total_text))
                
                # Status
                status = quotation.status.value if quotation.status else "draft"
                self.quotations_table.setItem(row, 4, QTableWidgetItem(status.title()))
                
                # Created
                created = quotation.created_at.strftime("%Y-%m-%d") if quotation.created_at else "-"
                self.quotations_table.setItem(row, 5, QTableWidgetItem(created))
                
                # Actions (same as refresh_quotations_table)
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(5, 2, 5, 2)
                
                view_btn = QPushButton("👁")
                edit_btn = QPushButton("✎")
                delete_btn = QPushButton("×")
                
                for btn in [view_btn, edit_btn, delete_btn]:
                    btn.setMaximumSize(30, 24)
                
                view_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; border: none; border-radius: 4px; font-weight: bold; font-size: 12px; } QPushButton:hover { background-color: #388E3C; }")
                edit_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; border: none; border-radius: 4px; font-weight: bold; font-size: 12px; } QPushButton:hover { background-color: #1976D2; }")
                delete_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; border: none; border-radius: 4px; font-weight: bold; font-size: 12px; } QPushButton:hover { background-color: #d32f2f; }")
                
                actions_layout.addWidget(view_btn)
                actions_layout.addWidget(edit_btn)
                actions_layout.addWidget(delete_btn)
                actions_layout.addStretch()
                
                self.quotations_table.setCellWidget(row, 6, actions_widget)
            
            QMessageBox.information(self, "Filters Applied", f"Found {len(quotations)} quotations matching filters.")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to apply filters:\n{str(e)}")
    
    def add_new_customer(self):
        """Open dialog to add a new customer."""
        dialog = CustomerDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_customers_table()
    
    def edit_customer(self, customer):
        """Open dialog to edit an existing customer."""
        dialog = CustomerDialog(self, customer)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_customers_table()
    
    def delete_customer(self, customer):
        """Delete a customer after confirmation."""
        reply = QMessageBox.question(
            self, 
            "Confirm Delete", 
            f"Are you sure you want to delete customer '{customer.name}'?\n\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                CustomerService.delete_customer(customer.id)
                QMessageBox.information(self, "Success", f"Customer '{customer.name}' deleted successfully!")
                self.refresh_customers_table()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete customer:\n{str(e)}")
    
    def add_new_product(self):
        """Open dialog to add a new product."""
        dialog = ProductDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_products_table()
    
    def edit_product(self, product):
        """Open dialog to edit an existing product."""
        dialog = ProductDialog(self, product)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_products_table()
    
    def delete_product(self, product):
        """Delete a product after confirmation."""
        reply = QMessageBox.question(
            self, 
            "Confirm Delete", 
            f"Are you sure you want to delete product '{product.name}'?\n\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                ProductService.delete_product(product.id)
                QMessageBox.information(self, "Success", f"Product '{product.name}' deleted successfully!")
                self.refresh_products_table()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete product:\n{str(e)}")
    
    def create_new_assignment(self):
        """Create a new assignment (simplified implementation)."""
        # For now, show a simple message - could be expanded to a full dialog
        QMessageBox.information(
            self, 
            "New Assignment", 
            "Assignment creation dialog will be implemented in the next phase.\n\n"
            "For now, assignments can be created programmatically through the AssignmentService."
        )
    
    def edit_assignment(self, assignment):
        """Edit an existing assignment."""
        QMessageBox.information(
            self, 
            "Edit Assignment", 
            f"Edit assignment for {assignment.quotation.customer.name if assignment.quotation and assignment.quotation.customer else 'Unknown'}\n\n"
            "Assignment editing dialog will be implemented in the next phase."
        )
    
    def mark_assignment_done(self, assignment):
        """Mark an assignment as done."""
        reply = QMessageBox.question(
            self,
            "Mark Assignment Done",
            f"Mark assignment as completed?\n\n"
            f"Type: {assignment.type.value.title() if assignment.type else 'Unknown'}\n"
            f"Customer: {assignment.quotation.customer.name if assignment.quotation and assignment.quotation.customer else 'Unknown'}\n"
            f"Date: {assignment.scheduled_date.strftime('%Y-%m-%d') if assignment.scheduled_date else 'Not scheduled'}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.Yes:
            try:
                AssignmentService.update_assignment_status(assignment.id, "done")
                QMessageBox.information(self, "Success", "Assignment marked as completed!")
                self.refresh_assignments_table()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to update assignment:\n{str(e)}")
    
    def delete_assignment(self, assignment):
        """Delete an assignment after confirmation."""
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete this assignment?\n\n"
            f"Type: {assignment.type.value.title() if assignment.type else 'Unknown'}\n"
            f"Customer: {assignment.quotation.customer.name if assignment.quotation and assignment.quotation.customer else 'Unknown'}\n\n"
            "This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                AssignmentService.delete_assignment(assignment.id)
                QMessageBox.information(self, "Success", "Assignment deleted successfully!")
                self.refresh_assignments_table()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete assignment:\n{str(e)}")
    
    def export_current_quotation(self):
        """Export current quotation to PDF (basic implementation)."""
        try:
            from PySide6.QtPrintSupport import QPrinter
            from PySide6.QtGui import QTextDocument
            
            # For now, create a simple HTML document
            html_content = """
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; }
                    .header { text-align: center; margin-bottom: 30px; }
                    .company-name { font-size: 24px; font-weight: bold; color: #4CAF50; }
                    .quotation-title { font-size: 18px; margin: 20px 0; }
                    .customer-info { margin: 20px 0; }
                    .items-table { width: 100%; border-collapse: collapse; margin: 20px 0; }
                    .items-table th, .items-table td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                    .items-table th { background-color: #f2f2f2; }
                    .totals { float: right; margin: 20px 0; }
                    .grand-total { font-size: 18px; font-weight: bold; color: #4CAF50; }
                </style>
            </head>
            <body>
                <div class="header">
                    <div class="company-name">ADHLAL CURTAIN BUSINESS</div>
                    <div>Professional Curtain Solutions</div>
                </div>
                
                <div class="quotation-title">QUOTATION</div>
                
                <div class="customer-info">
                    <strong>Customer:</strong> Sample Customer<br>
                    <strong>Date:</strong> """ + datetime.now().strftime("%Y-%m-%d") + """<br>
                    <strong>Quotation #:</strong> Q-2024-000001
                </div>
                
                <table class="items-table">
                    <tr>
                        <th>Item</th>
                        <th>Dimensions</th>
                        <th>Qty</th>
                        <th>Unit Price</th>
                        <th>Total</th>
                    </tr>
                    <tr>
                        <td>Sample Curtain</td>
                        <td>2.0m x 3.0m</td>
                        <td>1</td>
                        <td>150.00 SAR</td>
                        <td>150.00 SAR</td>
                    </tr>
                </table>
                
                <div class="totals">
                    <div><strong>Subtotal (ex VAT): 150.00 SAR</strong></div>
                    <div><strong>VAT 15%: 22.50 SAR</strong></div>
                    <div class="grand-total"><strong>Grand Total: 172.50 SAR</strong></div>
                </div>
                
                <div style="margin-top: 50px;">
                    <p><strong>Terms & Conditions:</strong></p>
                    <ul>
                        <li>Quotation valid for 30 days</li>
                        <li>50% deposit required to start work</li>
                        <li>Installation included in price</li>
                    </ul>
                </div>
            </body>
            </html>
            """
            
            # Create PDF
            document = QTextDocument()
            document.setHtml(html_content)
            
            printer = QPrinter(QPrinter.PdfFormat)
            
            # Get save location
            file_path = QFileDialog.getSaveFileName(
                self, 
                "Export Quotation to PDF",
                f"Quotation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                "PDF Files (*.pdf)"
            )[0]
            
            if file_path:
                printer.setOutputFileName(file_path)
                document.print(printer)
                QMessageBox.information(self, "Success", f"Quotation exported to:\n{file_path}")
            
        except ImportError:
            QMessageBox.warning(self, "PDF Export", "PDF export requires additional Qt components.\nFeature will be fully implemented in the next phase.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export PDF:\n{str(e)}")
    
    def show_company_settings(self):
        QMessageBox.information(self, "Info", "Company settings coming soon!")


if __name__ == "__main__":
    # This allows testing the window directly
    from PySide6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
