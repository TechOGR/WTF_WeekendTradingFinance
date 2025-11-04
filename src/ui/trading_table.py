"""
Widget de tabla para la interfaz de trading
"""

from PyQt5.QtWidgets import (QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QBrush, QColor
from src.utils.i18n import tr

class TradingTableWidget(QTableWidget):
    """Tabla personalizada para mostrar y editar datos de trading"""
    
    save_status_changed = pyqtSignal(str)  # Señal para actualizar el estado de guardado
    data_changed = pyqtSignal()  # Señal para notificar cambios en los datos
    
    def __init__(self, data_model):
        super().__init__()
        self.data_model = data_model
        self.setup_table()
        self.load_data()
    
    def setup_table(self):
        """Configurar la tabla"""
        self.setColumnCount(3)
        self.setRowCount(5)
        
        # Configurar encabezados
        self.setHorizontalHeaderLabels([
            tr('day_column'),
            tr('amount_column'),
            tr('destination_column')
        ])
        
        # Configurar encabezado vertical
        self.verticalHeader().setVisible(False)
        
        # Configurar columnas
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        
        # Hacer la columna de destino no editable
        self.setEditTriggers(self.DoubleClicked | self.SelectedClicked | self.EditKeyPressed)
        
        # Conectar señales
        self.cellChanged.connect(self.on_cell_changed)
    
    def load_data(self):
        """Cargar datos en la tabla"""
        self.blockSignals(True)  # Bloquear señales mientras cargamos
        
        for row, day in enumerate(self.data_model.days):
            # Día
            day_item = QTableWidgetItem(day)
            day_item.setFlags(day_item.flags() & ~Qt.ItemIsEditable)  # No editable
            day_item.setFont(QFont("Arial", 10, QFont.Bold))
            self.setItem(row, 0, day_item)
            
            # Monto
            amount = self.data_model.data[day]['amount']
            amount_item = QTableWidgetItem(f"{amount:.2f}")
            amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            
            # Colorear según positivo/negativo
            if amount > 0:
                amount_item.setForeground(QBrush(QColor("#27ae60")))
            elif amount < 0:
                amount_item.setForeground(QBrush(QColor("#e74c3c")))
            else:
                amount_item.setForeground(QBrush(QColor("#7f8c8d")))
            
            self.setItem(row, 1, amount_item)
            
            # Destino
            destination = self.data_model.data[day]['destination']
            dest_item = QTableWidgetItem(destination)
            dest_item.setFlags(dest_item.flags() & ~Qt.ItemIsEditable)  # No editable
            
            # Colorear destinos
            if destination in {"Retiro Personal", "Personal Withdrawal", tr('personal_withdrawal')}:
                dest_item.setForeground(QBrush(QColor("#3498db")))
            else:
                dest_item.setForeground(QBrush(QColor("#f39c12")))
            
            self.setItem(row, 2, dest_item)
        
        self.blockSignals(False)  # Desbloquear señales
    
    def on_cell_changed(self, row, column):
        """Manejar cambios en las celdas"""
        if column == 1:  # Solo procesar cambios en la columna de montos
            try:
                day = self.item(row, 0).text()
                text = self.item(row, column).text()
                
                # Convertir a número
                amount = float(text.replace(',', '.'))
                
                # Actualizar el modelo
                self.data_model.update_day(day, amount)
                
                # Emitir señales de cambio
                self.data_changed.emit()
                self.save_status_changed.emit(tr('saving'))
                
                # Recargar datos para actualizar colores
                self.load_data()
                
                # Emitir señal de guardado completado
                self.save_status_changed.emit(tr('save_success'))
                
            except ValueError:
                # Si no es un número válido, restaurar el valor anterior
                self.load_data()
                print(f"{tr('invalid_amount')}: {text}")
    
    def get_data(self):
        """Obtener los datos actuales de la tabla"""
        data = {}
        for row in range(self.rowCount()):
            day = self.item(row, 0).text()
            try:
                amount = float(self.item(row, 1).text())
            except ValueError:
                amount = 0.0
            data[day] = amount
        return data

    def apply_language(self):
        """Actualizar encabezados y textos según el idioma actual"""
        self.setHorizontalHeaderLabels([
            tr('day_column'),
            tr('amount_column'),
            tr('destination_column')
        ])
        # Recargar para reflejar posibles cambios visibles
        self.load_data()