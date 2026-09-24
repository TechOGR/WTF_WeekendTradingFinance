"""
Ventana de exportación: Excel, CSV o JSON de la semana actual o de todo el historial,
con vista previa real de los datos y destino recordado entre sesiones.
"""

import os

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QScrollArea, QFrame, QPushButton,
                             QLineEdit, QFileDialog, QMessageBox, QTableWidget, QTableWidgetItem,
                             QHeaderView, QApplication, QWidget, QButtonGroup, QAbstractItemView)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QDesktopServices, QColor, QPixmap

from src.styles.themes import ThemeManager
from src.ui.animations import ToggleSwitch, fade_in
from src.utils.export_manager import (FORMAT_EXCEL, FORMAT_CSV, FORMAT_JSON, EXTENSIONS, collect_weeks,
                                      count_saved_weeks, export_weeks, flat_rows, _headers)
from src.utils.i18n import tr
from src.utils.resources import logo_path

FORMATS = [
    (FORMAT_EXCEL, '📊', 'Excel', 'fmt_excel_desc', 'Fórmulas y gráficos'),
    (FORMAT_CSV, '📋', 'CSV', 'fmt_csv_desc', 'Tabla universal'),
    (FORMAT_JSON, '🧩', 'JSON', 'fmt_json_desc', 'Para desarrolladores'),
]
PREVIEW_ROWS = 6


class ExportDialog(QDialog):
    def __init__(self, model, settings, fmt=FORMAT_EXCEL, is_dark=True, parent=None):
        super().__init__(parent)
        self.model = model
        self.settings = settings
        self.c = ThemeManager.colors(is_dark)
        self.last_path = None
        self.setWindowTitle(tr('export_dialog_title'))
        self.setModal(True)
        screen = QApplication.primaryScreen()
        available = screen.availableGeometry().height() if screen else 900
        self.resize(780, min(910, available - 60))

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_header())

        body = QWidget()
        body.setObjectName('transparent')
        self.body = QVBoxLayout(body)
        self.body.setContentsMargins(24, 18, 24, 18)
        self.body.setSpacing(14)
        self._cards = []
        self._build_format(fmt if fmt in EXTENSIONS else FORMAT_EXCEL)
        self._build_scope_and_options()
        self._build_destination()
        self._build_preview()
        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setFrameShape(QFrame.NoFrame)
        area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        area.setWidget(body)
        root.addWidget(area, 1)
        root.addWidget(self._build_footer())

        self._refresh()

    # ------------------------------------------------------------ construcción
    def _build_header(self):
        header = QFrame()
        header.setObjectName('header')
        hl = QHBoxLayout(header)
        hl.setContentsMargins(24, 16, 24, 16)
        hl.setSpacing(14)
        logo = logo_path()
        if logo:
            icon = QLabel()
            icon.setPixmap(QPixmap(logo).scaled(44, 44, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            hl.addWidget(icon)
        texts = QVBoxLayout()
        texts.setSpacing(2)
        title = QLabel('📤 ' + tr('export_dialog_title'))
        title.setObjectName('h1')
        sub = QLabel(tr('export_subtitle', 'Descarga tus resultados para analizarlos o compartirlos.'))
        sub.setObjectName('muted')
        texts.addWidget(title)
        texts.addWidget(sub)
        hl.addLayout(texts, 1)
        return header

    def _card(self, title):
        card = QFrame()
        card.setObjectName('card')
        v = QVBoxLayout(card)
        v.setContentsMargins(18, 14, 18, 14)
        v.setSpacing(10)
        lbl = QLabel(title)
        lbl.setObjectName('h3')
        v.addWidget(lbl)
        self.body.addWidget(card)
        self._cards.append(card)
        return v

    def _build_format(self, fmt):
        card = self._card('📁  ' + tr('format_label').rstrip(':'))
        row = QHBoxLayout()
        row.setSpacing(10)
        self.format_group = QButtonGroup(self)
        self.format_buttons = {}
        for key, icon, name, desc_key, desc in FORMATS:
            btn = QPushButton(f"{icon}  {name}\n{tr(desc_key, desc)}")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setMinimumHeight(64)
            btn.setStyleSheet(f"""
                QPushButton {{
                    text-align: left; padding: 10px 14px; border-radius: 12px;
                    background-color: {self.c['surface_alt']}; border: 1px solid {self.c['border']};
                    font-weight: 600;
                }}
                QPushButton:hover {{ border-color: {self.c['accent']}; }}
                QPushButton:checked {{
                    background-color: {self.c['accent_soft']}; border: 2px solid {self.c['accent']};
                }}
            """)
            btn.setChecked(key == fmt)
            self.format_group.addButton(btn)
            self.format_buttons[key] = btn
            row.addWidget(btn, 1)
        self.format_group.buttonClicked.connect(lambda _: self._refresh())
        card.addLayout(row)

    def _toggle_row(self, title, desc, checked):
        """Opción con interruptor; devuelve (interruptor, contenedor) para poder ocultarla."""
        box = QFrame()
        box.setObjectName('cardAlt')
        row = QHBoxLayout(box)
        row.setContentsMargins(12, 8, 12, 8)
        texts = QVBoxLayout()
        texts.setSpacing(1)
        t = QLabel(title)
        t.setStyleSheet('font-weight: 600;')
        texts.addWidget(t)
        if desc:
            d = QLabel(desc)
            d.setObjectName('muted')
            d.setStyleSheet('font-size: 8pt;')
            d.setWordWrap(True)
            texts.addWidget(d)
        row.addLayout(texts, 1)
        sw = ToggleSwitch(checked=checked)
        row.addWidget(sw, 0, Qt.AlignVCenter)
        return sw, box

    def _build_scope_and_options(self):
        card = self._card('⚙️  ' + tr('export_options', 'Qué y cómo exportar'))
        scope_row = QHBoxLayout()
        scope_row.setSpacing(6)
        self.scope_group = QButtonGroup(self)
        start = getattr(self.model, 'week_start_date', None)
        self.scope_current = QPushButton('📅  ' + tr('current_week', 'Semana actual') +
                                         (f"  ({start.strftime('%d/%m/%Y')})" if start else ''))
        self.saved_weeks = count_saved_weeks(self.model)
        self.scope_all = QPushButton('🗂️  ' + tr('all_weeks', 'Todo el historial') + f"  ({self.saved_weeks})")
        for b in (self.scope_current, self.scope_all):
            b.setObjectName('segment')
            b.setCheckable(True)
            b.setCursor(Qt.PointingHandCursor)
            b.setMinimumHeight(34)
            self.scope_group.addButton(b)
            scope_row.addWidget(b)
        scope_row.addStretch()
        self.scope_current.setChecked(True)
        self.scope_all.setEnabled(self.saved_weeks > 1)
        self.scope_group.buttonClicked.connect(lambda _: self._refresh())
        card.addLayout(scope_row)

        self.summary_switch, summary_box = self._toggle_row(
            tr('include_detailed_summary'),
            tr('include_summary_desc', 'Capital, rendimiento, tasa de acierto, retiro y capital de la próxima semana.'),
            self.settings.get_bool('export_summary'))
        self.open_switch, open_box = self._toggle_row(
            tr('open_after_export', 'Abrir el archivo al terminar'),
            tr('open_after_export_desc', 'Se abre con la aplicación predeterminada.'),
            self.settings.get_bool('export_open_after'))
        # Opciones propias de cada formato: comparten celda y solo se ve la que aplica
        self.charts_switch, self.charts_box = self._toggle_row(
            tr('include_charts', 'Incluir gráficos'),
            tr('include_charts_desc', 'Resultados por día y evolución del balance (solo Excel).'),
            self.settings.get_bool('export_charts'))
        self.regional_switch, self.regional_box = self._toggle_row(
            tr('csv_regional', 'CSV para Excel en español'),
            tr('csv_regional_desc', 'Usa punto y coma (;) y coma decimal para que Excel lo abra en columnas.'),
            self.settings.get_bool('export_csv_regional'))
        grid = QGridLayout()
        grid.setSpacing(8)
        grid.addWidget(summary_box, 0, 0)
        grid.addWidget(open_box, 0, 1)
        grid.addWidget(self.charts_box, 1, 0)
        grid.addWidget(self.regional_box, 1, 0)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        card.addLayout(grid)

    def _build_destination(self):
        card = self._card('💾  ' + tr('destination', 'Destino'))
        row = QHBoxLayout()
        row.setSpacing(8)
        self.path_edit = QLineEdit()
        self.path_edit.textEdited.connect(lambda _: self._set_status(''))
        row.addWidget(self.path_edit, 1)
        browse = QPushButton('📂  ' + tr('change', 'Cambiar'))
        browse.setCursor(Qt.PointingHandCursor)
        browse.clicked.connect(self._browse)
        row.addWidget(browse)
        card.addLayout(row)

    def _build_preview(self):
        card = self._card('👁️  ' + tr('preview_title').replace('👁️', '').strip())
        self.preview_info = QLabel()
        self.preview_info.setObjectName('muted')
        self.preview_info.setStyleSheet('font-size: 9pt;')
        card.addWidget(self.preview_info)
        self.table = QTableWidget()
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setDefaultSectionSize(32)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        card.addWidget(self.table, 1)

    def _build_footer(self):
        footer = QFrame()
        footer.setObjectName('header')
        fl = QHBoxLayout(footer)
        fl.setContentsMargins(24, 12, 24, 12)
        fl.setSpacing(10)
        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        fl.addWidget(self.status_label, 1)
        self.open_file_btn = QPushButton('📄  ' + tr('open_file', 'Abrir archivo'))
        self.open_folder_btn = QPushButton('↗  ' + tr('open_folder', 'Abrir carpeta'))
        for b in (self.open_file_btn, self.open_folder_btn):
            b.setObjectName('ghost')
            b.setCursor(Qt.PointingHandCursor)
            b.setVisible(False)
            fl.addWidget(b)
        self.open_file_btn.clicked.connect(lambda: self._open(self.last_path))
        self.open_folder_btn.clicked.connect(lambda: self._open(os.path.dirname(self.last_path or '')))
        close = QPushButton(tr('close'))
        close.setObjectName('ghost')
        close.setCursor(Qt.PointingHandCursor)
        close.clicked.connect(self.reject)
        fl.addWidget(close)
        self.export_btn = QPushButton('🚀  ' + tr('export', 'Exportar'))
        self.export_btn.setObjectName('primary')
        self.export_btn.setCursor(Qt.PointingHandCursor)
        self.export_btn.setDefault(True)
        self.export_btn.clicked.connect(self._export)
        fl.addWidget(self.export_btn)
        return footer

    # ------------------------------------------------------------ estado
    def _format(self):
        return next(k for k, b in self.format_buttons.items() if b.isChecked())

    def _all_weeks(self):
        return self.scope_all.isChecked()

    def _default_filename(self):
        start = getattr(self.model, 'week_start_date', None)
        if self._all_weeks():
            from datetime import date
            base = f"WTF_{tr('history', 'Historial').lower()}_{date.today().isoformat()}"
        else:
            base = f"WTF_{tr('week').lower()}_{start.isoformat() if start else 'actual'}"
        return base + EXTENSIONS[self._format()]

    def _refresh(self):
        fmt = self._format()
        # Mantener la carpeta elegida y regenerar el nombre según formato/alcance
        folder = os.path.dirname(self.path_edit.text().strip()) or self.settings.get('export_dir')
        self.path_edit.setText(os.path.normpath(os.path.join(folder, self._default_filename())))

        self.charts_box.setVisible(fmt == FORMAT_EXCEL)
        self.regional_box.setVisible(fmt == FORMAT_CSV)

        self.weeks = collect_weeks(self.model, self._all_weeks())
        self._fill_preview()
        self._set_status('')

    def _fill_preview(self):
        rows = flat_rows(self.weeks)
        headers = _headers()
        if not self._all_weeks():
            headers, rows = headers[1:], [r[1:] for r in rows]
        # Columnas visibles en la vista previa (las más útiles)
        hidden = {len(headers) - 1}  # destino
        if self._all_weeks():
            hidden.add(2)  # fecha del día
        shown = [i for i in range(len(headers)) if i not in hidden]
        self.table.setColumnCount(len(shown))
        self.table.setHorizontalHeaderLabels([headers[i] for i in shown])
        visible = rows[:PREVIEW_ROWS]
        self.table.setRowCount(len(visible))
        money_cols = {headers.index(h) for h in headers[-4:-1]}
        result_col = len(headers) - 4
        for r, row in enumerate(visible):
            for c, i in enumerate(shown):
                value = row[i]
                if i in money_cols:
                    text = f"{'+' if i == result_col and value > 0 else ''}{'-' if value < 0 else ''}${abs(value):,.2f}"
                    item = QTableWidgetItem(text)
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    if i == result_col and abs(value) > 1e-9:
                        item.setForeground(QColor(self.c['success'] if value > 0 else self.c['danger']))
                else:
                    item = QTableWidgetItem(str(value))
                self.table.setItem(r, c, item)
        self.table.setFixedHeight(max(1, len(visible)) * 32 + self.table.horizontalHeader().sizeHint().height() + 8)

        total = sum(w['total'] for w in self.weeks)
        weeks_text = (f"{len(self.weeks)} {tr('weeks_word', 'semanas')}" if self._all_weeks()
                      else f"{tr('week')} {self.weeks[0]['start'].strftime('%d/%m/%Y')}" if self.weeks[0]['start'] else '')
        more = f" · {tr('showing_first', 'mostrando las primeras {n}').format(n=PREVIEW_ROWS)}" \
            if len(rows) > PREVIEW_ROWS else ''
        self.preview_info.setText(f"{weeks_text} · {len(rows)} {tr('rows_word', 'filas')} · "
                                  f"{tr('result_column', 'Resultado')} {'+' if total >= 0 else '-'}${abs(total):,.2f}{more}")

    def _set_status(self, text, ok=True):
        color = self.c['success'] if ok else self.c['danger']
        self.status_label.setStyleSheet(f"color: {color}; font-weight: 600;")
        self.status_label.setText(text)
        if not text:
            self.open_file_btn.setVisible(False)
            self.open_folder_btn.setVisible(False)

    # ------------------------------------------------------------ acciones
    def _browse(self):
        fmt = self._format()
        ext = EXTENSIONS[fmt]
        name = dict((k, n) for k, _, n, *_ in FORMATS)[fmt]
        path, _ = QFileDialog.getSaveFileName(self, tr('export_save_title'), self.path_edit.text(),
                                              f"{name} (*{ext})")
        if path:
            if not path.lower().endswith(ext):
                path += ext
            self.path_edit.setText(path)
            self._set_status('')

    def _open(self, path):
        if path and os.path.exists(path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    def _export(self):
        path = self.path_edit.text().strip()
        fmt = self._format()
        if not path:
            self._browse()
            path = self.path_edit.text().strip()
            if not path:
                return
        if not path.lower().endswith(EXTENSIONS[fmt]):
            path += EXTENSIONS[fmt]
        if os.path.exists(path):
            answer = QMessageBox.question(
                self, tr('export_dialog_title'),
                tr('overwrite_question', 'El archivo ya existe. ¿Quieres reemplazarlo?') + f"\n\n{path}",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if answer != QMessageBox.Yes:
                return

        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
            export_weeks(self.weeks, path, fmt,
                         include_charts=self.charts_switch.isChecked(),
                         include_summary=self.summary_switch.isChecked(),
                         csv_regional=self.regional_switch.isChecked())
        except PermissionError:
            QApplication.restoreOverrideCursor()
            self._set_status('❌ ' + tr('file_in_use', 'No se pudo escribir: ¿el archivo está abierto en Excel?'), ok=False)
            return
        except Exception as e:
            QApplication.restoreOverrideCursor()
            self._set_status(f"❌ {tr('export_error')}: {e}", ok=False)
            return
        QApplication.restoreOverrideCursor()

        self.last_path = path
        self._remember(path)
        self._set_status(f"✅ {tr('export_success')} · {os.path.basename(path)}")
        self.open_file_btn.setVisible(True)
        self.open_folder_btn.setVisible(True)
        self.export_btn.setText('🔁  ' + tr('export_again', 'Exportar de nuevo'))
        if self.open_switch.isChecked():
            self._open(path)

    def _remember(self, path):
        self.settings.set('export_dir', os.path.dirname(path))
        self.settings.set('export_format', self._format())
        self.settings.set('export_charts', self.charts_switch.isChecked())
        self.settings.set('export_summary', self.summary_switch.isChecked())
        self.settings.set('export_csv_regional', self.regional_switch.isChecked())
        self.settings.set('export_open_after', self.open_switch.isChecked())

    def showEvent(self, event):
        super().showEvent(event)
        for i, w in enumerate(self._cards):
            fade_in(w, duration=360, delay=30 + i * 60, slide=8)
        self._cards = []


def show_export_dialog(model, settings, fmt=None, is_dark=True, parent=None) -> bool:
    """Mostrar la ventana de exportación. `fmt` preselecciona el formato (por defecto, el último usado)."""
    dialog = ExportDialog(model, settings, fmt or settings.get('export_format'), is_dark, parent)
    return dialog.exec_() == QDialog.Accepted
