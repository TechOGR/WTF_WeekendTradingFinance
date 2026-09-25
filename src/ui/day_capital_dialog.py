"""
Diálogo del modo edición por capital: se escribe con cuánto empezó y terminó el día
y se calcula la ganancia/pérdida (con porcentaje) antes de guardarla.
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
                             QLineEdit, QPushButton, QButtonGroup)
from PyQt5.QtGui import QRegExpValidator, QPixmap
from PyQt5.QtCore import Qt, QRegExp
from src.styles.themes import ThemeManager
from src.ui.animations import AnimatedNumberLabel, fade_in
from src.utils.i18n import tr
from src.utils.resources import logo_path


def _money(v):
    return f"{'-' if v < 0 else ''}${abs(v):,.2f}"


def _signed(v):
    return f"{'+' if v >= 0 else '-'}${abs(v):,.2f}"


def _parse(text):
    try:
        return float((text or '').replace('$', '').replace(' ', '').replace(',', '.'))
    except ValueError:
        return None


class DayCapitalDialog(QDialog):
    """Calcular el resultado de un día a partir del capital inicial y final.

    day_start: balance con el que arrancó el día (capital semanal + días anteriores).
    week_initial: capital inicial de la semana. current_amount: resultado ya guardado del día.
    """

    def __init__(self, parent=None, day_label='', week_initial=0.0, day_start=None, current_amount=0.0,
                 is_dark=True):
        super().__init__(parent)
        self.c = ThemeManager.colors(is_dark)
        self.day_label = day_label
        self.week_initial = float(week_initial or 0.0)
        self.day_start = float(day_start if day_start is not None else self.week_initial)
        self.current_amount = float(current_amount or 0.0)
        self._profit_loss = 0.0
        self.setWindowTitle(tr('day_capital_title', 'Capital del día'))
        self.setModal(True)
        self.setFixedWidth(520)
        self._setup_ui()

    # ------------------------------------------------------------------ UI
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(26, 22, 26, 20)

        head = QHBoxLayout()
        head.setSpacing(14)
        logo = logo_path()
        if logo:
            icon = QLabel()
            icon.setPixmap(QPixmap(logo).scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            head.addWidget(icon, 0, Qt.AlignTop)
        texts = QVBoxLayout()
        texts.setSpacing(3)
        title = QLabel('🧮 ' + tr('day_capital_title', 'Capital del día')
                       + (f' · {self.day_label}' if self.day_label else ''))
        title.setObjectName('h2')
        desc = QLabel(tr('day_capital_desc', 'Escribe con cuánto empezaste y con cuánto terminaste el día: '
                                             'calculamos la ganancia o pérdida por ti.'))
        desc.setObjectName('muted')
        desc.setWordWrap(True)
        texts.addWidget(title)
        texts.addWidget(desc)
        head.addLayout(texts, 1)
        layout.addLayout(head)

        # Referencia rápida para el capital inicial
        self.ref_group = QButtonGroup(self)
        refs = [(tr('day_start_ref', 'Inicio del día'), self.day_start)]
        if abs(self.day_start - self.week_initial) > 1e-9:
            refs.append((tr('week_capital_ref', 'Capital semanal'), self.week_initial))
        ref_row = QHBoxLayout()
        ref_row.setSpacing(6)
        ref_lbl = QLabel(tr('start_from', 'Empezar desde:'))
        ref_lbl.setObjectName('muted')
        ref_row.addWidget(ref_lbl)
        for text, value in refs:
            btn = QPushButton(f'{text} · {_money(value)}')
            btn.setObjectName('segment')
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _, v=value: self._use_reference(v))
            self.ref_group.addButton(btn)
            ref_row.addWidget(btn)
        ref_row.addStretch()
        layout.addLayout(ref_row)

        # Tarjeta: inicial → final
        self.hero = QFrame()
        self.hero.setObjectName('heroCard')
        hv = QHBoxLayout(self.hero)
        hv.setContentsMargins(18, 16, 18, 16)
        hv.setSpacing(12)
        validator = QRegExpValidator(QRegExp(r'^\d{0,9}([.,]\d{0,2})?$'), self)
        self.input_initial = self._amount_field(hv, tr('initial_capital_caps', 'CAPITAL INICIAL'), validator)
        arrow = QLabel('➜')
        arrow.setStyleSheet(f"font-size: 18pt; color: {self.c['text_muted']};")
        hv.addWidget(arrow, 0, Qt.AlignBottom)
        self.input_current = self._amount_field(hv, tr('final_capital_caps', 'CAPITAL FINAL'), validator)
        layout.addWidget(self.hero)

        # Resultado en vivo
        self.result_box = QFrame()
        self.result_box.setObjectName('cardAlt')
        rv = QHBoxLayout(self.result_box)
        rv.setContentsMargins(18, 12, 18, 12)
        left = QVBoxLayout()
        left.setSpacing(2)
        cap = QLabel(tr('day_result_caps', 'RESULTADO DEL DÍA'))
        cap.setObjectName('caption')
        self.result_label = AnimatedNumberLabel(_signed)
        self.result_label.setStyleSheet('font-size: 22pt; font-weight: 900;')
        left.addWidget(cap)
        left.addWidget(self.result_label)
        rv.addLayout(left, 1)
        right = QVBoxLayout()
        right.setSpacing(4)
        self.pct_chip = QLabel('0.00%')
        self.pct_chip.setObjectName('chip')
        self.pct_chip.setAlignment(Qt.AlignCenter)
        self.previous_label = QLabel('')
        self.previous_label.setObjectName('muted')
        self.previous_label.setStyleSheet('font-size: 8.5pt;')
        self.previous_label.setAlignment(Qt.AlignRight)
        right.addWidget(self.pct_chip, 0, Qt.AlignRight)
        right.addWidget(self.previous_label)
        rv.addLayout(right)
        layout.addWidget(self.result_box)

        hint = QLabel('💡 ' + tr('day_capital_hint', 'Enter guarda · Esc cancela. Puedes desactivar este modo en '
                                                     'Configuración → Trading.'))
        hint.setObjectName('muted')
        hint.setWordWrap(True)
        hint.setStyleSheet('font-size: 8.5pt;')
        layout.addWidget(hint)

        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        buttons.addStretch()
        cancel = QPushButton(tr('cancel'))
        cancel.setObjectName('ghost')
        cancel.setCursor(Qt.PointingHandCursor)
        cancel.clicked.connect(self.reject)
        self.ok_button = QPushButton('💾  ' + tr('save_result', 'Guardar resultado'))
        self.ok_button.setObjectName('primary')
        self.ok_button.setCursor(Qt.PointingHandCursor)
        self.ok_button.setDefault(True)
        self.ok_button.clicked.connect(self._on_accept)
        buttons.addWidget(cancel)
        buttons.addWidget(self.ok_button)
        layout.addLayout(buttons)

        self.input_initial.textChanged.connect(self._recalc)
        self.input_current.textChanged.connect(self._recalc)

        # Valores iniciales: inicio del día y, si el día ya tenía resultado, el capital final correspondiente
        self.input_initial.setText(f'{self.day_start:.2f}')
        if abs(self.current_amount) > 1e-9:
            self.input_current.setText(f'{self.day_start + self.current_amount:.2f}')
            self.previous_label.setText(tr('saved_before', 'Guardado: {v}').format(v=_signed(self.current_amount)))
        self._recalc()
        self.input_current.setFocus()
        self.input_current.selectAll()

    def _amount_field(self, parent_layout, caption, validator):
        box = QVBoxLayout()
        box.setSpacing(6)
        cap = QLabel(caption)
        cap.setObjectName('caption')
        row = QHBoxLayout()
        row.setSpacing(6)
        cur = QLabel('$')
        cur.setStyleSheet('font-size: 18pt; font-weight: 800;')
        edit = QLineEdit()
        edit.setValidator(validator)
        edit.setPlaceholderText('0.00')
        edit.setStyleSheet('font-size: 17pt; font-weight: 700; padding: 6px 10px;')
        row.addWidget(cur)
        row.addWidget(edit, 1)
        box.addWidget(cap)
        box.addLayout(row)
        parent_layout.addLayout(box, 1)
        return edit

    def showEvent(self, event):
        super().showEvent(event)
        fade_in(self.hero, duration=380, slide=8)
        fade_in(self.result_box, duration=420, delay=90, slide=8)

    # ------------------------------------------------------------ lógica
    def _use_reference(self, value):
        self.input_initial.setText(f'{value:.2f}')
        self.input_current.setFocus()
        self.input_current.selectAll()

    def _sync_references(self, initial):
        for btn in self.ref_group.buttons():
            value = self.day_start if btn is self.ref_group.buttons()[0] else self.week_initial
            btn.setChecked(initial is not None and abs(initial - value) < 1e-9)

    def _recalc(self):
        initial = _parse(self.input_initial.text())
        current = _parse(self.input_current.text())
        self._sync_references(initial)
        valid = initial is not None and current is not None
        self.ok_button.setEnabled(valid)
        pl = (current - initial) if valid else 0.0
        self._profit_loss = pl
        color = self.c['success'] if pl > 1e-9 else self.c['danger'] if pl < -1e-9 else self.c['text_secondary']
        self.result_label.setStyleSheet(f'font-size: 22pt; font-weight: 900; color: {color};')
        self.result_label.set_value(pl)
        pct = (pl / initial * 100) if valid and initial else 0.0
        self.pct_chip.setText(f'{pct:+.2f}%' if valid else '—')
        self.pct_chip.setStyleSheet(f'color: {color};')

    # ------------------------------------------------------------ API
    def set_initial_capital(self, value: float):
        self.input_initial.setText(f"{float(value or 0.0):.2f}")

    def get_profit_loss(self) -> float:
        return round(float(self._profit_loss), 2)

    def _on_accept(self):
        self._recalc()
        if self.ok_button.isEnabled():
            self.accept()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self._on_accept()
        else:
            super().keyPressEvent(event)
