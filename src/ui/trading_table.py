"""
Widget de tabla para la interfaz de trading
"""

from PyQt5.QtWidgets import (QTableWidget, QTableWidgetItem, QHeaderView, QMenu, QAbstractItemView)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QBrush, QColor
from src.styles.themes import ThemeManager
from src.utils.i18n import tr
from src.utils.settings_store import CURRENCY_PAIRS

DAY_KEYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

COL_DAY, COL_AMOUNT, COL_SESSION, COL_DEST = range(4)


class TradingTableWidget(QTableWidget):
    """Tabla personalizada para mostrar y editar datos de trading"""

    save_status_changed = pyqtSignal(str)  # Señal para actualizar el estado de guardado
    data_changed = pyqtSignal()  # Señal para notificar cambios en los datos
    generate_image_requested = pyqtSignal(str)  # Día para el que generar la imagen

    def __init__(self, data_model):
        super().__init__()
        self.data_model = data_model
        self.capital_edit_mode = False
        self.is_dark = True
        self.setup_table()
        self.load_data()

    def setup_table(self):
        """Configurar la tabla"""
        self.setColumnCount(4)
        self.setRowCount(len(self.data_model.days))
        self._set_headers()

        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(44)
        self.setShowGrid(False)
        self.setAlternatingRowColors(False)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setFocusPolicy(Qt.StrongFocus)

        header = self.horizontalHeader()
        header.setSectionResizeMode(COL_DAY, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(COL_AMOUNT, QHeaderView.Stretch)
        header.setSectionResizeMode(COL_SESSION, QHeaderView.Stretch)
        header.setSectionResizeMode(COL_DEST, QHeaderView.ResizeToContents)
        header.setHighlightSections(False)

        self.setEditTriggers(self.DoubleClicked | self.SelectedClicked | self.EditKeyPressed)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

        self.cellChanged.connect(self.on_cell_changed)
        self.cellDoubleClicked.connect(self.on_cell_double_clicked)

        # Altura justa para 5 filas sin barra de desplazamiento
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setMinimumHeight(44 * len(self.data_model.days) + 52)
        self.setMaximumHeight(44 * len(self.data_model.days) + 60)

    def _set_headers(self):
        self.setHorizontalHeaderLabels([
            tr('day_column'),
            tr('amount_column'),
            tr('session_column', 'Sesión (par · duración)'),
            tr('destination_column'),
        ])

    def set_theme(self, is_dark: bool):
        self.is_dark = is_dark
        self.load_data()

    def load_data(self):
        """Cargar datos en la tabla"""
        c = ThemeManager.colors(self.is_dark)
        self.blockSignals(True)

        for row, day in enumerate(self.data_model.days):
            info = self.data_model.data[day]

            day_item = QTableWidgetItem(day)
            day_item.setFlags(day_item.flags() & ~Qt.ItemIsEditable)
            day_item.setFont(QFont("Segoe UI", 10, QFont.Bold))
            self.setItem(row, COL_DAY, day_item)

            amount = info['amount']
            amount_item = QTableWidgetItem(f"{amount:.2f}")
            amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            amount_item.setFont(QFont("Segoe UI", 11, QFont.Bold))
            if amount > 0:
                amount_item.setForeground(QBrush(QColor(c['success'])))
            elif amount < 0:
                amount_item.setForeground(QBrush(QColor(c['danger'])))
            else:
                amount_item.setForeground(QBrush(QColor(c['text_muted'])))
            amount_item.setToolTip(tr('amount_tooltip', 'Doble clic para editar la ganancia/pérdida del día'))
            self.setItem(row, COL_AMOUNT, amount_item)

            pair, duration = info.get('pair', ''), info.get('duration', '')
            session_text = ' · '.join(filter(None, [pair, duration])) or '＋ ' + tr('add_session', 'Añadir')
            session_item = QTableWidgetItem(session_text)
            session_item.setFlags(session_item.flags() & ~Qt.ItemIsEditable)
            session_item.setForeground(QBrush(QColor(c['accent2'] if pair or duration else c['text_muted'])))
            session_item.setToolTip(tr('session_tooltip', 'Doble clic para anotar par de divisas y duración'))
            self.setItem(row, COL_SESSION, session_item)

            destination = info['destination']
            dest_item = QTableWidgetItem(destination)
            dest_item.setFlags(dest_item.flags() & ~Qt.ItemIsEditable)
            if destination in {"Retiro Personal", "Personal Withdrawal", tr('personal_withdrawal')}:
                dest_item.setForeground(QBrush(QColor(c['accent_hover'])))
            else:
                dest_item.setForeground(QBrush(QColor(c['warning'])))
            self.setItem(row, COL_DEST, dest_item)

        self.blockSignals(False)

    def on_cell_changed(self, row, column):
        """Manejar cambios en las celdas"""
        if column != COL_AMOUNT:
            return
        text = self.item(row, column).text()
        try:
            day = self.item(row, COL_DAY).text()
            amount = float(text.replace(',', '.').replace('$', '').strip())
            self.data_model.update_day(day, amount)
            self.data_changed.emit()
            self.save_status_changed.emit(tr('saving'))
            self.load_data()
            self.save_status_changed.emit("✅ " + tr('save_success'))
        except ValueError:
            self.load_data()
            print(f"{tr('invalid_amount')}: {text}")

    def set_capital_edit_mode(self, enabled: bool):
        """Activar o desactivar el modo de edición por capital."""
        self.capital_edit_mode = bool(enabled)

    def on_cell_double_clicked(self, row, column):
        if column == COL_SESSION:
            self.edit_session(row)
            return
        if column != COL_AMOUNT or not self.capital_edit_mode:
            return

        day = self.item(row, COL_DAY).text()
        try:
            from src.ui.day_capital_dialog import DayCapitalDialog
            initial = float(getattr(self.data_model, 'initial_capital', 0.0) or 0.0)
            previous = sum(float(self.data_model.data[d].get('amount', 0.0) or 0.0)
                           for d in self.data_model.days[:row])
            dialog = DayCapitalDialog(parent=self, day_label=self._day_label(row), week_initial=initial,
                                      day_start=initial + previous,
                                      current_amount=self.data_model.data[day].get('amount', 0.0),
                                      is_dark=self.is_dark)
            if dialog.exec_():
                profit_loss = dialog.get_profit_loss()
                self.blockSignals(True)
                self.data_model.update_day(day, float(profit_loss))
                self.blockSignals(False)
                self.data_changed.emit()
                self.save_status_changed.emit(tr('saving'))
                self.load_data()
                self.save_status_changed.emit("✅ " + tr('save_success'))
        except Exception as e:
            print(f"Error al abrir diálogo de capital: {e}")

    def edit_session(self, row):
        """Anotar par de divisas y duración del día."""
        from src.ui.day_details_dialog import DayDetailsDialog
        day = self.item(row, COL_DAY).text()
        info = self.data_model.data[day]
        pair = info.get('pair', '') or getattr(self, 'default_pair', CURRENCY_PAIRS[0])
        duration = info.get('duration', '') or getattr(self, 'default_duration', '15 min')
        dialog = DayDetailsDialog(self._day_label(row), pair, duration, self)
        if dialog.exec_():
            pair, duration = dialog.values()
            self.data_model.set_day_details(day, pair, duration)
            self.load_data()
            self.data_changed.emit()
            self.save_status_changed.emit("✅ " + tr('save_success'))

    def _day_label(self, row):
        return tr(DAY_KEYS[row]) if row < len(DAY_KEYS) else self.item(row, COL_DAY).text()

    def _show_context_menu(self, pos):
        index = self.indexAt(pos)
        if not index.isValid():
            return
        row = index.row()
        day = self.item(row, COL_DAY).text()
        menu = QMenu(self)
        menu.addAction('✏️  ' + tr('edit_amount', 'Editar resultado'),
                       lambda: self.editItem(self.item(row, COL_AMOUNT)))
        menu.addAction('📝  ' + tr('session_details', 'Detalles de la sesión'), lambda: self.edit_session(row))
        menu.addSeparator()
        menu.addAction('🖼️  ' + tr('generate_result_image', 'Generar imagen del resultado'),
                       lambda: self.generate_image_requested.emit(day))
        menu.exec_(self.viewport().mapToGlobal(pos))

    def selected_day(self):
        row = self.currentRow()
        if 0 <= row < self.rowCount():
            return self.item(row, COL_DAY).text()
        return None

    def get_data(self):
        """Obtener los datos actuales de la tabla"""
        data = {}
        for row in range(self.rowCount()):
            day = self.item(row, COL_DAY).text()
            try:
                amount = float(self.item(row, COL_AMOUNT).text())
            except ValueError:
                amount = 0.0
            data[day] = amount
        return data

    def apply_language(self):
        """Actualizar encabezados y textos según el idioma actual"""
        self._set_headers()
        self.load_data()
