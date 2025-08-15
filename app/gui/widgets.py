"""
Custom widgets for the Curtain Quotation System.
Reusable UI components with consistent styling.
"""

from decimal import Decimal
from typing import Optional, List, Callable
from PySide6.QtWidgets import (
    QPushButton, QLabel, QFrame, QVBoxLayout, QHBoxLayout, 
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QSpinBox, QDoubleSpinBox, QComboBox, QLineEdit, QTextEdit,
    QWidget, QGroupBox, QFormLayout, QDialog, QDialogButtonBox,
    QFileDialog, QMessageBox, QApplication
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QColor, QPixmap, QClipboard


class ModernButton(QPushButton):
    """Modern styled button with different variants."""
    
    def __init__(self, text: str, style: str = "default", size: str = "normal"):
        super().__init__(text)
        
        if size == "large":
            self.setMinimumHeight(50)
        elif size == "small":
            self.setMinimumHeight(28)
        else:
            self.setMinimumHeight(40)
        
        # No custom styling - using default Qt appearance


class DashboardCard(QFrame):
    """Dashboard statistics card with click functionality."""
    
    clicked = Signal()
    
    def __init__(self, title: str, value: str, subtitle: str = "", icon: str = "", clickable: bool = True):
        super().__init__()
        self.clickable = clickable
        self.setMinimumSize(250, 160)
        self.setMaximumHeight(160)
        self.setFrameStyle(QFrame.Box)
        
        # No custom styling - using default Qt appearance
        if clickable:
            self.setCursor(Qt.PointingHandCursor)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        # Header with icon and title
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        if icon:
            icon_label = QLabel(icon)
            icon_label.setFixedSize(24, 24)
            header_layout.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setWordWrap(True)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Value
        self.value_label = QLabel(str(value))
        self.value_label.setStyleSheet("""
            QLabel {
                color: #4CAF50; 
                font-size: 28px; 
                font-weight: bold; 
                margin: 0px;
                padding: 0px;
                background-color: transparent;
                border: none;
                line-height: 1.2;
            }
        """)
        self.value_label.setAlignment(Qt.AlignLeft)
        self.value_label.setWordWrap(False)
        self.value_label.setAttribute(Qt.WA_TranslucentBackground, False)
        self.value_label.setMinimumHeight(40)
        layout.addWidget(self.value_label)
        
        # Subtitle
        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setStyleSheet("color: #888888; font-size: 11px; margin-top: 2px;")
            subtitle_label.setWordWrap(True)
            layout.addWidget(subtitle_label)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def mousePressEvent(self, event):
        if self.clickable and event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
    
    def update_value(self, value):
        """Update the card value."""
        self.value_label.setText(str(value))
        self.value_label.setVisible(True)
        self.value_label.show()
        self.value_label.repaint()
        self.repaint()
        self.update()


class EditableTable(QTableWidget):
    """Enhanced table widget with editing capabilities."""
    
    def __init__(self, columns: List[str]):
        super().__init__()
        self.setColumnCount(len(columns))
        self.setHorizontalHeaderLabels(columns)
        
        # Configure table
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setSortingEnabled(False)
        
        # No custom styling - using default Qt appearance
        
        # Configure header
        header = self.horizontalHeader()
        header.setDefaultSectionSize(120)
        header.setStretchLastSection(True)


class CopyableLineEdit(QLineEdit):
    """Line edit with copy button functionality."""
    
    def __init__(self, copy_format: str = "{text}", tooltip: str = ""):
        super().__init__()
        self.copy_format = copy_format
        if tooltip:
            self.setToolTip(tooltip)
    
    def contextMenuEvent(self, event):
        """Add copy formatted option to context menu."""
        menu = self.createStandardContextMenu()
        
        if self.text():
            menu.addSeparator()
            copy_formatted_action = menu.addAction("Copy Formatted")
            copy_formatted_action.triggered.connect(self.copy_formatted)
        
        menu.exec(event.globalPos())
    
    def copy_formatted(self):
        """Copy text using the specified format."""
        formatted_text = self.copy_format.format(text=self.text())
        clipboard = QApplication.clipboard()
        clipboard.setText(formatted_text)


class DecimalSpinBox(QDoubleSpinBox):
    """Decimal spin box with proper decimal handling."""
    
    def __init__(self, decimals: int = 2, minimum: float = 0.0, maximum: float = 999999.99):
        super().__init__()
        self.setDecimals(decimals)
        self.setMinimum(minimum)
        self.setMaximum(maximum)
        self.setSingleStep(0.01 if decimals > 0 else 1)
        
        # No custom styling - using default Qt appearance
    
    def get_decimal_value(self) -> Decimal:
        """Get value as Decimal for precise calculations."""
        return Decimal(str(self.value()))
    
    def set_decimal_value(self, value: Decimal):
        """Set value from Decimal."""
        self.setValue(float(value))


class StyledComboBox(QComboBox):
    """Styled combo box with consistent appearance."""
    
    def __init__(self):
        super().__init__()
        
        # No custom styling - using default Qt appearance


class ImageLabel(QLabel):
    """Label for displaying images with click-to-change functionality."""
    
    clicked = Signal()
    
    def __init__(self, size: tuple = (100, 100)):
        super().__init__()
        self.image_size = size
        self.setFixedSize(*size)
        self.setAlignment(Qt.AlignCenter)
        # No custom styling - using default Qt appearance
        self.setText("Click to\nselect image")
        self.setCursor(Qt.PointingHandCursor)
        self.current_path = None
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
    
    def set_image(self, image_path: str):
        """Set image from file path."""
        if image_path and Path(image_path).exists():
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    *self.image_size, 
                    Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation
                )
                self.setPixmap(scaled_pixmap)
                self.current_path = image_path
                return
        
        # Reset to placeholder
        self.clear()
        self.setText("Click to\nselect image")
        self.current_path = None
    
    def get_image_path(self) -> Optional[str]:
        """Get current image path."""
        return self.current_path


# Import Path for ImageLabel
from pathlib import Path
