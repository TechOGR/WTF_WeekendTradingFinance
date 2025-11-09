"""
🚀 W-T-F Trading Manager - Export Dialog
=========================================
Diálogo profesional para exportar datos de trading a múltiples formatos.

Autor: W-T-F Trading Manager Team
Versión: 2.1.0
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QComboBox, QGroupBox, QTextEdit,
                             QProgressBar, QFileDialog, QMessageBox, QCheckBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot, QTimer
from PyQt5.QtGui import QIcon, QPixmap, QFont
import os
import pandas as pd
from typing import Dict, Any, Optional
from src.utils.i18n import tr

# Importar nuestro gestor de exportación
from ..utils.export_manager import ExportManager


class ExportWorker(QThread):
    """Worker thread para exportación sin bloquear la UI."""
    
    progress_updated = pyqtSignal(int)
    status_message = pyqtSignal(str)
    export_completed = pyqtSignal(str)
    export_error = pyqtSignal(str)
    
    def __init__(self, export_manager: ExportManager, data: Dict[str, Any], 
                 week_number: int, file_path: str, include_charts: bool = False):
        super().__init__()
        self.export_manager = export_manager
        self.data = data
        self.week_number = week_number
        self.file_path = file_path
        self.include_charts = include_charts
        
    def run(self):
        """Ejecuta la exportación en segundo plano."""
        try:
            self.status_message.emit("Preparando datos para exportación...")
            self.progress_updated.emit(10)
            
            # Conectar señales del export manager
            self.export_manager.export_completed.connect(self.on_export_completed)
            self.export_manager.export_error.connect(self.on_export_error)
            
            self.status_message.emit("Exportando datos...")
            self.progress_updated.emit(50)
            
            # Realizar exportación
            success = self.export_manager.export_data(
                self.data, self.week_number, self.file_path
            )
            
            if success:
                self.progress_updated.emit(100)
                self.status_message.emit("¡Exportación completada exitosamente!")
            else:
                self.export_error.emit("La exportación falló")
                
        except Exception as e:
            self.export_error.emit(f"Error durante la exportación: {str(e)}")
    
    @pyqtSlot(str)
    def on_export_completed(self, message: str):
        """Maneja la finalización exitosa de la exportación."""
        self.export_completed.emit(message)
    
    @pyqtSlot(str)
    def on_export_error(self, error: str):
        """Maneja errores de exportación."""
        self.export_error.emit(error)


class ExportDialog(QDialog):
    """Diálogo principal de exportación con opciones avanzadas."""
    
    def __init__(self, data: Dict[str, Any], week_number: int, parent=None):
        super().__init__(parent)
        self.data = data
        self.week_number = week_number
        self.export_manager = ExportManager()
        self.export_worker = None
        self.selected_file_path = None
        
        # Configurar diálogo
        self.setWindowTitle(tr("export_dialog_title"))
        self.setModal(True)
        self.setFixedSize(600, 500)
        
        # Establecer icono si existe
        # self.setWindowIcon(QIcon("assets/export_icon.png"))
        
        self.setup_ui()
        self.connect_signals()
        self.update_preview()
    
    def setup_ui(self):
        """Configura la interfaz de usuario."""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Título principal
        title_label = QLabel(tr("export_dialog_title"))
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: #2C3E50;
                padding: 10px;
                background-color: #ECF0F1;
                border-radius: 5px;
            }
        """)
        main_layout.addWidget(title_label)
        
        # Información de la semana
        week_info = QLabel(f"{tr('week')} #{self.week_number} - {tr('export_completed')}")
        week_info.setAlignment(Qt.AlignCenter)
        week_info.setStyleSheet("color: #7F8C8D; font-size: 12px;")
        main_layout.addWidget(week_info)
        
        # Grupo de opciones de formato
        format_group = QGroupBox("📁 " + tr("menu_export"))
        format_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #BDC3C7;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        format_layout = QVBoxLayout()
        
        # Selector de formato
        format_selector_layout = QHBoxLayout()
        format_label = QLabel(tr("format_label"))
        self.format_combo = QComboBox()
        self.format_combo.addItems([
            tr("format_excel_recommended"),
            tr("format_csv_compatible"),
            tr("format_json_developers")
        ])
        format_selector_layout.addWidget(format_label)
        format_selector_layout.addWidget(self.format_combo)
        format_selector_layout.addStretch()
        format_layout.addLayout(format_selector_layout)
        
        # Opciones adicionales
        self.include_charts_check = QCheckBox(tr("include_charts_excel"))
        self.include_charts_check.setChecked(True)
        format_layout.addWidget(self.include_charts_check)
        
        self.include_summary_check = QCheckBox(tr("include_detailed_summary"))
        self.include_summary_check.setChecked(True)
        format_layout.addWidget(self.include_summary_check)
        
        format_group.setLayout(format_layout)
        main_layout.addWidget(format_group)
        
        # Vista previa de datos
        preview_group = QGroupBox(tr("preview_title"))
        preview_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #BDC3C7;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        preview_layout = QVBoxLayout()
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(150)
        self.preview_text.setStyleSheet("""
            QTextEdit {
                background-color: #F8F9FA;
                border: 1px solid #DEE2E6;
                border-radius: 3px;
                font-family: 'Courier New';
                font-size: 10px;
            }
        """)
        preview_layout.addWidget(self.preview_text)
        preview_group.setLayout(preview_layout)
        main_layout.addWidget(preview_group)
        
        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #BDC3C7;
                border-radius: 5px;
                text-align: center;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #3498DB;
                width: 10px;
                margin: 1px;
            }
        """)
        main_layout.addWidget(self.progress_bar)
        
        # Estado de exportación
        self.status_label = QLabel(tr("operation_completed"))
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #27AE60; font-style: italic;")
        main_layout.addWidget(self.status_label)
        
        # Botones de acción
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.select_file_btn = QPushButton("📁 " + tr("select_file"))
        self.select_file_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498DB;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980B9;
            }
            QPushButton:pressed {
                background-color: #21618C;
            }
        """)
        button_layout.addWidget(self.select_file_btn)
        
        self.export_btn = QPushButton("🚀 " + tr("menu_export"))
        self.export_btn.setEnabled(False)
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #27AE60;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:pressed {
                background-color: #1E8449;
            }
            QPushButton:disabled {
                background-color: #BDC3C7;
                color: #7F8C8D;
            }
        """)
        button_layout.addWidget(self.export_btn)
        
        self.cancel_btn = QPushButton("❌ " + tr("cancel"))
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #E74C3C;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #C0392B;
            }
            QPushButton:pressed {
                background-color: #A93226;
            }
        """)
        button_layout.addWidget(self.cancel_btn)
        
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)
    
    def connect_signals(self):
        """Conecta las señales de la interfaz."""
        self.select_file_btn.clicked.connect(self.select_file)
        self.export_btn.clicked.connect(self.start_export)
        self.cancel_btn.clicked.connect(self.reject)
        self.format_combo.currentTextChanged.connect(self.update_preview)
        self.include_charts_check.stateChanged.connect(self.update_preview)
        self.include_summary_check.stateChanged.connect(self.update_preview)
        
        # Conectar señales del export manager
        self.export_manager.export_completed.connect(self.on_export_success)
        self.export_manager.export_error.connect(self.on_export_error)
    
    def update_preview(self):
        """Actualiza la vista previa según el formato seleccionado."""
        format_text = self.format_combo.currentText()
        
        if "Excel" in format_text:
            preview = """📊 Formato Excel (.xlsx)
✅ Tabla con formato profesional
✅ Resumen con gráficos incluidos
✅ Múltiples hojas de trabajo
✅ Fórmulas y formatos de moneda"""
        elif "CSV" in format_text:
            preview = """📋 Formato CSV (.csv)
✅ Compatible con Excel, Google Sheets
✅ Formato simple y universal
✅ Fácil de importar en otros programas
✅ Tamaño de archivo mínimo"""
        else:  # JSON
            preview = """💻 Formato JSON (.json)
✅ Para desarrolladores y APIs
✅ Estructura de datos completa
✅ Incluye metadata y timestamps
✅ Fácil de procesar programáticamente"""
        
        # Agregar información de los datos
        daily_data = self.data.get('daily_data', {})
        active_days = sum(1 for day_data in daily_data.values() 
                         if day_data.get('amount', 0) != 0)
        
        total_week = self.data.get('weekly_total', self.data.get('total_weekly', self.data.get('total_profit_loss', 0)))
        perf = self.data.get('performance_percentage', self.data.get('profit_loss_percentage', 0))
        preview += f"""

📈 Estadísticas de exportación:
   • Días activos: {active_days}/7
   • Capital inicial: ${self.data.get('initial_capital', 0):,.2f}
   • Total semanal: ${total_week:,.2f}
   • Rendimiento: {perf:.2f}%"""
        
        self.preview_text.setPlainText(preview)
    
    def select_file(self):
        """Muestra diálogo para seleccionar archivo de destino."""
        format_text = self.format_combo.currentText()
        
        # Determinar extensión y filtro
        if "Excel" in format_text:
            ext = ".xlsx"
            filter_text = "Excel Files (*.xlsx)"
        elif "CSV" in format_text:
            ext = ".csv"
            filter_text = "CSV Files (*.csv)"
        else:
            ext = ".json"
            filter_text = "JSON Files (*.json)"
        
        # Generar nombre por defecto
        default_name = f"trading_semana_{self.week_number}_{pd.Timestamp.now().strftime('%Y%m%d')}{ext}"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            tr("export_save_title"),
            default_name,
            f"{filter_text};;All Files (*)"
        )
        
        if file_path:
            self.selected_file_path = file_path
            self.export_btn.setEnabled(True)
            self.status_label.setText(f"{tr('selected_file')}: {os.path.basename(file_path)}")
            self.status_label.setStyleSheet("color: #27AE60; font-style: italic;")
    
    def start_export(self):
        """Inicia el proceso de exportación."""
        if not self.selected_file_path:
            QMessageBox.warning(self, tr("warning"), tr("export_failed"))
            return
        
        try:
            # Deshabilitar controles durante la exportación
            self.set_controls_enabled(False)
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.status_label.setText(tr("starting_export"))
            self.status_label.setStyleSheet("color: #3498DB; font-style: italic;")
            
            # Crear y ejecutar worker
            self.export_worker = ExportWorker(
                self.export_manager,
                self.data,
                self.week_number,
                self.selected_file_path,
                self.include_charts_check.isChecked()
            )
            
            # Conectar señales del worker
            self.export_worker.progress_updated.connect(self.update_progress)
            self.export_worker.status_message.connect(self.update_status)
            self.export_worker.export_completed.connect(self.on_export_success)
            self.export_worker.export_error.connect(self.on_export_error)
            
            # Iniciar exportación
            self.export_worker.start()
            
        except Exception as e:
            self.on_export_error(f"{tr('export_error')}: {str(e)}")
    
    def set_controls_enabled(self, enabled: bool):
        """Habilita/deshabilita controles durante la exportación."""
        self.format_combo.setEnabled(enabled)
        self.include_charts_check.setEnabled(enabled)
        self.include_summary_check.setEnabled(enabled)
        self.select_file_btn.setEnabled(enabled)
        self.export_btn.setEnabled(enabled and self.selected_file_path is not None)
    
    @pyqtSlot(int)
    def update_progress(self, value: int):
        """Actualiza la barra de progreso."""
        self.progress_bar.setValue(value)
    
    @pyqtSlot(str)
    def update_status(self, message: str):
        """Actualiza el mensaje de estado."""
        self.status_label.setText(message)
    
    @pyqtSlot(str)
    def on_export_success(self, message: str):
        """Maneja el éxito de la exportación."""
        self.progress_bar.setValue(100)
        self.status_label.setText(f"✅ {tr('export_success')}")
        self.status_label.setStyleSheet("color: #27AE60; font-weight: bold;")
        self.set_controls_enabled(True)
        
        # Mostrar mensaje de éxito
        res = QMessageBox.information(
            self,
            tr("export_success"),
            f"{tr('export_completed')}\n\n{message}\n\n{tr('open_file_location_question')}",
            QMessageBox.Yes | QMessageBox.No
        )
        
        # Abrir ubicación del archivo si el usuario lo desea
        if res == QMessageBox.Yes:
            self.open_file_location()
        
        # Cerrar diálogo después de un breve delay
        self.export_worker = None
        QTimer.singleShot(1500, self.accept)
    
    @pyqtSlot(str)
    def on_export_error(self, error: str):
        """Maneja errores de exportación."""
        self.status_label.setText(f"❌ {tr('export_error')}: {error}")
        self.status_label.setStyleSheet("color: #E74C3C; font-weight: bold;")
        self.progress_bar.setVisible(False)
        self.set_controls_enabled(True)
        self.export_worker = None
        
        QMessageBox.critical(self, tr("export_error"), 
                           f"{tr('export_failed')}:\n\n{error}")
    
    def open_file_location(self):
        """Abre la ubicación del archivo exportado."""
        if self.selected_file_path and os.path.exists(self.selected_file_path):
            folder_path = os.path.dirname(self.selected_file_path)
            os.startfile(folder_path)  # Windows
            # Para Linux/Mac: os.system(f'xdg-open "{folder_path}"')


# =============================================================================
# 🎯 FUNCIONES DE UTILIDAD
# =============================================================================

def show_export_dialog(data: Dict[str, Any], week_number: int, parent=None) -> bool:
    """
    Muestra el diálogo de exportación y retorna True si fue exitoso.
    
    Args:
        data: Datos de trading a exportar
        week_number: Número de semana
        parent: Widget padre
        
    Returns:
        bool: True si la exportación fue exitosa
    """
    dialog = ExportDialog(data, week_number, parent)
    result = dialog.exec_()
    return result == QDialog.Accepted