# 🚀 W-T-F (Weekend Trading Finance) Trading Manager v3.2

## 📊 Tu asistente personal de trading semanal ( xd solo da consejos )

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-green.svg)](https://www.riverbankcomputing.com/software/pyqt/)
[![Version](https://img.shields.io/badge/Versión-3.2.0-7c5cff.svg)]()
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active%20Development-brightgreen.svg)]()

### 🎯 Gestiona tu rendimiento de trading como un profesional

<img src="https://img.shields.io/badge/Modo%20Oscuro-✅-purple.svg" alt="Dark Mode">
<img src="https://img.shields.io/badge/Gráfico-2D%20%2F%203D-00d4ff.svg" alt="Charts">
<img src="https://img.shields.io/badge/Imagen%20de%20resultado-IA%20%2B%20local-orange.svg" alt="Result image">
<img src="https://img.shields.io/badge/Exporta-Excel%20·%20CSV%20·%20JSON-0f9f6e.svg" alt="Export">
<img src="https://img.shields.io/badge/Idiomas-ES%20·%20EN-blue.svg" alt="i18n">

</div>

---

## 🌟 ¿Qué es W-T-F Trading Manager?

**W-T-F Trading Manager** es una aplicación de escritorio para traders que quieren llevar un control detallado de su semana: resultado de cada día, par de divisas y duración de la sesión, balance, retiro recomendado y capital para la semana siguiente. Si todavía no eres rentable, te ayuda a seguir un plan semanal con disciplina.

### 💡 Pensada para
- 📈 Traders que operan por sesiones (lunes a viernes)
- 🎯 Seguir un plan de retiro (30%) y reinversión
- 📊 Analizar tu rendimiento semana a semana
- 📸 Compartir tus resultados con una imagen profesional
- 🤖 Frases y consejos míos

---

## ✨ Novedades de la versión 3.2

- 📥 **Importar y analizar** (botón *Importar* de la cabecera, `Ctrl+I` o arrastrando archivos a la ventana):
  - Lee **Excel, CSV o JSON**: el historial de operaciones del bróker (p. ej. Quotex: activo, hora, dirección, monto e ingreso), las exportaciones de W-T-F o cualquier tabla con fecha y resultado. El formato se detecta solo.
  - Combina varios archivos sin duplicar operaciones (mismo ID).
  - **Resumen**: resultado neto, promedio diario y por operación, tasa de acierto, profit factor, ganancia/pérdida media, mejor/peor día, máximo drawdown, rachas, monto medio, payout medio y acierto mínimo para no perder.
  - **Gráficos** con tooltips: evolución del balance con drawdown, resultado por día (con línea de promedio), ganadas/perdidas, por hora, por día de la semana, por activo, por dirección y por monto invertido.
  - Tablas **por día**, **por activo** y de **operaciones**, filtros por período y activo, y *Lectura rápida* con conclusiones.
  - **Exportar análisis** a Excel con gráficos y **Cargar en la semana**: escribe el neto de cada día en la semana actual.
- 🧮 **Capital del día rediseñado** (modo edición por capital): parte del balance con el que empezó el día (o del capital semanal), muestra el resultado y el % en vivo y recuerda lo que ya estaba guardado.

## ✨ Novedades de la versión 3.1

- 👋 **Bienvenida en el primer arranque**: establece tu capital inicial con montos rápidos ($50 … $1,000).
- 📊 **Resumen semanal Pro**: balance animado, tasa de acierto, mejor/peor día, promedio diario, desglose por día con barras y plan de retiro/reinversión. Botón para **copiar el resumen** y pegarlo en Telegram o WhatsApp.
- 📤 **Exportación renovada**:
  - Semana actual **o todo el historial** (hoja de historial + detalle con filtros + una hoja por semana).
  - Excel con formato, **fórmulas vivas**, barras de datos y gráficos de resultados y evolución del balance.
  - CSV compatible con **Excel en español** (`;` y coma decimal, acentos correctos).
  - Vista previa real de los datos, destino recordado y botones para abrir el archivo o la carpeta.
  - Corregido: el total y los gráficos de Excel omitían el viernes; el resumen del CSV salía en 0.
- 📁 **Carpeta de semanas configurable** (Configuración → Datos): guarda y carga tus semanas desde donde quieras (p. ej. OneDrive o Google Drive), con opción de copiar las existentes. En "Cargar semana" puedes abrir **otra carpeta** solo esa vez.
- 🚩 **Banderas en la imagen de resultado**: al cambiar de par, la IA también cambia las banderas de la tarjeta.
- 💱 **Nueva lista de pares**: NZD/CAD, USD/EGP, USD/BDT, EUR/CAD, USD/INR, GBP/AUD, EUR/GBP.
- 📖 **Ayuda y Acerca de rediseñados**, con accesos directos a mis redes sociales.

---

## ✨ Características

### 🎨 Interfaz
- 🌓 **Modo oscuro/claro** estilo fintech, aplicado a toda la app (también a los diálogos).
- 🎞️ **Animaciones suaves**: contadores animados, apariciones con desvanecido e interruptores tipo iOS.
- 🌐 **Español e inglés**, cambiables al instante.
- ⚙️ **Configuración central** (Ctrl+,): apariencia, trading, datos, IA e información de ayuda.

### 📅 Registro semanal
- 📝 **Doble clic en el monto** para anotar la ganancia/pérdida del día.
- 💱 **Doble clic en Sesión** para anotar el par y la duración (se muestran en el gráfico).
- 💰 **Modo edición por capital**: escribe el capital inicial y final del día y la app calcula el resultado.
- 🗓️ **Nueva semana automática** los sábados, con el capital actualizado tras el retiro recomendado.
- 💾 **Auto-guardado** en SQLite y copia en JSON en tu carpeta de semanas.

### 📊 Análisis
- 📈 **Gráfico 2D o 3D** (arrástralo para rotarlo en 3D).
- 🧮 **Panel de resumen**: balance, resultado, rendimiento, retiro y reinversión.
- 💡 **Consejo del día** y **análisis** automático de tu semana.
- 📊 **Resumen semanal Pro** con KPIs y plan para la próxima semana.

### ✨ Imagen de resultado (Ctrl+G)
- 🤖 **Motor IA (Pollinations)**: edita tu tarjeta de referencia cambiando solo los valores (par, banderas, duración, día y ganancia) o genera una desde cero.
- 🎯 **Motor local (Pillow)**: dibuja la tarjeta sin conexión con los valores **exactos**.
- 🖼️ Imagen de referencia, modelo, prompt y carpeta de salida configurables.

---

## 📦 Instalación

### 🪟 Opción 1: Instalador para Windows (recomendado)
1. Descarga `WTF-Setup-3.2.0.exe`.
2. Ejecútalo: se instala **solo para tu usuario** (sin permisos de administrador) y se registra en *Configuración → Aplicaciones*.
3. Si ya tenías una versión anterior, el instalador la **actualiza conservando tus datos** (base de datos, semanas, imágenes, exportaciones y API key), con copia de seguridad en `Documentos\W-T-F Backups`.

### 🐍 Opción 2: Desde el código
```bash
# Clonar el repositorio
git clone https://github.com/TechOGR/W-T-F---Weekend-Trading-Finance--.git
cd W-T-F---Weekend-Trading-Finance--

# Instalar dependencias
pip install -r requirements.txt

# ¡Ejecutar!
python main.py
```

### 🔑 API key de Pollinations (opcional, solo para el motor IA)
Crea un archivo `.env` junto a `main.py` (o pégala en *Configuración → IA · Imagen de resultado*):
```env
POLLINATIONS_API_KEY=tu_clave
```
Consigue tu clave en [enter.pollinations.ai/keys](https://enter.pollinations.ai/keys). El archivo `.env` está en `.gitignore`: tu clave nunca se sube al repositorio. El motor local no necesita clave ni conexión.

### 🏗️ Compilar el instalador
```bash
pip install pyinstaller pillow
python buildInstaller.py            # build completo
python buildInstaller.py --skip-app # reutiliza el ejecutable de la app ya compilado
```
Resultado: `InstallerSetup/dist/WTF-Setup-<versión>.exe`. La versión sale de `src/version.py`, la fuente única para la app, el build y el instalador.

---

## 🎯 Guía rápida

1. 🚀 **Abre la app**: la primera vez te pedirá el **capital inicial** de la semana.
2. 📝 **Registra cada día**: doble clic en el monto y en la sesión (par · duración).
3. 📊 **Revisa tu progreso** en el gráfico y el panel de resumen.
4. ✨ **Genera la imagen del día** con Ctrl+G (o clic derecho sobre una fila).
5. 📋 **Consulta el resumen semanal** y exporta tus resultados con Ctrl+E.
6. 📥 **Importa el historial de tu bróker** con Ctrl+I para ver promedios y gráficos de todas tus operaciones.

### ⌨️ Atajos de teclado

| Atajo | Acción |
|-------|--------|
| `Ctrl+S` | Guardar semana |
| `Ctrl+O` | Cargar semana |
| `Ctrl+G` | Imagen de resultado |
| `Ctrl+E` | Exportar (último formato usado) |
| `Ctrl+I` | Importar y analizar Excel/CSV |
| `Ctrl+,` | Configuración |
| `Ctrl+D` | Modo oscuro / claro |

### 📂 Dónde se guardan tus datos

| Dato | Ubicación por defecto |
|------|----------------------|
| Base de datos | `trading_data.db` |
| Semanas (JSON) | `Weekend-Saved/`, configurable en *Configuración → Datos* |
| Exportaciones | `Exports/`, se recuerda la última carpeta usada |
| Imágenes de resultado | `Result-Images/` |
| API key | `.env` |

---

## 🏗️ Arquitectura del proyecto

```
W-T-F ( Weekend Trading Finance )/
│
├── 📁 src/
│   ├── 🏷️ version.py                    # Versión única (app, build e instalador)
│   ├── 📁 models/
│   │   ├── 🤖 ai_analyzer.py            # Análisis automático de la semana
│   │   ├── 📊 trading_model.py          # Modelo base
│   │   └── 💾 trading_model_with_db.py  # Modelo con persistencia en SQLite
│   │
│   ├── 📁 ui/
│   │   ├── 🎞️ animations.py             # Fade-in, brillos, contadores, interruptores
│   │   ├── 💰 capital_dialog.py         # Capital inicial (bienvenida en el primer arranque)
│   │   ├── 🧮 day_capital_dialog.py     # Resultado del día a partir del capital
│   │   ├── 📝 day_details_dialog.py     # Par de divisas y duración de la sesión
│   │   ├── 📈 enhanced_chart_widget.py  # Gráfico 2D/3D
│   │   ├── 📤 export_dialog.py          # Exportación Excel/CSV/JSON con vista previa
│   │   ├── 📥 import_dialog.py          # Importación y análisis con gráficos
│   │   ├── 📖 help_dialogs.py           # Instrucciones y Acerca de (redes sociales)
│   │   ├── 📂 load_week_dialog.py       # Cargar semanas guardadas
│   │   ├── 🧭 main_menu.py              # Menú principal
│   │   ├── ✨ result_image_dialog.py    # Imagen de resultado (IA / local)
│   │   ├── ⚙️ settings_dialog.py        # Configuración central
│   │   ├── 📋 summary_panel.py          # Panel de resumen
│   │   ├── 📊 trading_table.py          # Tabla semanal editable
│   │   └── 📊 weekly_summary_dialog.py  # Resumen semanal Pro
│   │
│   ├── 📁 services/
│   │   ├── 🤖 pollinations_image.py     # API de Pollinations y prompts (incluye banderas)
│   │   └── 🎯 card_renderer.py          # Tarjeta local con Pillow
│   │
│   ├── 📁 database/
│   │   └── 💾 database_manager.py       # SQLite (semanas, detalles y configuración)
│   │
│   ├── 📁 styles/
│   │   └── 🎨 themes.py                 # Temas claro/oscuro por tokens
│   │
│   ├── 📁 images/                       # Logo, redes sociales e imagen de referencia
│   │
│   └── 📁 utils/
│       ├── 💡 advice.py                 # Consejos diarios y resumen semanal
│       ├── 📤 export_manager.py         # Motor de exportación
│       ├── 📥 import_manager.py         # Lectura de Excel/CSV/JSON y estadísticas
│       ├── 🌐 i18n.py                   # Traducciones ES / EN
│       ├── 🖼️ resources.py              # Localización de imágenes
│       └── ⚙️ settings_store.py         # Configuración persistente, pares y banderas
│
├── 🚀 main.py                           # Punto de entrada
├── 📋 requirements.txt                  # Dependencias
└── 📖 README.md                         # Documentación
```

---

## 🔧 Tecnologías

<div align="center">

| Tecnología | Propósito |
|------------|-----------|
| ![Python](https://img.shields.io/badge/Python-3.10%2B-blue) | Lenguaje principal |
| ![PyQt5](https://img.shields.io/badge/PyQt5-5.15-green) | Interfaz gráfica |
| ![Matplotlib](https://img.shields.io/badge/Matplotlib-3.x-orange) | Gráficos 2D/3D |
| ![SQLite](https://img.shields.io/badge/SQLite-Embedded-lightgrey) | Base de datos local |
| ![XlsxWriter](https://img.shields.io/badge/XlsxWriter-3.x-blue) | Exportación a Excel con gráficos |
| ![Pillow](https://img.shields.io/badge/Pillow-9%2B-yellow) | Tarjeta de resultado local |
| ![Pollinations](https://img.shields.io/badge/Pollinations-API-7c5cff) | Imagen de resultado con IA |
| ![PyInstaller](https://img.shields.io/badge/PyInstaller-6.x-informational) | Ejecutable e instalador |

</div>

---

## 🛡️ Privacidad

- 🔒 **Datos locales**: tus semanas y tu base de datos se quedan en tu computadora.
- 🌐 **Única conexión opcional**: el motor IA envía a Pollinations la imagen de referencia y los valores de la tarjeta. El motor local funciona 100% offline.
- 🔑 **API key fuera del código**: vive en `.env`, que no se sube al repositorio.
- 💾 **Copias de seguridad** automáticas al actualizar o desinstalar.

---

## 🚀 Roadmap

- [ ] 🏦 **Múltiples cuentas**: gestiona varios portafolios
- [ ] 🔔 **Notificaciones**: recordatorios de sesión y cierre de semana
- [ ] 📱 **App móvil**: sincronización con el escritorio
- [ ] 🌍 **Más idiomas**

---

## 🤝 Contribuir

1. **🍴 Haz fork** del proyecto
2. **🌿 Crea una rama** (`git checkout -b feature/AmazingFeature`)
3. **💾 Haz commit** (`git commit -m 'Add some AmazingFeature'`)
4. **🚀 Haz push** (`git push origin feature/AmazingFeature`)
5. **📋 Abre un Pull Request**

Son bienvenidos los reportes de bugs, las ideas, las mejoras de UI/UX, la documentación y las traducciones.

---

## 📞 Soporte y comunidad

- 📖 **Ayuda dentro de la app**: *Configuración → Ayuda* o menú *Ayuda → Instrucciones*.
- 💬 **Redes sociales**: [Telegram](https://t.me/onel_crack) · [YouTube](https://www.youtube.com/@OnelCrack) · [Instagram](https://www.instagram.com/onel_crack) · [Facebook](https://www.facebook.com/profile.php?id=61570586445561) · [GitHub](https://github.com/TechOGR)

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Consulta el archivo [LICENSE](LICENSE) para más detalles.

---

<div align="center">

### 🌟 **¿Te ha sido útil este proyecto?**

[![GitHub Stars](https://img.shields.io/github/stars/TechOGR/W-T-F---Weekend-Trading-Finance--?style=social)](https://github.com/TechOGR/W-T-F---Weekend-Trading-Finance--)

**¡Dale una estrella ⭐ si te ha gustado!**

---

**Desarrollado con ❤️ por Onel Crack**

*"Gestiona tu trading como un profesional, sin complicaciones"*

</div>
