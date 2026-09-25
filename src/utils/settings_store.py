"""
Configuración persistente de la aplicación (guardada en la tabla app_config de SQLite).
Los secretos (API key de Pollinations) viven en el archivo .env, nunca en la base de datos.
"""

import os
import sys

from dotenv import load_dotenv, set_key

# Prompt para generar la tarjeta desde cero (cuando no hay imagen de referencia)
DEFAULT_GENERATION_TEMPLATE = (
    'A professional financial trading results card for the platform Quotex, dark mode UI mobile '
    'application design. In the very top center, the official minimalist red "QUOTEX" logo with its white '
    'text branding is displayed against a dark background. Centered below it, there is a prominent floating '
    'glassmorphism rounded rectangle card with a glowing green neon bottom edge reflection. Inside this glass '
    'card, the top row shows a circular icon merging {flags}, next to the bold white '
    'text "{asset}" and a smaller grey label "Asset". The middle row is split into distinct metrics columns '
    'with clean vector icons: a green clock icon next to "Duration {duration}", a green calendar icon next to '
    '"Day {day}", and a green pulse line icon. The lower section of the card displays the centered grey text '
    '"TOTAL PROFIT" with an info icon, followed by a massive, glowing neon green text that reads "{profit}". '
    'The entire background is a very dark, out-of-focus background featuring abstract green and red financial '
    'candlestick charts with a soft reflection on a glossy surface below. Ultra-clean typography, premium '
    'fintech UI design, highly detailed, professional mobile trading interface, consistent spacing and '
    'alignment.\n\n'
    'Exact, clean and legible UI text. All specified financial values must be reproduced exactly as written. '
    'Do not invent, alter, misspell or stylize the financial values.'
)

PROMPT_PLACEHOLDERS = ('{asset}', '{flags}', '{duration}', '{day}', '{profit}')

# Motores de imagen de la ventana "Imagen de resultado"
ENGINE_AI = 'ai'          # Pollinations (edición de la referencia o generación desde cero)
ENGINE_LOCAL = 'local'    # Pillow: valores exactos garantizados, sin conexión

CURRENCY_PAIRS = ['NZD/CAD', 'USD/EGP', 'USD/BDT', 'EUR/CAD', 'USD/INR', 'GBP/AUD', 'EUR/GBP']

# Bandera de cada divisa, descrita para que la IA la dibuje correctamente
CURRENCY_FLAGS = {
    'EUR': 'European Union flag (blue with a circle of yellow stars)',
    'USD': 'United States flag (stars and stripes)',
    'GBP': 'United Kingdom flag (Union Jack)',
    'CAD': 'Canada flag (red and white with a red maple leaf)',
    'NZD': 'New Zealand flag (dark blue with the Union Jack and four red stars)',
    'AUD': 'Australia flag (dark blue with the Union Jack and white stars)',
    'EGP': 'Egypt flag (red, white and black horizontal stripes with the golden eagle)',
    'BDT': 'Bangladesh flag (green with a red circle)',
    'INR': 'India flag (saffron, white and green stripes with the blue Ashoka wheel)',
    'JPY': 'Japan flag (white with a red circle)',
    'CHF': 'Switzerland flag (red with a white cross)',
    'BRL': 'Brazil flag (green with a yellow diamond and a blue globe)',
}


def pair_flags(pair: str):
    """Descripción de las dos banderas de un par ('EUR/GBP' -> (UE, Reino Unido)), o None."""
    codes = (pair or '').upper().replace('(OTC)', '').strip().split('/')
    if len(codes) != 2:
        return None
    flags = tuple(CURRENCY_FLAGS.get(c.strip()) for c in codes)
    return flags if all(flags) else None


DURATIONS = ['5 min', '10 min', '15 min', '30 min', '45 min', '1 h', '2 h', '3 h']

# Nombre en inglés de cada día del modelo (el prompt está en inglés)
DAY_NAMES_EN = {
    'Lunes': 'Monday', 'Martes': 'Tuesday', 'Miércoles': 'Wednesday',
    'Jueves': 'Thursday', 'Viernes': 'Friday', 'Sábado': 'Saturday', 'Domingo': 'Sunday',
}


def app_base_dir() -> str:
    return os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.abspath(os.getcwd())


def default_weeks_dir() -> str:
    """Carpeta Weekend-Saved junto al ejecutable (congelado) o en la raíz del proyecto."""
    if getattr(sys, 'frozen', False):
        root = os.path.dirname(sys.executable)
    else:
        root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(root, 'Weekend-Saved')


ENV_PATH = os.path.join(app_base_dir(), '.env')
load_dotenv(ENV_PATH)

REF_IMAGE_RELATIVE = os.path.join('src', 'images', 'ref_image', 'img_ref.png')

DEFAULTS = {
    'image_engine': ENGINE_AI,
    'poll_image_model': 'black-forest-labs/flux.1-kontext-pro',
    'poll_generation_template': DEFAULT_GENERATION_TEMPLATE,
    'image_ref_path': os.path.join(app_base_dir(), REF_IMAGE_RELATIVE),
    # Valores que muestra la imagen de referencia (lo que la IA debe sustituir)
    'ref_asset': 'EUR/USD',
    'ref_duration': '15 min',
    'ref_day': 'Friday',
    'ref_profit': '+$52.20',
    'default_pair': CURRENCY_PAIRS[0],
    'default_duration': '15 min',
    'image_output_dir': os.path.join(app_base_dir(), 'Result-Images'),
    'image_autosave': '1',
    'weeks_dir': '',  # vacío = default_weeks_dir()
    'export_dir': os.path.join(app_base_dir(), 'Exports'),
    'export_format': 'excel',
    'export_charts': '1',
    'export_summary': '1',
    'export_csv_regional': '1',
    'export_open_after': '0',
    'import_dir': '',  # última carpeta usada al importar
    'dark_mode': '1',
    'language': 'es',
    'chart_mode': '3d',
    'chart_animations': '1',
    'legend_visible': '1',
    'show_daily_advice': '1',
    'capital_edit_mode': '0',
}


def format_result(amount: float) -> str:
    """Formatear el resultado como en la tarjeta: +$52.20 / -$12.00"""
    sign = '+' if amount >= 0 else '-'
    return f"{sign}${abs(amount):,.2f}"


def save_api_key(key: str) -> None:
    """Guardar la API key de Pollinations en .env y aplicarla a la sesión actual."""
    key = (key or '').strip()
    if not os.path.exists(ENV_PATH):
        open(ENV_PATH, 'a', encoding='utf-8').close()
    set_key(ENV_PATH, 'POLLINATIONS_API_KEY', key, quote_mode='never')
    os.environ['POLLINATIONS_API_KEY'] = key


class SettingsStore:
    """Acceso tipado a la configuración guardada en la base de datos."""

    def __init__(self, db_manager):
        self.db = db_manager

    def get(self, key: str) -> str:
        value = self.db.get_config(key, None)
        if value is None:
            value = DEFAULTS.get(key, '')
        return value

    def get_bool(self, key: str) -> bool:
        return str(self.get(key)).strip() in ('1', 'true', 'True', 'yes')

    def set(self, key: str, value) -> None:
        if isinstance(value, bool):
            value = '1' if value else '0'
        self.db.set_config(key, str(value))

    def weeks_dir(self) -> str:
        """Carpeta donde se guardan y desde donde se cargan las semanas (JSON)."""
        return (self.get('weeks_dir') or '').strip() or default_weeks_dir()
