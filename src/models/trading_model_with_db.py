"""
Modelo de datos mejorado con integración de base de datos
"""

from datetime import datetime
from typing import Dict, Optional
from .trading_model import TradingDataModel
from ..database.database_manager import DatabaseManager

class TradingDataModelWithDB(TradingDataModel):
    """Modelo de datos con persistencia en base de datos"""
    
    def __init__(self):
        super().__init__()
        self.db_manager = DatabaseManager()
        
        # Agregar atributos para compatibilidad con el gráfico
        self.daily_amounts = {day: 0.0 for day in self.days}
        self.daily_destinations = self.destinations.copy()
        
        # Capital inicial de la semana
        self.initial_capital = 100.0  # Valor por defecto
        
        # Cargar datos guardados automáticamente al iniciar
        self.load_saved_data()
        
    def update_day(self, day: str, amount: float):
        """Actualizar el monto para un día específico y guardar en BD"""
        super().update_day(day, amount)
        # Actualizar daily_amounts y daily_destinations para compatibilidad con el gráfico
        if day in self.daily_amounts:
            self.daily_amounts[day] = amount
            self.daily_destinations[day] = self.data[day].get('destination', self.destinations[day])
        # Guardar automáticamente en la base de datos
        self.db_manager.save_weekly_data(self.to_dict())
        
    def load_saved_data(self):
        """Cargar datos guardados desde la base de datos"""
        try:
            # Intentar cargar la última semana guardada
            saved_data = self.db_manager.load_latest_week()
            if saved_data:
                # Si hay datos guardados para la semana actual o una semana reciente, cargarlos
                self.from_dict(saved_data)
                print("Datos cargados exitosamente desde la base de datos")
            else:
                print("No se encontraron datos previos, iniciando con valores por defecto")
        except Exception as e:
            print(f"Error al cargar datos guardados: {e}")
            print("Iniciando con valores por defecto")
    
    def to_dict(self) -> Dict:
        """Convertir a diccionario para guardar, incluyendo capital inicial"""
        base_dict = super().to_dict()
        base_dict['initial_capital'] = self.initial_capital
        return base_dict
    
    def from_dict(self, data: Dict):
        """Cargar desde diccionario"""
        super().from_dict(data)
        # Sincronizar daily_amounts y daily_destinations con los datos cargados
        for day in self.days:
            if day in self.data:
                self.daily_amounts[day] = self.data[day].get('amount', 0.0)
                self.daily_destinations[day] = self.data[day].get('destination', self.destinations[day])
        # Cargar capital inicial si existe
        self.initial_capital = data.get('initial_capital', 100.0)
    
    def save_current_week(self):
        """Guardar la semana actual en la base de datos"""
        try:
            self.db_manager.save_weekly_data(self.to_dict())
            return True
        except Exception as e:
            print(f"Error al guardar la semana actual: {e}")
            return False
    
    def load_latest_week(self):
        """Cargar la última semana guardada"""
        try:
            saved_data = self.db_manager.load_latest_week()
            if saved_data:
                self.from_dict(saved_data)
                return True
            return False
        except Exception as e:
            print(f"Error al cargar la última semana: {e}")
            return False
    
    def load_specific_week(self, week_date: str):
        """Cargar una semana específica"""
        try:
            saved_data = self.db_manager.load_week_by_date(week_date)
            if saved_data:
                self.from_dict(saved_data)
                return True
            return False
        except Exception as e:
            print(f"Error al cargar la semana {week_date}: {e}")
            return False
    
    def load_week(self, week_date: str):
        """Alias para load_specific_week para mantener compatibilidad"""
        return self.load_specific_week(week_date)
    
    def get_all_saved_weeks(self):
        """Obtener todas las semanas guardadas"""
        try:
            weeks_data = self.db_manager.get_all_weeks()
            # Devolver solo las fechas como strings
            return [week['week_start_date'] for week in weeks_data]
        except Exception as e:
            print(f"Error al obtener semanas guardadas: {e}")
            return []
    
    def save_to_file(self, filename: str):
        """Guardar datos en archivo JSON"""
        try:
            import json
            import os
            
            # Crear directorio si no existe
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            # Guardar datos
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
            
            print(f"Datos guardados exitosamente en: {filename}")
            return True
            
        except Exception as e:
            print(f"Error al guardar en archivo: {e}")
            return False
    
    def load_from_file(self, filename: str):
        """Cargar datos desde archivo JSON"""
        try:
            import json
            
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.from_dict(data)
            print(f"Datos cargados exitosamente desde: {filename}")
            return True
            
        except Exception as e:
            print(f"Error al cargar desde archivo: {e}")
            return False
    
    def get_current_balance(self):
        """Obtener el balance actual (capital inicial + total ganancias/pérdidas)"""
        total_change = sum(self.daily_amounts[day] for day in self.days)
        return self.initial_capital + total_change
    
    def get_total_profit_loss(self):
        """Obtener el total de ganancias/pérdidas de la semana"""
        return sum(self.daily_amounts[day] for day in self.days)
    
    def get_profit_loss_percentage(self):
        """Obtener el porcentaje de ganancia/pérdida respecto al capital inicial"""
        total_change = self.get_total_profit_loss()
        if self.initial_capital == 0:
            return 0.0
        return (total_change / self.initial_capital) * 100
    
    def set_initial_capital(self, capital: float):
        """Establecer el capital inicial de la semana"""
        self.initial_capital = max(0.0, capital)  # Asegurar que no sea negativo
        # Guardar automáticamente en la base de datos
        self.db_manager.save_weekly_data(self.to_dict())
    
    def get_weekly_data(self):
        """Obtener todos los datos de la semana actual para exportación"""
        return {
            'days': self.days,
            'daily_amounts': self.daily_amounts.copy(),
            'daily_destinations': self.daily_destinations.copy(),
            'initial_capital': self.initial_capital,
            'week_start_date': self.week_start_date.isoformat(),
            'current_balance': self.get_current_balance(),
            'total_profit_loss': self.get_total_profit_loss(),
            'profit_loss_percentage': self.get_profit_loss_percentage()
        }