# 🚀 W-T-F (Weekend Trading Finance) Trading Manager v2.0

## 📊 Tu Asistente Personal de Trading Semanal con Inteligencia Artificial ( xd solo da consejos )

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/)
[![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-green.svg)](https://www.riverbankcomputing.com/software/pyqt/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active%20Development-brightgreen.svg)]()

### 🎯 Gestiona tu rendimiento de trading como un profesional

<img src="https://img.shields.io/badge/Modo%20Oscuro-✅%20Implementado-purple.svg" alt="Dark Mode">
<img src="https://img.shields.io/badge/Análisis%20AI-✅%20Integrado-orange.svg" alt="AI Analysis">
<img src="https://img.shields.io/badge/Base%20de%20Datos-SQLite-blue.svg" alt="SQLite">

</div>

---

## 🌟 ¿Qué es W-T-F Trading Manager?

**W-T-F Trading Manager** es una aplicación de escritorio profesional diseñada para traders que quieren llevar un control detallado de su rendimiento semanal. Con una interfaz moderna y análisis impulsado por inteligencia artificial, esta herramienta te ayudará si no eres aún rentable en el trading, a seguir un plan de trading semanal para mejorar tu rendimiento.

### 💡 La solución perfecta para:
- 📈 Traders de fin de semana
- 📊 Gestión de portafolios personales
- 🎯 Análisis de rendimiento semanal
- 🤖 Frases y consejos míos
- 📱 Control desde tu escritorio

---

## ✨ Características Destacadas

### 🎨 Interfaz de Usuario Premium
- **🌓 Modo Oscuro/Claro**: Cambio dinámico con estilos elegantes
- **📱 Diseño Responsivo**: Adaptable a diferentes tamaños de pantalla
- **🎯 Interfaz Intuitiva**: Fácil de usar desde el primer momento
- **⚡ Rendimiento Optimizado**: Fluido y rápido en todas las operaciones

### 📊 Gestión de Datos Avanzada
- **📅 Control Semanal**: Registro diario con destino inteligente
- **💰 Retiros Personales**: Gestión de ganancias personales
- **🔄 Reinversión Automática**: Optimización de capital
- **💾 Auto-guardado**: Nunca pierdas tus datos

### 🤖 Inteligencia Artificial Integrada
- **📈 Análisis de Rendimiento**: Evaluación automática semanal
- **💡 Recomendaciones Personalizadas**: Consejos basados en tus datos
- **⚠️ Evaluación de Riesgos**: Alertas inteligentes
- **🎯 Insights de Mercado**: Patrones y tendencias detectadas

### 📊 Visualizaciones Profesionales
- **📊 Gráficos Interactivos**: Barras dinámicas con colores inteligentes
- **📈 Tendencias Claras**: Visualización de patrones semanales
- **🎨 Colores Adaptativos**: Prioridad de pérdidas/ganancias sobre tipos de día
- **📱 Responsive Charts**: Se adaptan al tema seleccionado

---

## 🚀 Demo Visual

<div align="center">

### 🌓 Modo Oscuro Elegante
![Dark Mode Preview](https://via.placeholder.com/800x400/1e1e1e/e0e0e0?text=Modo+Oscuro+Premium)

### ☀️ Modo Claro Profesional
![Light Mode Preview](https://via.placeholder.com/800x400/f8f9fa/2c3e50?text=Modo+Claro+Profesional)

### 📊 Panel de Análisis AI
![AI Analysis](https://via.placeholder.com/800x400/ffffff/3498db?text=Análisis+AI+Inteligente)

</div>

---

## 📦 Instalación Rápida

### ⚡ Método 1: Instalación Express (Recomendado)
```bash
# Clonar el repositorio
git clone https://github.com/TechOGR/WTF_WeekendTradingFinance.git

# Entrar al directorio
cd WTF_WeekendTradingFinance

# Instalar dependencias automáticamente
pip install -r requirements.txt

# ¡Ejecutar!
python main.py
```

### 🔧 Método 2: Instalación Manual
```bash
# Instalar dependencias individuales
pip install PyQt5==5.15.9
pip install matplotlib==3.7.1
pip install pandas==2.0.3
pip install numpy==1.24.3

# Ejecutar
python main.py
```

---

## 🎯 Guía de Uso Rápida

### 📅 Primeros Pasos
1. **🚀 Inicia la aplicación**: `python main.py`
2. **💰 Establece tu capital inicial**: `Archivo → Establecer Capital Inicial`
3. **📝 Registra tus operaciones diarias**: Haz clic en cualquier celda
4. **🎯 Selecciona el destino**: Retiro Personal o Reinversión

### 📊 Análisis en Tiempo Real
- **📈 Gráfico dinámico**: Se actualiza automáticamente
- **📊 Estadísticas claras**: Panel derecho con métricas clave
- **🤖 Consejo del día**: Recomendaciones diarias personalizadas
- **📋 Resumen semanal**: Análisis completo cada semana

### 📤 Exportación Profesional
- **📊 Excel (.xlsx)**: Con gráficos y formato profesional
- **📋 CSV**: Datos sin procesar para análisis externo
- **📄 JSON**: Formato estructurado para integraciones
- **🎨 Estilos adaptativos**: Se ajustan al tema actual

### 🎨 Personalización
- **🌓 Cambiar tema**: `Vista → Modo Oscuro` (Ctrl+T)
- **💾 Guardar datos**: `Archivo → Guardar Semana` (Ctrl+S)
- **📂 Cargar semana**: `Archivo → Cargar Semana` (Ctrl+O)
- **🔄 Actualizar BD**: `Archivo → Cargar desde Base de Datos`

### 📤 Exportación de Datos
- **📊 Exportar Excel**: `Exportar → Excel` (Ctrl+E)
- **📋 Exportar CSV**: `Exportar → CSV` (Ctrl+Shift+C)
- **📄 Exportar JSON**: `Exportar → JSON` (Ctrl+Shift+J)
- **📈 Incluye gráficos**: Los archivos Excel incluyen gráficos profesionales

---

## 🏗️ Arquitectura del Proyecto

```
W-T-F ( Weekend Trading Finance )/
│
├── 📁 src/                             # Código fuente principal
│   ├── 📁 models/                      # Modelos de datos y lógica
│   │   ├── 🤖 ai_analyzer.py           # Motor de análisis AI
│   │   ├── 📊 trading_model.py         # Modelo base de trading
│   │   └── 💾 trading_model_with_db.py # Modelo con persistencia en SQLite
│   │
│   ├── 📁 ui/                          # Interfaz de usuario (PyQt5)
│   │   ├── 💰 capital_dialog.py        # Diálogo para capital inicial/edición
│   │   ├── 📈 chart_widget.py          # Widget de gráfico
│   │   ├── 📅 day_capital_dialog.py    # Diálogo de edición por día
│   │   ├── 🎨 enhanced_chart_widget.py # Gráficos interactivos mejorados
│   │   ├── 📤 export_dialog.py         # Diálogo de exportación
│   │   ├── 📂 load_week_dialog.py      # Diálogo para cargar semanas guardadas
│   │   ├── 🧭 main_menu.py             # Barra de menú principal (modo claro/oscuro)
│   │   ├── 📋 summary_panel.py         # Panel de resumen semanal
│   │   └── 📊 trading_table.py         # Tabla editable de operaciones
│   │
│   ├── 📁 database/                    # Persistencia de datos
│   │   └── 💾 database_manager.py      # Administrador de SQLite
│   │
│   ├── 📁 styles/                      # Temas y estilos
│   │   └── 🎨 themes.py                # Gestor de temas (claro/oscuro)
│   │
│   ├── 📁 images/                      # Recursos gráficos
│   │   └── 🔗 socials/                 # Iconos de redes sociales (Acerca de)
│   │
│   └── 📁 utils/                       # Utilidades
│       ├── 💡 advice.py                # Generador de consejos diarios
│       ├── 📤 export_manager.py        # Sistema de exportación (Excel/CSV/JSON)
│       └── 🌐 i18n.py                  # Internacionalización y textos
│
├── 📁 scripts/                         # Scripts auxiliares
├── 📁 Weekend-Saved/                   # Semanas guardadas
├── 🚀 main.py                          # Punto de entrada principal
├── 📋 requirements.txt                 # Dependencias del proyecto
├── 🧹 .gitignore                        # Reglas de exclusión Git
└── 📖 README.md                        # Documentación
```

---

## 🔧 Tecnologías Utilizadas

<div align="center">

| Tecnología | Versión | Propósito |
|------------|---------|-----------|
| ![Python](https://img.shields.io/badge/Python-3.7%2B-blue) | 3.7+ | Lenguaje principal |
| ![PyQt5](https://img.shields.io/badge/PyQt5-5.15.9-green) | 5.15.9 | Interfaz gráfica |
| ![Matplotlib](https://img.shields.io/badge/Matplotlib-3.7.1-orange) | 3.7.1 | Visualizaciones |
| ![Pandas](https://img.shields.io/badge/Pandas-2.0.3-red) | 2.0.3 | Procesamiento de datos |
| ![NumPy](https://img.shields.io/badge/NumPy-1.24.3-yellow) | 1.24.3 | Cálculos numéricos |
| ![SQLite](https://img.shields.io/badge/SQLite-Embedded-lightgrey) | Embedded | Base de datos local |
| ![OpenPyXL](https://img.shields.io/badge/OpenPyXL-3.1.2-green) | 3.1.2 | Exportación Excel |
| ![XlsxWriter](https://img.shields.io/badge/XlsxWriter-3.1.9-blue) | 3.1.9 | Formato Excel avanzado |

</div>

---

## 🌟 Características Avanzadas

### 🎨 Sistema de Temas Inteligente
- **🔄 Cambio dinámico**: Sin reiniciar la aplicación
- **🎯 Colores adaptativos**: Se ajustan al contenido
- **♿ Accesibilidad**: Alto contraste para mejor legibilidad
- **🌈 Paletas coherentes**: Todos los componentes se actualizan

### 📊 Lógica de Colores Inteligente
- **🔴 Rojo**: Pérdidas (prioridad máxima)
- **🟢 Verde**: Ganancias normales
- **🟡 Amarillo**: Retiros personales con ganancias
- **⚪ Gris**: Días no operativos
- **🎯 Prioridad**: Pérdidas siempre visibles en rojo

### 🤖 Motor de Análisis AI
- **📈 Patrones de trading**: Detecta tendencias automáticamente
- **💡 Recomendaciones personalizadas**: Basadas en tu historial
- **⚠️ Alertas de riesgo**: Prevención de pérdidas
- **🎯 Metas semanales**: Sugerencias realistas

---

## 🛡️ Seguridad y Confianza

- **🔒 Datos locales**: Tu información nunca sale de tu computadora
- **💾 Auto-respaldado**: Múltiples capas de protección
- **🔧 Código abierto**: Transparencia total
- **📊 Sin conexión externa**: Funciona 100% offline

---

## 🚀 Próximas Características (Roadmap 2026)

### 🔮 Versión 2.3 - En Planificación
- [ ] 🏦 **Múltiples cuentas**: Gestiona varios portafolios
- [ ] 🔔 **Notificaciones inteligentes**: Alertas personalizadas
- [ ] 🌐 **Modo web**: Acceso desde cualquier dispositivo
- [ ] 📱 **App móvil**: Sincronización con escritorio
- [ ] 🌍 **Multi-idioma**: Soporte para más idiomas

---

## 🤝 Contribuir al Proyecto

¡Tu ayuda hace la diferencia! 🌟

### 🎯 Cómo Contribuir
1. **🍴 Fork** el proyecto
2. **🌿 Crea** una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. **💾 Commit** tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. **🚀 Push** a la rama (`git push origin feature/AmazingFeature`)
5. **📋 Abre** un Pull Request

### 🏷️ Tipos de Contribuciones Bienvenidas
- 🐛 **Reportar bugs**: Ayúdame a mejorar
- 💡 **Sugerir features**: Tu idea puede ser la próxima gran función
- 🎨 **Mejorar UI/UX**: Házlo más hermoso y usable
- 📖 **Documentación**: Mejora esta guía
- 🌍 **Traducciones**: Llévalo a más personas

---

## 📞 Soporte y Comunidad

### 💬 ¿Necesitas Ayuda?
- 📖 **Lee este README**: La respuesta puede estar aquí
- 📧 **Contacto directo**: **Redes Sociales**

### 🌟 Apoya el Proyecto
- ⭐ **Da una estrella**: Si te gusta el proyecto
- 🍴 **Haz fork**: Para tu propio uso
- 📤 **Comparte**: Con otros traders

---

## 📄 Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

### 📋 Resumen de la Licencia
- ✅ **Uso comercial**: Puedes usarlo para tu negocio
- ✅ **Modificación**: Puedes personalizarlo a tu gusto
- ✅ **Distribución**: Puedes compartirlo con otros
- ✅ **Privacidad**: Tu información es tuya

---

## 🙏 Agradecimientos

### 💖 Contribuidores Especiales
Gracias a todos los que han contribuido a hacer este proyecto mejor:

- 🌟 **Tú**: Por usar y apoyar el proyecto
- 🤝 **Comunidad**: Por los reportes y sugerencias
- 📊 **Traders**: Por compartir sus necesidades

### 🛠️ Tecnologías que Hacen Esto Posible
- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) - Framework GUI
- [Matplotlib](https://matplotlib.org/) - Visualizaciones
- [Pandas](https://pandas.pydata.org/) - Análisis de datos
- [Python](https://www.python.org/) - Lenguaje principal

---

<div align="center">

### 🌟 **¿Te ha sido útil este proyecto?**

[![GitHub Stars](https://img.shields.io/github/stars/TechOGR/W-T-F-Trading-Manager?style=social)](https://github.com/TechOGR/W-T-F-Trading-Manager)

**¡Dale una estrella ⭐ si te ha gustado!**

### 🚀 **Comparte con otros traders**

[![Twitter](https://img.shields.io/twitter/url?style=social&url=https%3A%2F%2Fgithub.com%2Ftu-usuario%2FW-T-F-Trading-Manager)](https://twitter.com/intent/tweet?text=Check%20out%20this%20amazing%20trading%20manager!&url=https://github.com/tu-usuario/W-T-F-Trading-Manager)
[![LinkedIn](https://img.shields.io/badge/Share-LinkedIn-blue?style=flat-square&logo=linkedin)](https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/tu-usuario/W-T-F-Trading-Manager)

---

**Desarrollado con ❤️ por OnelCrack Trading**

*"Gestiona tu trading como un profesional, sin complicaciones"*

</div>
