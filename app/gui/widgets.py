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
            font_size = "16px"
        elif size == "small":
            self.setMinimumHeight(28)
            font_size = "12px"
        else:
            self.setMinimumHeight(40)
            font_size = "14px"
        
        base_style = f"""
            QPushButton {{
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: {font_size};
                font-weight: 600;
                text-align: center;
            }}
            QPushButton:hover {{
                opacity: 0.9;
            }}
            QPushButton:pressed {{
                opacity: 0.8;
            }}
            QPushButton:disabled {{
                opacity: 0.6;
            }}
        """
        
        if style == "primary":
            color_style = """
                QPushButton {
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                                stop: 0 #4CAF50, stop: 1 #2E7D32);
                    color: white;
                }
                QPushButton:hover {
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                                stop: 0 #66BB6A, stop: 1 #388E3C);
                }
                QPushButton:pressed {
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                                stop: 0 #2E7D32, stop: 1 #1B5E20);
                }
            """
        elif style == "danger":
            color_style = """
                QPushButton {
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                                stop: 0 #f44336, stop: 1 #c62828);
                    color: white;
                }
                QPushButton:hover {
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                                stop: 0 #ef5350, stop: 1 #d32f2f);
                }
                QPushButton:pressed {
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                                stop: 0 #c62828, stop: 1 #b71c1c);
                }
            """
        elif style == "secondary":
            color_style = """
                QPushButton {
                    background-color: #6c757d;
                    color: white;
                }
                QPushButton:hover {
                    background-color: #5a6268;
                }
                QPushButton:pressed {
                    background-color: #545b62;
                }
            """
        else:  # default
            color_style = """
                QPushButton {
                    background-color: #404040;
                    color: #ffffff;
                    border: 1px solid #555555;
                }
                QPushButton:hover {
                    background-color: #4a4a4a;
                    border-color: #666666;
                }
                QPushButton:pressed {
                    background-color: #353535;
                }
            """
        
        self.setStyleSheet(base_style + color_style)


class DashboardCard(QFrame):
    """Dashboard statistics card with click functionality."""
    
    clicked = Signal()
    
    def __init__(self, title: str, value: str, subtitle: str = "", icon: str = "", clickable: bool = True):
        super().__init__()
        self.clickable = clickable
        self.setMinimumSize(250, 160)
        self.setMaximumHeight(160)
        self.setFrameStyle(QFrame.Box)
        
        card_style = """
            QFrame {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                                            stop: 0 #2d2d2d, stop: 1 #1e1e1e);
                border: 1px solid #404040;
                border-radius: 12px;
                margin: 5px;
            }
        """
        
        if clickable:
            card_style += """
                QFrame:hover {
                    border-color: #4CAF50;
                    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                                                stop: 0 #3d3d3d, stop: 1 #2e2e2e);
                }
            """
            self.setCursor(Qt.PointingHandCursor)
        
        self.setStyleSheet(card_style)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        # Header with icon and title
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        if icon:
            icon_label = QLabel(icon)
            icon_label.setStyleSheet("font-size: 20px; color: #4CAF50; margin-right: 8px;")
            icon_label.setFixedSize(24, 24)
            header_layout.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #cccccc; font-size: 13px; font-weight: 600;")
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
        
        # Style the table
        self.setStyleSheet("""
            QTableWidget {
                background-color: #2d2d2d;
                border: 1px solid #404040;
                border-radius: 8px;
                gridline-color: #404040;
                color: #ffffff;
                selection-background-color: #4CAF50;
            }
            QTableWidget::item {
                padding: 8px;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #4CAF50;
                color: #ffffff;
            }
            QTableWidget::item:alternate {
                background-color: #242424;
            }
            QHeaderView::section {
                background-color: #404040;
                color: #ffffff;
                border: 1px solid #555555;
                font-weight: bold;
                padding: 8px;
            }
            QScrollBar:vertical {
                background-color: #2d2d2d;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #4CAF50;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #66BB6A;
            }
        """)
        
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
        
        # Style the spin box
        self.setStyleSheet("""
            QDoubleSpinBox {
                background-color: #404040;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 8px;
                color: #ffffff;
                font-size: 14px;
            }
            QDoubleSpinBox:focus {
                border-color: #4CAF50;
                background-color: #4a4a4a;
            }
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
                background-color: #555555;
                border: none;
                width: 16px;
            }
            QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {
                background-color: #666666;
            }
        """)
    
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
        
        self.setStyleSheet("""
            QComboBox {
                background-color: #404040;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 8px;
                color: #ffffff;
                font-size: 14px;
                min-width: 120px;
            }
            QComboBox:focus {
                border-color: #4CAF50;
                background-color: #4a4a4a;
            }
            QComboBox::drop-down {
                border: none;
                background-color: #555555;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #cccccc;
                margin-right: 5px;
            }
            QComboBox QAbstractItemView {
                background-color: #404040;
                border: 1px solid #555555;
                color: #ffffff;
                selection-background-color: #4CAF50;
            }
        """)


class ImageLabel(QLabel):
    """Label for displaying images with click-to-change functionality."""
    
    clicked = Signal()
    
    def __init__(self, size: tuple = (100, 100)):
        super().__init__()
        self.image_size = size
        self.setFixedSize(*size)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #555555;
                border-radius: 8px;
                background-color: #2d2d2d;
                color: #888888;
            }
            QLabel:hover {
                border-color: #4CAF50;
                background-color: #3d3d3d;
            }
        """)
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
