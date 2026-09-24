"""
Menú principal con opción de modo oscuro
"""

from PyQt5.QtWidgets import (QMenuBar, QMenu, QAction, QMessageBox, QFileDialog,
                             QApplication, QStyle, QDialog, QVBoxLayout, QLabel,
                             QPushButton, QHBoxLayout)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QIcon, QKeySequence
from src.utils.i18n import tr, set_language as set_global_language
from src.utils.i18n import current_language as i18n_current_language
from src.utils import i18n
from src.ui.help_dialogs import show_about_dialog, show_instructions_dialog

class MainMenuBar(QMenuBar):
    """Menú principal de la aplicación"""
    
    # Señales
    save_triggered = pyqtSignal()
    load_triggered = pyqtSignal()
    load_from_db_triggered = pyqtSignal()
    set_capital_triggered = pyqtSignal()
    theme_changed = pyqtSignal(bool)  # True para modo oscuro
    legend_visibility_changed = pyqtSignal(bool)
    day_capital_edit_mode_changed = pyqtSignal(bool)
    show_daily_advice_triggered = pyqtSignal()
    daily_advice_visibility_changed = pyqtSignal(bool)
    show_weekly_summary_triggered = pyqtSignal()
    start_new_week_triggered = pyqtSignal()
    export_excel_triggered = pyqtSignal()
    export_csv_triggered = pyqtSignal()
    export_json_triggered = pyqtSignal()
    language_changed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.dark_mode = False
        self.current_language = i18n_current_language
        # Referencias a menús y acciones para aplicar traducción
        self._menus = {}
        self._actions = {}
        self.setup_menus()
        self.apply_language()
    
    def setup_menus(self):
        """Configurar los menús"""
        # Menú Archivo
        self._menus['file'] = self.addMenu(tr('menu_file'))
        
        # Acción Guardar
        self._actions['save'] = QAction(tr('save_week'), self)
        self._actions['save'].setShortcut(QKeySequence.Save)
        self._actions['save'].setStatusTip(tr('status_save_week'))
        self._actions['save'].triggered.connect(self.save_triggered.emit)
        self._menus['file'].addAction(self._actions['save'])
        
        # Acción Cargar
        self._actions['load'] = QAction(tr('load_week'), self)
        self._actions['load'].setShortcut(QKeySequence.Open)
        self._actions['load'].setStatusTip(tr('status_load_week'))
        self._actions['load'].triggered.connect(self.load_triggered.emit)
        self._menus['file'].addAction(self._actions['load'])
        
        # Acción Cargar desde BD
        self._actions['load_db'] = QAction(tr('load_from_db'), self)
        self._actions['load_db'].setStatusTip(tr('status_load_db'))
        self._actions['load_db'].triggered.connect(self.load_from_db_triggered.emit)
        self._menus['file'].addAction(self._actions['load_db'])
        
        self._menus['file'].addSeparator()
        
        # Acción Establecer Capital Inicial
        self._actions['set_capital'] = QAction(tr('set_capital'), self)
        self._actions['set_capital'].setStatusTip(tr('status_set_capital'))
        self._actions['set_capital'].triggered.connect(self.set_capital_triggered.emit)
        self._menus['file'].addAction(self._actions['set_capital'])
        
        self._menus['file'].addSeparator()
        
        # Acción Salir
        self._actions['exit'] = QAction(tr('exit'), self)
        self._actions['exit'].setShortcut(QKeySequence.Quit)
        self._actions['exit'].setStatusTip(tr('status_exit'))
        self._actions['exit'].triggered.connect(self.parent().close)
        self._menus['file'].addAction(self._actions['exit'])
        
        # Menú Vista
        self._menus['view'] = self.addMenu(tr('menu_view'))
        
        # Acción Modo Oscuro
        self.dark_mode_action = QAction(tr('dark_mode'), self)
        self.dark_mode_action.setCheckable(True)
        self.dark_mode_action.setStatusTip(tr('status_dark_mode'))
        self.dark_mode_action.triggered.connect(self.toggle_dark_mode)
        self._menus['view'].addAction(self.dark_mode_action)
        self._actions['dark_mode'] = self.dark_mode_action

        # Acción Mostrar/Ocultar Leyenda
        self.legend_toggle_action = QAction(tr('toggle_legend'), self)
        self.legend_toggle_action.setCheckable(True)
        self.legend_toggle_action.setChecked(True)
        self.legend_toggle_action.setStatusTip(tr('status_toggle_legend'))
        self.legend_toggle_action.toggled.connect(self.legend_visibility_changed.emit)
        self._menus['view'].addAction(self.legend_toggle_action)
        self._actions['toggle_legend'] = self.legend_toggle_action

        # Acción Modo edición por capital
        self.capital_edit_mode_action = QAction(tr('capital_edit_mode'), self)
        self.capital_edit_mode_action.setCheckable(True)
        self.capital_edit_mode_action.setStatusTip(tr('status_capital_edit_mode'))
        self.capital_edit_mode_action.toggled.connect(self.day_capital_edit_mode_changed.emit)
        self._menus['view'].addAction(self.capital_edit_mode_action)
        self._actions['capital_edit_mode'] = self.capital_edit_mode_action
        
        # Menú Asistente
        self._menus['assistant'] = self.addMenu(tr('menu_assistant'))
        self._actions['daily_advice'] = QAction(tr('daily_advice'), self)
        self._actions['daily_advice'].setCheckable(True)
        self._actions['daily_advice'].setChecked(True)
        self._actions['daily_advice'].setStatusTip(tr('status_daily_advice'))
        # toggle de visibilidad y disparar actualización de contenido
        self._actions['daily_advice'].toggled.connect(self.daily_advice_visibility_changed.emit)
        self._actions['daily_advice'].triggered.connect(self.show_daily_advice_triggered.emit)
        self._menus['assistant'].addAction(self._actions['daily_advice'])

        self._actions['weekly_summary'] = QAction(tr('weekly_summary'), self)
        self._actions['weekly_summary'].setStatusTip(tr('status_weekly_summary'))
        self._actions['weekly_summary'].triggered.connect(self.show_weekly_summary_triggered.emit)
        self._menus['assistant'].addAction(self._actions['weekly_summary'])

        # Acción: Empezar nueva semana (reiniciar datos)
        self._actions['start_new_week_reset'] = QAction(tr('start_new_week_reset'), self)
        self._actions['start_new_week_reset'].setStatusTip(tr('status_start_new_week_reset'))
        self._actions['start_new_week_reset'].triggered.connect(self.start_new_week_triggered.emit)
        self._menus['assistant'].addAction(self._actions['start_new_week_reset'])
        
        # Menú Exportar
        self._menus['export'] = self.addMenu(tr('menu_export'))
        
        self._actions['export_excel'] = QAction(tr('export_excel'), self)
        self._actions['export_excel'].setShortcut('Ctrl+E')
        self._actions['export_excel'].setStatusTip(tr('status_export_excel'))
        self._actions['export_excel'].triggered.connect(self.export_excel_triggered)
        self._menus['export'].addAction(self._actions['export_excel'])
        
        self._actions['export_csv'] = QAction(tr('export_csv'), self)
        self._actions['export_csv'].setShortcut('Ctrl+Shift+C')
        self._actions['export_csv'].setStatusTip(tr('status_export_csv'))
        self._actions['export_csv'].triggered.connect(self.export_csv_triggered)
        self._menus['export'].addAction(self._actions['export_csv'])
        
        self._actions['export_json'] = QAction(tr('export_json'), self)
        self._actions['export_json'].setStatusTip(tr('status_export_json'))
        self._actions['export_json'].triggered.connect(self.export_json_triggered)
        self._menus['export'].addAction(self._actions['export_json'])
        
        # Menú Ayuda
        self._menus['help'] = self.addMenu(tr('menu_help'))
        
        # Acción Acerca de
        self._actions['about'] = QAction(tr('about'), self)
        self._actions['about'].setStatusTip(tr('status_about'))
        self._actions['about'].triggered.connect(self.show_about)
        self._menus['help'].addAction(self._actions['about'])
        
        # Acción Instrucciones
        self._actions['instructions'] = QAction(tr('instructions'), self)
        self._actions['instructions'].setStatusTip(tr('status_instructions'))
        self._actions['instructions'].triggered.connect(self.show_instructions)
        self._menus['help'].addAction(self._actions['instructions'])

        # Menú Idioma
        self._menus['language'] = self.addMenu(tr('menu_language'))
        self._actions['lang_es'] = QAction('🇪🇸 ' + tr('spanish'), self)
        self._actions['lang_en'] = QAction('🇺🇸 ' + tr('english'), self)
        self._actions['lang_es'].triggered.connect(lambda: self.set_language('es'))
        self._actions['lang_en'].triggered.connect(lambda: self.set_language('en'))
        self._menus['language'].addAction(self._actions['lang_es'])
        self._menus['language'].addAction(self._actions['lang_en'])
    
    def toggle_dark_mode(self, checked):
        """Cambiar entre modo claro y oscuro"""
        self.dark_mode = checked
        self.theme_changed.emit(checked)
        self.apply_theme_to_menu()
    
    def apply_theme_to_menu(self):
        """El stylesheet global de la aplicación ya tematiza QMenuBar/QMenu.
        Limpiamos cualquier override local para que herede esos colores."""
        self.setStyleSheet("")

    def _t(self, key: str) -> str:
        return tr(key)

    def set_language(self, lang: str):
        """Cambiar idioma y aplicar traducciones básicas"""
        set_global_language(lang)
        self.current_language = lang
        self.apply_language()
        self.language_changed.emit(lang)

    def apply_language(self):
        """Aplicar textos traducidos a menús y acciones principales"""
        # Menús
        if 'file' in self._menus:
            self._menus['file'].setTitle(tr('menu_file'))
        if 'view' in self._menus:
            self._menus['view'].setTitle(tr('menu_view'))
        if 'assistant' in self._menus:
            self._menus['assistant'].setTitle(tr('menu_assistant'))
        if 'export' in self._menus:
            self._menus['export'].setTitle(tr('menu_export'))
        if 'help' in self._menus:
            self._menus['help'].setTitle(tr('menu_help'))
        if 'language' in self._menus:
            self._menus['language'].setTitle(tr('menu_language'))

        # Acciones
        if 'save' in self._actions:
            self._actions['save'].setText(tr('save_week'))
        if 'load' in self._actions:
            self._actions['load'].setText(tr('load_week'))
        if 'load_db' in self._actions:
            self._actions['load_db'].setText(tr('load_from_db'))
        if 'set_capital' in self._actions:
            self._actions['set_capital'].setText(tr('set_capital'))
        if 'exit' in self._actions:
            self._actions['exit'].setText(tr('exit'))
        if 'dark_mode' in self._actions:
            self._actions['dark_mode'].setText(tr('dark_mode'))
        if 'toggle_legend' in self._actions:
            self._actions['toggle_legend'].setText(tr('toggle_legend'))
        if 'capital_edit_mode' in self._actions:
            self._actions['capital_edit_mode'].setText(tr('capital_edit_mode'))
        if 'daily_advice' in self._actions:
            self._actions['daily_advice'].setText(tr('daily_advice'))
        if 'weekly_summary' in self._actions:
            self._actions['weekly_summary'].setText(tr('weekly_summary'))
        if 'start_new_week_reset' in self._actions:
            self._actions['start_new_week_reset'].setText(tr('start_new_week_reset'))
        if 'export_excel' in self._actions:
            self._actions['export_excel'].setText(tr('export_excel'))
        if 'export_csv' in self._actions:
            self._actions['export_csv'].setText(tr('export_csv'))
        if 'export_json' in self._actions:
            self._actions['export_json'].setText(tr('export_json'))
        if 'about' in self._actions:
            self._actions['about'].setText(tr('about'))
        if 'instructions' in self._actions:
            self._actions['instructions'].setText(tr('instructions'))
        if 'lang_es' in self._actions:
            self._actions['lang_es'].setText('🇪🇸 ' + tr('spanish'))
        if 'lang_en' in self._actions:
            self._actions['lang_en'].setText('🇺🇸 ' + tr('english'))

        # StatusTips
        if 'save' in self._actions:
            self._actions['save'].setStatusTip(tr('status_save_week'))
        if 'load' in self._actions:
            self._actions['load'].setStatusTip(tr('status_load_week'))
        if 'load_db' in self._actions:
            self._actions['load_db'].setStatusTip(tr('status_load_db'))
        if 'set_capital' in self._actions:
            self._actions['set_capital'].setStatusTip(tr('status_set_capital'))
        if 'exit' in self._actions:
            self._actions['exit'].setStatusTip(tr('status_exit'))
        if 'dark_mode' in self._actions:
            self._actions['dark_mode'].setStatusTip(tr('status_dark_mode'))
        if 'toggle_legend' in self._actions:
            self._actions['toggle_legend'].setStatusTip(tr('status_toggle_legend'))
        if 'capital_edit_mode' in self._actions:
            self._actions['capital_edit_mode'].setStatusTip(tr('status_capital_edit_mode'))
        if 'daily_advice' in self._actions:
            self._actions['daily_advice'].setStatusTip(tr('status_daily_advice'))
        if 'weekly_summary' in self._actions:
            self._actions['weekly_summary'].setStatusTip(tr('status_weekly_summary'))
        if 'start_new_week_reset' in self._actions:
            self._actions['start_new_week_reset'].setStatusTip(tr('status_start_new_week_reset'))
        if 'export_excel' in self._actions:
            self._actions['export_excel'].setStatusTip(tr('status_export_excel'))
        if 'export_csv' in self._actions:
            self._actions['export_csv'].setStatusTip(tr('status_export_csv'))
        if 'export_json' in self._actions:
            self._actions['export_json'].setStatusTip(tr('status_export_json'))
        if 'about' in self._actions:
            self._actions['about'].setStatusTip(tr('status_about'))
        if 'instructions' in self._actions:
            self._actions['instructions'].setStatusTip(tr('status_instructions'))

    def show_about(self):
        show_about_dialog(self)

    def show_instructions(self):
        show_instructions_dialog(self)
