"""
Diálogo de capital para un día específico: ingresar capital inicial y actual,
y calcular ganancia/pérdida.
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton)
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtCore import Qt
from src.utils.i18n import tr


class DayCapitalDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr('Day_Capital') or 'Ingresar capital del día')
        self.setModal(True)
        self.setFixedSize(420, 260)
        self._initial_capital = 0.0
        self._current_capital = 0.0
        self._profit_loss = 0.0
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel(tr('Calc Day Capital') or 'Ingresar capital del día')
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet('font-size: 14pt; font-weight: bold;')
        layout.addWidget(title)

        # Inicial
        row1 = QHBoxLayout()
        lbl_initial = QLabel(tr('initial_capital') or 'Capital inicial')
        lbl_initial.setMinimumWidth(140)
        self.input_initial = QLineEdit()
        self.input_initial.setPlaceholderText(tr('initial_capital') or 'Capital inicial')
        self.input_initial.setValidator(QDoubleValidator(0.0, 1_000_000.0, 2))
        row1.addWidget(lbl_initial)
        row1.addWidget(self.input_initial)
        layout.addLayout(row1)

        # Actual
        row2 = QHBoxLayout()
        lbl_current = QLabel(tr('current_capital') or 'Capital actual')
        lbl_current.setMinimumWidth(140)
        self.input_current = QLineEdit()
        self.input_current.setPlaceholderText(tr('current_capital') or 'Capital actual')
        self.input_current.setValidator(QDoubleValidator(0.0, 1_000_000.0, 2))
        row2.addWidget(lbl_current)
        row2.addWidget(self.input_current)
        layout.addLayout(row2)

        # Resultado
        self.result_label = QLabel('')
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setStyleSheet('font-size: 12pt; color: #2c3e50;')
        layout.addWidget(self.result_label)

        # Botones
        buttons = QHBoxLayout()
        btn_cancel = QPushButton(tr('cancel'))
        btn_cancel.clicked.connect(self.reject)
        btn_ok = QPushButton(tr('accept') or 'Aceptar')
        btn_ok.setDefault(True)
        btn_ok.clicked.connect(self._on_accept)
        buttons.addWidget(btn_cancel)
        buttons.addWidget(btn_ok)

        layout.addLayout(buttons)
        self.setLayout(layout)

        # Eventos de actualización
        self.input_initial.textChanged.connect(self._recalc)
        self.input_current.textChanged.connect(self._recalc)

    def set_initial_capital(self, value: float):
        self._initial_capital = float(value or 0.0)
        self.input_initial.setText(f"{self._initial_capital:.2f}")

    def get_profit_loss(self) -> float:
        return float(self._profit_loss)

    def _recalc(self):
        try:
            initial = float(self.input_initial.text() or 0)
            current = float(self.input_current.text() or 0)
            self._profit_loss = current - initial
            sign = '+' if self._profit_loss >= 0 else ''
            self.result_label.setText(f"Resultado: {sign}{self._profit_loss:.2f}")
        except ValueError:
            self.result_label.setText('')

    def _on_accept(self):
        self._recalc()
        self.accept()