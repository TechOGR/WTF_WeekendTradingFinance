"""
🚀 W-T-F Trading Manager - Export Manager
==========================================
Módulo para exportar datos de trading a formatos Excel y CSV con estilos profesionales.

Autor: W-T-F Trading Manager Team
Versión: 2.1.0
"""

import pandas as pd
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from PyQt5.QtCore import QObject, pyqtSignal
import xlsxwriter
from .i18n import tr


class ExportManager(QObject):
    """Gestor de exportación de datos de trading a múltiples formatos."""
    
    export_completed = pyqtSignal(str)  # Señal cuando la exportación termina
    export_error = pyqtSignal(str)    # Señal cuando hay error
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.supported_formats = {
            'Excel (*.xlsx)': self.export_to_excel,
            'CSV (*.csv)': self.export_to_csv,
            'JSON (*.json)': self.export_to_json
        }
    
    def export_data(self, data: Dict[str, Any], week_number: int, 
                   file_path: Optional[str] = None, file_format: Optional[str] = None) -> bool:
        """
        Exporta los datos de trading al formato especificado.
        
        Args:
            data: Diccionario con los datos de trading
            week_number: Número de semana
            file_path: Ruta del archivo (opcional)
            file_format: Formato de exportación (opcional)
            
        Returns:
            bool: True si la exportación fue exitosa
        """
        try:
            if not file_path:
                file_path = self._get_save_path(file_format)
                if not file_path:
                    return False
            
            # Determinar formato por extensión si no se especifica
            if not file_format:
                file_format = self._get_format_from_path(file_path)
            
            # Obtener la función de exportación
            export_func = self._get_export_function(file_format)
            if not export_func:
                raise ValueError(f"Formato no soportado: {file_format}")
            
            # Ejecutar exportación
            success = export_func(data, file_path, week_number)
            
            if success:
                self.export_completed.emit(f"Datos exportados exitosamente a: {file_path}")
                return True
            else:
                return False
                
        except Exception as e:
            error_msg = f"Error al exportar datos: {str(e)}"
            self.export_error.emit(error_msg)
            return False
    
    def _get_save_path(self, suggested_format: Optional[str] = None) -> Optional[str]:
        """Muestra diálogo para seleccionar ruta de guardado."""
        
        # Determinar filtro de formato
        if suggested_format:
            filter_text = f"{suggested_format};;All Files (*.*)"
        else:
            filter_text = ";;".join(self.supported_formats.keys()) + ";;All Files (*.*)"
        
        # Diálogo de guardado
        file_path, selected_filter = QFileDialog.getSaveFileName(
            None,
            "Exportar Datos de Trading",
            self._get_default_filename(),
            filter_text
        )
        
        return file_path if file_path else None
    
    def _get_default_filename(self) -> str:
        """Genera nombre de archivo por defecto con fecha y hora."""
        now = datetime.now()
        return f"trading_data_{now.strftime('%Y%m%d_%H%M%S')}"
    
    def _get_format_from_path(self, file_path: str) -> str:
        """Determina el formato basado en la extensión del archivo."""
        ext = os.path.splitext(file_path)[1].lower()
        format_map = {
            '.xlsx': 'Excel (*.xlsx)',
            '.csv': 'CSV (*.csv)', 
            '.json': 'JSON (*.json)'
        }
        return format_map.get(ext, 'Excel (*.xlsx)')
    
    def _get_export_function(self, file_format: str):
        """Obtiene la función de exportación según el formato."""
        return self.supported_formats.get(file_format)

    # ---------------------------------------------------------------------
    # Normalización de datos de entrada
    # ---------------------------------------------------------------------
    def _normalize_daily_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normaliza el bloque de datos diarios desde diferentes esquemas."""
        # Caso 1: ya viene como 'daily_data'
        if isinstance(data.get('daily_data'), dict):
            return data.get('daily_data') or {}
        # Caso 2: viene como 'data' del modelo base/BD
        if isinstance(data.get('data'), dict):
            return data.get('data') or {}
        # Caso 3: viene separado en 'daily_amounts' y 'daily_destinations'
        amounts = data.get('daily_amounts')
        dests = data.get('daily_destinations')
        if isinstance(amounts, dict):
            daily = {}
            for day, amount in amounts.items():
                daily[day] = {
                    'amount': amount,
                    'destination': dests.get(day, '') if isinstance(dests, dict) else '',
                    'type': '',
                    'comments': ''
                }
            return daily
        return {}

    def _summary_field(self, data: Dict[str, Any], *keys, default: Any = 0) -> Any:
        """Obtiene un campo de resumen con clave alternativa y valor por defecto."""
        for k in keys:
            if k in data:
                return data[k]
        return default
    
    def export_to_excel(self, data: Dict[str, Any], file_path: str, week_number: int) -> bool:
        """Exporta datos a formato Excel con estilo profesional y gráficos."""
        try:
            # Crear workbook de xlsxwriter
            workbook = xlsxwriter.Workbook(file_path)

            # Paleta y formatos
            header_format = workbook.add_format({
                'bold': True,
                'font_color': 'white',
                'bg_color': '#1F4E79',  # azul profundo
                'border': 1,
                'align': 'center',
                'valign': 'vcenter'
            })

            money_format = workbook.add_format({
                'num_format': '$#,##0.00',
                'border': 1,
                'align': 'right'
            })
            green_money_format = workbook.add_format({
                'num_format': '$#,##0.00',
                'border': 1,
                'align': 'right',
                'font_color': '#1E8449'  # verde
            })
            red_money_format = workbook.add_format({
                'num_format': '$#,##0.00',
                'border': 1,
                'align': 'right',
                'font_color': '#C0392B'  # rojo
            })

            percentage_format = workbook.add_format({
                'num_format': '0.00%',
                'border': 1,
                'align': 'right'
            })

            date_format = workbook.add_format({
                'num_format': 'mm/dd/yyyy',
                'border': 1,
                'align': 'center'
            })

            border_format = workbook.add_format({'border': 1})

            kpi_title = workbook.add_format({'bold': True, 'font_size': 16})
            kpi_label = workbook.add_format({'bold': True, 'bg_color': '#F2F2F2', 'border': 1})
            kpi_value_currency = workbook.add_format({'num_format': '$#,##0.00', 'border': 1, 'bold': True})
            kpi_value_number = workbook.add_format({'border': 1, 'bold': True})
            kpi_value_percent = workbook.add_format({'num_format': '0.00%', 'border': 1, 'bold': True})

            # Hoja de datos diarios
            sheet_name = f"{tr('week')} {week_number}"
            worksheet = workbook.add_worksheet(sheet_name)

            # Encabezados
            headers = [
                tr('day_column'),
                'Fecha' if tr('monday') == 'Lunes' else 'Date',
                tr('amount_column'),
                tr('destination_column'),
                tr('type_column') if tr('type_column', None) != 'type_column' else ('Tipo' if tr('monday') == 'Lunes' else 'Type'),
                tr('comments_column') if tr('comments_column', None) != 'comments_column' else ('Comentarios' if tr('monday') == 'Lunes' else 'Comments')
            ]
            for col, header in enumerate(headers):
                worksheet.write(0, col, header, header_format)

            # Datos diarios
            row = 1
            daily_data = self._normalize_daily_data(data)
            for day, day_data in daily_data.items():
                worksheet.write(row, 0, day.capitalize(), border_format)
                worksheet.write(row, 1, day_data.get('date', ''), date_format)
                amount = day_data.get('amount', 0)
                if amount > 0:
                    worksheet.write(row, 2, amount, green_money_format)
                elif amount < 0:
                    worksheet.write(row, 2, amount, red_money_format)
                else:
                    worksheet.write(row, 2, '', border_format)
                worksheet.write(row, 3, day_data.get('destination', ''), border_format)
                worksheet.write(row, 4, day_data.get('type', ''), border_format)
                worksheet.write(row, 5, day_data.get('comments', ''), border_format)
                row += 1

            last_row = row - 1

            # Tabla y estilos de la sección diaria
            worksheet.add_table(0, 0, last_row, 5, {
                'style': 'Table Style Medium 9',
                'columns': [{'header': h} for h in headers]
            })
            worksheet.freeze_panes(1, 0)
            column_widths = [12, 15, 15, 18, 14, 28]
            for col, width in enumerate(column_widths):
                worksheet.set_column(col, col, width)

            # Formato condicional en montos
            worksheet.conditional_format(1, 2, last_row, 2, {
                'type': 'cell', 'criteria': '>', 'value': 0, 'format': green_money_format
            })
            worksheet.conditional_format(1, 2, last_row, 2, {
                'type': 'cell', 'criteria': '<', 'value': 0, 'format': red_money_format
            })

            # Hoja de resumen (KPIs)
            summary_sheet = workbook.add_worksheet('Resumen' if tr('monday') == 'Lunes' else 'Summary')
            summary_sheet.write(0, 0, ('Resumen Semanal' if tr('monday') == 'Lunes' else 'Weekly Summary'), kpi_title)

            # KPI labels
            summary_sheet.write(2, 0, 'Capital Inicial', kpi_label)
            summary_sheet.write(3, 0, 'Total Semanal', kpi_label)
            summary_sheet.write(4, 0, 'Rendimiento %', kpi_label)
            summary_sheet.write(5, 0, 'Días Positivos', kpi_label)
            summary_sheet.write(6, 0, 'Días Negativos', kpi_label)

            # KPI values (con fórmulas donde aplica)
            initial_capital = self._summary_field(data, 'initial_capital', default=0)
            summary_sheet.write(2, 1, initial_capital, kpi_value_currency)
            # SUM de montos en hoja diaria
            summary_sheet.write_formula(3, 1, f"=SUM('{sheet_name}'!C2:C{last_row})", kpi_value_currency)
            # Rendimiento = Total / Capital
            summary_sheet.write_formula(4, 1, f"=IF(B3>0,B4/B3,0)", kpi_value_percent)
            summary_sheet.write_formula(5, 1, f"=COUNTIF('{sheet_name}'!C2:C{last_row},\">0\")", kpi_value_number)
            summary_sheet.write_formula(6, 1, f"=COUNTIF('{sheet_name}'!C2:C{last_row},\"<0\")", kpi_value_number)
            summary_sheet.set_column(0, 1, 22)

            # Totales por destino (para gráfico de torta)
            totals_by_destination = {}
            for r in range(1, last_row + 1):
                # Leer desde la hoja diaria por consistencia
                # Nota: No tenemos acceso directo a valores ya escritos; usamos daily_data
                pass
            # Construir desde daily_data
            for _, dd in daily_data.items():
                dest = dd.get('destination', '') or 'Sin destino'
                amt = dd.get('amount', 0) or 0
                totals_by_destination[dest] = totals_by_destination.get(dest, 0) + (amt or 0)

            dest_start_row = 9
            summary_sheet.write(dest_start_row, 0, ('Totales por destino' if tr('monday') == 'Lunes' else 'Totals by destination'), kpi_label)
            dr = dest_start_row + 1
            for dest, total in totals_by_destination.items():
                summary_sheet.write(dr, 0, dest, border_format)
                summary_sheet.write(dr, 1, total, money_format)
                dr += 1

            # Hoja de gráficos
            chart_sheet = workbook.add_worksheet('Gráficos' if tr('monday') == 'Lunes' else 'Charts')
            chart_sheet.write(0, 0, tr('day_column'), header_format)
            chart_sheet.write(0, 1, tr('amount_column'), header_format)
            chart_sheet.write(0, 2, ('Acumulado' if tr('monday') == 'Lunes' else 'Cumulative'), header_format)

            # Replicar nombres de días y vincular montos a la hoja diaria
            chart_row = 1
            for r in range(2, last_row + 1):
                chart_sheet.write_formula(chart_row, 0, f"='{sheet_name}'!A{r}", border_format)
                chart_sheet.write_formula(chart_row, 1, f"='{sheet_name}'!C{r}", money_format)
                # Acumulado sobre la columna B del propio sheet
                if chart_row == 1:
                    chart_sheet.write_formula(chart_row, 2, "=B2", money_format)
                else:
                    chart_sheet.write_formula(chart_row, 2, f"=SUM(B$2:B{chart_row+1})", money_format)
                chart_row += 1

            # Gráfico de columnas (montos diarios)
            column_chart = workbook.add_chart({'type': 'column'})
            column_chart.add_series({
                'name': ('Montos por día' if tr('monday') == 'Lunes' else 'Daily amounts'),
                'categories': [chart_sheet.get_name(), 1, 0, chart_row - 1, 0],
                'values': [chart_sheet.get_name(), 1, 1, chart_row - 1, 1],
            })
            column_chart.set_title({'name': ('Desempeño semanal' if tr('monday') == 'Lunes' else 'Weekly Performance')})
            column_chart.set_x_axis({'name': ('Días' if tr('monday') == 'Lunes' else 'Days')})
            column_chart.set_y_axis({'name': ('Monto ($)' if tr('monday') == 'Lunes' else 'Amount ($)')})
            chart_sheet.insert_chart('E2', column_chart)

            # Gráfico de línea (acumulado)
            line_chart = workbook.add_chart({'type': 'line'})
            line_chart.add_series({
                'name': ('Acumulado' if tr('monday') == 'Lunes' else 'Cumulative'),
                'categories': [chart_sheet.get_name(), 1, 0, chart_row - 1, 0],
                'values': [chart_sheet.get_name(), 1, 2, chart_row - 1, 2],
            })
            line_chart.set_title({'name': ('Saldo acumulado' if tr('monday') == 'Lunes' else 'Cumulative balance')})
            chart_sheet.insert_chart('E18', line_chart)

            # Gráfico de torta (por destino)
            if totals_by_destination:
                pie_chart = workbook.add_chart({'type': 'pie'})
                # Rango en hoja de resumen
                start = dest_start_row + 1
                end = dr - 1
                pie_chart.add_series({
                    'name': ('Distribución por destino' if tr('monday') == 'Lunes' else 'Distribution by destination'),
                    'categories': [summary_sheet.get_name(), start, 0, end, 0],
                    'values': [summary_sheet.get_name(), start, 1, end, 1],
                })
                pie_chart.set_title({'name': ('Destinos' if tr('monday') == 'Lunes' else 'Destinations')})
                chart_sheet.insert_chart('E34', pie_chart)

            workbook.close()
            return True
        
        except Exception as e:
            self.export_error.emit(f"Error al exportar a Excel: {str(e)}")
            return False
    
    def export_to_csv(self, data: Dict[str, Any], file_path: str, week_number: int) -> bool:
        """Exporta datos a formato CSV simple."""
        try:
            daily_data = self._normalize_daily_data(data)
            
            # Encabezados y filas diarias consistentes
            headers = ['Semana', 'Día', 'Fecha', 'Monto', 'Destino', 'Tipo', 'Comentarios']
            rows_daily = []
            for day, day_data in daily_data.items():
                rows_daily.append([
                    week_number,
                    day.capitalize(),
                    day_data.get('date', ''),
                    day_data.get('amount', 0),
                    day_data.get('destination', ''),
                    day_data.get('type', ''),
                    day_data.get('comments', '')
                ])
            
            # Exportar sección diaria con DataFrame
            df_daily = pd.DataFrame(rows_daily, columns=headers)
            df_daily.to_csv(file_path, index=False, encoding='utf-8')
            
            # Agregar sección de resumen como texto para evitar discrepancias de columnas
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write('\n')
                f.write('RESUMEN SEMANAL\n')
                f.write(f'Capital Inicial,{data.get("initial_capital", 0)}\n')
                f.write(f'Total Semanal,{data.get("weekly_total", 0)}\n')
                f.write(f'Rendimiento %,{data.get("performance_percentage", 0)}\n')
                f.write(f'Días Positivos,{data.get("positive_days", 0)}\n')
                f.write(f'Días Negativos,{data.get("negative_days", 0)}\n')
                f.write(f'Total Retiros,{data.get("total_withdrawals", 0)}\n')
                f.write(f'Total Reinvertido,{data.get("total_reinvestment", 0)}\n')
            
            return True
            
        except Exception as e:
            self.export_error.emit(f"Error al exportar a CSV: {str(e)}")
            return False
    
    def export_to_json(self, data: Dict[str, Any], file_path: str, week_number: int) -> bool:
        """Exporta datos a formato JSON con formato bonito."""
        try:
            # Agregar metadata
            export_data = {
                'metadata': {
                    'version': '2.1.0',
                    'export_date': datetime.now().isoformat(),
                    'week_number': week_number,
                    'application': 'W-T-F Trading Manager'
                },
                'data': data
            }
            
            # Exportar JSON con formato
            with open(file_path, 'w', encoding='utf-8') as f:
                import json
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            self.export_error.emit(f"{tr('export_error')}: {str(e)}")
            return False
    
    def show_export_dialog(self, data: Dict[str, Any], week_number: int) -> bool:
        """Muestra el diálogo de exportación y ejecuta la exportación."""
        try:
            file_path = self._get_save_path()
            if not file_path:
                return False
            
            return self.export_data(data, week_number, file_path)
            
        except Exception as e:
            self.export_error.emit(f"{tr('export_error')}: {str(e)}")
            return False


# =============================================================================
# 🎯 FUNCIONES DE UTILIDAD RÁPIDA
# =============================================================================

def quick_export_to_excel(data: Dict[str, Any], week_number: int, file_path: str) -> bool:
    """Exportación rápida a Excel sin interfaz gráfica."""
    exporter = ExportManager()
    return exporter.export_to_excel(data, file_path, week_number)


def quick_export_to_csv(data: Dict[str, Any], week_number: int, file_path: str) -> bool:
    """Exportación rápida a CSV sin interfaz gráfica."""
    exporter = ExportManager()
    return exporter.export_to_csv(data, file_path, week_number)


def export_with_dialog(data: Dict[str, Any], week_number: int) -> bool:
    """Exportación con diálogo de archivo."""
    exporter = ExportManager()
    return exporter.show_export_dialog(data, week_number)