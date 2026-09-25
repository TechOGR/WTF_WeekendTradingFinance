"""
Ventana de configuración: reúne todas las funciones de la aplicación
(apariencia, trading, datos, IA para imágenes y ayuda) en un solo lugar.
"""

import os
import shutil

from PyQt5.QtWidgets import (QDialog, QHBoxLayout, QVBoxLayout, QLabel, QListWidget, QListWidgetItem,
                             QStackedWidget, QFrame, QPushButton, QComboBox, QLineEdit, QPlainTextEdit,
                             QWidget, QScrollArea, QFileDialog, QGridLayout, QMessageBox)
from PyQt5.QtCore import Qt, QUrl, QSize
from PyQt5.QtGui import QDesktopServices, QPixmap

from src.services.pollinations_image import ApiWorker, check_api_key, KEYS_URL, EDIT_MODELS, API_KEY_ENV
from src.ui.animations import ToggleSwitch, fade_in
from src.ui.day_details_dialog import make_editable_combo
from src.ui.main_menu import show_about_dialog, show_instructions_dialog
from src.utils import i18n
from src.version import APP_VERSION
from src.utils.i18n import tr
from src.utils.settings_store import (CURRENCY_PAIRS, DURATIONS, DEFAULTS, DEFAULT_GENERATION_TEMPLATE,
                                      PROMPT_PLACEHOLDERS, ENGINE_AI, ENGINE_LOCAL, save_api_key,
                                      default_weeks_dir)

PAGES = [
    ('appearance', '🎨', 'settings_appearance', 'Apariencia'),
    ('trading', '📈', 'settings_trading', 'Trading'),
    ('data', '💾', 'settings_data', 'Datos y exportación'),
    ('ai', '✨', 'settings_ai', 'IA · Imagen de resultado'),
    ('about', 'ℹ️', 'settings_about', 'Ayuda'),
]



class SettingsDialog(QDialog):
    """Configuración central. `host` es la ventana principal (ejecuta las acciones)."""

    def __init__(self, host, settings, page='appearance'):
        super().__init__(host)
        self.host = host
        self.settings = settings
        self._worker = None
        self.setWindowTitle(tr('settings_title', 'Configuración'))
        self.resize(940, 680)

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # --- Barra lateral
        sidebar = QFrame()
        sidebar.setObjectName('sidebar')
        sidebar.setFixedWidth(250)
        sv = QVBoxLayout(sidebar)
        sv.setContentsMargins(14, 22, 14, 18)
        sv.setSpacing(6)
        title = QLabel('⚙️ ' + tr('settings_title', 'Configuración'))
        title.setObjectName('h2')
        sv.addWidget(title)
        sv.addSpacing(10)
        self.nav = QListWidget()
        self.nav.setObjectName('nav')
        self.nav.setIconSize(QSize(18, 18))
        for key, icon, tkey, default in PAGES:
            item = QListWidgetItem(f"{icon}   {tr(tkey, default)}")
            item.setData(Qt.UserRole, key)
            self.nav.addItem(item)
        sv.addWidget(self.nav, 1)
        version = QLabel(f'W-T-F Trading Manager v{APP_VERSION}')
        version.setObjectName('caption')
        sv.addWidget(version)
        root.addWidget(sidebar)

        # --- Contenido
        content = QVBoxLayout()
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(0)
        self.stack = QStackedWidget()
        self._pages = {}
        builders = {
            'appearance': self._page_appearance, 'trading': self._page_trading,
            'data': self._page_data, 'ai': self._page_ai, 'about': self._page_about,
        }
        for key, *_ in PAGES:
            page_widget = self._scroll(builders[key]())
            self._pages[key] = self.stack.addWidget(page_widget)
        content.addWidget(self.stack, 1)

        footer = QFrame()
        footer.setObjectName('header')
        fl = QHBoxLayout(footer)
        fl.setContentsMargins(24, 12, 24, 12)
        self.footer_hint = QLabel('')
        self.footer_hint.setObjectName('muted')
        fl.addWidget(self.footer_hint, 1)
        close_btn = QPushButton(tr('close'))
        close_btn.setObjectName('ghost')
        close_btn.clicked.connect(self.reject)
        save_btn = QPushButton('💾  ' + tr('save_changes', 'Guardar cambios'))
        save_btn.setObjectName('primary')
        save_btn.clicked.connect(self._save_and_close)
        fl.addWidget(close_btn)
        fl.addWidget(save_btn)
        content.addWidget(footer)
        root.addLayout(content, 1)

        self.nav.currentRowChanged.connect(self._switch_page)
        keys = [p[0] for p in PAGES]
        self.nav.setCurrentRow(keys.index(page) if page in keys else 0)

    # ------------------------------------------------------------ layout
    def _scroll(self, widget):
        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        area.setWidget(widget)
        return area

    def _switch_page(self, row):
        self.stack.setCurrentIndex(row)
        fade_in(self.stack.currentWidget(), duration=320, slide=14)

    def _page(self, title, subtitle):
        page = QWidget()
        page.setObjectName('transparent')
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 26, 30, 26)
        layout.setSpacing(14)
        t = QLabel(title)
        t.setObjectName('h1')
        s = QLabel(subtitle)
        s.setObjectName('muted')
        s.setWordWrap(True)
        layout.addWidget(t)
        layout.addWidget(s)
        layout.addSpacing(6)
        return page, layout

    def _card(self, layout, title=None):
        card = QFrame()
        card.setObjectName('card')
        v = QVBoxLayout(card)
        v.setContentsMargins(20, 16, 20, 16)
        v.setSpacing(12)
        if title:
            lbl = QLabel(title)
            lbl.setObjectName('h3')
            v.addWidget(lbl)
        layout.addWidget(card)
        return v

    def _row(self, card_layout, title, description, widget):
        row = QHBoxLayout()
        texts = QVBoxLayout()
        texts.setSpacing(2)
        t = QLabel(title)
        t.setStyleSheet('font-weight: 600;')
        texts.addWidget(t)
        if description:
            d = QLabel(description)
            d.setObjectName('muted')
            d.setWordWrap(True)
            d.setStyleSheet('font-size: 9pt;')
            texts.addWidget(d)
        row.addLayout(texts, 1)
        row.addWidget(widget, 0, Qt.AlignVCenter)
        card_layout.addLayout(row)
        return widget

    def _action(self, text, slot, name=None):
        btn = QPushButton(text)
        if name:
            btn.setObjectName(name)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(slot)
        return btn

    def _toggle(self, key, on_change):
        sw = ToggleSwitch(checked=self.settings.get_bool(key))

        def changed(value):
            self.settings.set(key, value)
            on_change(value)
        sw.toggled.connect(changed)
        return sw

    # ------------------------------------------------------------- páginas
    def _page_appearance(self):
        page, layout = self._page('🎨 ' + tr('settings_appearance', 'Apariencia'),
                                  tr('settings_appearance_desc', 'Tema, idioma y estilo del gráfico. Los cambios se aplican al instante.'))
        card = self._card(layout, tr('theme_section', 'Tema e idioma'))
        self._row(card, tr('dark_mode'), tr('dark_mode_desc', 'Interfaz oscura estilo fintech.'),
                  self._toggle('dark_mode', self.host.set_dark_mode))
        lang = QComboBox()
        lang.addItem('🇪🇸  Español', 'es')
        lang.addItem('🇺🇸  English', 'en')
        lang.setCurrentIndex(0 if i18n.current_language == 'es' else 1)
        lang.currentIndexChanged.connect(lambda _: self._change_language(lang.currentData()))
        self._row(card, tr('menu_language'), tr('language_desc', 'Algunos textos se actualizan al reabrir esta ventana.'), lang)

        card = self._card(layout, tr('chart_section', 'Gráfico'))
        mode = QComboBox()
        mode.addItem(tr('chart_3d', '3D volumétrico (arrastra para rotar)'), '3d')
        mode.addItem(tr('chart_2d', '2D con brillo neón'), '2d')
        mode.setCurrentIndex(0 if self.settings.get('chart_mode') == '3d' else 1)
        mode.currentIndexChanged.connect(lambda _: self.host.set_chart_mode(mode.currentData()))
        self._row(card, tr('chart_mode', 'Vista del gráfico'), '', mode)
        self._row(card, tr('chart_animations', 'Animaciones'), tr('chart_animations_desc', 'Crecimiento de barras y barrido de cámara al actualizar.'),
                  self._toggle('chart_animations', self.host.set_chart_animations))
        self._row(card, tr('toggle_legend'), '', self._toggle('legend_visible', self.host.on_toggle_legend))
        layout.addStretch()
        return page

    def _page_trading(self):
        page, layout = self._page('📈 ' + tr('settings_trading', 'Trading'),
                                  tr('settings_trading_desc', 'Capital, modo de edición y ciclo semanal.'))
        card = self._card(layout, tr('capital_section', 'Capital'))
        self._row(card, tr('set_capital'), tr('status_set_capital'),
                  self._action(tr('edit', 'Editar'), self.host.set_initial_capital))
        self._row(card, tr('capital_edit_mode'), tr('status_capital_edit_mode'),
                  self._toggle('capital_edit_mode', self.host.set_capital_edit_mode))

        card = self._card(layout, tr('menu_assistant'))
        self._row(card, tr('daily_advice'), tr('status_daily_advice'),
                  self._toggle('show_daily_advice', self.host.on_toggle_daily_advice_visibility))
        self._row(card, tr('weekly_summary'), tr('status_weekly_summary'),
                  self._action(tr('show', 'Mostrar'), self.host.show_weekly_summary_notification))

        card = self._card(layout, tr('week_section', 'Semana'))
        self._row(card, tr('start_new_week_reset'), tr('status_start_new_week_reset'),
                  self._action(tr('start', 'Iniciar'), self.host.start_new_week_reset, 'danger'))
        layout.addStretch()
        return page

    def _page_data(self):
        page, layout = self._page('💾 ' + tr('settings_data', 'Datos y exportación'),
                                  tr('settings_data_desc', 'Guarda, carga, exporta e importa tus semanas.'))
        card = self._card(layout, tr('menu_file'))
        self._row(card, tr('save_week'), tr('status_save_week') + '  (Ctrl+S)',
                  self._action(tr('save', 'Guardar'), self.host.save_week, 'primary'))
        self._row(card, tr('load_week'), tr('status_load_week') + '  (Ctrl+O)',
                  self._action(tr('open', 'Abrir'), self._close_then(self.host.load_week)))
        self._row(card, tr('load_from_db'), tr('status_load_db'),
                  self._action(tr('open', 'Abrir'), self._close_then(self.host.load_from_database)))

        card = self._card(layout, '📁 ' + tr('weeks_folder', 'Carpeta de semanas'))
        desc = QLabel(tr('weeks_folder_desc', 'Aquí se guardan tus semanas (Ctrl+S) y desde aquí se cargan (Ctrl+O). '
                                             'Puedes usar una carpeta sincronizada (OneDrive, Google Drive...).'))
        desc.setObjectName('muted')
        desc.setWordWrap(True)
        desc.setStyleSheet('font-size: 9pt;')
        card.addWidget(desc)
        self.weeks_dir_edit = QLineEdit(self.settings.weeks_dir())
        self.weeks_dir_edit.setReadOnly(True)
        card.addWidget(self.weeks_dir_edit)
        buttons = QHBoxLayout()
        buttons.setSpacing(8)
        buttons.addWidget(self._action('📂  ' + tr('change_folder', 'Cambiar carpeta'), self._browse_weeks_dir, 'primary'))
        buttons.addWidget(self._action('↗  ' + tr('open_folder', 'Abrir carpeta'), self._open_weeks_dir))
        self.weeks_reset_btn = self._action('↺  ' + tr('restore_default', 'Restablecer'),
                                            lambda: self._set_weeks_dir(default_weeks_dir()), 'ghost')
        buttons.addWidget(self.weeks_reset_btn)
        buttons.addStretch()
        card.addLayout(buttons)
        self._refresh_weeks_dir()

        card = self._card(layout, tr('menu_export'))
        self._row(card, tr('export_excel') + ' / CSV / JSON', tr('status_export_excel') + '  (Ctrl+E)',
                  self._action(tr('export', 'Exportar'), self._close_then(self.host.export_data)))
        self._row(card, '📥 ' + tr('import_title', 'Importar y analizar operaciones'),
                  tr('import_row_desc', 'Excel o CSV del bróker o de W-T-F: promedios, gráficos y estadísticas.')
                  + '  (Ctrl+I)',
                  self._action(tr('import_analyze', 'Importar'), self._close_then(self.host.open_import), 'primary'))
        layout.addStretch()
        return page

    def _page_ai(self):
        page, layout = self._page('✨ ' + tr('settings_ai', 'IA · Imagen de resultado'),
                                  tr('settings_ai_desc', 'Edita tu tarjeta de referencia con Pollinations '
                                                         '(FLUX.1 Kontext) o genérala en local con valores exactos.'))

        card = self._card(layout, '⚙️ ' + tr('image_engine', 'Motor de imagen'))
        self.engine = QComboBox()
        self.engine.addItem('✨  ' + tr('engine_ai', 'IA · Pollinations'), ENGINE_AI)
        self.engine.addItem('🎯  ' + tr('engine_local', 'Local · valores exactos (Pillow)'), ENGINE_LOCAL)
        self.engine.setCurrentIndex(0 if self.settings.get('image_engine') == ENGINE_AI else 1)
        self._row(card, tr('image_engine', 'Motor de imagen'),
                  tr('image_engine_desc', 'Local: gratis, sin conexión y con los números siempre exactos.'),
                  self.engine)

        card = self._card(layout, '🔑 ' + tr('api_key', 'API key de Pollinations'))
        key_row = QHBoxLayout()
        self.api_key = QLineEdit(os.environ.get(API_KEY_ENV, ''))
        self.api_key.setEchoMode(QLineEdit.Password)
        self.api_key.setPlaceholderText('sk_…')
        eye = QPushButton('👁')
        eye.setObjectName('ghost')
        eye.setCheckable(True)
        eye.setFixedWidth(44)
        eye.setMinimumWidth(44)
        eye.toggled.connect(lambda on: self.api_key.setEchoMode(QLineEdit.Normal if on else QLineEdit.Password))
        key_row.addWidget(self.api_key, 1)
        key_row.addWidget(eye)
        card.addLayout(key_row)
        links = QHBoxLayout()
        get_key = self._action('🌐  ' + tr('get_api_key', 'Obtener clave'),
                               lambda: QDesktopServices.openUrl(QUrl(KEYS_URL)), 'ghost')
        self.test_btn = self._action('⚡  ' + tr('test_connection', 'Probar conexión'), self._test_connection)
        self.test_result = QLabel('')
        self.test_result.setObjectName('muted')
        self.test_result.setWordWrap(True)
        links.addWidget(get_key)
        links.addWidget(self.test_btn)
        links.addWidget(self.test_result, 1)
        card.addLayout(links)
        note = QLabel(tr('api_key_note', 'Se guarda en el archivo .env de la aplicación como '
                                         'POLLINATIONS_API_KEY (nunca en el código ni en la base de datos). '
                                         'Usa una clave secreta sk_.'))
        note.setObjectName('muted')
        note.setWordWrap(True)
        note.setStyleSheet('font-size: 8.5pt;')
        card.addWidget(note)

        card = self._card(layout, '🖼️ ' + tr('ref_image', 'Imagen de referencia'))
        ref_row = QHBoxLayout()
        ref_row.setSpacing(14)
        self.ref_preview = QLabel()
        self.ref_preview.setFixedSize(96, 128)
        self.ref_preview.setAlignment(Qt.AlignCenter)
        self.ref_preview.setObjectName('muted')
        self.ref_preview.setWordWrap(True)
        ref_row.addWidget(self.ref_preview)
        ref_texts = QVBoxLayout()
        ref_hint = QLabel(tr('ref_image_hint', 'La tarjeta base que la IA edita. Si no existe, la tarjeta '
                                               'se genera desde cero con el prompt de generación.'))
        ref_hint.setObjectName('muted')
        ref_hint.setWordWrap(True)
        self.ref_path = QLineEdit(self.settings.get('image_ref_path'))
        self.ref_path.textChanged.connect(self._update_ref_preview)
        choose = self._action('📂  ' + tr('choose_image', 'Elegir imagen…'), self._choose_ref_image)
        ref_texts.addWidget(ref_hint)
        ref_texts.addWidget(self.ref_path)
        ref_texts.addWidget(choose, 0, Qt.AlignLeft)
        ref_row.addLayout(ref_texts, 1)
        card.addLayout(ref_row)
        self._update_ref_preview()

        values_hint = QLabel(tr('ref_values_hint', 'Valores que aparecen escritos en la imagen de referencia '
                                                   '(la IA los sustituye por los nuevos):'))
        values_hint.setObjectName('muted')
        values_hint.setWordWrap(True)
        card.addWidget(values_hint)
        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(8)
        self.ref_fields = {}
        for i, (key, label) in enumerate([('ref_asset', 'Asset'), ('ref_duration', 'Duration'),
                                          ('ref_day', 'Day'), ('ref_profit', 'Total profit')]):
            edit = QLineEdit(self.settings.get(key))
            self.ref_fields[key] = edit
            lbl = QLabel(label)
            lbl.setStyleSheet('font-weight: 600;')
            grid.addWidget(lbl, i // 2, (i % 2) * 2)
            grid.addWidget(edit, i // 2, (i % 2) * 2 + 1)
        card.addLayout(grid)

        card = self._card(layout, '🤖 ' + tr('model_section', 'Modelo e imagen'))
        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(10)
        self.model = make_editable_combo(EDIT_MODELS, self.settings.get('poll_image_model'))
        self.default_pair = make_editable_combo(CURRENCY_PAIRS, self.settings.get('default_pair'))
        self.default_duration = make_editable_combo(DURATIONS, self.settings.get('default_duration'))
        for r, (label, widget) in enumerate([
            (tr('model', 'Modelo'), self.model),
            (tr('default_pair', 'Par por defecto'), self.default_pair),
            (tr('default_duration', 'Duración por defecto'), self.default_duration),
        ]):
            lbl = QLabel(label)
            lbl.setStyleSheet('font-weight: 600;')
            grid.addWidget(lbl, r, 0)
            grid.addWidget(widget, r, 1)
        grid.setColumnStretch(1, 1)
        card.addLayout(grid)

        folder_row = QHBoxLayout()
        self.output_dir = QLineEdit(self.settings.get('image_output_dir'))
        browse = self._action('📂', self._browse_folder)
        browse.setMinimumWidth(44)
        folder_row.addWidget(QLabel(tr('output_folder', 'Carpeta de imágenes')))
        folder_row.addWidget(self.output_dir, 1)
        folder_row.addWidget(browse)
        card.addLayout(folder_row)
        self.autosave = ToggleSwitch(checked=self.settings.get_bool('image_autosave'))
        self._row(card, tr('autosave_images', 'Guardar automáticamente cada imagen generada'), '', self.autosave)

        card = self._card(layout, '📝 ' + tr('prompt_template', 'Prompt de generación desde cero'))
        hint = QLabel(tr('prompt_hint', 'Se usa solo cuando no hay imagen de referencia. Variables: ') +
                      '  '.join(f"<b>{p}</b>" for p in PROMPT_PLACEHOLDERS) + '<br>' +
                      tr('edit_prompt_hint', 'El prompt de edición se construye automáticamente con los '
                                             'valores que cambian.'))
        hint.setObjectName('muted')
        hint.setWordWrap(True)
        card.addWidget(hint)
        self.prompt = QPlainTextEdit(self.settings.get('poll_generation_template'))
        self.prompt.setMinimumHeight(200)
        self.prompt.setStyleSheet("font-family: 'Cascadia Code', 'Consolas', monospace; font-size: 9pt;")
        card.addWidget(self.prompt)
        restore = self._action('↺  ' + tr('restore_default', 'Restaurar predeterminado'),
                               lambda: self.prompt.setPlainText(DEFAULT_GENERATION_TEMPLATE), 'ghost')
        card.addWidget(restore, 0, Qt.AlignLeft)
        layout.addStretch()
        return page

    def _update_ref_preview(self):
        path = self.ref_path.text().strip()
        pix = QPixmap(path) if os.path.isfile(path) else QPixmap()
        if pix.isNull():
            self.ref_preview.setPixmap(QPixmap())
            self.ref_preview.setText('⚠️ ' + tr('missing', 'No encontrada'))
        else:
            self.ref_preview.setPixmap(pix.scaled(self.ref_preview.size(), Qt.KeepAspectRatio,
                                                  Qt.SmoothTransformation))

    def _choose_ref_image(self):
        path, _ = QFileDialog.getOpenFileName(self, tr('ref_image', 'Imagen de referencia'), '',
                                              'Imagen (*.png *.jpg *.jpeg *.webp)')
        if not path:
            return
        # Copiar a la ubicación estándar para que la app la encuentre siempre
        dest = DEFAULTS['image_ref_path']
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        if os.path.normcase(os.path.abspath(path)) != os.path.normcase(os.path.abspath(dest)):
            shutil.copy2(path, dest)
        self.ref_path.setText(dest)
        self._update_ref_preview()

    def _page_about(self):
        page, layout = self._page('ℹ️ ' + tr('settings_about', 'Ayuda'),
                                  tr('settings_about_desc', 'Información de la aplicación y guía de uso.'))
        card = self._card(layout)
        self._row(card, tr('instructions'), tr('status_instructions'),
                  self._action(tr('show', 'Mostrar'), lambda: show_instructions_dialog(self)))
        self._row(card, tr('about'), tr('status_about'),
                  self._action(tr('show', 'Mostrar'), lambda: show_about_dialog(self)))
        card = self._card(layout, '⌨️ ' + tr('shortcuts', 'Atajos de teclado'))
        for keys, text in [('Ctrl+S', tr('save_week')), ('Ctrl+O', tr('load_week')),
                           ('Ctrl+G', tr('generate_result_image', 'Generar imagen del resultado')),
                           ('Ctrl+,', tr('settings_title', 'Configuración')), ('Ctrl+E', tr('menu_export')),
                           ('Ctrl+I', tr('import_title', 'Importar y analizar operaciones')),
                           ('Ctrl+D', tr('dark_mode'))]:
            row = QHBoxLayout()
            k = QLabel(keys)
            k.setObjectName('chip')
            row.addWidget(k)
            row.addWidget(QLabel(text), 1)
            card.addLayout(row)
        layout.addStretch()
        return page

    # ------------------------------------------------------------ acciones
    def _close_then(self, fn):
        def run():
            self.accept()
            fn()
        return run

    def _change_language(self, lang):
        self.host.change_language(lang)
        self.footer_hint.setText('🌍 ' + tr('language_applied', 'Idioma aplicado'))

    def _refresh_weeks_dir(self):
        current = self.settings.weeks_dir()
        self.weeks_dir_edit.setText(current)
        self.weeks_dir_edit.setToolTip(current)
        self.weeks_reset_btn.setEnabled(os.path.normcase(os.path.abspath(current))
                                        != os.path.normcase(os.path.abspath(default_weeks_dir())))

    def _open_weeks_dir(self):
        folder = self.settings.weeks_dir()
        os.makedirs(folder, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(folder))

    def _browse_weeks_dir(self):
        folder = QFileDialog.getExistingDirectory(self, tr('weeks_folder', 'Carpeta de semanas'),
                                                  self.settings.weeks_dir())
        if folder:
            self._set_weeks_dir(folder)

    def _set_weeks_dir(self, folder):
        old = self.settings.weeks_dir()
        if os.path.normcase(os.path.abspath(folder)) == os.path.normcase(os.path.abspath(old)):
            return
        # Ofrecer copiar las semanas existentes a la nueva carpeta (sin borrar las originales)
        weeks = [f for f in os.listdir(old) if f.lower().endswith('.json')] if os.path.isdir(old) else []
        if weeks:
            answer = QMessageBox.question(
                self, tr('weeks_folder', 'Carpeta de semanas'),
                tr('copy_weeks_question', '¿Copiar las {n} semanas guardadas a la nueva carpeta?\n'
                                          'Los archivos originales no se borran.').format(n=len(weeks)),
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Yes)
            if answer == QMessageBox.Cancel:
                return
            if answer == QMessageBox.Yes:
                try:
                    os.makedirs(folder, exist_ok=True)
                    for name in weeks:
                        target = os.path.join(folder, name)
                        if not os.path.exists(target):  # nunca sobrescribir semanas de la carpeta nueva
                            shutil.copy2(os.path.join(old, name), target)
                except OSError as e:
                    QMessageBox.warning(self, tr('warning'), f"{tr('operation_failed')}: {e}")
                    return
        is_default = (os.path.normcase(os.path.abspath(folder))
                      == os.path.normcase(os.path.abspath(default_weeks_dir())))
        self.settings.set('weeks_dir', '' if is_default else folder)
        self._refresh_weeks_dir()
        self.footer_hint.setText('📁 ' + tr('weeks_folder_changed', 'Carpeta de semanas actualizada'))

    def _browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, tr('output_folder', 'Carpeta de imágenes'),
                                                  self.output_dir.text() or os.getcwd())
        if folder:
            self.output_dir.setText(folder)

    def _test_connection(self):
        if self._worker is not None:
            return
        self.test_btn.setEnabled(False)
        self.test_result.setText('⏳ ' + tr('testing', 'Probando…'))
        self._worker = ApiWorker(check_api_key, self.api_key.text().strip())
        self._worker.succeeded.connect(lambda info: self._test_done(f"✅ {info}"))
        self._worker.failed.connect(lambda e: self._test_done(f"❌ {e}"))
        self._worker.start()

    def _test_done(self, text):
        self.test_result.setText(text)
        self.test_btn.setEnabled(True)
        self._worker = None

    def save_ai_settings(self):
        key = self.api_key.text().strip()
        if key != os.environ.get(API_KEY_ENV, ''):
            save_api_key(key)
        self.settings.set('image_engine', self.engine.currentData())
        self.settings.set('poll_image_model', self.model.currentText().strip() or DEFAULTS['poll_image_model'])
        self.settings.set('image_ref_path', self.ref_path.text().strip() or DEFAULTS['image_ref_path'])
        for key_name, edit in self.ref_fields.items():
            self.settings.set(key_name, edit.text().strip() or DEFAULTS[key_name])
        self.settings.set('default_pair', self.default_pair.currentText().strip())
        self.settings.set('default_duration', self.default_duration.currentText().strip())
        self.settings.set('image_output_dir', self.output_dir.text().strip())
        self.settings.set('image_autosave', self.autosave.isChecked())
        self.settings.set('poll_generation_template',
                          self.prompt.toPlainText().strip() or DEFAULT_GENERATION_TEMPLATE)

    def _save_and_close(self):
        self.save_ai_settings()
        self.accept()

    def done(self, result):
        # No destruir el hilo de prueba si sigue en marcha
        if self._worker is not None:
            try:
                self._worker.succeeded.disconnect()
                self._worker.failed.disconnect()
            except TypeError:
                pass
            from src.ui.result_image_dialog import _RUNNING_WORKERS
            w = self._worker
            _RUNNING_WORKERS.add(w)
            w.finished.connect(lambda: _RUNNING_WORKERS.discard(w))
            self._worker = None
        super().done(result)
