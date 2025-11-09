"""
Gestión de temas para la aplicación W-T-F Trading Manager
"""

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor

class ThemeManager:
    """Gestor de temas para la aplicación"""
    
    def __init__(self):
        self.current_theme = "light"
        self.themes = {
            "light": self.get_light_theme(),
            "dark": self.get_dark_theme()
        }
    
    def get_light_theme(self):
        """Obtener estilo del tema claro"""
        return """
            /* Estilo general */
            QWidget {
                background-color: #f8f9fa;
                color: #2c3e50;
                font-family: 'Segoe UI', 'Arial', sans-serif;
                font-size: 10pt;
            }
            
            /* QTableWidget */
            QTableWidget {
                background-color: white;
                alternate-background-color: #f8f9fa;
                gridline-color: #dee2e6;
                selection-background-color: #3498db;
                selection-color: white;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 5px;
            }
            
            QTableWidget::item {
                padding: 8px;
                border: none;
            }
            
            QTableWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            
            QHeaderView::section {
                background-color: #3498db;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
            
            /* QComboBox */
            QComboBox {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 6px 12px;
                min-width: 120px;
            }
            
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #3498db;
            }
            
            QComboBox QAbstractItemView {
                background-color: white;
                border: 1px solid #dee2e6;
                selection-background-color: #3498db;
                selection-color: white;
            }
            
            /* QPushButton */
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
                min-width: 80px;
            }
            
            QPushButton:hover {
                background-color: #2980b9;
            }
            
            QPushButton:pressed {
                background-color: #21618c;
            }
            
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
            
            /* QLineEdit */
            QLineEdit {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 6px 12px;
                selection-background-color: #3498db;
                selection-color: white;
            }
            
            QLineEdit:focus {
                border: 2px solid #3498db;
            }
            
            /* QGroupBox */
            QGroupBox {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                background-color: #f8f9fa;
                color: #3498db;
            }
            
            /* QScrollBar */
            QScrollBar:vertical {
                background-color: #f8f9fa;
                width: 12px;
                border-radius: 6px;
            }
            
            QScrollBar::handle:vertical {
                background-color: #bdc3c7;
                border-radius: 6px;
                min-height: 20px;
            }
            
            QScrollBar::handle:vertical:hover {
                background-color: #95a5a6;
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
            
            /* QSplitter */
            QSplitter::handle {
                background-color: #dee2e6;
            }
            
            QSplitter::handle:horizontal {
                width: 2px;
            }
            
            QSplitter::handle:vertical {
                height: 2px;
            }
            
            /* QStatusBar */
            QStatusBar {
                background-color: #ecf0f1;
                color: #2c3e50;
                border-top: 1px solid #bdc3c7;
            }
            
            /* QLabel */
            QLabel {
                background-color: transparent;
                color: #2c3e50;
            }
            
            QLabel#summary_title {
                background-color: #3498db;
                color: white;
                font-size: 14pt;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
            
            QLabel#summary_value {
                font-size: 14pt;
                font-weight: bold;
            }
            
            QLabel#positive {
                color: #27ae60;
                font-weight: bold;
            }
            
            QLabel#negative {
                color: #e74c3c;
                font-weight: bold;
            }
            
            /* QTextEdit */
            QTextEdit {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px;
                color: #2c3e50;
                selection-background-color: #3498db;
                selection-color: white;
            }
            
            /* QFrame */
            QFrame {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 5px;
            }
        """
    
    def get_dark_theme(self):
        """Obtener estilo del tema oscuro"""
        return """
            /* Estilo general */
            QWidget {
                background-color: #121212;
                color: #e0e0e0;
                font-family: 'Segoe UI', 'Arial', sans-serif;
                font-size: 10pt;
            }
            
            /* QTableWidget */
            QTableWidget {
                background-color: #1e1e1e;
                alternate-background-color: #121212;
                gridline-color: #2a2a2a;
                selection-background-color: #3a3a3a;
                selection-color: #e0e0e0;
                border: 1px solid #2a2a2a;
                border-radius: 5px;
                padding: 5px;
            }
            
            QTableWidget::item {
                padding: 8px;
                border: none;
            }
            
            QTableWidget::item:selected {
                background-color: #3a3a3a;
                color: #e0e0e0;
            }
            
            QHeaderView::section {
                background-color: #2a2a2a;
                color: #e0e0e0;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
            
            /* QComboBox */
            QComboBox {
                background-color: #1e1e1e;
                border: 1px solid #2a2a2a;
                border-radius: 4px;
                padding: 6px 12px;
                min-width: 120px;
                color: #e0e0e0;
            }
            
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #e0e0e0;
            }
            
            QComboBox QAbstractItemView {
                background-color: #1e1e1e;
                border: 1px solid #2a2a2a;
                selection-background-color: #3a3a3a;
                selection-color: #e0e0e0;
                color: #e0e0e0;
            }
            
            /* QPushButton */
            QPushButton {
                background-color: #2a2a2a;
                color: #e0e0e0;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
                min-width: 80px;
            }
            
            QPushButton:hover {
                background-color: #3a3a3a;
            }
            
            QPushButton:pressed {
                background-color: #4a4a4a;
            }
            
            QPushButton:disabled {
                background-color: #2a2a2a;
                color: #777777;
            }
            
            /* QLineEdit */
            QLineEdit {
                background-color: #1e1e1e;
                border: 1px solid #2a2a2a;
                border-radius: 4px;
                padding: 6px 12px;
                selection-background-color: #3a3a3a;
                selection-color: #e0e0e0;
                color: #e0e0e0;
            }
            
            QLineEdit:focus {
                border: 2px solid #3a3a3a;
            }
            
            /* QGroupBox */
            QGroupBox {
                background-color: #1e1e1e;
                border: 1px solid #2a2a2a;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                background-color: #121212;
                color: #e0e0e0;
            }
            
            /* QScrollBar */
            QScrollBar:vertical {
                background-color: #2c3e50;
                width: 12px;
                border-radius: 6px;
            }
            
            QScrollBar::handle:vertical {
                background-color: #7f8c8d;
                border-radius: 6px;
                min-height: 20px;
            }
            
            QScrollBar::handle:vertical:hover {
                background-color: #95a5a6;
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
            
            /* QSplitter */
            QSplitter::handle {
                background-color: #7f8c8d;
            }
            
            QSplitter::handle:horizontal {
                width: 2px;
            }
            
            QSplitter::handle:vertical {
                height: 2px;
            }
            
            /* QStatusBar */
            QStatusBar {
                background-color: #1e1e1e;
                color: #ecf0f1;
                border-top: 1px solid #2a2a2a;
            }
            
            /* QLabel */
            QLabel {
                background-color: transparent;
                color: #ecf0f1;
            }
            
            QLabel#summary_title {
                background-color: #1e1e1e;
                color: #e0e0e0;
                font-size: 14pt;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
                border: 1px solid #2a2a2a;
            }
            
            QLabel#summary_value {
                font-size: 14pt;
                font-weight: bold;
            }
            
            QLabel#positive {
                color: #2ecc71;
                font-weight: bold;
            }
            
            QLabel#negative {
                color: #e74c3c;
                font-weight: bold;
            }
            
            /* QTextEdit */
            QTextEdit {
                background-color: #1e1e1e;
                border: 1px solid #2a2a2a;
                border-radius: 4px;
                padding: 8px;
                color: #ecf0f1;
                selection-background-color: #8ab4f8;
                selection-color: white;
            }
            
            /* QFrame */
            QFrame {
                background-color: #1e1e1e;
                border: 1px solid #2a2a2a;
                border-radius: 5px;
            }
        """
    
    def apply_theme(self, widget, is_dark: bool):
        """Aplicar tema a un widget y todos sus hijos"""
        self.current_theme = "dark" if is_dark else "light"
        
        # Aplicar estilos
        widget.setStyleSheet(self.themes[self.current_theme])
        
        # Si es la ventana principal, aplicar paleta de colores
        if hasattr(widget, 'setPalette'):
            self.apply_palette(widget, is_dark)
        
        # Aplicar tema recursivamente a todos los hijos
        self._apply_theme_recursive(widget, is_dark)
    
    def _apply_theme_recursive(self, widget, is_dark: bool):
        """Aplicar tema recursivamente a todos los widgets hijos"""
        from PyQt5.QtWidgets import QMenuBar, QStatusBar, QDialog, QFileDialog, QInputDialog, QMessageBox
        from PyQt5.QtCore import QObject
        
        # Obtener todos los hijos del widget
        children = widget.findChildren(QObject)
        
        for child in children:
            if hasattr(child, 'setStyleSheet'):
                # Aplicar estilo específico para diferentes tipos de widgets
                if isinstance(child, QMenuBar):
                    child.setStyleSheet(self._get_menubar_style(is_dark))
                elif isinstance(child, QStatusBar):
                    child.setStyleSheet(self._get_statusbar_style(is_dark))
                elif isinstance(child, (QDialog, QFileDialog, QInputDialog, QMessageBox)):
                    child.setStyleSheet(self._get_dialog_style(is_dark))
                else:
                    # Aplicar el tema general
                    child.setStyleSheet(self.themes[self.current_theme])
    
    def _get_menubar_style(self, is_dark: bool):
        """Obtener estilo para QMenuBar"""
        if is_dark:
            return """
                QMenuBar {
                    background-color: #2d2d2d;
                    color: #e0e0e0;
                    border-bottom: 1px solid #3a3a3a;
                    padding: 2px;
                }
                
                QMenuBar::item {
                    background-color: transparent;
                    padding: 6px 12px;
                    border-radius: 4px;
                    spacing: 3px;
                }
                
                QMenuBar::item:selected {
                    background-color: #3a3a3a;
                }
                
                QMenuBar::item:pressed {
                    background-color: #4a4a4a;
                }
                
                QMenu {
                    background-color: #2d2d2d;
                    color: #e0e0e0;
                    border: 1px solid #3a3a3a;
                    border-radius: 4px;
                    padding: 4px;
                }
                
                QMenu::item {
                    padding: 8px 24px 8px 12px;
                    border-radius: 3px;
                }
                
                QMenu::item:selected {
                    background-color: #3a3a3a;
                }
                
                QMenu::item:disabled {
                    color: #666666;
                }
                
                QMenu::separator {
                    height: 1px;
                    background-color: #3a3a3a;
                    margin: 4px 0;
                }
            """
        else:
            return """
                QMenuBar {
                    background-color: #f8f9fa;
                    color: #2c3e50;
                    border-bottom: 1px solid #dee2e6;
                    padding: 2px;
                }
                
                QMenuBar::item {
                    background-color: transparent;
                    padding: 6px 12px;
                    border-radius: 4px;
                }
                
                QMenuBar::item:selected {
                    background-color: #e9ecef;
                }
                
                QMenuBar::item:pressed {
                    background-color: #dee2e6;
                }
            """
    
    def _get_statusbar_style(self, is_dark: bool):
        """Obtener estilo para QStatusBar"""
        if is_dark:
            return """
                QStatusBar {
                    background-color: #2d2d2d;
                    color: #e0e0e0;
                    border-top: 1px solid #3a3a3a;
                    padding: 4px;
                }
                
                QStatusBar QLabel {
                    color: #e0e0e0;
                }
            """
        else:
            return """
                QStatusBar {
                    background-color: #ecf0f1;
                    color: #2c3e50;
                    border-top: 1px solid #bdc3c7;
                    padding: 4px;
                }
            """
    
    def _get_dialog_style(self, is_dark: bool):
        """Obtener estilo para diálogos"""
        if is_dark:
            return """
                QDialog, QFileDialog, QInputDialog, QMessageBox {
                    background-color: #2d2d2d;
                    color: #e0e0e0;
                }
                
                QDialog QLineEdit, QFileDialog QLineEdit, QInputDialog QLineEdit {
                    background-color: #2d2d2d;
                    color: #e0e0e0;
                    border: 1px solid #3a3a3a;
                    border-radius: 4px;
                    padding: 6px;
                }
                
                QDialog QComboBox, QFileDialog QComboBox {
                    background-color: #2d2d2d;
                    color: #e0e0e0;
                    border: 1px solid #3a3a3a;
                    border-radius: 4px;
                    padding: 6px;
                }
                
                QDialog QPushButton, QFileDialog QPushButton, QInputDialog QPushButton, QMessageBox QPushButton {
                    background-color: #3b82f6; /* azul elegante */
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 16px;
                    font-weight: bold;
                    min-width: 80px;
                }
                
                QDialog QPushButton:hover, QFileDialog QPushButton:hover, QInputDialog QPushButton:hover, QMessageBox QPushButton:hover {
                    background-color: #2563eb;
                }
                
                QDialog QPushButton:pressed, QFileDialog QPushButton:pressed, QInputDialog QPushButton:pressed, QMessageBox QPushButton:pressed {
                    background-color: #1d4ed8;
                }
            """
        else:
            return """
                QDialog, QFileDialog, QInputDialog, QMessageBox {
                    background-color: #f8f9fa;
                    color: #2c3e50;
                }
            """
    
    def apply_palette(self, widget, is_dark: bool):
        """Aplicar paleta de colores"""
        palette = QPalette()
        
        if is_dark:
            # Colores modo oscuro elegantes y limpios
            palette.setColor(QPalette.Window, QColor(18, 18, 18))      # #121212
            palette.setColor(QPalette.WindowText, QColor(224, 224, 224))
            palette.setColor(QPalette.Base, QColor(30, 30, 30))        # #1e1e1e
            palette.setColor(QPalette.AlternateBase, QColor(18, 18, 18))
            palette.setColor(QPalette.ToolTipBase, QColor(30, 30, 30))
            palette.setColor(QPalette.ToolTipText, QColor(224, 224, 224))
            palette.setColor(QPalette.Text, QColor(224, 224, 224))
            palette.setColor(QPalette.Button, QColor(42, 42, 42))      # #2a2a2a
            palette.setColor(QPalette.ButtonText, QColor(224, 224, 224))
            palette.setColor(QPalette.BrightText, Qt.red)
            palette.setColor(QPalette.Link, QColor(160, 160, 160))     # neutro
            palette.setColor(QPalette.Highlight, QColor(58, 58, 58))   # #3a3a3a
            palette.setColor(QPalette.HighlightedText, QColor(224, 224, 224))
        else:
            # Colores modo claro
            palette.setColor(QPalette.Window, QColor(248, 249, 250))
            palette.setColor(QPalette.WindowText, QColor(44, 62, 80))
            palette.setColor(QPalette.Base, Qt.white)
            palette.setColor(QPalette.AlternateBase, QColor(248, 249, 250))
            palette.setColor(QPalette.ToolTipBase, Qt.white)
            palette.setColor(QPalette.ToolTipText, QColor(44, 62, 80))
            palette.setColor(QPalette.Text, QColor(44, 62, 80))
            palette.setColor(QPalette.Button, Qt.white)
            palette.setColor(QPalette.ButtonText, QColor(44, 62, 80))
            palette.setColor(QPalette.BrightText, Qt.red)
            palette.setColor(QPalette.Link, QColor(52, 152, 219))
            palette.setColor(QPalette.Highlight, QColor(52, 152, 219))
            palette.setColor(QPalette.HighlightedText, Qt.white)
        
        widget.setPalette(palette)
    
    def get_widget_styles(self, is_dark: bool):
        """Obtener estilos específicos para widgets personalizados"""
        if is_dark:
            return """
                /* Estilos específicos para widgets personalizados en modo oscuro */
                QFrame#summary_frame {
                    background-color: #1e1e1e;
                    border: 1px solid #2a2a2a;
                    border-radius: 5px;
                }
                
                QLabel#status_label {
                    background-color: #27ae60;
                    color: white;
                    padding: 5px;
                    border-radius: 3px;
                    font-size: 9pt;
                }
                
                QLabel#error_status {
                    background-color: #e74c3c;
                    color: white;
                }
                
                QLabel#warning_status {
                    background-color: #f39c12;
                    color: white;
                }
            """
        else:
            return """
                /* Estilos específicos para widgets personalizados en modo claro */
                QFrame#summary_frame {
                    background-color: white;
                    border: 1px solid #dee2e6;
                    border-radius: 5px;
                }
                
                QLabel#status_label {
                    background-color: #27ae60;
                    color: white;
                    padding: 5px;
                    border-radius: 3px;
                    font-size: 9pt;
                }
                
                QLabel#error_status {
                    background-color: #e74c3c;
                    color: white;
                }
                
                QLabel#warning_status {
                    background-color: #f39c12;
                    color: white;
                }
            """