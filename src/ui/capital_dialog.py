"""
Diálogo para establecer el capital inicial de la semana.
En el primer arranque se muestra como pantalla de bienvenida.
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
                             QLineEdit, QPushButton, QMessageBox)
from PyQt5.QtGui import QDoubleValidator, QPixmap
from PyQt5.QtCore import Qt, pyqtSignal
from src.ui.animations import fade_in
from src.utils.i18n import tr
from src.utils.resources import logo_path

PRESETS = (50, 100, 250, 500, 1000)


class CapitalDialog(QDialog):
    """Diálogo para configurar el capital inicial de la semana"""

    capital_updated = pyqtSignal(float)  # Señal emitida cuando se actualiza el capital

    def __init__(self, current_capital=100.0, parent=None, first_time=False):
        super().__init__(parent)
        self.current_capital = current_capital
        self.first_time = first_time
        self.setWindowTitle(tr("capital_dialog_title"))
        self.setModal(True)
        self.setFixedWidth(460)

        self.setup_ui()

    def setup_ui(self):
        """Configurar la interfaz del diálogo"""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(26, 24, 26, 22)

        # Cabecera: logo + título
        head = QHBoxLayout()
        head.setSpacing(14)
        logo = logo_path()
        if logo:
            icon = QLabel()
            icon.setPixmap(QPixmap(logo).scaled(52, 52, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            head.addWidget(icon, 0, Qt.AlignTop)
        texts = QVBoxLayout()
        texts.setSpacing(4)
        self.title_label = QLabel()
        self.title_label.setObjectName('h1')
        self.desc_label = QLabel()
        self.desc_label.setObjectName('muted')
        self.desc_label.setWordWrap(True)
        texts.addWidget(self.title_label)
        texts.addWidget(self.desc_label)
        head.addLayout(texts, 1)
        layout.addLayout(head)

        # Tarjeta con el monto
        self.hero = QFrame()
        self.hero.setObjectName('heroCard')
        hv = QVBoxLayout(self.hero)
        hv.setContentsMargins(20, 16, 20, 18)
        hv.setSpacing(10)
        self.amount_caption = QLabel()
        self.amount_caption.setObjectName('caption')
        hv.addWidget(self.amount_caption)

        input_row = QHBoxLayout()
        input_row.setSpacing(8)
        self.currency_label = QLabel("$")
        self.currency_label.setStyleSheet("font-size: 24pt; font-weight: 800;")
        input_row.addWidget(self.currency_label)

        self.capital_input = QLineEdit()
        self.capital_input.setText(f"{self.current_capital:.2f}")
        self.capital_input.setPlaceholderText(tr("capital_placeholder"))
        # Validador para números decimales positivos
        validator = QDoubleValidator(0.01, 999999.99, 2)
        validator.setNotation(QDoubleValidator.StandardNotation)
        self.capital_input.setValidator(validator)
        self.capital_input.setStyleSheet("font-size: 22pt; font-weight: 700; padding: 8px 14px;")
        self.capital_input.textChanged.connect(self._sync_presets)
        input_row.addWidget(self.capital_input, 1)
        hv.addLayout(input_row)

        # Montos rápidos
        presets_row = QHBoxLayout()
        presets_row.setSpacing(6)
        self.preset_buttons = []
        for value in PRESETS:
            btn = QPushButton(f"${value:,}")
            btn.setObjectName('segment')
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _, v=value: self._use_preset(v))
            presets_row.addWidget(btn)
            self.preset_buttons.append((value, btn))
        presets_row.addStretch()
        hv.addLayout(presets_row)
        layout.addWidget(self.hero)

        # Nota informativa
        self.hint_label = QLabel()
        self.hint_label.setObjectName('muted')
        self.hint_label.setWordWrap(True)
        self.hint_label.setStyleSheet("font-size: 9pt;")
        layout.addWidget(self.hint_label)

        # Botones
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_layout.addStretch()
        self.cancel_button = QPushButton()
        self.cancel_button.setObjectName('ghost')
        self.cancel_button.setCursor(Qt.PointingHandCursor)
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        self.accept_button = QPushButton()
        self.accept_button.setObjectName('primary')
        self.accept_button.setCursor(Qt.PointingHandCursor)
        self.accept_button.setDefault(True)
        self.accept_button.clicked.connect(self.accept)
        button_layout.addWidget(self.accept_button)
        layout.addLayout(button_layout)

        self.apply_language()
        self._sync_presets()

        # Enfocar el campo de entrada
        self.capital_input.setFocus()
        self.capital_input.selectAll()

    def showEvent(self, event):
        super().showEvent(event)
        fade_in(self.hero, duration=420, slide=10)

    def _use_preset(self, value):
        self.capital_input.setText(f"{value:.2f}")
        self.capital_input.setFocus()
        self.capital_input.selectAll()

    def _sync_presets(self):
        """Marcar el monto rápido que coincide con el valor escrito."""
        try:
            current = float(self.capital_input.text())
        except ValueError:
            current = None
        for value, btn in self.preset_buttons:
            btn.setChecked(current is not None and abs(current - value) < 1e-9)
        self.accept_button.setEnabled(current is not None and current > 0)

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
            QMessageBox.warning(self, tr("warning"), tr("capital_required"))

    def keyPressEvent(self, event):
        """Manejar eventos de teclado"""
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.accept()
        elif event.key() == Qt.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)

    def apply_language(self):
        """Actualizar textos al cambiar idioma"""
        self.setWindowTitle(tr("capital_dialog_title"))
        if self.first_time:
            self.title_label.setText('👋 ' + tr('welcome_title', '¡Bienvenido a W-T-F!'))
            self.desc_label.setText(tr('welcome_capital_desc',
                                       'Para empezar, indica con cuánto capital arrancas esta semana. '
                                       'Lo usaremos para calcular tu balance y rendimiento.'))
            self.cancel_button.setText(tr('use_default_capital', 'Usar $100 por defecto'))
            self.accept_button.setText('🚀  ' + tr('start_week', 'Empezar semana'))
        else:
            self.title_label.setText('💰 ' + tr("capital_dialog_title"))
            self.desc_label.setText(tr("capital_tooltip"))
            self.cancel_button.setText(tr("cancel"))
            self.accept_button.setText(tr('save_capital', 'Guardar capital'))
        self.amount_caption.setText(tr('initial_capital_caps', 'CAPITAL INICIAL'))
        self.hint_label.setText('💡 ' + tr('capital_hint',
                                          'Puedes cambiarlo cuando quieras en Configuración → Trading.'))
