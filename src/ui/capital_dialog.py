"""
Diálogo para establecer el capital inicial de la semana
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                               QLineEdit, QPushButton)
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtCore import Qt, pyqtSignal
from src.utils.i18n import tr


class CapitalDialog(QDialog):
    """Diálogo para configurar el capital inicial de la semana"""
    
    capital_updated = pyqtSignal(float)  # Señal emitida cuando se actualiza el capital
    
    def __init__(self, current_capital=100.0, parent=None):
        super().__init__(parent)
        self.current_capital = current_capital
        self.setWindowTitle(tr("capital_dialog_title"))
        self.setModal(True)
        self.setFixedSize(400, 500)
        
        self.setup_ui()
        
    def setup_ui(self):
        """Configurar la interfaz del diálogo"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Título
        self.title_label = QLabel(tr("capital_dialog_title"))
        self.title_label.setStyleSheet("""
            QLabel {
                font-size: 16pt;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 10px;
            }
        """)
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label)
        
        # Descripción
        self.desc_label = QLabel(tr("capital_tooltip"))
        self.desc_label.setStyleSheet("font-size: 11pt; color: #34495e; margin-bottom: 10px;")
        self.desc_label.setWordWrap(True)
        layout.addWidget(self.desc_label)
        
        # Campo de entrada
        input_layout = QHBoxLayout()
        
        self.currency_label = QLabel("$")
        self.currency_label.setStyleSheet("font-size: 14pt; font-weight: bold; color: #2c3e50;")
        input_layout.addWidget(self.currency_label)
        
        self.capital_input = QLineEdit()
        self.capital_input.setText(str(self.current_capital))
        self.capital_input.setPlaceholderText("Ej: 100.00")
        
        # Validador para números decimales positivos
        validator = QDoubleValidator(0.01, 999999.99, 2)
        validator.setNotation(QDoubleValidator.StandardNotation)
        self.capital_input.setValidator(validator)
        
        self.capital_input.setStyleSheet("""
            QLineEdit {
                font-size: 14pt;
                padding: 10px;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                background-color: #ffffff;
                min-width: 200px;
            }
            QLineEdit:focus {
                border-color: #3498db;
                background-color: #f8f9fa;
            }
        """)
        input_layout.addWidget(self.capital_input)
        
        layout.addLayout(input_layout)
        
        # Botones
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        self.cancel_button = QPushButton(tr("cancel"))
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 11pt;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
            QPushButton:pressed {
                background-color: #6c7b7d;
            }
        """)
        button_layout.addWidget(self.cancel_button)
        
        self.accept_button = QPushButton(tr("set_capital"))
        self.accept_button.clicked.connect(self.accept)
        self.accept_button.setDefault(True)
        self.accept_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 11pt;
                font-weight: bold;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
        """)
        button_layout.addWidget(self.accept_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Enfocar el campo de entrada
        self.capital_input.setFocus()
        self.capital_input.selectAll()
    
    def get_capital(self):
        """Obtener el capital ingresado"""
        try:
            return float(self.capital_input.text())
        except ValueError:
            return self.current_capital
    
    def accept(self):
        """Aceptar el diálogo y emitir señal"""
        capital = self.get_capital()
        if capital > 0:
            self.capital_updated.emit(capital)
            super().accept()
        else:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, tr("warning"), tr("capital_required"))
    
    def keyPressEvent(self, event):
        """Manejar eventos de teclado"""
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.accept()
        elif event.key() == Qt.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)

    def apply_language(self):
        """Actualizar textos al cambiar idioma"""
        self.setWindowTitle(tr("capital_dialog_title"))
        self.title_label.setText(tr("capital_dialog_title"))
        self.desc_label.setText(tr("capital_tooltip"))
        self.cancel_button.setText(tr("cancel"))
        self.accept_button.setText(tr("set_capital"))