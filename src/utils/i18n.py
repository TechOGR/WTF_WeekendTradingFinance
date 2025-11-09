"""
Módulo de internacionalización (i18n) para W-T-F Trading Manager.
Traducciones completas de todos los textos de la interfaz.
"""

# Diccionario de traducciones
TRANSLATIONS = {
    "es": {
        # Títulos de ventanas
        "app_title": "W-T-F (Weekend Trading Finance) Trading Manager v2.2",
        "capital_dialog_title": "Establecer Capital Inicial",
        "export_dialog_title": "Exportar Datos",
        "about_title": "Acerca de W-T-F Trading Manager",
        "instructions_title": "Instrucciones de Uso",
        "save_week_title": "Guardar Semana",
        "load_week_title": "Cargar Semana",
        
        # Menú principal
        "menu_file": "📁 Archivo",
        "menu_view": "👁️ Vista",
        "menu_assistant": "🧭 Asistente",
        "menu_export": "📊 Exportar",
        "menu_help": "❓ Ayuda",
        "menu_language": "🌍 Idioma",
        
        # Acciones de menú
        "save_week": "💾 Guardar Semana",
        "load_week": "📂 Cargar Semana",
        "load_from_db": "🗄️ Cargar desde Base de Datos",
        "set_capital": "💰 Establecer Capital Inicial",
        "exit": "🚪 Salir",
        "dark_mode": "🌙 Modo Oscuro",
        "toggle_legend": "👁️ Mostrar leyenda",
        "daily_advice": "📌 Mostrar consejo del día",
        "weekly_summary": "🗓️ Resumen semanal",
        "start_new_week_reset": "🆕 Empezar nueva semana (reiniciar datos)",
        "export_excel": "📈 Exportar a Excel",
        "export_csv": "📋 Exportar a CSV",
        "export_json": "📄 Exportar a JSON",
        "about": "ℹ️ Acerca de",
        "instructions": "📖 Instrucciones",
        "capital_edit_mode": "💹 Modo edición por capital",
        
        # Descripciones (StatusTip) del menú
        "status_save_week": "Guardar datos de la semana actual",
        "status_load_week": "Cargar datos desde archivo",
        "status_load_db": "Cargar datos guardados en la base de datos",
        "status_set_capital": "Configurar el capital inicial de la semana",
        "status_exit": "Salir de la aplicación",
        "status_dark_mode": "Activar/desactivar modo oscuro",
        "status_toggle_legend": "Mostrar u ocultar la leyenda del gráfico",
        "status_daily_advice": "Ver recomendaciones según el día actual",
        "status_weekly_summary": "Mostrar resumen con sugerencia de retiro y reinversión",
        "status_start_new_week_reset": "Crear semana nueva con datos en cero y capital actualizado",
        "status_export_excel": "Exportar datos a formato Excel (.xlsx)",
        "status_export_csv": "Exportar datos a formato CSV",
        "status_export_json": "Exportar datos a formato JSON",
        "status_about": "Información sobre la aplicación",
        "status_instructions": "Ver instrucciones de uso",
        "status_capital_edit_mode": "Editar el monto por capital inicial/actual",
        
        # Idiomas
        "spanish": "Español",
        "english": "English",
        
        # Botones y etiquetas generales
        "accept": "Aceptar",
        "cancel": "Cancelar",
        "save": "Guardar",
        "close": "Cerrar",
        "yes": "Sí",
        "no": "No",
        
        # Diálogo de capital
        "capital_label": "Capital Inicial:",
        "capital_tooltip": "Ingrese el capital inicial para la semana",
        "capital_placeholder": "Ej: 100.00",
        "day_capital_dialog_title": "Ingresar capital del día",
        "initial_capital": "Capital inicial",
        "current_capital": "Capital actual",
        
        # Tabla de trading
        "day_column": "Día",
        "type_column": "Tipo",
        "comments_column": "Comentarios",
        "amount_column": "Monto",
        "destination_column": "Destino",
        "profit_loss_column": "G/P",
        "profit_loss_pct_column": "G/P %",
        
        # Destinos
        "personal_withdrawal": "Retiro Personal",
        "reinvestment": "Reinversion",
        "not_operated": "No Operado",
        
        # Panel de resumen
        "weekly_summary_panel": "📊 Resumen Semanal",
        "total_week": "Total Semana:",
        "performance": "Rendimiento:",
        "ai_advice": "💡 Consejo AI",
        "daily_advice_title": "Consejo del día",
        "days_label": "Días: +{positive} / -{negative}",
        "capital_initial": "Capital Inicial:",
        "current_balance": "Saldo Actual:",
        "total_profit_loss": "Ganancia/Pérdida Total:",
        "profit_loss_percentage": "Porcentaje G/P:",
        
        # Gráfico
        "weekly_chart_title": "📊 Gráfico de Rendimiento Semanal",
        "profit_loss_chart": "Gráfico de Ganancias/Pérdidas",
        "daily_performance_title": "Rendimiento Diario de Trading",
        "weekly_performance_title": "Rendimiento Semanal de Trading",
        "days_of_week_label": "Días de la Semana",
        "amount_axis_label": "Monto ($)",
        "profit_loss_axis_label": "Ganancia/Pérdida ($)",
        "average_label": "Promedio:",
        "legend_gain": "Ganancia",
        "legend_loss": "Pérdida",
        "legend_neutral": "Neutro",
        "legend_gain_withdrawal": "Ganancia (Retiro)",
        "legend_gain_reinvestment": "Ganancia (Reinversión)",
        "chart_error_update": "Error al actualizar el gráfico",
        "chart_error_load": "Error al cargar gráfico",
        
        # Exportación
        "export_success": "Exportación exitosa",
        "export_error": "Error al exportar",
        "export_completed": "Los datos se han exportado correctamente",
        "export_failed": "No se pudieron exportar los datos",
        "export_save_title": "Guardar archivo de exportación",
        "selected_file": "Archivo seleccionado",
        "starting_export": "Iniciando exportación...",
        "open_file_location_question": "¿Deseas abrir la ubicación del archivo?",
        "no_data_to_export": "No hay datos para exportar",
        "format_label": "Formato:",
        "format_excel_recommended": "Excel (.xlsx) - Recomendado",
        "format_csv_compatible": "CSV (.csv) - Compatible con todos",
        "format_json_developers": "JSON (.json) - Para desarrolladores",
        "include_charts_excel": "Incluir gráficos en Excel (si es posible)",
        "include_detailed_summary": "Incluir resumen detallado",
        "preview_title": "👁️ Vista Previa",
        "select_file": "Seleccionar archivo",
        
        # Mensajes generales
        "initial_data_loaded_db": "Datos iniciales cargados desde base de datos",
        "no_previous_data_new_week": "No hay datos previos, comenzando con semana nueva",
        "confirm_close_title": "Confirmar cierre",
        "close_anyway_question": "¿Desea cerrar de todos modos?",
        
        # Mensajes de archivo
        "save_success": "Datos guardados correctamente",
        "load_success": "Datos cargados correctamente",
        "save_error": "Error al guardar",
        "load_error": "Error al cargar",
        "file_not_found": "Archivo no encontrado",
        "invalid_format": "Formato de archivo inválido",
        
        # Mensajes de validación
        "invalid_amount": "Monto inválido",
        "invalid_capital": "Capital inválido",
        "capital_required": "Debe establecer un capital inicial",
        "saving": "Guardando...",
        
        # Días de la semana
        "monday": "Lunes",
        "tuesday": "Martes",
        "wednesday": "Miércoles",
        "thursday": "Jueves",
        "friday": "Viernes",
        "saturday": "Sábado",
        "sunday": "Domingo",
        
        # Consejos AI
        "ai_analysis_title": "📈 Análisis de Rendimiento AI",
        "ai_recommendation": "💡 Recomendación AI",
        "ai_risk_alert": "⚠️ Alerta de Riesgo",
        "insights": "INSIGHTS",
        "recommendations": "RECOMENDACIONES",
        "risk_assessment": "EVALUACIÓN DE RIESGO",
        "rating": "CALIFICACIÓN",
        "no_analysis": "Sin análisis disponible",
        
        # Otros
        "week": "Semana",
        "loading": "Cargando...",
        "error": "Error",
        "success": "Éxito",
        "warning": "Advertencia",
        "information": "Información",
        "confirm": "Confirmar",
        "operation_completed": "Operación completada",
        "operation_failed": "Operación fallida",
        
        # Diálogo de cargar semana guardada
        "load_week_dialog_title": "Seleccionar semana guardada",
        "load_week_action": "Cargar semana",
        "delete_week": "Borrar semana",
        "no_saved_weeks": "No hay semanas guardadas",
        "select_week_first": "Seleccione una semana primero",
        "confirm_delete_week_title": "Confirmar eliminación",
        "confirm_delete_week_message": "¿Desea borrar la semana seleccionada?",
        "week_label": "Semana",
        "delete_success": "Semana borrada correctamente",
        "delete_error": "Error al borrar la semana"
    },
    "en": {
        # Window titles
        "app_title": "W-T-F (Weekend Trading Finance) Trading Manager v2.2",
        "capital_dialog_title": "Set Initial Capital",
        "export_dialog_title": "Export Data",
        "about_title": "About W-T-F Trading Manager",
        "instructions_title": "Usage Instructions",
        "save_week_title": "Save Week",
        "load_week_title": "Load Week",
        
        # Main menu
        "menu_file": "📁 File",
        "menu_view": "👁️ View",
        "menu_assistant": "🧭 Assistant",
        "menu_export": "📊 Export",
        "menu_help": "❓ Help",
        "menu_language": "🌍 Language",
        
        # Menu actions
        "save_week": "💾 Save Week",
        "load_week": "📂 Load Week",
        "load_from_db": "🗄️ Load from Database",
        "set_capital": "💰 Set Initial Capital",
        "exit": "🚪 Exit",
        "dark_mode": "🌙 Dark Mode",
        "toggle_legend": "👁️ Show Legend",
        "daily_advice": "📌 Show daily advice",
        "weekly_summary": "🗓️ Weekly summary",
        "start_new_week_reset": "🆕 Start new week (reset data)",
        "export_excel": "📈 Export to Excel",
        "export_csv": "📋 Export to CSV",
        "export_json": "📄 Export to JSON",
        "about": "ℹ️ About",
        "instructions": "📖 Instructions",
        "capital_edit_mode": "💹 Capital edit mode",
        
        # Menu StatusTips
        "status_save_week": "Save current week's data",
        "status_load_week": "Load data from file",
        "status_load_db": "Load saved data from database",
        "status_set_capital": "Set the week's initial capital",
        "status_exit": "Exit the application",
        "status_dark_mode": "Toggle dark mode",
        "status_toggle_legend": "Show or hide the chart legend",
        "status_daily_advice": "View recommendations for the current day",
        "status_weekly_summary": "Show summary with withdrawal and reinvestment suggestion",
        "status_start_new_week_reset": "Create a new week with zeroed data and updated capital",
        "status_export_excel": "Export data to Excel (.xlsx)",
        "status_export_csv": "Export data to CSV",
        "status_export_json": "Export data to JSON",
        "status_about": "Information about the application",
        "status_instructions": "View usage instructions",
        "status_capital_edit_mode": "Edit day amount by initial/current capital",
        
        # Languages
        "spanish": "Spanish",
        "english": "English",
        
        # Buttons and general labels
        "accept": "Accept",
        "cancel": "Cancel",
        "save": "Save",
        "close": "Close",
        "yes": "Yes",
        "no": "No",
        
        # Capital dialog
        "capital_label": "Initial Capital:",
        "capital_tooltip": "Enter initial capital for the week",
        "capital_placeholder": "e.g.: 100.00",
        "day_capital_dialog_title": "Enter day capital",
        "initial_capital": "Initial capital",
        "current_capital": "Current capital",
        
        # Trading table
        "day_column": "Day",
        "date_column": "Date",
        "type_column": "Type",
        "comments_column": "Comments",
        "amount_column": "Amount",
        "destination_column": "Destination",
        "profit_loss_column": "P/L",
        "profit_loss_pct_column": "P/L %",
        
        # Destinations
        "personal_withdrawal": "Personal Withdrawal",
        "reinvestment": "Reinvestment",
        "not_operated": "Not Operated",
        
        # Summary panel
        "weekly_summary_panel": "📊 Weekly Summary",
        "total_week": "Weekly Total:",
        "performance": "Performance:",
        "ai_advice": "💡 AI Advice",
        "daily_advice_title": "Daily Advice",
        "days_label": "Days: +{positive} / -{negative}",
        "capital_initial": "Initial Capital:",
        "current_balance": "Current Balance:",
        "total_profit_loss": "Total Profit/Loss:",
        "profit_loss_percentage": "P/L Percentage:",
        
        # Chart
        "weekly_chart_title": "📊 Weekly Performance Chart",
        "profit_loss_chart": "Profit/Loss Chart",
        "daily_performance_title": "Daily Trading Performance",
        "weekly_performance_title": "Weekly Trading Performance",
        "days_of_week_label": "Days of the Week",
        "amount_axis_label": "Amount ($)",
        "profit_loss_axis_label": "Profit/Loss ($)",
        "average_label": "Average:",
        "legend_gain": "Gain",
        "legend_loss": "Loss",
        "legend_neutral": "Neutral",
        "legend_gain_withdrawal": "Gain (Withdrawal)",
        "legend_gain_reinvestment": "Gain (Reinvestment)",
        "chart_error_update": "Error updating chart",
        "chart_error_load": "Error loading chart",
        
        # Export
        "export_success": "Export successful",
        "export_error": "Export error",
        "export_completed": "Data has been exported successfully",
        "export_failed": "Could not export data",
        "export_save_title": "Save export file",
        "selected_file": "Selected file",
        "starting_export": "Starting export...",
        "open_file_location_question": "Do you want to open the file location?",
        "no_data_to_export": "No data to export",
        "format_label": "Format:",
        "format_excel_recommended": "Excel (.xlsx) - Recommended",
        "format_csv_compatible": "CSV (.csv) - Compatible everywhere",
        "format_json_developers": "JSON (.json) - For developers",
        "include_charts_excel": "Include charts in Excel (if possible)",
        "include_detailed_summary": "Include detailed summary",
        "preview_title": "👁️ Preview",
        "select_file": "Select file",
        
        # General messages
        "initial_data_loaded_db": "Initial data loaded from database",
        "no_previous_data_new_week": "No previous data, starting a new week",
        "confirm_close_title": "Confirm close",
        "close_anyway_question": "Do you want to close anyway?",
        
        # File messages
        "save_success": "Data saved successfully",
        "load_success": "Data loaded successfully",
        "save_error": "Save error",
        "load_error": "Load error",
        "file_not_found": "File not found",
        "invalid_format": "Invalid file format",
        
        # Validation messages
        "invalid_amount": "Invalid amount",
        "invalid_capital": "Invalid capital",
        "capital_required": "You must set an initial capital",
        "saving": "Saving...",
        
        # Days of the week
        "monday": "Monday",
        "tuesday": "Tuesday",
        "wednesday": "Wednesday",
        "thursday": "Thursday",
        "friday": "Friday",
        "saturday": "Saturday",
        "sunday": "Sunday",
        
        # AI Advice
        "ai_analysis_title": "📈 AI Performance Analysis",
        "ai_recommendation": "💡 AI Recommendation",
        "ai_risk_alert": "⚠️ Risk Alert",
        "insights": "INSIGHTS",
        "recommendations": "RECOMMENDATIONS",
        "risk_assessment": "RISK ASSESSMENT",
        "rating": "RATING",
        "no_analysis": "No analysis available",
        
        # Other
        "week": "Week",
        "loading": "Loading...",
        "error": "Error",
        "success": "Success",
        "warning": "Warning",
        "information": "Information",
        "confirm": "Confirm",
        "operation_completed": "Operation completed",
        "operation_failed": "Operation failed",
        
        # Load saved week dialog
        "load_week_dialog_title": "Select saved week",
        "load_week_action": "Load week",
        "delete_week": "Delete week",
        "no_saved_weeks": "No saved weeks",
        "select_week_first": "Select a week first",
        "confirm_delete_week_title": "Confirm deletion",
        "confirm_delete_week_message": "Do you want to delete the selected week?",
        "week_label": "Week",
        "delete_success": "Week deleted successfully",
        "delete_error": "Error deleting week"
    }
}

# Idioma actual
current_language = "es"

def set_language(lang):
    """Cambiar el idioma actual"""
    global current_language
    if lang in TRANSLATIONS:
        current_language = lang

def tr(key, default=None):
    """Obtener traducción para una clave"""
    return TRANSLATIONS[current_language].get(key, default or key)

def get_available_languages():
    """Obtener lista de idiomas disponibles"""
    return list(TRANSLATIONS.keys())
