"""
Generación y edición de tarjetas de resultado con la API de Pollinations.

Documentación: https://github.com/pollinations/pollinations/blob/main/APIDOCS.md

- Edición (hay imagen de referencia):
    POST {BASE}/v1/images/edits   multipart/form-data
         image=<archivo local>, prompt, model, n, response_format
- Generación desde cero (no hay referencia):
    POST {BASE}/v1/images/generations   JSON {prompt, model, n, size, response_format}
- Autenticación: cabecera  Authorization: Bearer <POLLINATIONS_API_KEY>
- Respuesta: {"data": [{"b64_json": "..."} | {"url": "https://media.pollinations.ai/..."}]}

La clave se lee de la variable de entorno POLLINATIONS_API_KEY (cargada desde .env).
Nunca se escribe en el código ni en los registros.
"""

import base64
import logging
import mimetypes
import os

import requests
from PyQt5.QtCore import QThread, pyqtSignal

from src.utils.settings_store import pair_flags

log = logging.getLogger('wtf.pollinations')

POLLINATIONS_BASE_URL = 'https://gen.pollinations.ai'
POLLINATIONS_IMAGE_MODEL = 'black-forest-labs/flux.1-kontext-pro'
API_KEY_ENV = 'POLLINATIONS_API_KEY'
KEYS_URL = 'https://enter.pollinations.ai/keys'
IMAGES_PER_REQUEST = 1  # la API admite como máximo 1 imagen por petición

EDIT_MODELS = [
    'black-forest-labs/flux.1-kontext-pro',
    'black-forest-labs/flux.2-klein-4b',
    'google/gemini-2.5-flash-image',
    'prunaai/p-image-edit',
]


class PollinationsError(Exception):
    """Error con un mensaje apto para mostrar al usuario."""


# ------------------------------------------------------------------ prompts
def _q(text):
    return f'"{text}"'


def build_edit_prompt(original: dict, new: dict) -> str:
    """Prompt de edición que pide cambiar SOLO los campos que realmente cambian.

    original / new: dicts con las claves asset, duration, day, profit.
    """
    changes = []
    flags_change = ''
    if new['asset'] != original['asset']:
        changes.append(f"Change ONLY the asset text from {_q(original['asset'])} to {_q(new['asset'])}.\n"
                       f"Keep the label \"Asset\" exactly unchanged.")
        flags_change = _flags_instruction(original['asset'], new['asset'])
        if flags_change:
            changes.append(flags_change)
    if new['duration'] != original['duration']:
        changes.append(f"Change ONLY the duration value from {_q(original['duration'])} to {_q(new['duration'])}.\n"
                       f"Keep the label \"Duration\" exactly unchanged.")
    if new['day'] != original['day']:
        changes.append(f"Change ONLY the day value from {_q(original['day'])} to {_q(new['day'])}.\n"
                       f"Keep the label \"Day\" exactly unchanged.")
    if new['profit'] != original['profit']:
        changes.append(f"Change ONLY the total profit value from {_q(original['profit'])} to {_q(new['profit'])}.\n"
                       f"Keep the label \"TOTAL PROFIT\" exactly unchanged.")
    if not changes:
        return ''
    count = {1: 'one requested value', 2: 'two requested values', 3: 'three requested values'}.get(
        len(changes), f'{len(changes)} requested values')
    icons = '- the other icons (only the flag icons change)' if flags_change else '- icons'
    return (
        "Edit the provided trading card image.\n\n"
        + "\n\n".join(changes)
        + "\n\nWrite every new value exactly as given, character by character.\n\n"
        "Preserve the original image composition exactly.\n"
        "Do not redesign or regenerate the card.\n\n"
        "Keep unchanged:\n"
        "- QUOTEX logo\n- card dimensions and position\n- glassmorphism panel\n- dark background\n"
        f"- candlestick chart background\n{icons}\n- typography style\n- font sizes\n- spacing\n"
        "- borders\n- shadows\n- neon green glow\n- colors\n- lighting\n- reflections\n"
        "- all other text and visual elements\n\n"
        f"Only modify the {count}.\n\n"
        "The final image must look like the original reference image, with only those values changed."
    )


def _flags_instruction(old_pair: str, new_pair: str) -> str:
    """Instrucción para cambiar las dos banderas circulares de la esquina superior izquierda."""
    new_flags = pair_flags(new_pair)
    if not new_flags or new_flags == pair_flags(old_pair):
        return ''
    old_flags = pair_flags(old_pair)
    current = (f" (currently the {old_flags[0]} on the left, behind, and the {old_flags[1]} on the right, in front)"
               if old_flags else '')
    return (f"Replace the two overlapping circular flag icons in the top-left corner of the card{current} "
            f"with the {new_flags[0]} on the left (behind) and the {new_flags[1]} on the right (in front).\n"
            "Keep the same circular shape, size, position, overlap and lighting of the flag icons.")


def _flags_text(pair: str) -> str:
    flags = pair_flags(pair)
    return f"the {flags[0]} and the {flags[1]}" if flags else f"the flags of the {pair} currencies"


# Frase fija de las plantillas guardadas antes de existir {flags}
_LEGACY_FLAGS_TEXT = 'the European Union and USA flags'


def build_generation_prompt(template: str, values: dict) -> str:
    """Rellenar la plantilla de generación desde cero con los valores dinámicos."""
    flags = _flags_text(values['asset'])
    prompt = template.replace('{flags}', flags).replace(_LEGACY_FLAGS_TEXT, flags)
    for key in ('asset', 'duration', 'day', 'profit'):
        prompt = prompt.replace('{' + key + '}', values[key])
    return prompt


# -------------------------------------------------------------- utilidades
def get_api_key() -> str:
    key = (os.environ.get(API_KEY_ENV) or '').strip()
    if not key:
        raise PollinationsError(f'Falta la API key de Pollinations. Define {API_KEY_ENV} en el archivo .env.')
    return key


def _masked(key: str) -> str:
    return f"{key[:3]}…{key[-4:]}" if len(key) > 10 else '***'


def _raise_for_error(resp: requests.Response, model: str = ''):
    if resp.ok:
        return
    try:
        body = resp.json()
        err = body.get('error', body)
        message = err.get('message') if isinstance(err, dict) else str(err)
    except ValueError:
        message = resp.text
    message = (message or '').strip()[:400]
    log.error('Pollinations HTTP %s (%s): %s', resp.status_code, resp.request.url if resp.request else '', message)
    status = resp.status_code
    retry = resp.headers.get('Retry-After')
    if status == 401:
        raise PollinationsError('API key de Pollinations inválida o caducada (401).')
    if status == 402:
        raise PollinationsError('Sin saldo de Pollen en la cuenta o en esta clave (402). '
                                f'Revisa tu saldo en {KEYS_URL}.')
    if status == 403:
        raise PollinationsError(f'La clave no tiene permiso para usar este recurso o modelo (403). {message}')
    if status == 404 or (status == 400 and 'model' in message.lower()):
        raise PollinationsError(f'Modelo no disponible: {model or "?"}. {message}')
    if status == 429:
        raise PollinationsError('Demasiadas peticiones (429).'
                                + (f' Espera {retry} s y vuelve a intentarlo.' if retry else ' Espera un momento.'))
    if status in (502, 503):
        raise PollinationsError(f'El proveedor del modelo no está disponible ahora mismo ({status}).'
                                + (f' Reintenta en {retry} s.' if retry else ' Reintenta en unos segundos.'))
    if status >= 500:
        raise PollinationsError(f'Error interno de Pollinations ({status}). {message}')
    raise PollinationsError(f'Error de Pollinations ({status}): {message}')


def _extract_image(resp_json: dict, timeout: int):
    """Obtener los bytes de la imagen de la respuesta (b64_json o url)."""
    items = resp_json.get('data') or []
    if not items:
        log.error('Respuesta sin imagen: %s', str(resp_json)[:300])
        raise PollinationsError('Pollinations no devolvió ninguna imagen (posible filtro de seguridad).')
    item = items[0]
    if item.get('b64_json'):
        return base64.b64decode(item['b64_json'])
    if item.get('url'):
        try:
            img = requests.get(item['url'], timeout=timeout)
            img.raise_for_status()
        except requests.RequestException as e:
            log.error('Error al descargar la imagen %s: %s', item['url'], e)
            raise PollinationsError(f'No se pudo descargar la imagen generada: {e}')
        return img.content
    raise PollinationsError('La respuesta de Pollinations no contiene datos de imagen.')


def _mime_of(data: bytes) -> str:
    if data[:8] == b'\x89PNG\r\n\x1a\n':
        return 'image/png'
    if data[:3] == b'\xff\xd8\xff':
        return 'image/jpeg'
    if data[:4] == b'RIFF' and data[8:12] == b'WEBP':
        return 'image/webp'
    return 'image/png'


# ------------------------------------------------------------ operaciones
def edit_trading_card(ref_image_path: str, prompt: str, model: str = POLLINATIONS_IMAGE_MODEL,
                      timeout: int = 180):
    """Editar la tarjeta de referencia. Devuelve (bytes, mime)."""
    key = get_api_key()
    if not os.path.isfile(ref_image_path):
        raise PollinationsError(f'No se encontró la imagen de referencia:\n{ref_image_path}')
    if not prompt:
        raise PollinationsError('No hay cambios que aplicar: los valores coinciden con la imagen de referencia.')
    mime = mimetypes.guess_type(ref_image_path)[0] or 'image/png'
    log.info('Editando tarjeta con %s (clave %s)', model, _masked(key))
    with open(ref_image_path, 'rb') as f:
        resp = requests.post(
            f'{POLLINATIONS_BASE_URL}/v1/images/edits',
            headers={'Authorization': f'Bearer {key}'},
            files={'image': (os.path.basename(ref_image_path), f, mime)},
            data={'prompt': prompt, 'model': model, 'n': str(IMAGES_PER_REQUEST), 'response_format': 'b64_json'},
            timeout=timeout,
        )
    _raise_for_error(resp, model)
    data = _extract_image(resp.json(), timeout)
    return data, _mime_of(data)


def generate_trading_card(prompt: str, model: str = POLLINATIONS_IMAGE_MODEL, size: str = '768x1344',
                          timeout: int = 180):
    """Generar una tarjeta desde cero. Devuelve (bytes, mime)."""
    key = get_api_key()
    log.info('Generando tarjeta desde cero con %s (clave %s)', model, _masked(key))
    resp = requests.post(
        f'{POLLINATIONS_BASE_URL}/v1/images/generations',
        headers={'Authorization': f'Bearer {key}'},
        json={'prompt': prompt, 'model': model, 'n': IMAGES_PER_REQUEST, 'size': size,
              'response_format': 'b64_json'},
        timeout=timeout,
    )
    _raise_for_error(resp, model)
    data = _extract_image(resp.json(), timeout)
    return data, _mime_of(data)


def check_api_key(key: str = None, timeout: int = 20) -> str:
    """Validar la clave. Devuelve un texto descriptivo (con saldo si está disponible)."""
    key = (key or '').strip() or get_api_key()
    resp = requests.get(f'{POLLINATIONS_BASE_URL}/account/balance',
                        headers={'Authorization': f'Bearer {key}'}, timeout=timeout)
    if resp.status_code == 401:
        raise PollinationsError('API key inválida (401).')
    if resp.status_code == 403:
        return 'Clave válida (sin permiso para consultar el saldo)'
    _raise_for_error(resp)
    balance = resp.json().get('balance')
    return f'Clave válida · saldo {balance} pollen' if balance is not None else 'Clave válida'


class ApiWorker(QThread):
    """Ejecuta una llamada bloqueante fuera del hilo de la interfaz."""

    succeeded = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self._fn, self._args, self._kwargs = fn, args, kwargs

    def run(self):
        try:
            self.succeeded.emit(self._fn(*self._args, **self._kwargs))
        except requests.exceptions.Timeout:
            log.error('Timeout al contactar con Pollinations')
            self.failed.emit('Tiempo de espera agotado con Pollinations. Reintenta: la API reutiliza '
                             'la generación en curso si repites la misma petición.')
        except requests.exceptions.ConnectionError as e:
            log.error('Error de conexión con Pollinations: %s', e)
            self.failed.emit('No hay conexión con Pollinations. Revisa tu internet.')
        except PollinationsError as e:
            self.failed.emit(str(e))
        except Exception as e:
            log.exception('Error inesperado en la generación de imagen')
            self.failed.emit(f'Error inesperado: {e}')
