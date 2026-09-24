"""
Localización de imágenes de la aplicación (logo e iconos de redes sociales).
Busca junto al ejecutable (build congelado) o en el directorio de trabajo,
y como respaldo dentro del propio paquete `src`.
"""

import os
import sys

_SRC_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _images_dirs():
    base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.abspath(os.getcwd())
    return [os.path.join(base_dir, 'src', 'images'), os.path.join(_SRC_DIR, 'images')]


def image_path(*parts):
    """Ruta absoluta de una imagen dentro de src/images, o None si no existe."""
    for images_dir in _images_dirs():
        path = os.path.join(images_dir, *parts)
        if os.path.isfile(path):
            return path
    return None


def logo_path():
    return image_path('logo.png')


def social_icon_path(name):
    """Icono de una red social en src/images/socials (png, svg, jpg o ico)."""
    for ext in ('png', 'svg', 'jpg', 'ico'):
        path = image_path('socials', f"{name}.{ext}")
        if path:
            return path
    return None
