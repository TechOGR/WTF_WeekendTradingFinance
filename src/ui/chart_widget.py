"""
Widget de gráficos mejorado para visualización de datos de trading
"""

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QWidget, QVBoxLayout
import pandas as pd
import numpy as np
from src.utils.i18n import tr

class ChartWidget(QWidget):
    """Widget de gráficos mejorado para mostrar el rendimiento de trading"""
    
    def __init__(self):
        super().__init__()
        self.legend_visible = True
        self.legend_position = 'outside_right'
        self.setup_chart()
    
    def setup_chart(self):
        """Configurar el gráfico"""
        # Crear figura con mejor estilo
        self.figure = Figure(figsize=(10, 6), dpi=100, facecolor='none')
        self.canvas = FigureCanvas(self.figure)
        
        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        
        # Configurar estilo inicial
        self.ax = self.figure.add_subplot(111)
        self.ax.set_title(tr('daily_performance_title'), fontsize=14, fontweight='bold', pad=20)
        self.ax.set_xlabel(tr('days_of_week_label'), fontsize=12)
        self.ax.set_ylabel(tr('profit_loss_axis_label'), fontsize=12)
        
        # Mejorar la cuadrícula
        self.ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
        self.ax.set_axisbelow(True)
        
        # Configurar línea base en y=0
        self.ax.axhline(y=0, color='black', linestyle='-', alpha=0.5, linewidth=1)
        
        self.canvas.draw()
    
    def update_chart(self, data: dict):
        """Actualizar el gráfico con nuevos datos"""
        # Guardar referencia para poder regenerar con nuevo idioma
        self.last_data = data
        self.ax.clear()
        
        # Configurar el gráfico nuevamente
        self.ax.set_title(tr('daily_performance_title'), fontsize=14, fontweight='bold', pad=20)
        self.ax.set_xlabel(tr('days_of_week_label'), fontsize=12)
        self.ax.set_ylabel(tr('profit_loss_axis_label'), fontsize=12)
        self.ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
        self.ax.set_axisbelow(True)
        self.ax.axhline(y=0, color='black', linestyle='-', alpha=0.5, linewidth=1)
        
        # Preparar datos
        days = list(data.keys())
        amounts = [data[day]['amount'] for day in days]
        destinations = [data[day]['destination'] for day in days]
        
        # Crear colores basados en destino y valor
        colors = []
        for i, (amount, destination) in enumerate(zip(amounts, destinations)):
            if amount > 0:
                if destination in (tr('personal_withdrawal'), "Retiro Personal"):
                    colors.append('#2ecc71')  # Verde brillante para retiros positivos
                else:
                    colors.append('#27ae60')  # Verde más oscuro para reinversión
            elif amount < 0:
                colors.append('#e74c3c')  # Rojo para pérdidas
            else:
                colors.append('#95a5a6')  # Gris para valores neutros
        
        # Crear gráfico de barras mejorado
        bars = self.ax.bar(days, amounts, color=colors, alpha=0.8, 
                          edgecolor='black', linewidth=1, width=0.6)
        
        # Añadir bordes más gruesos a las barras positivas
        for i, (bar, amount) in enumerate(zip(bars, amounts)):
            if amount > 0:
                bar.set_linewidth(1.5)
                bar.set_edgecolor('#27ae60')
        
        # Añadir valores en las barras con mejor posicionamiento
        for i, (bar, amount) in enumerate(zip(bars, amounts)):
            if amount != 0:
                height = bar.get_height()
                # Calcular posición y-offset basado en el valor
                y_offset = 5 if height >= 0 else -15
                
                # Asegurar que el texto no se salga del gráfico
                y_pos = height + y_offset if height >= 0 else height + y_offset
                
                self.ax.text(bar.get_x() + bar.get_width()/2., y_pos,
                           f'${amount:.2f}',
                           ha='center', va='bottom' if height >= 0 else 'top',
                           fontweight='bold', fontsize=10,
                           bbox=dict(boxstyle='round,pad=0.3', 
                                   facecolor='white', 
                                   alpha=0.8,
                                   edgecolor='none'))
        
        # Ajustar límites del eje Y para dar espacio a los valores
        y_min, y_max = self.ax.get_ylim()
        
        # Si hay valores positivos, dar más espacio arriba
        if max(amounts) > 0:
            y_max = max(y_max, max(amounts) * 1.2)
        
        # Si hay valores negativos, dar más espacio abajo
        if min(amounts) < 0:
            y_min = min(y_min, min(amounts) * 1.2)
        
        # Si todo está en 0, establecer límites por defecto
        if y_min == 0 and y_max == 0:
            y_min, y_max = -10, 10
        
        self.ax.set_ylim(y_min, y_max)
        
        # Mejorar las etiquetas del eje X
        self.ax.set_xticks(range(len(days)))
        self.ax.set_xticklabels(days, rotation=0, ha='center')
        
        # Añadir leyenda mejorada sin solapar la barra del viernes
        from matplotlib.patches import Patch
        if self.legend_visible:
            legend_elements = [
                Patch(facecolor='#27ae60', label=tr('legend_gain_reinvestment')),
                Patch(facecolor='#2ecc71', label=tr('legend_gain_withdrawal')),
                Patch(facecolor='#e74c3c', label=tr('legend_loss')),
                Patch(facecolor='#95a5a6', label=tr('legend_neutral'))
            ]
            if self.legend_position == 'outside_right':
                self.ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1.02, 1),
                               frameon=True, fancybox=True, shadow=True)
                try:
                    self.figure.tight_layout(pad=2.0, rect=[0, 0, 0.82, 1])
                except Exception:
                    self.figure.tight_layout(pad=2.0)
            elif self.legend_position == 'upper_center':
                self.ax.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, 1.12),
                               frameon=True, fancybox=True, shadow=True, ncol=2)
            else:
                self.ax.legend(handles=legend_elements, loc='upper right',
                               frameon=True, fancybox=True, shadow=True)
        
        # Ajustar márgenes
        try:
            if self.legend_visible and self.legend_position == 'outside_right':
                self.figure.tight_layout(pad=2.0, rect=[0, 0, 0.82, 1])
            else:
                self.figure.tight_layout(pad=2.0)
        except Exception:
            self.figure.tight_layout(pad=2.0)
        
        # Actualizar canvas
        self.canvas.draw()
    
    def apply_language(self):
        """Actualizar idioma del gráfico"""
        # Si hay datos cargados, regenerar el gráfico con nuevas traducciones
        if hasattr(self, 'last_data') and self.last_data:
            self.update_chart(self.last_data)

    def clear_chart(self):
        """Limpiar el gráfico"""
        self.ax.clear()
        self.setup_chart()
        self.canvas.draw()

    def set_legend_visible(self, visible: bool):
        """Mostrar u ocultar la leyenda y redibujar."""
        self.legend_visible = bool(visible)
        if hasattr(self, 'last_data') and self.last_data:
            self.update_chart(self.last_data)

    def set_legend_position(self, position: str):
        """Cambiar la posición de la leyenda y redibujar.
        Posiciones soportadas: 'outside_right', 'upper_right', 'upper_center'
        """
        if position in ('outside_right', 'upper_right', 'upper_center'):
            self.legend_position = position
            if hasattr(self, 'last_data') and self.last_data:
                self.update_chart(self.last_data)