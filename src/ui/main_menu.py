"""
Menú principal con opción de modo oscuro
"""

from PyQt5.QtWidgets import (QMenuBar, QMenu, QAction, QMessageBox, QFileDialog,
                             QApplication, QStyle)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QIcon, QKeySequence
import os
from src.utils.i18n import tr, set_language as set_global_language
from src.utils.i18n import current_language as i18n_current_language

class MainMenuBar(QMenuBar):
    """Menú principal de la aplicación"""
    
    # Señales
    save_triggered = pyqtSignal()
    load_triggered = pyqtSignal()
    load_from_db_triggered = pyqtSignal()
    set_capital_triggered = pyqtSignal()
    theme_changed = pyqtSignal(bool)  # True para modo oscuro
    show_daily_advice_triggered = pyqtSignal()
    show_weekly_summary_triggered = pyqtSignal()
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
        self._actions['save'].setStatusTip('Guardar datos de la semana actual')
        self._actions['save'].triggered.connect(self.save_triggered.emit)
        self._menus['file'].addAction(self._actions['save'])
        
        # Acción Cargar
        self._actions['load'] = QAction(tr('load_week'), self)
        self._actions['load'].setShortcut(QKeySequence.Open)
        self._actions['load'].setStatusTip('Cargar datos desde archivo')
        self._actions['load'].triggered.connect(self.load_triggered.emit)
        self._menus['file'].addAction(self._actions['load'])
        
        # Acción Cargar desde BD
        self._actions['load_db'] = QAction(tr('load_from_db'), self)
        self._actions['load_db'].setStatusTip('Cargar datos guardados en la base de datos')
        self._actions['load_db'].triggered.connect(self.load_from_db_triggered.emit)
        self._menus['file'].addAction(self._actions['load_db'])
        
        self._menus['file'].addSeparator()
        
        # Acción Establecer Capital Inicial
        self._actions['set_capital'] = QAction(tr('set_capital'), self)
        self._actions['set_capital'].setStatusTip('Configurar el capital inicial de la semana')
        self._actions['set_capital'].triggered.connect(self.set_capital_triggered.emit)
        self._menus['file'].addAction(self._actions['set_capital'])
        
        self._menus['file'].addSeparator()
        
        # Acción Salir
        self._actions['exit'] = QAction(tr('exit'), self)
        self._actions['exit'].setShortcut(QKeySequence.Quit)
        self._actions['exit'].setStatusTip('Salir de la aplicación')
        self._actions['exit'].triggered.connect(self.parent().close)
        self._menus['file'].addAction(self._actions['exit'])
        
        # Menú Vista
        self._menus['view'] = self.addMenu(tr('menu_view'))
        
        # Acción Modo Oscuro
        self.dark_mode_action = QAction(tr('dark_mode'), self)
        self.dark_mode_action.setCheckable(True)
        self.dark_mode_action.setStatusTip('Activar/desactivar modo oscuro')
        self.dark_mode_action.triggered.connect(self.toggle_dark_mode)
        self._menus['view'].addAction(self.dark_mode_action)
        self._actions['dark_mode'] = self.dark_mode_action
        
        # Menú Asistente
        self._menus['assistant'] = self.addMenu(tr('menu_assistant'))
        self._actions['daily_advice'] = QAction(tr('daily_advice'), self)
        self._actions['daily_advice'].setStatusTip('Ver recomendaciones según el día actual')
        self._actions['daily_advice'].triggered.connect(self.show_daily_advice_triggered.emit)
        self._menus['assistant'].addAction(self._actions['daily_advice'])

        self._actions['weekly_summary'] = QAction(tr('weekly_summary'), self)
        self._actions['weekly_summary'].setStatusTip('Mostrar resumen con sugerencia de retiro y reinversión')
        self._actions['weekly_summary'].triggered.connect(self.show_weekly_summary_triggered.emit)
        self._menus['assistant'].addAction(self._actions['weekly_summary'])
        
        # Menú Exportar
        self._menus['export'] = self.addMenu(tr('menu_export'))
        
        self._actions['export_excel'] = QAction(tr('export_excel'), self)
        self._actions['export_excel'].setShortcut('Ctrl+E')
        self._actions['export_excel'].setStatusTip('Exportar datos a formato Excel (.xlsx)')
        self._actions['export_excel'].triggered.connect(self.export_excel_triggered)
        self._menus['export'].addAction(self._actions['export_excel'])
        
        self._actions['export_csv'] = QAction(tr('export_csv'), self)
        self._actions['export_csv'].setShortcut('Ctrl+Shift+C')
        self._actions['export_csv'].setStatusTip('Exportar datos a formato CSV')
        self._actions['export_csv'].triggered.connect(self.export_csv_triggered)
        self._menus['export'].addAction(self._actions['export_csv'])
        
        self._actions['export_json'] = QAction(tr('export_json'), self)
        self._actions['export_json'].setStatusTip('Exportar datos a formato JSON')
        self._actions['export_json'].triggered.connect(self.export_json_triggered)
        self._menus['export'].addAction(self._actions['export_json'])
        
        # Menú Ayuda
        self._menus['help'] = self.addMenu(tr('menu_help'))
        
        # Acción Acerca de
        self._actions['about'] = QAction(tr('about'), self)
        self._actions['about'].setStatusTip('Información sobre la aplicación')
        self._actions['about'].triggered.connect(self.show_about)
        self._menus['help'].addAction(self._actions['about'])
        
        # Acción Instrucciones
        self._actions['instructions'] = QAction(tr('instructions'), self)
        self._actions['instructions'].setStatusTip('Ver instrucciones de uso')
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
        """Aplicar tema al menú"""
        if self.dark_mode:
            # Estilo modo oscuro para el menú
            self.setStyleSheet("""
                QMenuBar {
                    background-color: #1e1e1e;
                    color: #e0e0e0;
                    padding: 5px;
                    border-bottom: 1px solid #2a2a2a;
                }
                
                QMenuBar::item {
                    background-color: transparent;
                    padding: 8px 15px;
                    margin: 2px;
                    border-radius: 4px;
                }
                
                QMenuBar::item:selected {
                    background-color: #2a2a2a;
                    color: #e0e0e0;
                }
                
                QMenuBar::item:pressed {
                    background-color: #3a3a3a;
                    color: #e0e0e0;
                }
                
                QMenu {
                    background-color: #1e1e1e;
                    color: #e0e0e0;
                    border: 1px solid #2a2a2a;
                    border-radius: 4px;
                    padding: 5px;
                }
                
                QMenu::item {
                    padding: 8px 20px;
                    margin: 2px;
                    border-radius: 3px;
                }
                
                QMenu::item:selected {
                    background-color: #2a2a2a;
                    color: #e0e0e0;
                }
                
                QMenu::separator {
                    height: 1px;
                    background-color: #2a2a2a;
                    margin: 5px 10px;
                }
            """)
        else:
            # Estilo modo claro para el menú
            self.setStyleSheet("""
                QMenuBar {
                    background-color: #f8f9fa;
                    color: #2c3e50;
                    padding: 5px;
                    border-bottom: 1px solid #dee2e6;
                }
                
                QMenuBar::item {
                    background-color: transparent;
                    padding: 8px 15px;
                    margin: 2px;
                    border-radius: 4px;
                }
                
                QMenuBar::item:selected {
                    background-color: #e9ecef;
                    color: #3498db;
                }
                
                QMenuBar::item:pressed {
                    background-color: #3498db;
                    color: white;
                }
                
                QMenu {
                    background-color: white;
                    color: #2c3e50;
                    border: 1px solid #dee2e6;
                    border-radius: 4px;
                    padding: 5px;
                }
                
                QMenu::item {
                    padding: 8px 20px;
                    margin: 2px;
                    border-radius: 3px;
                }
                
                QMenu::item:selected {
                    background-color: #3498db;
                    color: white;
                }
                
                QMenu::separator {
                    height: 1px;
                    background-color: #dee2e6;
                    margin: 5px 10px;
                }
            """)

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
        if 'daily_advice' in self._actions:
            self._actions['daily_advice'].setText(tr('daily_advice'))
        if 'weekly_summary' in self._actions:
            self._actions['weekly_summary'].setText(tr('weekly_summary'))
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
    
    def show_about(self):
        """Mostrar diálogo Acerca de"""
        title = tr("about_title")
        if self.current_language == 'es':
            content = """
            <h3>W-T-F (Weekend Trading Finance) Manager</h3>
            <p><strong>Versión:</strong> 2.2</p>
            <p><strong>Descripción:</strong> Aplicación para gestionar y analizar el rendimiento semanal de trading,
            con análisis AI, persistencia de datos y visualizaciones mejoradas.</p>
            <p><strong>Características:</strong></p>
            <ul>
                <li>✅ Gestión de datos semanales</li>
                <li>✅ Análisis AI de rendimiento</li>
                <li>✅ Persistencia en SQLite</li>
                <li>✅ Visualizaciones interactivas</li>
                <li>✅ Modo oscuro/claro</li>
                <li>✅ Exportación de datos</li>
            </ul>
            <p><strong>Tecnologías:</strong> Python, PyQt5, Matplotlib, SQLite</p>
            """
        else:
            content = """
            <h3>W-T-F (Weekend Trading Finance) Manager</h3>
            <p><strong>Version:</strong> 2.2</p>
            <p><strong>Description:</strong> Application to manage and analyze weekly trading performance,
            with AI analysis, data persistence, and enhanced visualizations.</p>
            <p><strong>Features:</strong></p>
            <ul>
                <li>✅ Weekly data management</li>
                <li>✅ AI performance analysis</li>
                <li>✅ SQLite persistence</li>
                <li>✅ Interactive visualizations</li>
                <li>✅ Dark/Light mode</li>
                <li>✅ Data export</li>
            </ul>
            <p><strong>Tech:</strong> Python, PyQt5, Matplotlib, SQLite</p>
            """
        QMessageBox.about(self, title, content)
    
    def show_instructions(self):
        """Mostrar instrucciones de uso"""
        title = tr("instructions_title")
        if self.current_language == 'es':
            content = """
            <h3>📖 Instrucciones de Uso</h3>
            <h4>📝 Ingreso de Datos:</h4>
            <ul>
                <li>Haz clic en cualquier celda de la tabla</li>
                <li>Ingresa el monto del día</li>
                <li>Selecciona el destino (Retiro Personal o Reinversión)</li>
                <li>Los cambios se guardan automáticamente</li>
            </ul>
            <h4>💾 Guardar y Cargar:</h4>
            <ul>
                <li><strong>Guardar:</strong> Archivo → Guardar Semana (Ctrl+S)</li>
                <li><strong>Cargar:</strong> Archivo → Cargar Semana (Ctrl+O)</li>
                <li><strong>BD:</strong> Archivo → Cargar desde Base de Datos</li>
                <li><strong>Capital:</strong> Archivo → Establecer Capital Inicial</li>
            </ul>
            <h4>🎨 Personalización:</h4>
            <ul>
                <li>Vista → Modo Oscuro para cambiar el tema</li>
                <li>Los gráficos se actualizan automáticamente</li>
                <li>El análisis AI se genera con cada cambio</li>
            </ul>
            <h4>📊 Análisis:</h4>
            <ul>
                <li>Resumen semanal en el panel derecho</li>
                <li>Gráfico de barras con colores por tipo</li>
                <li>Análisis AI con recomendaciones</li>
                <li>Estadísticas de rendimiento</li>
            </ul>
            <p><strong>💡 Consejo:</strong> Usa el análisis AI para mejorar tu estrategia de trading.</p>
            """
        else:
            content = """
            <h3>📖 Usage Instructions</h3>
            <h4>📝 Data Entry:</h4>
            <ul>
                <li>Click any table cell</li>
                <li>Enter the day amount</li>
                <li>Select destination (Personal Withdrawal or Reinvestment)</li>
                <li>Changes are saved automatically</li>
            </ul>
            <h4>💾 Save and Load:</h4>
            <ul>
                <li><strong>Save:</strong> File → Save Week (Ctrl+S)</li>
                <li><strong>Load:</strong> File → Load Week (Ctrl+O)</li>
                <li><strong>DB:</strong> File → Load from Database</li>
                <li><strong>Capital:</strong> File → Set Initial Capital</li>
            </ul>
            <h4>🎨 Personalization:</h4>
            <ul>
                <li>View → Dark Mode to change theme</li>
                <li>Charts update automatically</li>
                <li>AI analysis is generated on each change</li>
            </ul>
            <h4>📊 Analysis:</h4>
            <ul>
                <li>Weekly summary on the right panel</li>
                <li>Bar chart with colors by type</li>
                <li>AI analysis with recommendations</li>
                <li>Performance statistics</li>
            </ul>
            <p><strong>💡 Tip:</strong> Use AI analysis to improve your trading strategy.</p>
            """
        QMessageBox.information(self, title, content)