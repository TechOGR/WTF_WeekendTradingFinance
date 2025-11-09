"""
Widget de gráfico mejorado con mejor visualización
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from PyQt5.QtCore import QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from datetime import datetime
import numpy as np
from src.utils.i18n import tr

class EnhancedChartWidget(QWidget):
    """Widget de gráfico mejorado con mejor visualización"""
    
    def __init__(self):
        super().__init__()
        self.is_dark = False
        self.legend_visible = True
        # Posición por defecto dentro del gráfico para evitar encoger el área
        self.legend_position = 'upper_right'  # opciones: outside_right, upper_right, upper_center
        self.setup_ui()
        
    def setup_ui(self):
        """Configurar la interfaz del gráfico"""
        layout = QVBoxLayout()

        # Crear figura y canvas (usar constrained_layout para mejorar ajuste inicial)
        self.figure = Figure(figsize=(12, 6), dpi=100, facecolor='white', edgecolor='none', constrained_layout=True)
        self.canvas = FigureCanvas(self.figure)
        # Asegurar que el canvas se expanda con el contenedor
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.canvas.updateGeometry()
        layout.addWidget(self.canvas)

        self.setLayout(layout)

        # Configurar estilo inicial
        self.setup_chart_style()

    def showEvent(self, event):
        """Tras mostrar el widget, rehacer el layout del gráfico para capturar el tamaño real."""
        super().showEvent(event)
        QTimer.singleShot(0, self._post_show_adjust)

    def _post_show_adjust(self):
        try:
            if hasattr(self, 'last_data_model') and self.last_data_model:
                # Redibujar con datos ya cargados para ajustar al tamaño real
                self.update_chart(self.last_data_model)
            else:
                # Ajuste mínimo si no hay datos aún
                self.figure.tight_layout()
                self.canvas.draw()
        except Exception:
            pass
    
    def setup_chart_style(self):
        """Configurar el estilo del gráfico"""
        # Estilo profesional
        try:
            plt.style.use('seaborn-v0_8-whitegrid')
        except Exception:
            plt.style.use('seaborn')

        # Paleta de colores elegante
        self.colors = {
            'positive': '#2ecc71',      # Verde suave
            'negative': '#e74c3c',      # Rojo elegante
            # 'withdrawal': '#8e44ad',
            'withdrawal': '#2ecc71',    # Púrpura para retiro personal
            'reinvestment': '#f1c40f',  # Dorado para reinversión
            'neutral': '#bdc3c7',       # Gris
            'text': '#2c3e50',          # Texto oscuro
            'grid': '#ecf0f1',          # Grilla clara
            'avg_line': '#3498db'       # Línea de promedio
        }

        # Configurar fuentes
        plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['font.sans-serif'] = ['Segoe UI', 'Arial', 'DejaVu Sans']
        plt.rcParams['font.size'] = 10
    
    def update_chart(self, data_model):
        """Actualizar el gráfico con datos del modelo"""
        # Guardar referencia para poder regenerar con nuevo idioma
        self.last_data_model = data_model
        try:
            self.figure.clear()
            
            # Crear subplot principal
            ax = self.figure.add_subplot(111)
            
            # Obtener datos, usando días dinámicos del modelo
            base_daily_data = []
            model_days = getattr(data_model, 'days', [])
            # Mapeo de claves de días para etiquetas traducidas
            day_keys = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

            for i, day_key in enumerate(model_days):
                amount = data_model.daily_amounts.get(day_key, 0)
                destination = data_model.daily_destinations.get(day_key, '')
                # Etiqueta visible: abreviatura del nombre traducido (si disponible)
                # Si el modelo usa claves como 'monday', 'tuesday', etc., usar directamente la traducción
                label_name = tr(day_key)[:3] if day_key in day_keys else (tr(day_keys[i])[:3] if i < len(day_keys) else day_key[:3])
                base_daily_data.append({
                    'day': label_name,
                    'amount': amount,
                    'destination': destination,
                    'is_positive': amount > 0,
                    'is_withdrawal': destination in (tr('personal_withdrawal'), 'Retiro Personal', 'Personal Withdrawal'),
                    'is_reinvestment': destination in (tr('reinvestment'), 'Reinversión', 'Reinvestment')
                })

            # Extender visualmente el gráfico como si tuviera sábado y domingo
            daily_data = list(base_daily_data)
            # Agregar placeholders solo si no existen ya en el modelo
            if 'saturday' not in model_days:
                daily_data.append({
                    'day': tr('saturday')[:3],
                    'amount': 0,
                    'destination': '',
                    'is_positive': False,
                    'is_withdrawal': False,
                    'is_reinvestment': False
                })
            if 'sunday' not in model_days:
                daily_data.append({
                    'day': tr('sunday')[:3],
                    'amount': 0,
                    'destination': '',
                    'is_positive': False,
                    'is_withdrawal': False,
                    'is_reinvestment': False
                })
            
            # Preparar datos para el gráfico
            x_positions = np.arange(len(daily_data))
            # Guardar montos base (sin placeholders) para cálculos como promedio
            base_amounts = [d['amount'] for d in base_daily_data]
            amounts = [d['amount'] for d in daily_data]
            
            # Determinar colores de las barras
            colors = []
            for data in daily_data:
                if data['amount'] < 0:
                    colors.append(self.colors['negative'])
                elif data['amount'] == 0:
                    colors.append(self.colors['neutral'])
                else:  # Positivo
                    if data.get('is_withdrawal'):
                        colors.append(self.colors['withdrawal'])
                    elif data.get('is_reinvestment'):
                        colors.append(self.colors['reinvestment'])
                    else:
                        colors.append(self.colors['positive'])
            
            # Crear barras con mejor proporción
            bar_width = 0.6
            bars = ax.bar(x_positions, amounts, bar_width, color=colors, 
                         alpha=0.8, edgecolor='white', linewidth=1.5)
            
            # Configurar el gráfico
            ax.set_xlabel(tr('days_of_week_label'), fontsize=12, fontweight='bold', color=self.colors['text'])
            ax.set_ylabel(tr('amount_axis_label'), fontsize=12, fontweight='bold', color=self.colors['text'])
            # Título sin emoji para evitar advertencias de fuente
            weekly_total = sum(amounts)
            ax.set_title(tr('weekly_performance_title'), fontsize=16, fontweight='bold', 
                        color=self.colors['text'], pad=16)
            
            # Configurar ejes
            ax.set_xticks(x_positions)
            ax.set_xticklabels([d['day'] for d in daily_data], fontsize=10, color=self.colors['text'])
            
            # Configurar grid
            ax.grid(True, axis='y', alpha=0.35, color=self.colors['grid'], linestyle='-', linewidth=0.8)
            ax.set_axisbelow(True)
            
            # Configurar línea base en cero
            ax.axhline(y=0, color=self.colors['text'], linewidth=1, alpha=0.5)
            
            # Añadir etiquetas de valores con mejor posicionamiento
            for i, (bar, data) in enumerate(zip(bars, daily_data)):
                height = bar.get_height()
                
                if height != 0:  # Solo mostrar etiquetas para barras con valor
                    # Determinar posición de la etiqueta
                    if height > 0:
                        y_pos = height + (max(amounts + [1]) * 0.02)  # margen por encima
                        va = 'bottom'
                    else:
                        y_pos = height - (max(abs(np.array(amounts)) + 1) * 0.02)  # margen por debajo
                        va = 'top'
                    
                    # Formatear el valor
                    value_text = f'${height:.0f}'
                    
                    # Añadir etiqueta
                    bbox_face = '#1e1e1e' if self.is_dark else 'white'
                    bbox_edge = '#2a2a2a' if self.is_dark else 'none'
                    ax.text(bar.get_x() + bar.get_width()/2., y_pos, value_text,
                           ha='center', va=va, fontsize=9, fontweight='bold',
                           color=self.colors['text'], 
                           bbox=dict(boxstyle='round,pad=0.3', facecolor=bbox_face, 
                                   alpha=0.85, edgecolor=bbox_edge))

            # Añadir línea de promedio semanal
            if base_amounts:
                avg = np.mean(base_amounts)
                ax.axhline(avg, color=self.colors['avg_line'], linestyle='--', linewidth=1.5, alpha=0.8)
                ax.text(0.99, 0.02, f"{tr('average_label')} ${avg:.2f}", transform=ax.transAxes,
                        ha='right', va='bottom', fontsize=9, color=self.colors['avg_line'],
                        bbox=dict(boxstyle='round,pad=0.25', facecolor='white', alpha=0.7, edgecolor='none'))
            
            # Ajustar límites del eje Y para dar espacio a las etiquetas
            y_min, y_max = ax.get_ylim()
            y_range = y_max - y_min
            
            if y_min < 0:
                ax.set_ylim(y_min - y_range * 0.1, y_max + y_range * 0.15)
            else:
                ax.set_ylim(y_min, y_max + y_range * 0.15)
            
            # Añadir leyenda mejorada (opcional y sin solapar barras)
            if self.legend_visible:
                legend_elements = [
                    patches.Patch(color=self.colors['reinvestment'], label=tr('legend_gain_reinvestment')),
                    patches.Patch(color=self.colors['withdrawal'], label=tr('legend_gain_withdrawal')),
                    patches.Patch(color=self.colors['negative'], label=tr('legend_loss')),
                    patches.Patch(color=self.colors['neutral'], label=tr('legend_neutral'))
                ]

                if self.legend_position == 'outside_right':
                    # Colocar la leyenda fuera del área del gráfico, a la derecha
                    ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1.02, 1),
                              frameon=True, fancybox=True, shadow=True, fontsize=9, borderaxespad=0.0)
                    # Reducir el espacio del subplot para dejar sitio a la leyenda a la derecha
                    try:
                        self.figure.tight_layout(rect=[0, 0, 0.82, 1])
                    except Exception:
                        self.figure.tight_layout()
                elif self.legend_position == 'upper_center':
                    ax.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, 1.12),
                              frameon=True, fancybox=True, shadow=True, fontsize=9, ncol=2)
                else:  # 'upper_right' por defecto
                    ax.legend(handles=legend_elements, loc='upper right',
                              frameon=True, fancybox=True, shadow=True, fontsize=9)

            # Subtítulo con total semanal
            ax.text(0.01, 1.00, f"{tr('total_week')} ${weekly_total:.2f}", transform=ax.transAxes,
                    ha='left', va='bottom', fontsize=10, color=self.colors['text'])
            
            # Mejorar la apariencia general
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color(self.colors['text'])
            ax.spines['bottom'].set_color(self.colors['text'])
            
            # Ajustar márgenes
            try:
                if self.legend_visible and self.legend_position == 'outside_right':
                    self.figure.tight_layout(rect=[0, 0, 0.82, 1])
                else:
                    self.figure.tight_layout()
            except Exception:
                self.figure.tight_layout()
            
            # Actualizar canvas
            self.canvas.draw()
            
        except Exception as e:
            print(f"{tr('chart_error_update')}: {e}")
            self.show_error_message(str(e))
    
    def show_error_message(self, error_msg):
        """Mostrar mensaje de error en el gráfico"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        ax.text(0.5, 0.5, f"{tr('chart_error_load')}:\n{error_msg}", 
                ha='center', va='center', transform=ax.transAxes,
                fontsize=12, color='red', weight='bold')
        
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        self.canvas.draw()
    
    def clear_chart(self):
        """Limpiar el gráfico"""
        self.figure.clear()
        self.canvas.draw()
    
    def apply_language(self):
        """Actualizar idioma del gráfico"""
        # Si hay datos cargados, regenerar el gráfico con nuevas traducciones
        if hasattr(self, 'last_data_model') and self.last_data_model:
            self.update_chart(self.last_data_model)

    def set_theme(self, is_dark: bool):
        """Cambiar tema del gráfico"""
        self.is_dark = is_dark
        if is_dark:
            self.figure.patch.set_facecolor('#121212')
            plt.rcParams['text.color'] = '#e0e0e0'
            plt.rcParams['axes.facecolor'] = '#1e1e1e'
            plt.rcParams['axes.edgecolor'] = '#e0e0e0'
            plt.rcParams['axes.labelcolor'] = '#e0e0e0'
            plt.rcParams['xtick.color'] = '#e0e0e0'
            plt.rcParams['ytick.color'] = '#e0e0e0'
            plt.rcParams['grid.color'] = '#3a3a3a'
        else:
            self.figure.patch.set_facecolor('white')
            plt.rcParams['text.color'] = '#2c3e50'
            plt.rcParams['axes.facecolor'] = 'white'
            plt.rcParams['axes.edgecolor'] = '#2c3e50'
            plt.rcParams['axes.labelcolor'] = '#2c3e50'
            plt.rcParams['xtick.color'] = '#2c3e50'
            plt.rcParams['ytick.color'] = '#2c3e50'
            plt.rcParams['grid.color'] = '#ecf0f1'
        
        # Actualizar colores según tema
        if is_dark:
            self.colors['text'] = '#e0e0e0'
            self.colors['grid'] = '#3a3a3a'
        else:
            self.colors['text'] = '#2c3e50'
            self.colors['grid'] = '#ecf0f1'

    def set_legend_visible(self, visible: bool):
        """Mostrar u ocultar la leyenda y redibujar."""
        self.legend_visible = bool(visible)
        if hasattr(self, 'last_data_model') and self.last_data_model:
            self.update_chart(self.last_data_model)

    def set_legend_position(self, position: str):
        """Cambiar la posición de la leyenda y redibujar.
        Posiciones soportadas: 'outside_right', 'upper_right', 'upper_center'
        """
        if position in ('outside_right', 'upper_right', 'upper_center'):
            self.legend_position = position
            if hasattr(self, 'last_data_model') and self.last_data_model:
                self.update_chart(self.last_data_model)