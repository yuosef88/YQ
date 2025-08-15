"""
Rich quotation form with 14-column items grid and real-time calculations.
Implements the complete quotation workflow as specified.
"""

from decimal import Decimal
from typing import Optional, List, Dict, Any
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QLabel,
    QComboBox, QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox,
    QFrame, QSplitter, QScrollArea, QMessageBox, QDialog, QDialogButtonBox,
    QCheckBox, QApplication, QInputDialog
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QColor, QClipboard

from core.models import (
    Customer, Product, ProductVariation, Quotation, QuoteItem,
    UnitType, DiscountType, QuotationStatus, Payment, PaymentMethod
)
from core.services import (
    CustomerService, ProductService, QuotationService, PaymentService
)
from core.calculations import calc_line_totals, calc_quotation_totals
from gui.widgets import ModernButton, DecimalSpinBox, StyledComboBox


class ProductSelectorDialog(QDialog):
    """Dialog for selecting products with variations and linked items."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_product = None
        self.selected_variation = None
        self.linked_items_to_add = []
        
        self.setWindowTitle("Select Product")
        self.setModal(True)
        self.setMinimumSize(800, 600)
        self.setup_ui()
        self.load_products()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Search section
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Type product name or category...")
        self.search_edit.textChanged.connect(self.filter_products)
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_edit)
        layout.addLayout(search_layout)
        
        # Products list
        self.products_table = QTableWidget()
        self.products_table.setColumnCount(4)
        self.products_table.setHorizontalHeaderLabels([
            "Name", "Category", "Unit Type", "Base Price"
        ])
        self.products_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.products_table.setSelectionMode(QTableWidget.SingleSelection)
        self.products_table.itemSelectionChanged.connect(self.on_product_selected)
        layout.addWidget(self.products_table)
        
        # Product details section
        details_group = QGroupBox("Product Details")
        details_layout = QVBoxLayout(details_group)
        
        # Variations
        variations_label = QLabel("Variations:")
        self.variations_combo = StyledComboBox()
        self.variations_combo.addItem("No variation", None)
        details_layout.addWidget(variations_label)
        details_layout.addWidget(self.variations_combo)
        
        # Note: Linked items functionality moved to action buttons in the quotation table
        layout.addWidget(details_group)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def load_products(self):
        """Load all products into the table."""
        products = ProductService.get_all_products()
        self.products_table.setRowCount(len(products))
        
        for row, product in enumerate(products):
            self.products_table.setItem(row, 0, QTableWidgetItem(product.name))
            self.products_table.setItem(row, 1, QTableWidgetItem(product.category or ""))
            self.products_table.setItem(row, 2, QTableWidgetItem(product.unit_type.value))
            
            price_item = QTableWidgetItem(f"{product.base_unit_price:.2f}")
            price_item.setForeground(QColor("#4CAF50"))
            self.products_table.setItem(row, 3, price_item)
            
            # Store product object
            self.products_table.item(row, 0).setData(Qt.UserRole, product)
    
    def filter_products(self):
        """Filter products based on search text."""
        search_text = self.search_edit.text().lower()
        
        for row in range(self.products_table.rowCount()):
            name_item = self.products_table.item(row, 0)
            category_item = self.products_table.item(row, 1)
            
            name_match = search_text in name_item.text().lower()
            category_match = search_text in (category_item.text().lower() if category_item else "")
            
            self.products_table.setRowHidden(row, not (name_match or category_match))
    
    def on_product_selected(self):
        """Handle product selection."""
        selected_rows = self.products_table.selectionModel().selectedRows()
        if not selected_rows:
            self.selected_product = None
            self.variations_combo.clear()
            self.variations_combo.addItem("No variation", None)
            self.linked_items_group.setVisible(False)
            return
        
        row = selected_rows[0].row()
        product_item = self.products_table.item(row, 0)
        self.selected_product = product_item.data(Qt.UserRole)
        
        # Load variations
        self.variations_combo.clear()
        self.variations_combo.addItem("No variation", None)
        
        if self.selected_product.variations:
            for variation in self.selected_product.variations:
                price_text = f" (${variation.unit_price_override:.2f})" if variation.unit_price_override else ""
                self.variations_combo.addItem(
                    f"{variation.name}{price_text}", 
                    variation
                )
        
        # Linked items are now handled via action buttons in the table
    
    # Linked items methods removed - functionality moved to action buttons

    def accept(self):
        """Accept dialog and collect selected items."""
        if not self.selected_product:
            QMessageBox.warning(self, "Warning", "Please select a product.")
            return
        
        # Get selected variation
        variation_data = self.variations_combo.currentData()
        self.selected_variation = variation_data
        
        super().accept()


class DiscountWidget(QWidget):
    """Widget for entering discounts with type selection."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(4)
        
        # Discount type combo
        self.type_combo = QComboBox()
        self.type_combo.addItem("Fixed", DiscountType.FIXED)
        self.type_combo.addItem("%", DiscountType.PERCENT)
        self.type_combo.setMaximumWidth(50)
        self.type_combo.currentTextChanged.connect(self.on_type_changed)
        
        # Discount value input - simple line edit instead of spinbox
        self.value_edit = QLineEdit()
        self.value_edit.setMaximumWidth(60)
        self.value_edit.setPlaceholderText("0.00")
        self.value_edit.textChanged.connect(self.on_value_changed)
        
        layout.addWidget(self.type_combo)
        layout.addWidget(self.value_edit)
        
        # Store current values
        self.discount_type = DiscountType.FIXED
        self.discount_value = Decimal('0')
        
    def on_type_changed(self):
        """Handle discount type change."""
        self.discount_type = self.type_combo.currentData()
        self.on_value_changed()
        
    def on_value_changed(self):
        """Handle discount value change."""
        try:
            text = self.value_edit.text().strip()
            if text:
                self.discount_value = Decimal(text)
            else:
                self.discount_value = Decimal('0')
        except (ValueError, TypeError):
            self.discount_value = Decimal('0')
        
    def get_discount_data(self):
        """Get current discount data."""
        return {
            'type': self.discount_type,
            'value': self.discount_value
        }
        
    def set_discount_data(self, discount_type: DiscountType, discount_value: Decimal):
        """Set discount data."""
        self.discount_type = discount_type
        self.discount_value = discount_value
        
        # Update UI
        index = self.type_combo.findData(discount_type)
        if index >= 0:
            self.type_combo.setCurrentIndex(index)
        self.value_edit.setText(f"{float(discount_value):.2f}")


class QuotationItemsTable(QTableWidget):
    """Enhanced table for quotation items with 14 columns."""
    
    # Signals
    item_changed_signal = Signal()
    item_copied_signal = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.setup_table()
        self.current_quotation = None
        self.items_data = []
        
        # Connect signals
        self.cellChanged.connect(self.on_cell_changed)
        
        # Set subtle selection colors
        self.setStyleSheet("""
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: #000000;
            }
            QTableWidget::item:selected:active {
                background-color: #bbdefb;
                color: #000000;
            }
        """)
    
    def setup_table(self):
        """Set up the 14-column table structure."""
        columns = [
            "Item", "Color", "W", "H", "Area", "Qty", "Total Area", 
            "Unit Price", "Discount", "Line Total (ex VAT)", "VAT (15%)", 
            "Line Total (inc VAT)", "Notes", "Actions"
        ]
        
        self.setColumnCount(len(columns))
        self.setHorizontalHeaderLabels(columns)
        
        # Configure table behavior
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setSortingEnabled(False)
        
        # Enable horizontal scrolling for full screen usage
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Set column widths
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)  # Item - fixed width
        header.setSectionResizeMode(1, QHeaderView.Fixed)  # Color - fixed width
        header.setSectionResizeMode(2, QHeaderView.Fixed)  # W - fixed width
        header.setSectionResizeMode(3, QHeaderView.Fixed)  # H - fixed width
        header.setSectionResizeMode(4, QHeaderView.Fixed)  # Area - fixed width
        header.setSectionResizeMode(5, QHeaderView.Fixed)  # Qty - fixed width
        header.setSectionResizeMode(6, QHeaderView.Fixed)  # Total Area - fixed width
        header.setSectionResizeMode(7, QHeaderView.Fixed)  # Unit Price - fixed width
        header.setSectionResizeMode(8, QHeaderView.Fixed)  # Discount - fixed width
        header.setSectionResizeMode(9, QHeaderView.Fixed)  # Line Total ex VAT - fixed width
        header.setSectionResizeMode(10, QHeaderView.Fixed) # VAT - fixed width
        header.setSectionResizeMode(11, QHeaderView.Fixed) # Line Total inc VAT - fixed width
        header.setSectionResizeMode(12, QHeaderView.Fixed) # Notes - fixed width
        header.setSectionResizeMode(13, QHeaderView.Fixed) # Actions - fixed width
        
        # Set minimum column widths - properly distributed for full screen
        self.setColumnWidth(0, 207)  # Item - keep as is
        self.setColumnWidth(1, 80)   # Color - increased from 75px (+5px)
        self.setColumnWidth(2, 85)   # W - increased from 80px (+5px)
        self.setColumnWidth(3, 85)   # H - increased from 80px (+5px)
        self.setColumnWidth(4, 100)  # Area - increased from 95px (+5px)
        self.setColumnWidth(5, 65)   # Qty - increased from 60px (+5px)
        self.setColumnWidth(6, 110)  # Total Area - increased from 105px (+5px)
        self.setColumnWidth(7, 120)  # Unit Price - increased from 115px (+5px)
        self.setColumnWidth(8, 140)  # Discount - increased from 135px (+5px)
        self.setColumnWidth(9, 140)  # Line Total ex VAT - increased from 135px (+5px)
        self.setColumnWidth(10, 120) # VAT - increased from 115px (+5px)
        self.setColumnWidth(11, 140) # Line Total inc VAT - increased from 135px (+5px)
        self.setColumnWidth(12, 120) # Notes - increased from 115px (+5px)
        self.setColumnWidth(13, 70)  # Actions - reduced from 135px to 70px (-65px)
        
        # Row height
        self.verticalHeader().setDefaultSectionSize(40)
        
        # No custom styling - using default Qt appearance
    
    def add_item_row(self, product: Product, variation: ProductVariation = None,
                    width: Decimal = None, height: Decimal = None, quantity: int = 1,
                    color_text: str = "", notes: str = ""):
        """Add a new item row to the table."""
        row = self.rowCount()
        self.setRowCount(row + 1)
        
        # Calculate initial values
        width = width or Decimal('0')
        height = height or Decimal('0')
        
        # Get effective unit price
        if variation and variation.unit_price_override:
            unit_price = variation.unit_price_override
        else:
            unit_price = product.base_unit_price
        
        # Calculate line totals (initially without discount)
        totals = calc_line_totals(
            width=width,
            height=height,
            quantity=quantity,
            unit_type=product.unit_type,
            base_unit_price=product.base_unit_price,
            variation_price=variation.unit_price_override if variation else None,
            discount_type=DiscountType.FIXED,
            discount_value=Decimal('0')
        )
        
        # Column 0: Item (Product name + variation)
        item_text = product.name
        if variation:
            item_text += f" ({variation.name})"
        item_widget = QTableWidgetItem(item_text)
        item_widget.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)  # Read-only
        self.setItem(row, 0, item_widget)
        
        # Column 1: Color
        color_widget = QTableWidgetItem(color_text or (variation.name if variation else ""))
        self.setItem(row, 1, color_widget)
        
        # Column 2: Width
        width_widget = QTableWidgetItem(f"{width:.3f}")
        self.setItem(row, 2, width_widget)
        
        # Column 3: Height
        height_widget = QTableWidgetItem(f"{height:.3f}")
        self.setItem(row, 3, height_widget)
        
        # Column 4: Area (read-only, calculated)
        area_widget = QTableWidgetItem(f"{totals['area']:.3f}")
        area_widget.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        area_widget.setForeground(QColor("#4CAF50"))
        self.setItem(row, 4, area_widget)
        
        # Column 5: Quantity
        qty_widget = QTableWidgetItem(str(quantity))
        self.setItem(row, 5, qty_widget)
        
        # Column 6: Total Area (read-only, calculated)
        total_area_widget = QTableWidgetItem(f"{totals['total_area']:.3f}")
        total_area_widget.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        total_area_widget.setForeground(QColor("#4CAF50"))
        self.setItem(row, 6, total_area_widget)
        
        # Column 7: Unit Price
        price_widget = QTableWidgetItem(f"{totals['unit_price']:.2f}")
        self.setItem(row, 7, price_widget)
        
        # Column 8: Discount (new widget)
        discount_widget = DiscountWidget()
        discount_widget.value_edit.textChanged.connect(lambda: self.recalculate_row(row))
        discount_widget.type_combo.currentTextChanged.connect(lambda: self.recalculate_row(row))
        self.setCellWidget(row, 8, discount_widget)
        
        # Column 9: Line Total (ex VAT) - read-only
        line_ex_vat_widget = QTableWidgetItem(f"{totals['line_total_ex_vat']:.2f}")
        line_ex_vat_widget.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        line_ex_vat_widget.setForeground(QColor("#66BB6A"))
        self.setItem(row, 9, line_ex_vat_widget)
        
        # Column 10: VAT (15%) - read-only
        vat_widget = QTableWidgetItem(f"{totals['vat_amount']:.2f}")
        vat_widget.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        vat_widget.setForeground(QColor("#FFA726"))
        self.setItem(row, 10, vat_widget)
        
        # Column 11: Line Total (inc VAT) - read-only
        line_inc_vat_widget = QTableWidgetItem(f"{totals['line_total_inc_vat']:.2f}")
        line_inc_vat_widget.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        line_inc_vat_widget.setForeground(QColor("#4CAF50"))
        line_inc_vat_widget.setFont(QFont("", 0, QFont.Bold))
        self.setItem(row, 11, line_ex_vat_widget)
        
        # Column 12: Notes
        notes_widget = QTableWidgetItem(notes)
        self.setItem(row, 12, notes_widget)
        
        # Column 13: Actions (Copy + Delete buttons)
        self.create_action_buttons(row, product)
        
        # Store item data
        item_data = {
            'product': product,
            'variation': variation,
            'totals': totals,
            'row': row
        }
        
        if len(self.items_data) <= row:
            self.items_data.extend([None] * (row + 1 - len(self.items_data)))
        self.items_data[row] = item_data
        
        # Emit change signal
        self.item_changed_signal.emit()
    
    def create_action_buttons(self, row: int, product: Product):
        """Create action buttons for a row."""
        actions_widget = QWidget()
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(2, 2, 2, 2)
        actions_layout.setSpacing(4)
        
        # Copy button
        copy_btn = QPushButton("📋")
        copy_btn.setToolTip('Copy item as: "{ItemName} {Color} {W} {H}"')
        copy_btn.setMaximumSize(24, 24)
        copy_btn.setFont(QFont("Arial", 8))
        copy_btn.clicked.connect(lambda: self.copy_item(row))
        actions_layout.addWidget(copy_btn)
        
        # Linked Items button (only if product has linked items)
        if self.has_linked_items(product):
            linked_btn = QPushButton("🔗")
            linked_btn.setToolTip("Add linked items")
            linked_btn.setMaximumSize(24, 24)
            linked_btn.setFont(QFont("Arial", 8))
            linked_btn.clicked.connect(lambda: self.show_linked_items_popup(product))
            actions_layout.addWidget(linked_btn)
        
        # Delete button
        delete_btn = QPushButton("🗑")
        delete_btn.setToolTip("Delete this item")
        delete_btn.setMaximumSize(24, 24)
        delete_btn.setFont(QFont("Arial", 8))
        delete_btn.clicked.connect(lambda: self.delete_item(row))
        actions_layout.addWidget(delete_btn)
        
        self.setCellWidget(row, 13, actions_widget)
    
    def copy_item(self, row: int):
        """Copy item to clipboard in specified format."""
        if row >= len(self.items_data) or not self.items_data[row]:
            return
        
        item_data = self.items_data[row]
        product = item_data['product']
        
        # Get current values from table
        color = self.item(row, 1).text() if self.item(row, 1) else ""
        width = self.item(row, 2).text() if self.item(row, 2) else "0"
        height = self.item(row, 3).text() if self.item(row, 3) else "0"
        
        # Format: "{ItemName} {Color} {W} {H}"
        copy_text = f'"{product.name} {color} {width} {height}"'
        
        # Copy to clipboard
        clipboard = QApplication.clipboard()
        clipboard.setText(copy_text)
        
        # Emit signal
        self.item_copied_signal.emit(copy_text)
    
    def delete_item(self, row: int):
        """Delete an item row."""
        reply = QMessageBox.question(
            self, "Confirm Delete",
            "Are you sure you want to delete this item?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.removeRow(row)
            
            # Update items_data
            if row < len(self.items_data):
                self.items_data.pop(row)
            
            # Update row numbers in remaining data
            for i in range(row, len(self.items_data)):
                if self.items_data[i]:
                    self.items_data[i]['row'] = i
            
            # Recreate action buttons for all rows (row indices changed)
            for i in range(self.rowCount()):
                if i < len(self.items_data) and self.items_data[i]:
                    product = self.items_data[i]['product']
                    self.create_action_buttons(i, product)
            
            # Emit change signal
            self.item_changed_signal.emit()
    
    def on_cell_changed(self, row: int, column: int):
        """Handle cell value changes and recalculate."""
        if row >= len(self.items_data) or not self.items_data[row]:
            return
        
        # Only recalculate for editable columns that affect calculations
        if column in [2, 3, 5, 7, 8]:  # W, H, Qty, Unit Price, Discount
            self.recalculate_row(row)
    
    def recalculate_row(self, row: int):
        """Recalculate totals for a specific row."""
        try:
            if row >= len(self.items_data) or not self.items_data[row]:
                return
            
            item_data = self.items_data[row]
            product = item_data['product']
            
            # Get current values from table
            width = Decimal(self.item(row, 2).text() or '1.0')
            height = Decimal(self.item(row, 3).text() or '1.0')
            quantity = int(self.item(row, 5).text() or '1')
            unit_price = Decimal(self.item(row, 7).text() or '0')
            
            # Get discount data from the DiscountWidget
            discount_widget = self.cellWidget(row, 8)
            if discount_widget:
                discount_type = discount_widget.discount_type
                discount_value = discount_widget.discount_value
            else:
                discount_type = DiscountType.FIXED
                discount_value = Decimal('0')
            
            # Calculate new totals
            totals = calc_line_totals(
                width=width,
                height=height,
                quantity=quantity,
                unit_type=product.unit_type,
                base_unit_price=unit_price,  # Use table value, not base price
                variation_price=None,  # Don't override with variation price
                discount_type=discount_type,
                discount_value=discount_value
            )
            
            # Update calculated fields
            self.item(row, 4).setText(f"{totals['area']:.3f}")  # Area
            self.item(row, 6).setText(f"{totals['total_area']:.3f}")  # Total Area
            self.item(row, 9).setText(f"{totals['line_total_ex_vat']:.2f}")  # Line Total ex VAT
            self.item(row, 10).setText(f"{totals['vat_amount']:.2f}")  # VAT
            self.item(row, 11).setText(f"{totals['line_total_inc_vat']:.2f}")  # Line Total inc VAT
            
            # Update stored totals
            item_data['totals'] = totals
            
            # Emit change signal
            self.item_changed_signal.emit()
            
        except (ValueError, TypeError) as e:
            print(f"Error recalculating row {row}: {e}")
    
    def get_items_data(self) -> List[Dict[str, Any]]:
        """Get all items data for quotation totals calculation."""
        items = []
        for row in range(self.rowCount()):
            if row < len(self.items_data) and self.items_data[row]:
                try:
                    line_total_ex_vat = Decimal(self.item(row, 9).text() or '0')
                    
                    # Get discount data from widget
                    discount_widget = self.cellWidget(row, 8)
                    if discount_widget:
                        discount_amount = Decimal('0')
                        if discount_widget.discount_type == DiscountType.PERCENT:
                            # Calculate discount amount from percentage
                            base_amount = Decimal(self.item(row, 7).text() or '0') * Decimal(self.item(row, 5).text() or '1')
                            discount_amount = base_amount * (discount_widget.discount_value / Decimal('100'))
                        else:
                            # Fixed amount discount
                            discount_amount = discount_widget.discount_value
                    else:
                        discount_amount = Decimal('0')
                    
                    items.append({
                        'line_total_ex_vat': line_total_ex_vat,
                        'discount_amount': discount_amount
                    })
                except (ValueError, TypeError):
                    pass
        return items
    
    def get_full_items_data(self) -> List[Dict[str, Any]]:
        """Get all items data with full details for saving."""
        items = []
        for row in range(self.rowCount()):
            if row < len(self.items_data) and self.items_data[row]:
                # Get base item data
                item_data = self.items_data[row].copy()
                
                # Read current values from table cells
                try:
                    width_text = self.item(row, 2).text() if self.item(row, 2) else "1.0"
                    height_text = self.item(row, 3).text() if self.item(row, 3) else "1.0"
                    qty_text = self.item(row, 5).text() if self.item(row, 5) else "1"
                    color_text = self.item(row, 1).text() if self.item(row, 1) else ""
                    notes_text = self.item(row, 12).text() if self.item(row, 12) else ""
                    
                    # Get discount data from widget
                    discount_widget = self.cellWidget(row, 8)
                    if discount_widget:
                        discount_type = discount_widget.discount_type
                        discount_value = discount_widget.discount_value
                    else:
                        discount_type = DiscountType.FIXED
                        discount_value = Decimal('0')
                    
                    # Update item data with current table values
                    item_data.update({
                        'width': Decimal(width_text),
                        'height': Decimal(height_text), 
                        'quantity': int(qty_text),
                        'color': color_text,
                        'notes': notes_text,
                        'discount_type': discount_type,
                        'discount_value': discount_value
                    })
                    
                except (ValueError, TypeError, AttributeError) as e:
                    print(f"Error reading item data for row {row}: {e}")
                    # Use defaults if parsing fails
                    item_data.update({
                        'width': Decimal('1.0'),
                        'height': Decimal('1.0'),
                        'quantity': 1,
                        'color': '',
                        'notes': '',
                        'discount_type': DiscountType.FIXED,
                        'discount_value': Decimal('0')
                    })
                
                items.append(item_data)
        
        return items
    
    def has_linked_items(self, product: Product) -> bool:
        """Check if a product has linked items."""
        try:
            from core.database import get_db_session
            session = get_db_session()
            
            # Reload the product in this session
            fresh_product = session.get(Product, product.id)
            has_links = fresh_product and len(fresh_product.linked_products) > 0
            session.close()
            return has_links
            
        except Exception as e:
            print(f"Error checking linked items: {e}")
            return False
    
    def show_linked_items_popup(self, product: Product):
        """Show popup with linked items for selection."""
        try:
            from core.database import get_db_session
            session = get_db_session()
            
            # Reload the product in this session
            fresh_product = session.get(Product, product.id)
            if not fresh_product or not fresh_product.linked_products:
                session.close()
                QMessageBox.information(self, "No Linked Items", "This product has no linked items.")
                return
            
            # Create popup dialog
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Linked Items for {product.name}")
            dialog.setModal(True)
            dialog.setMinimumSize(400, 300)
            
            layout = QVBoxLayout(dialog)
            
            # Title
            title_label = QLabel(f"Select items to add with {product.name}:")
            title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #4CAF50; margin: 10px;")
            layout.addWidget(title_label)
            
            # Checkboxes for linked items
            checkboxes = []
            for link in fresh_product.linked_products:
                linked_product = link.linked_product
                checkbox = QCheckBox(f"{linked_product.name} - {float(linked_product.base_unit_price):.2f} SAR")
                checkbox.setProperty("product_id", linked_product.id)
                checkbox.setStyleSheet("""
                    QCheckBox {
                        color: #ffffff;
                        font-size: 14px;
                        padding: 8px;
                        margin: 4px;
                    }
                    QCheckBox::indicator {
                        width: 18px;
                        height: 18px;
                    }
                    QCheckBox::indicator:unchecked {
                        border: 2px solid #555555;
                        background-color: #2d2d2d;
                        border-radius: 3px;
                    }
                    QCheckBox::indicator:checked {
                        border: 2px solid #4CAF50;
                        background-color: #4CAF50;
                        border-radius: 3px;
                    }
                """)
                checkboxes.append(checkbox)
                layout.addWidget(checkbox)
            
            # Buttons
            button_layout = QHBoxLayout()
            
            add_btn = ModernButton("Add Selected Items", "primary")
            cancel_btn = ModernButton("Cancel", "secondary")
            
            def add_selected():
                selected_products = []
                for checkbox in checkboxes:
                    if checkbox.isChecked():
                        product_id = checkbox.property("product_id")
                        if product_id:
                            selected_products.append(product_id)
                
                if selected_products:
                    # Add selected products to quotation
                    for product_id in selected_products:
                        linked_product = session.get(Product, product_id)
                        if linked_product:
                            self.add_item_row(
                                product=linked_product,
                                width=Decimal('1.0'),
                                height=Decimal('1.0'),
                                quantity=1
                            )
                    
                    # Update totals and resize table
                    if hasattr(self, 'parent') and hasattr(self.parent(), 'update_totals'):
                        self.parent().update_totals()
                        self.parent().resize_table_to_content()
                    
                    QMessageBox.information(dialog, "Success", f"Added {len(selected_products)} linked items!")
                    dialog.accept()
                else:
                    QMessageBox.warning(dialog, "No Selection", "Please select at least one item.")
            
            add_btn.clicked.connect(add_selected)
            cancel_btn.clicked.connect(dialog.reject)
            
            button_layout.addWidget(add_btn)
            button_layout.addWidget(cancel_btn)
            layout.addLayout(button_layout)
            
            # Style the dialog
            dialog.setStyleSheet("""
                QDialog {
                    background-color: #1e1e1e;
                    color: #ffffff;
                }
            """)
            
            session.close()
            dialog.exec()
            
        except Exception as e:
            print(f"Error showing linked items popup: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load linked items: {str(e)}")


class QuotationTotalsPanel(QFrame):
    """Panel showing quotation totals with live updates."""
    
    # Signal for discount changes
    discount_changed_signal = Signal()
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
        # Initialize values
        self.items_subtotal = Decimal('0')
        self.header_discount_type = DiscountType.FIXED  # Always fixed amount
        self.header_discount_value = Decimal('0')
        self.tax_rate = Decimal('0.15')
    
    def setup_ui(self):
        """Set up the totals panel UI."""
        self.setFrameStyle(QFrame.Box)
        
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Quotation Totals")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(title_label)
        
        # Totals layout
        totals_layout = QFormLayout()
        totals_layout.setSpacing(10)
        
        # Items Subtotal (ex VAT)
        self.items_subtotal_label = QLabel("0.00 SAR")
        self.items_subtotal_label.setFont(QFont("Arial", 12, QFont.Bold))
        totals_layout.addRow("Items Subtotal (ex VAT):", self.items_subtotal_label)
        
        # Total Item Discounts (display only)
        self.item_discounts_label = QLabel("0.00 SAR")
        self.item_discounts_label.setFont(QFont("Arial", 12))
        totals_layout.addRow("Total Discount (from items):", self.item_discounts_label)
        
        # Additional Discount (header-level)
        discount_layout = QHBoxLayout()
        
        # No need for dropdown since it's always fixed amount
        discount_label = QLabel("Fixed Amount:")
        discount_label.setFont(QFont("Arial", 10))
        
        self.discount_value_spin = DecimalSpinBox(decimals=2, minimum=0, maximum=999999)
        self.discount_value_spin.setMaximumWidth(100)
        
        self.discount_value_spin.valueChanged.connect(self.on_discount_changed)
        
        discount_layout.addWidget(discount_label)
        discount_layout.addWidget(self.discount_value_spin)
        discount_layout.addStretch()
        
        totals_layout.addRow("Additional Discount:", discount_layout)
        
        # Subtotal after Discount (ex VAT)
        self.discounted_subtotal_label = QLabel("0.00 SAR")
        self.discounted_subtotal_label.setFont(QFont("Arial", 12, QFont.Bold))
        totals_layout.addRow("Subtotal after Discount (ex VAT):", self.discounted_subtotal_label)
        
        # VAT 15%
        self.vat_label = QLabel("0.00 SAR")
        self.vat_label.setFont(QFont("Arial", 12, QFont.Bold))
        totals_layout.addRow("VAT 15%:", self.vat_label)
        
        # Grand Total (inc VAT)
        self.grand_total_label = QLabel("0.00 SAR")
        self.grand_total_label.setFont(QFont("Arial", 14, QFont.Bold))
        totals_layout.addRow("Grand Total (inc VAT):", self.grand_total_label)
        
        layout.addLayout(totals_layout)
    
    def update_totals(self, items_data: List[Dict[str, Any]]):
        """Update totals based on items data."""
        try:
            # Calculate quotation totals
            totals = calc_quotation_totals(
                items_data=items_data,
                header_discount_type=self.header_discount_type,
                header_discount_value=self.header_discount_value,
                tax_rate=self.tax_rate
            )
            
            # Update labels
            self.items_subtotal_label.setText(f"{totals['items_subtotal_ex_vat']:.2f} SAR")
            self.item_discounts_label.setText(f"{totals['total_item_discounts']:.2f} SAR")
            self.discounted_subtotal_label.setText(f"{totals['discounted_ex_vat']:.2f} SAR")
            self.vat_label.setText(f"{totals['vat_amount']:.2f} SAR")
            self.grand_total_label.setText(f"{totals['grand_total']:.2f} SAR")
            
            # Force repaint
            self.repaint()
            
        except Exception as e:
            print(f"Error updating totals: {e}")
            import traceback
            traceback.print_exc()
    
    def on_discount_changed(self):
        """Handle discount changes."""
        self.header_discount_type = DiscountType.FIXED  # Always fixed amount
        self.header_discount_value = self.discount_value_spin.get_decimal_value()
        
        # Emit signal to trigger totals update
        self.discount_changed_signal.emit()


class PaymentsPanel(QFrame):
    """Simple payments panel for quotations."""
    
    def __init__(self):
        super().__init__()
        self.quotation_id = None
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the payments panel UI."""
        self.setFrameStyle(QFrame.Box)
        
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Payments")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title_label)
        
        # Payments table
        self.payments_table = QTableWidget(0, 5)
        self.payments_table.setHorizontalHeaderLabels(["Date", "Amount", "Method", "Reference", "Actions"])
        self.payments_table.horizontalHeader().setStretchLastSection(True)
        self.payments_table.setMaximumHeight(120)
        layout.addWidget(self.payments_table)
        
        # Add payment controls
        controls_layout = QHBoxLayout()
        
        self.add_payment_btn = ModernButton("Add Payment", "primary", "small")
        self.add_payment_btn.clicked.connect(self.add_payment)
        controls_layout.addWidget(self.add_payment_btn)
        
        controls_layout.addStretch()
        
        # Payment summary
        self.paid_label = QLabel("Paid: 0.00 SAR")
        self.balance_label = QLabel("Balance: 0.00 SAR")
        
        self.paid_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.balance_label.setFont(QFont("Arial", 12, QFont.Bold))
        
        controls_layout.addWidget(self.paid_label)
        controls_layout.addWidget(self.balance_label)
        
        layout.addLayout(controls_layout)
    
    def set_quotation(self, quotation_id, grand_total):
        """Set the quotation and update payments."""
        self.quotation_id = quotation_id
        self.grand_total = grand_total
        self.refresh_payments()
    
    def refresh_payments(self):
        """Refresh the payments table."""
        if not self.quotation_id:
            return
        
        try:
            summary = PaymentService.get_quotation_payment_summary(self.quotation_id)
            payments = PaymentService.get_quotation_payments(self.quotation_id)
            
            # Update table
            self.payments_table.setRowCount(len(payments))
            for row, payment in enumerate(payments):
                self.payments_table.setItem(row, 0, QTableWidgetItem(payment.date.strftime("%Y-%m-%d")))
                self.payments_table.setItem(row, 1, QTableWidgetItem(f"{float(payment.amount):.2f}"))
                self.payments_table.setItem(row, 2, QTableWidgetItem(payment.method.value.title()))
                self.payments_table.setItem(row, 3, QTableWidgetItem(payment.reference or "-"))
                
                # Actions
                delete_btn = QPushButton("×")
                delete_btn.setMaximumSize(24, 24)
                delete_btn.setFont(QFont("Arial", 12, QFont.Bold))
                delete_btn.clicked.connect(lambda checked, p=payment: self.delete_payment(p))
                self.payments_table.setCellWidget(row, 4, delete_btn)
            
            # Update summary
            self.paid_label.setText(f"Paid: {summary['paid_total']:.2f} SAR")
            self.balance_label.setText(f"Balance: {summary['balance']:.2f} SAR")
            
        except Exception as e:
            print(f"Error refreshing payments: {e}")
    
    def add_payment(self):
        """Add a new payment (simplified)."""
        if not self.quotation_id:
            QMessageBox.warning(None, "No Quotation", "Please save the quotation first before adding payments.")
            return
        
        # Simple payment dialog (basic implementation)
        amount, ok = QInputDialog.getDouble(None, "Add Payment", "Payment Amount (SAR):", 0.0, 0.0, 999999.99, 2)
        if ok and amount > 0:
            try:
                PaymentService.create_payment(
                    quotation_id=self.quotation_id,
                    amount=Decimal(str(amount)),
                    method=PaymentMethod.CASH,  # Default method
                    reference="Manual Entry"
                )
                self.refresh_payments()
                QMessageBox.information(None, "Success", f"Payment of {amount:.2f} SAR added successfully!")
            except Exception as e:
                QMessageBox.critical(None, "Error", f"Failed to add payment:\n{str(e)}")
    
    def delete_payment(self, payment):
        """Delete a payment."""
        reply = QMessageBox.question(
            None,
            "Delete Payment",
            f"Delete payment of {float(payment.amount):.2f} SAR?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                PaymentService.delete_payment(payment.id)
                self.refresh_payments()
                QMessageBox.information(None, "Success", "Payment deleted successfully!")
            except Exception as e:
                QMessageBox.critical(None, "Error", f"Failed to delete payment:\n{str(e)}")


class QuotationForm(QWidget):
    """Complete quotation form with items grid and totals."""
    
    # Signal to request navigation back to list
    back_requested = Signal()
    
    def __init__(self):
        super().__init__()
        self.current_quotation = None
        self.setup_ui()
        self.connect_signals()
    
    def setup_ui(self):
        """Set up the quotation form UI."""
        # Create main layout
        main_layout = QVBoxLayout(self)
        
        # Create scroll area for the entire form
        from PySide6.QtWidgets import QScrollArea
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Create content widget
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Create New Quotation")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        back_btn = ModernButton("← Back to Quotations", "secondary")
        back_btn.clicked.connect(self.back_requested.emit)
        header_layout.addWidget(back_btn)
        
        layout.addLayout(header_layout)
        
        # Customer selection
        customer_group = QGroupBox("Customer Information")
        customer_layout = QFormLayout(customer_group)
        
        self.customer_combo = StyledComboBox()
        customer_layout.addRow("Select Customer:", self.customer_combo)
        
        layout.addWidget(customer_group)
        
        # Add item section (restored simple input style)
        add_item_group = QGroupBox("Add Item")
        add_item_layout = QHBoxLayout(add_item_group)
        
        # Product selection
        self.add_item_btn = ModernButton("Select Product", "primary")
        self.add_item_btn.clicked.connect(self.select_product)
        add_item_layout.addWidget(self.add_item_btn)
        
        # Quick dimensions input
        add_item_layout.addWidget(QLabel("W:"))
        self.width_input = DecimalSpinBox(decimals=2, minimum=0, maximum=50)
        self.width_input.setValue(1.0)
        self.width_input.setMaximumWidth(80)
        add_item_layout.addWidget(self.width_input)
        
        add_item_layout.addWidget(QLabel("H:"))
        self.height_input = DecimalSpinBox(decimals=2, minimum=0, maximum=50)
        self.height_input.setValue(1.0)
        self.height_input.setMaximumWidth(80)
        add_item_layout.addWidget(self.height_input)
        
        add_item_layout.addWidget(QLabel("Qty:"))
        self.qty_input = QSpinBox()
        self.qty_input.setMinimum(1)
        self.qty_input.setMaximum(999)
        self.qty_input.setValue(1)
        self.qty_input.setMaximumWidth(60)
        add_item_layout.addWidget(self.qty_input)
        
        # Add and Clear buttons
        self.add_to_quote_btn = ModernButton("Add to Quote", "secondary", "small")
        self.add_to_quote_btn.clicked.connect(self.add_item_to_quote)
        self.add_to_quote_btn.setEnabled(False)  # Disabled until product selected
        add_item_layout.addWidget(self.add_to_quote_btn)
        
        self.clear_btn = ModernButton("Clear", "secondary", "small")
        self.clear_btn.clicked.connect(self.clear_inputs)
        add_item_layout.addWidget(self.clear_btn)
        
        add_item_layout.addStretch()
        
        layout.addWidget(add_item_group)
        
        # Items table (no splitter - let it grow naturally)
        items_label = QLabel("Quotation Items")
        items_label.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(items_label)
        
        self.items_table = QuotationItemsTable()
        # Disable internal scrolling - let the table grow naturally
        self.items_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.items_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Make table resize to content
        from PySide6.QtWidgets import QHeaderView
        self.items_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(self.items_table)
        
        # Enhanced totals panel with discount functionality
        self.totals_panel = QuotationTotalsPanel()
        layout.addWidget(self.totals_panel)
        
        # Action buttons below totals
        buttons_frame = QFrame()
        buttons_layout = QHBoxLayout(buttons_frame)
        
        self.export_pdf_btn = ModernButton("Export to PDF", "secondary")
        self.export_pdf_btn.clicked.connect(self.export_pdf)
        
        self.save_btn = ModernButton("Save Quotation", "primary")
        self.save_btn.clicked.connect(self.save_quotation)
        
        buttons_layout.addWidget(self.export_pdf_btn)
        buttons_layout.addWidget(self.save_btn)
        
        layout.addWidget(buttons_frame)
        
        # Load customers
        self.load_customers()
        
        # Add content to scroll area and scroll area to main layout
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
    
    def connect_signals(self):
        """Connect UI signals."""
        self.items_table.item_changed_signal.connect(self.update_totals)
        self.items_table.item_copied_signal.connect(self.on_item_copied)
        self.totals_panel.discount_changed_signal.connect(self.update_totals)
    
    def load_customers(self):
        """Load customers into combo box."""
        customers = CustomerService.get_all_customers()
        self.customer_combo.clear()
        self.customer_combo.addItem("Select Customer", None)
        
        for customer in customers:
            self.customer_combo.addItem(customer.name, customer.id)
    
    def select_product(self):
        """Open product selection dialog."""
        dialog = ProductSelectorDialog(self)
        if dialog.exec() == QDialog.Accepted:
            if dialog.selected_product:
                # Store selected product for the simple add workflow
                self.selected_product = dialog.selected_product
                self.selected_variation = dialog.selected_variation
                
                # Update button text to show selected product
                product_name = dialog.selected_product.name
                if dialog.selected_variation:
                    product_name += f" ({dialog.selected_variation.name})"
                self.add_item_btn.setText(f"Selected: {product_name[:30]}...")
                
                # Enable the add button
                self.add_to_quote_btn.setEnabled(True)
    
    def update_totals(self):
        """Update quotation totals."""
        items_data = self.items_table.get_items_data()
        
        try:
            # Update the totals panel with items data
            self.totals_panel.update_totals(items_data)
            
        except Exception as e:
            print(f"Error updating totals: {e}")
            # Set default values on error
            self.totals_panel.update_totals([])
    
    def on_item_copied(self, copied_text: str):
        """Handle item copied to clipboard."""
        # Could show a temporary notification
        print(f"Copied to clipboard: {copied_text}")
    
    def add_item_to_quote(self):
        """Add item to quote using the simple inputs."""
        if not hasattr(self, 'selected_product') or not self.selected_product:
            QMessageBox.warning(self, "No Product", "Please select a product first.")
            return
        
        try:
            width = self.width_input.get_decimal_value()
            height = self.height_input.get_decimal_value()
            quantity = self.qty_input.value()
            
            # Add to items table
            self.items_table.add_item_row(
                product=self.selected_product,
                variation=getattr(self, 'selected_variation', None),
                width=width,
                height=height,
                quantity=quantity
            )
            
            # Update totals
            self.update_totals()
            
            # Resize table to content
            self.resize_table_to_content()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add item: {str(e)}")
    
    def clear_inputs(self):
        """Clear the input fields."""
        self.width_input.setValue(1.0)
        self.height_input.setValue(1.0)
        self.qty_input.setValue(1)
        # Keep the selected product for convenience
    
    def resize_table_to_content(self):
        """Resize table to fit content without internal scrolling."""
        if self.items_table.rowCount() == 0:
            self.items_table.setMinimumHeight(100)
            return
        
        # Calculate height needed for all rows
        total_height = 0
        total_height += self.items_table.horizontalHeader().height()  # Header height
        
        for row in range(self.items_table.rowCount()):
            total_height += self.items_table.rowHeight(row)
        
        # Add some padding
        total_height += 20
        
        # Set the table height
        self.items_table.setMinimumHeight(total_height)
        self.items_table.setMaximumHeight(total_height)
    
    def save_quotation(self):
        """Save the current quotation."""
        try:
            # Get selected customer
            customer_id = self.customer_combo.currentData()
            if not customer_id:
                QMessageBox.warning(self, "No Customer", "Please select a customer first.")
                return
            
            # Check if we have items
            if self.items_table.rowCount() == 0:
                QMessageBox.warning(self, "No Items", "Please add at least one item to the quotation.")
                return
            
            # Create quotation
            quotation = QuotationService.create_quotation(
                customer_id=customer_id,
                notes="Created from quotation form"
            )
            
            # Add items to quotation
            items_data = self.items_table.get_full_items_data()
            for item_data in items_data:
                if item_data and 'product' in item_data:
                    QuotationService.add_quote_item(
                        quotation_id=quotation.id,
                        product_id=item_data['product'].id,
                        width=Decimal(str(item_data.get('width', 1.0))),
                        height=Decimal(str(item_data.get('height', 1.0))),
                        quantity=int(item_data.get('quantity', 1)),
                        product_variation_id=item_data.get('variation').id if item_data.get('variation') else None,
                        color_text=item_data.get('color', ''),
                        notes=item_data.get('notes', ''),
                        discount_type=item_data.get('discount_type', DiscountType.FIXED),
                        discount_value=item_data.get('discount_value', Decimal('0'))
                    )
            
            # Update quotation totals
            QuotationService.update_quotation_totals(quotation.id)
            
            QMessageBox.information(self, "Success", f"Quotation {quotation.serial_number} saved successfully!")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save quotation:\n{str(e)}")
    
    def export_pdf(self):
        """Export quotation to PDF."""
        try:
            from PySide6.QtPrintSupport import QPrinter
            from PySide6.QtGui import QTextDocument
            from PySide6.QtWidgets import QFileDialog
            
            # Get customer info
            customer_name = self.customer_combo.currentText()
            if customer_name == "Select Customer":
                customer_name = "Sample Customer"
            
            # Get items for PDF
            items_data = self.items_table.get_full_items_data()
            if not items_data:
                QMessageBox.warning(self, "No Items", "Please add items before exporting PDF.")
                return
            
            # Create HTML content
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; }}
                    .header {{ text-align: center; margin-bottom: 30px; }}
                    .company-name {{ font-size: 24px; font-weight: bold; color: #4CAF50; }}
                    .quotation-title {{ font-size: 18px; margin: 20px 0; }}
                    .customer-info {{ margin: 20px 0; }}
                    .items-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                    .items-table th, .items-table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    .items-table th {{ background-color: #f2f2f2; }}
                    .totals {{ float: right; margin: 20px 0; }}
                    .grand-total {{ font-size: 18px; font-weight: bold; color: #4CAF50; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <div class="company-name">ADHLAL CURTAIN BUSINESS</div>
                    <div>Professional Curtain Solutions</div>
                </div>
                
                <div class="quotation-title">QUOTATION</div>
                
                <div class="customer-info">
                    <strong>Customer:</strong> {customer_name}<br>
                    <strong>Date:</strong> {datetime.now().strftime("%Y-%m-%d")}<br>
                    <strong>Quotation #:</strong> Q-{datetime.now().strftime("%Y")}-000001
                </div>
                
                <table class="items-table">
                    <tr>
                        <th>Item</th>
                        <th>Color</th>
                        <th>Dimensions</th>
                        <th>Qty</th>
                        <th>Unit Price</th>
                        <th>Total</th>
                    </tr>
            """
            
            # Add items to HTML
            total_amount = Decimal('0')
            for item_data in items_data:
                if item_data and 'product' in item_data:
                    product_name = item_data['product'].name
                    color = item_data.get('color', 'N/A')
                    width = item_data.get('width', Decimal('0'))
                    height = item_data.get('height', Decimal('0'))
                    quantity = item_data.get('quantity', 1)
                    
                    # Get totals from the item_data if available
                    line_total = item_data.get('totals', {}).get('line_total_inc_vat', Decimal('0'))
                    unit_price = item_data.get('totals', {}).get('unit_price', Decimal('0'))
                    
                    total_amount += line_total
                    
                    html_content += f"""
                    <tr>
                        <td>{product_name}</td>
                        <td>{color}</td>
                        <td>{float(width):.2f}m x {float(height):.2f}m</td>
                        <td>{quantity}</td>
                        <td>{float(unit_price):.2f} SAR</td>
                        <td>{float(line_total):.2f} SAR</td>
                    </tr>
                    """
            
            # Calculate VAT
            vat_amount = total_amount * Decimal('0.15') / Decimal('1.15')  # Reverse VAT calculation
            subtotal = total_amount - vat_amount
            
            html_content += f"""
                </table>
                
                <div class="totals">
                    <div><strong>Subtotal (ex VAT): {float(subtotal):.2f} SAR</strong></div>
                    <div><strong>VAT 15%: {float(vat_amount):.2f} SAR</strong></div>
                    <div class="grand-total"><strong>Grand Total: {float(total_amount):.2f} SAR</strong></div>
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
            
            printer = QPrinter()
            printer.setOutputFormat(QPrinter.PdfFormat)
            
            # Get save location
            file_path = QFileDialog.getSaveFileName(
                self, 
                "Export Quotation to PDF",
                f"Quotation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                "PDF Files (*.pdf)"
            )[0]
            
            if file_path:
                printer.setOutputFileName(file_path)
                document.print_(printer)
                QMessageBox.information(self, "Success", f"Quotation exported to:\n{file_path}")
            
        except ImportError:
            QMessageBox.warning(self, "PDF Export", "PDF export requires additional Qt components.\nPlease install the full PySide6 package.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export PDF:\n{str(e)}")


if __name__ == "__main__":
    # Test the quotation form
    from PySide6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    form = QuotationForm()
    form.show()
    sys.exit(app.exec())
