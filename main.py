"""
W-T-F (Weekend Trading Finance) Trading Manager - Versión Modular
Aplicación principal que integra todos los componentes modulares
"""

import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, 
                           QVBoxLayout, QSplitter, QStatusBar, QMessageBox, QFileDialog, 
                           QDialog, QInputDialog)
from PyQt5.QtCore import Qt, QTimer, pyqtSlot
from PyQt5.QtGui import QPalette, QColor

# Importar componentes modulares
from src.ui.main_menu import MainMenuBar
from src.ui.trading_table import TradingTableWidget
from src.ui.summary_panel import SummaryPanel
from src.ui.enhanced_chart_widget import EnhancedChartWidget
from src.ui.capital_dialog import CapitalDialog
from src.ui.export_dialog import show_export_dialog
from src.models.trading_model_with_db import TradingDataModelWithDB
from src.models.ai_analyzer import AIAnalyzer
from src.styles.themes import ThemeManager
from src.utils.advice import get_daily_advice, get_weekly_summary_message
from src.utils.i18n import tr, set_language

class MainWindow(QMainWindow):
    """Ventana principal de la aplicación W-T-F Trading Manager"""
    
    def __init__(self):
        super().__init__()
        self.data_model = None
        self.ai_analyzer = None
        self.theme_manager = None
        self.dark_mode = False  # Agregar atributo dark_mode
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """Configurar la interfaz de usuario principal"""
        self.setWindowTitle(tr("app_title"))
        self.setGeometry(100, 100, 1400, 900)
        
        # Crear modelo de datos
        self.data_model = TradingDataModelWithDB()
        self.ai_analyzer = AIAnalyzer()
        self.theme_manager = ThemeManager()
        
        # Crear menú principal
        self.menu_bar = MainMenuBar(self)
        self.setMenuBar(self.menu_bar)
        
        # Crear widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Crear splitter para layout flexible
        splitter = QSplitter(Qt.Horizontal)
        
        # Panel izquierdo: Tabla de trading
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)
        
        # Tabla de trading
        self.table_widget = TradingTableWidget(self.data_model)
        left_layout.addWidget(self.table_widget)
        
        # Gráfico mejorado
        self.chart_widget = EnhancedChartWidget()
        left_layout.addWidget(self.chart_widget)
        
        # Panel derecho: Resumen y análisis
        self.summary_panel = SummaryPanel()
        
        # Añadir paneles al splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(self.summary_panel)
        
        # Configurar proporciones del splitter (70% - 30%)
        splitter.setSizes([980, 420])
        splitter.setStretchFactor(0, 7)
        splitter.setStretchFactor(1, 3)
        
        main_layout.addWidget(splitter)
        
        # Barra de estado
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("✅ " + tr("loading"))
        
        # Aplicar tema inicial (claro)
        self.apply_theme(False)
        
        # Cargar datos iniciales
        self.load_initial_data()
    
    def setup_connections(self):
        """Configurar conexiones entre componentes"""
        # Conexiones del menú
        self.menu_bar.save_triggered.connect(self.save_week)
        self.menu_bar.load_triggered.connect(self.load_week)
        self.menu_bar.load_from_db_triggered.connect(self.load_from_database)
        self.menu_bar.set_capital_triggered.connect(self.set_initial_capital)
        self.menu_bar.theme_changed.connect(self.apply_theme)
        self.menu_bar.show_daily_advice_triggered.connect(self.show_daily_advice)
        self.menu_bar.show_weekly_summary_triggered.connect(self.show_weekly_summary_notification)
        self.menu_bar.export_excel_triggered.connect(self.export_to_excel)
        self.menu_bar.export_csv_triggered.connect(self.export_to_csv)
        self.menu_bar.export_json_triggered.connect(self.export_to_json)
        # Cambio de idioma desde la barra de menú
        self.menu_bar.language_changed.connect(self.on_language_changed)
        
        # Conexiones de la tabla
        self.table_widget.data_changed.connect(self.on_data_changed)
        self.table_widget.save_status_changed.connect(self.update_save_status)
        
        # Conexiones del panel de resumen
        self.summary_panel.update_summary(self.data_model.get_weekly_summary(), {})
        
        # Mostrar consejo del día al iniciar
        self.show_daily_advice()
    
    def apply_theme(self, is_dark: bool):
        """Aplicar tema profesional a toda la aplicación"""
        self.dark_mode = is_dark  # Guardar estado del tema
        
        # Usar el ThemeManager mejorado para aplicar tema a toda la aplicación
        self.theme_manager.apply_theme(self, is_dark)
        
        # Actualizar gráfico
        self.chart_widget.set_theme(is_dark)
        # Forzar refresco del gráfico para aplicar nuevos colores
        try:
            if self.data_model:
                self.chart_widget.update_chart(self.data_model)
        except Exception:
            pass
        
        # Actualizar panel de resumen
        self.summary_panel.setStyleSheet(self.theme_manager.get_widget_styles(is_dark))
        # Aplicar tema específico al panel para ajustar colores internos
        try:
            self.summary_panel.set_theme(is_dark)
        except Exception:
            pass
        
        # Actualizar tabla
        self.table_widget.setStyleSheet(self.theme_manager.get_widget_styles(is_dark))
        
        # Actualizar barra de menú
        self.menu_bar.setStyleSheet(self.theme_manager.get_widget_styles(is_dark))
        
        # Actualizar barra de estado
        self.status_bar.setStyleSheet(self.theme_manager.get_widget_styles(is_dark))
        
        # Actualizar splitter y widgets principales
        if hasattr(self, 'centralWidget'):
            self.centralWidget().setStyleSheet(self.theme_manager.get_widget_styles(is_dark))
        
        # Aplicar tema a todos los diálogos abiertos
        for widget in QApplication.allWidgets():
            if isinstance(widget, (QDialog, QFileDialog, QInputDialog, QMessageBox)):
                widget.setStyleSheet(self.theme_manager.get_widget_styles(is_dark))
    
    def load_initial_data(self):
        """Cargar datos iniciales al iniciar la aplicación"""
        try:
            # Intentar cargar la última semana guardada
            if self.data_model.load_latest_week():
                self.table_widget.load_data()
                self.update_chart()  # Actualizar gráfico con datos cargados
                self.update_summary()
                self.status_bar.showMessage("✅ Datos iniciales cargados desde base de datos", 3000)
                # Consejos al cargar datos
                self.show_daily_advice()
                # Si es sábado, mostrar resumen semanal
                try:
                    from datetime import datetime
                    if datetime.now().weekday() == 5:
                        self.show_weekly_summary_notification()
                except Exception:
                    pass
            else:
                # Si no hay datos, preguntar por el capital inicial
                self.ask_for_initial_capital()
                # Actualizar gráfico con datos vacíos
                self.update_chart()
                self.status_bar.showMessage("ℹ️ No hay datos previos, comenzando con semana nueva", 3000)
                self.show_daily_advice()
                # Si es sábado, mostrar resumen semanal
                try:
                    from datetime import datetime
                    if datetime.now().weekday() == 5:
                        self.show_weekly_summary_notification()
                except Exception:
                    pass
                
        except Exception as e:
            QMessageBox.warning(self, tr("warning"), 
                              f"{tr('load_error')}: {str(e)}\n"
                              f"{tr('operation_failed')}.")
            # Asegurar que el gráfico se actualice incluso si hay error
            self.update_chart()
    
    @pyqtSlot()
    def on_data_changed(self):
        """Manejar cambios en los datos"""
        try:
            # Actualizar gráfico
            self.update_chart()
            
            # Actualizar resumen y análisis AI
            self.update_summary()
            
            # Guardar automáticamente en base de datos
            self.data_model.save_current_week()
            
        except Exception as e:
            QMessageBox.critical(self, tr("error"), f"{tr('operation_failed')}: {str(e)}")
    
    def update_chart(self):
        """Actualizar el gráfico con datos actuales"""
        try:
            self.chart_widget.update_chart(self.data_model)
        except Exception as e:
            print(f"Error al actualizar gráfico: {e}")
    
    def update_summary(self):
        """Actualizar el panel de resumen con análisis AI"""
        try:
            # Obtener resumen de datos
            summary_data = self.data_model.get_weekly_summary()
            
            # Generar análisis AI
            ai_analysis = self.ai_analyzer.analyze_weekly_performance(summary_data, self.data_model.data)
            
            # Preparar datos del capital
            capital_data = {
                'initial_capital': self.data_model.initial_capital,
                'current_balance': self.data_model.get_current_balance(),
                'total_profit_loss': self.data_model.get_total_profit_loss(),
                'profit_loss_percentage': self.data_model.get_profit_loss_percentage()
            }
            
            # Actualizar panel
            self.summary_panel.update_summary(summary_data, ai_analysis, capital_data)
            # Actualizar consejo del día
            try:
                advice = get_daily_advice(self.data_model)
                self.summary_panel.update_daily_advice(advice)
            except Exception:
                pass
            
        except Exception as e:
            print(f"Error al actualizar resumen: {e}")
            # Mostrar resumen sin análisis AI
            summary_data = self.data_model.get_weekly_summary()
            capital_data = {
                'initial_capital': getattr(self.data_model, 'initial_capital', 100.0),
                'current_balance': getattr(self.data_model, 'initial_capital', 100.0),
                'total_profit_loss': 0,
                'profit_loss_percentage': 0
            }
            self.summary_panel.update_summary(summary_data, {}, capital_data)
            # Intentar actualizar consejo del día
            try:
                advice = get_daily_advice(self.data_model)
                self.summary_panel.update_daily_advice(advice)
            except Exception:
                pass

    def show_daily_advice(self):
        """Mostrar consejo del día en el panel y en la barra de estado."""
        try:
            advice = get_daily_advice(self.data_model)
            self.summary_panel.update_daily_advice(advice)
            self.status_bar.showMessage("📌 " + tr("daily_advice"), 3000)
        except Exception as e:
            print(f"Error al generar consejo del día: {e}")

    def show_weekly_summary_notification(self):
        """Mostrar notificación de resumen semanal (útil para sábados)."""
        try:
            message = get_weekly_summary_message(self.data_model)
            QMessageBox.information(self, tr("weekly_summary_panel"), message)
        except Exception as e:
            QMessageBox.warning(self, tr("warning"), f"{tr('operation_failed')}: {e}")
    
    def on_language_changed(self, lang: str):
        """Actualizar textos y re-traducir widgets principales."""
        # Actualizar título de la ventana
        self.setWindowTitle(tr("app_title"))
        # Retraducir tabla de trading
        if hasattr(self.table_widget, 'apply_language'):
            self.table_widget.apply_language()
        # Retraducir panel de resumen
        if hasattr(self.summary_panel, 'apply_language'):
            self.summary_panel.apply_language()
    
    @pyqtSlot(str)
    def update_save_status(self, status):
        """Actualizar estado de guardado"""
        self.status_bar.showMessage(status, 3000)
        
        # Actualizar también el panel de resumen
        self.summary_panel.update_status(status)
    
    def save_week(self):
        """Guardar la semana actual en la carpeta Weekend-Saved"""
        try:
            # Crear carpeta Weekend-Saved si no existe
            import os
            save_folder = "Weekend-Saved"
            os.makedirs(save_folder, exist_ok=True)
            
            # Generar nombre de archivo con fecha actual
            from datetime import datetime
            current_date = datetime.now().strftime("%Y-%m-%d")
            default_filename = f"weekend_trading_{current_date}.json"
            
            # Guardar en archivo JSON
            dialog = QFileDialog(self, tr("save_week_title"))
            dialog.setNameFilter("JSON Files (*.json)")
            dialog.setDefaultSuffix("json")
            dialog.setAcceptMode(QFileDialog.AcceptSave)
            dialog.setDirectory(save_folder)
            dialog.selectFile(default_filename)
            
            # Aplicar tema al diálogo
            if self.dark_mode:
                dialog.setStyleSheet(self.theme_manager.get_widget_styles(True))
            
            if dialog.exec_() == QFileDialog.Accepted:
                filename = dialog.selectedFiles()[0]
                if self.data_model.save_to_file(filename):
                    self.update_save_status("✅ " + tr("save_success"))
                else:
                    self.update_save_status("❌ " + tr("save_error"))
                
        except Exception as e:
            QMessageBox.critical(self, tr("save_error"), str(e))
            self.update_save_status("❌ " + tr("save_error"))
    
    def load_week(self):
        """Cargar semana desde archivo de la carpeta Weekend-Saved"""
        try:
            # Verificar si existe la carpeta Weekend-Saved
            import os
            save_folder = "Weekend-Saved"
            
            if not os.path.exists(save_folder):
                QMessageBox.information(self, tr("information"), 
                                      f"{tr('file_not_found')}: Weekend-Saved\n"
                                      f"{tr('operation_completed')}.")
                return
            
            dialog = QFileDialog(self, tr("load_week_title"))
            dialog.setNameFilter("JSON Files (*.json)")
            dialog.setAcceptMode(QFileDialog.AcceptOpen)
            dialog.setDirectory(save_folder)
            
            # Aplicar tema al diálogo
            if self.dark_mode:
                dialog.setStyleSheet(self.theme_manager.get_widget_styles(True))
            
            if dialog.exec_() == QFileDialog.Accepted:
                filename = dialog.selectedFiles()[0]
                if self.data_model.load_from_file(filename):
                    self.table_widget.load_data()
                    self.update_chart()
                    self.update_summary()
                    self.update_save_status("✅ " + tr("load_success"))
                else:
                    self.update_save_status("❌ " + tr("load_error"))
                
        except Exception as e:
            QMessageBox.critical(self, tr("load_error"), str(e))
            self.update_save_status("❌ " + tr("load_error"))
    
    def load_from_database(self):
        """Cargar desde base de datos"""
        try:
            weeks = self.data_model.get_all_saved_weeks()

            if not weeks:
                QMessageBox.information(self, tr("information"), tr("file_not_found"))
                return

            if len(weeks) == 1:
                week_date = weeks[0]
            else:
                # Crear diálogo de selección
                from PyQt5.QtWidgets import QInputDialog
                dialog = QInputDialog(self)
                dialog.setWindowTitle(tr("load_week_title"))
                dialog.setLabelText(tr("week") + ":")
                dialog.setComboBoxItems([f"{tr('week')} {w}" for w in weeks])

                # Aplicar tema al diálogo
                if self.dark_mode:
                    dialog.setStyleSheet(self.theme_manager.get_widget_styles(True))

                if dialog.exec_() == QInputDialog.Accepted:
                    item = dialog.textValue()
                    week_date = item.replace("Semana del ", "")
                else:
                    return

            # Cargar la semana seleccionada
            if self.data_model.load_week(week_date):
                self.table_widget.load_data()
                self.update_chart()
                self.update_summary()
                self.update_save_status(f"✅ {tr('week')} {week_date} {tr('load_success')}")
            else:
                QMessageBox.warning(self, tr("warning"), f"{tr('load_error')} {week_date}")

        except Exception as e:
            QMessageBox.critical(self, tr("error"), f"{tr('load_error')} {str(e)}")
            self.update_save_status("❌ " + tr("load_error"))

    def ask_for_initial_capital(self):
        """Preguntar por el capital inicial al iniciar una semana nueva"""
        try:
            dialog = CapitalDialog(100.0, self)  # Capital inicial por defecto: $100
            
            # Aplicar tema al diálogo
            if self.dark_mode:
                dialog.setStyleSheet(self.theme_manager.get_widget_styles(True))
            
            if dialog.exec_() == CapitalDialog.Accepted:
                new_capital = dialog.get_capital()
                self.data_model.initial_capital = new_capital
                self.data_model.save_current_week()
                self.update_summary()
                self.status_bar.showMessage(f"✅ {tr('capital_initial')} ${new_capital:.2f}", 3000)
            else:
                # Si cancela, usar valor por defecto
                self.data_model.initial_capital = 100.0
                self.data_model.save_current_week()
                self.update_summary()
                self.status_bar.showMessage(f"ℹ️ {tr('capital_initial')} $100.00", 3000)
                
        except Exception as e:
            # En caso de error, usar valor por defecto
            self.data_model.initial_capital = 100.0
            print(f"Error al preguntar por capital inicial: {e}")
    
    def set_initial_capital(self):
        """Abrir diálogo para establecer el capital inicial"""
        try:
            dialog = CapitalDialog(self.data_model.initial_capital, self)
            
            # Aplicar tema al diálogo
            if self.dark_mode:
                dialog.setStyleSheet(self.theme_manager.get_widget_styles(True))
            
            if dialog.exec_() == CapitalDialog.Accepted:
                new_capital = dialog.get_capital()
                if new_capital != self.data_model.initial_capital:
                     self.data_model.initial_capital = new_capital
                     self.data_model.save_current_week()
                     self.update_summary()
                     self.update_save_status(f"✅ {tr('capital_initial')} ${new_capital:.2f}")
        except Exception as e:
            QMessageBox.critical(self, tr("error"), f"{tr('operation_failed')}: {str(e)}")
            self.update_save_status("❌ " + tr("operation_failed"))
    
    def export_to_excel(self):
        """Exportar datos a Excel"""
        try:
            if not self.data_model:
                QMessageBox.warning(self, tr("warning"), tr("no_data_to_export"))
                return
            
            # Obtener datos de la semana actual
            weekly_data = self.data_model.get_weekly_data()
            # Número de semana basado en fecha de inicio
            week_number = self.data_model.week_start_date.isocalendar()[1]
            
            # Mostrar diálogo de exportación
            show_export_dialog(weekly_data, week_number, self)
            
        except Exception as e:
            QMessageBox.critical(self, tr("error"), f"{tr('export_error')}: {str(e)}")
            self.update_save_status("❌ " + tr("export_error"))
    
    def export_to_csv(self):
        """Exportar datos a CSV"""
        try:
            if not self.data_model:
                QMessageBox.warning(self, tr("warning"), tr("no_data_to_export"))
                return
            
            # Obtener datos de la semana actual
            weekly_data = self.data_model.get_weekly_data()
            week_number = self.data_model.week_start_date.isocalendar()[1]
            
            # Mostrar diálogo de exportación
            show_export_dialog(weekly_data, week_number, self)
            
        except Exception as e:
            QMessageBox.critical(self, tr("error"), f"{tr('export_error')}: {str(e)}")
            self.update_save_status("❌ " + tr("export_error"))
    
    def export_to_json(self):
        """Exportar datos a JSON"""
        try:
            if not self.data_model:
                QMessageBox.warning(self, tr("warning"), tr("no_data_to_export"))
                return
            
            # Obtener datos de la semana actual
            weekly_data = self.data_model.get_weekly_data()
            week_number = self.data_model.week_start_date.isocalendar()[1]
            
            # Mostrar diálogo de exportación
            show_export_dialog(weekly_data, week_number, self)
            
        except Exception as e:
            QMessageBox.critical(self, tr("error"), f"{tr('export_error')}: {str(e)}")
            self.update_save_status("❌ " + tr("export_error"))
    
    def closeEvent(self, event):
        """Manejar cierre de la aplicación"""
        try:
            # Guardar estado actual antes de cerrar
            self.data_model.save_current_week()
            event.accept()
        except Exception as e:
            reply = QMessageBox.question(self, "Confirmar cierre",
                                       f"Error al guardar: {str(e)}\n¿Desea cerrar de todos modos?",
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                event.accept()
            else:
                event.ignore()

def main():
    """Función principal"""
    app = QApplication(sys.argv)
    
    # Configurar estilo de la aplicación
    app.setStyle('Fusion')
    
    # Crear y mostrar ventana principal
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()