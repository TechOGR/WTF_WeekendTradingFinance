"""
Administrador de base de datos SQLite
Maneja toda la persistencia de datos de la aplicación
"""

import sqlite3
from datetime import datetime
from typing import Dict, List, Optional

class DatabaseManager:
    """Administrador de base de datos SQLite para persistencia de datos"""
    
    def __init__(self, db_path: str = "trading_data.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Inicializar la base de datos y crear tablas si no existen"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Crear tabla de semanas de trading
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS trading_weeks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        week_start_date TEXT UNIQUE NOT NULL,
                        lunes_amount REAL DEFAULT 0.0,
                        martes_amount REAL DEFAULT 0.0,
                        miercoles_amount REAL DEFAULT 0.0,
                        jueves_amount REAL DEFAULT 0.0,
                        viernes_amount REAL DEFAULT 0.0,
                        initial_capital REAL DEFAULT 100.0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Agregar columna initial_capital si no existe (para bases de datos existentes)
                try:
                    cursor.execute("ALTER TABLE trading_weeks ADD COLUMN initial_capital REAL DEFAULT 100.0")
                except sqlite3.OperationalError:
                    # La columna ya existe, ignorar error
                    pass
                
                # Crear tabla de configuración
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS app_config (
                        key TEXT PRIMARY KEY,
                        value TEXT,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # Detalles de sesión por día (par de divisas y duración)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS day_details (
                        week_start_date TEXT NOT NULL,
                        day TEXT NOT NULL,
                        pair TEXT DEFAULT '',
                        duration TEXT DEFAULT '',
                        PRIMARY KEY (week_start_date, day)
                    )
                ''')

                conn.commit()
        except sqlite3.Error as e:
            print(f"Error al inicializar la base de datos: {e}")
    
    def save_weekly_data(self, data: Dict) -> bool:
        """Guardar o actualizar los datos de una semana"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                week_start_date = data['week_start_date']
                trading_data = data['data']
                
                # Preparar datos para la inserción/actualización
                lunes = trading_data['Lunes']['amount']
                martes = trading_data['Martes']['amount']
                miercoles = trading_data['Miércoles']['amount']
                jueves = trading_data['Jueves']['amount']
                viernes = trading_data['Viernes']['amount']
                
                # Intentar actualizar primero
                cursor.execute('''
                    UPDATE trading_weeks 
                    SET lunes_amount = ?, martes_amount = ?, miercoles_amount = ?, 
                        jueves_amount = ?, viernes_amount = ?, initial_capital = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE week_start_date = ?
                ''', (lunes, martes, miercoles, jueves, viernes, data.get('initial_capital', 100.0), week_start_date))
                
                # Si no se actualizó ninguna fila, insertar nueva
                if cursor.rowcount == 0:
                    cursor.execute('''
                        INSERT INTO trading_weeks 
                        (week_start_date, lunes_amount, martes_amount, miercoles_amount, 
                         jueves_amount, viernes_amount, initial_capital)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (week_start_date, lunes, martes, miercoles, jueves, viernes, data.get('initial_capital', 100.0)))

                # Guardar detalles de sesión (par / duración) de cada día
                for day, info in trading_data.items():
                    cursor.execute('''
                        INSERT OR REPLACE INTO day_details (week_start_date, day, pair, duration)
                        VALUES (?, ?, ?, ?)
                    ''', (week_start_date, day, info.get('pair', '') or '', info.get('duration', '') or ''))

                conn.commit()
                return True
                
        except sqlite3.Error as e:
            print(f"Error al guardar datos: {e}")
            return False
    
    def load_latest_week(self) -> Optional[Dict]:
        """Cargar la última semana guardada"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT week_start_date, lunes_amount, martes_amount, miercoles_amount, 
                           jueves_amount, viernes_amount, initial_capital
                    FROM trading_weeks
                    ORDER BY week_start_date DESC
                    LIMIT 1
                ''')
                
                row = cursor.fetchone()
                if row:
                    week_start_date, lunes, martes, miercoles, jueves, viernes, initial_capital = row
                    
                    # Convertir a formato compatible con el modelo
                    return self._with_day_details(cursor, {
                        'week_start_date': week_start_date,
                        'initial_capital': initial_capital,
                        'data': {
                            'Lunes': {'amount': lunes, 'destination': 'Retiro Personal'},
                            'Martes': {'amount': martes, 'destination': 'Retiro Personal'},
                            'Miércoles': {'amount': miercoles, 'destination': 'Reinversión'},
                            'Jueves': {'amount': jueves, 'destination': 'Retiro Personal'},
                            'Viernes': {'amount': viernes, 'destination': 'Retiro Personal'}
                        }
                    })
                return None
                
        except sqlite3.Error as e:
            print(f"Error al cargar última semana: {e}")
            return None
    
    def load_week_by_date(self, week_start_date: str) -> Optional[Dict]:
        """Cargar una semana específica por fecha"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT week_start_date, lunes_amount, martes_amount, miercoles_amount, 
                           jueves_amount, viernes_amount, initial_capital
                    FROM trading_weeks
                    WHERE week_start_date = ?
                ''', (week_start_date,))
                
                row = cursor.fetchone()
                if row:
                    week_start_date, lunes, martes, miercoles, jueves, viernes, initial_capital = row
                    
                    return self._with_day_details(cursor, {
                        'week_start_date': week_start_date,
                        'initial_capital': initial_capital,
                        'data': {
                            'Lunes': {'amount': lunes, 'destination': 'Retiro Personal'},
                            'Martes': {'amount': martes, 'destination': 'Retiro Personal'},
                            'Miércoles': {'amount': miercoles, 'destination': 'Reinversión'},
                            'Jueves': {'amount': jueves, 'destination': 'Retiro Personal'},
                            'Viernes': {'amount': viernes, 'destination': 'Retiro Personal'}
                        }
                    })
                return None
                
        except sqlite3.Error as e:
            print(f"Error al cargar semana por fecha: {e}")
            return None
    
    def get_all_weeks(self) -> List[Dict]:
        """Obtener todas las semanas guardadas"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT week_start_date, created_at
                    FROM trading_weeks
                    ORDER BY week_start_date DESC
                ''')
                
                rows = cursor.fetchall()
                return [
                    {
                        'week_start_date': row[0],
                        'created_at': row[1]
                    }
                    for row in rows
                ]
                
        except sqlite3.Error as e:
            print(f"Error al obtener todas las semanas: {e}")
            return []

    def _with_day_details(self, cursor, week: Dict) -> Dict:
        """Añadir par/duración guardados a cada día de la semana."""
        try:
            cursor.execute(
                'SELECT day, pair, duration FROM day_details WHERE week_start_date = ?',
                (week['week_start_date'],)
            )
            for day, pair, duration in cursor.fetchall():
                if day in week['data']:
                    week['data'][day]['pair'] = pair or ''
                    week['data'][day]['duration'] = duration or ''
        except sqlite3.Error as e:
            print(f"Error al cargar detalles de los días: {e}")
        return week

    def get_config(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Leer un valor de configuración de la aplicación."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                row = conn.execute('SELECT value FROM app_config WHERE key = ?', (key,)).fetchone()
                return row[0] if row and row[0] is not None else default
        except sqlite3.Error as e:
            print(f"Error al leer configuración '{key}': {e}")
            return default

    def set_config(self, key: str, value: str) -> bool:
        """Guardar un valor de configuración de la aplicación."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO app_config (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP) "
                    "ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP",
                    (key, value)
                )
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Error al guardar configuración '{key}': {e}")
            return False
