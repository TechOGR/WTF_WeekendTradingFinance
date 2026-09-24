"""
Diálogo para cargar (o borrar) una semana guardada en JSON.
Lista la carpeta de semanas configurada y permite explorar otra carpeta.
"""

import json
import os

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, QLabel, QFrame,
    QPushButton, QMessageBox, QFileDialog, QStackedWidget, QSizePolicy
)
from PyQt5.QtCore import Qt, QSize, QUrl
from PyQt5.QtGui import QDesktopServices

from src.utils.settings_store import default_weeks_dir


def _week_stats(path):
    """Leer capital inicial y resultado total de un archivo de semana."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        total = sum(float((d or {}).get('amount', 0.0) or 0.0) for d in data.get('data', {}).values())
        return float(data.get('initial_capital', 0.0) or 0.0), total
    except Exception:
        return None, None


class LoadWeekDialog(QDialog):
    def __init__(self, parent=None, tr=lambda k, d=None: d or k, folder=None):
        super().__init__(parent)
        self.tr = tr
        self.folder = folder or default_weeks_dir()
        self.setWindowTitle(self.tr("load_week_dialog_title"))
        self.setModal(True)
        self.resize(620, 540)

        self.selected_file_path = None

        root = QVBoxLayout(self)
        root.setContentsMargins(22, 20, 22, 18)
        root.setSpacing(12)

        title = QLabel('📂 ' + self.tr("load_week_dialog_title"))
        title.setObjectName('h2')
        root.addWidget(title)

        # Carpeta actual
        folder_card = QFrame()
        folder_card.setObjectName('cardAlt')
        fl = QHBoxLayout(folder_card)
        fl.setContentsMargins(12, 8, 8, 8)
        fl.setSpacing(8)
        self.folder_label = QLabel()
        self.folder_label.setObjectName('muted')
        self.folder_label.setStyleSheet('font-size: 9pt;')
        self.folder_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        fl.addWidget(self.folder_label, 1)
        browse = QPushButton('📁  ' + self.tr('other_folder', 'Otra carpeta'))
        browse.setObjectName('ghost')
        browse.setCursor(Qt.PointingHandCursor)
        browse.setToolTip(self.tr('other_folder_tip', 'Cargar semanas desde otra carpeta (solo esta vez)'))
        browse.clicked.connect(self._browse)
        fl.addWidget(browse)
        root.addWidget(folder_card)

        # Lista / estado vacío
        self.stack = QStackedWidget()
        self.list_widget = QListWidget()
        self.list_widget.setIconSize(QSize(18, 18))
        self.list_widget.setStyleSheet('QListWidget::item { padding: 10px 8px; }')
        self.list_widget.itemDoubleClicked.connect(self._load_selected_and_accept)
        self.list_widget.currentItemChanged.connect(self._update_buttons)
        self.stack.addWidget(self.list_widget)
        self.empty_label = QLabel()
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setObjectName('muted')
        self.empty_label.setWordWrap(True)
        self.stack.addWidget(self.empty_label)
        root.addWidget(self.stack, 1)

        # Botones
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(8)
        self.btn_delete = QPushButton('🗑  ' + self.tr("delete_week"))
        self.btn_delete.setObjectName('danger')
        btn_open = QPushButton('↗  ' + self.tr('open_folder', 'Abrir carpeta'))
        btn_open.setObjectName('ghost')
        btn_cancel = QPushButton(self.tr("cancel"))
        btn_cancel.setObjectName('ghost')
        self.btn_load = QPushButton(self.tr("load_week_action"))
        self.btn_load.setObjectName('primary')
        self.btn_load.setDefault(True)
        for b in (self.btn_delete, btn_open, btn_cancel, self.btn_load):
            b.setCursor(Qt.PointingHandCursor)

        self.btn_load.clicked.connect(self._load_selected_and_accept)
        self.btn_delete.clicked.connect(self._delete_selected)
        btn_open.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(self.folder)))
        btn_cancel.clicked.connect(self.reject)

        buttons_layout.addWidget(self.btn_delete)
        buttons_layout.addWidget(btn_open)
        buttons_layout.addStretch(1)
        buttons_layout.addWidget(btn_cancel)
        buttons_layout.addWidget(self.btn_load)
        root.addLayout(buttons_layout)

        self._populate()

    def _populate(self):
        self.list_widget.clear()
        metrics = self.folder_label.fontMetrics()
        self.folder_label.setText(metrics.elidedText(self.folder, Qt.ElideMiddle, 400))
        self.folder_label.setToolTip(self.folder)

        files = []
        if os.path.isdir(self.folder):
            files = [f for f in os.listdir(self.folder) if f.lower().endswith(".json")]
        # Recientes primero (el nombre contiene la fecha del lunes)
        files.sort(reverse=True)

        for fname in files:
            full_path = os.path.join(self.folder, fname)
            label = self._format_label(fname)
            initial, total = _week_stats(full_path)
            if total is not None:
                sign = '+' if total >= 0 else '-'
                label += f"    {'🟢' if total >= 0 else '🔴'} {sign}${abs(total):,.2f}"
                if initial:
                    label += f"   ·   {self.tr('capital_initial').rstrip(':')} ${initial:,.2f}"
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, full_path)
            item.setToolTip(full_path)
            self.list_widget.addItem(item)

        if files:
            self.stack.setCurrentIndex(0)
            self.list_widget.setCurrentRow(0)
        else:
            self.empty_label.setText('🗂️\n\n' + self.tr("no_saved_weeks"))
            self.stack.setCurrentIndex(1)
        self._update_buttons()

    def _browse(self):
        folder = QFileDialog.getExistingDirectory(self, self.tr('weeks_folder', 'Carpeta de semanas'), self.folder)
        if folder:
            self.folder = folder
            self._populate()

    def _update_buttons(self, *args):
        has = self.list_widget.currentItem() is not None
        self.btn_load.setEnabled(has)
        self.btn_delete.setEnabled(has)

    def _format_label(self, fname: str) -> str:
        # Expect pattern like weekend_trading_YYYY-MM-DD.json
        base = os.path.splitext(fname)[0]
        if "weekend_trading_" in base:
            date_part = base.split("weekend_trading_")[-1]
            return f"📅  {self.tr('week_label')} {date_part}"
        return f"📄  {base}"

    def _get_selected_path(self):
        item = self.list_widget.currentItem()
        if item is None:
            return None
        return item.data(Qt.UserRole)

    def _load_selected_and_accept(self):
        path = self._get_selected_path()
        if not path:
            QMessageBox.warning(self, self.tr("warning"), self.tr("select_week_first"))
            return
        self.selected_file_path = path
        self.accept()

    def _delete_selected(self):
        path = self._get_selected_path()
        if not path:
            QMessageBox.warning(self, self.tr("warning"), self.tr("select_week_first"))
            return

        resp = QMessageBox.question(
            self,
            self.tr("confirm_delete_week_title"),
            self.tr("confirm_delete_week_message"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if resp != QMessageBox.Yes:
            return

        try:
            os.remove(path)
            QMessageBox.information(self, self.tr("operation_completed"), self.tr("delete_success"))
            self._populate()
        except Exception:
            QMessageBox.critical(self, self.tr("error"), self.tr("delete_error"))

    def get_selected_file_path(self):
        return self.selected_file_path
