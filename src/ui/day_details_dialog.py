"""
Diálogo para anotar el par de divisas y la duración de la sesión de un día.
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
                             QPushButton, QFormLayout)
from PyQt5.QtCore import Qt
from src.utils.i18n import tr
from src.utils.settings_store import CURRENCY_PAIRS, DURATIONS


def make_editable_combo(options, value):
    combo = QComboBox()
    combo.setEditable(True)
    combo.addItems(options)
    combo.setCurrentText(value)
    combo.setInsertPolicy(QComboBox.NoInsert)
    return combo


class DayDetailsDialog(QDialog):
    def __init__(self, day_label: str, pair: str, duration: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr('session_details', 'Detalles de la sesión'))
        self.setModal(True)
        self.setMinimumWidth(380)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)

        title = QLabel(f"📝 {day_label}")
        title.setObjectName('h2')
        subtitle = QLabel(tr('session_details_hint', 'Se mostrará en el gráfico y en la imagen del resultado.'))
        subtitle.setObjectName('muted')
        subtitle.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(subtitle)

        form = QFormLayout()
        form.setSpacing(10)
        self.pair_combo = make_editable_combo(CURRENCY_PAIRS, pair)
        self.duration_combo = make_editable_combo(DURATIONS, duration)
        form.addRow(tr('currency_pair', 'Par de divisas'), self.pair_combo)
        form.addRow(tr('session_duration', 'Duración'), self.duration_combo)
        layout.addLayout(form)

        buttons = QHBoxLayout()
        buttons.addStretch()
        cancel = QPushButton(tr('cancel'))
        cancel.setObjectName('ghost')
        cancel.clicked.connect(self.reject)
        ok = QPushButton(tr('accept'))
        ok.setObjectName('primary')
        ok.setDefault(True)
        ok.clicked.connect(self.accept)
        buttons.addWidget(cancel)
        buttons.addWidget(ok)
        layout.addLayout(buttons)

    def values(self):
        return self.pair_combo.currentText().strip(), self.duration_combo.currentText().strip()
