"""
Sistema de consejos diarios y resumen semanal con soporte i18n.
"""

from datetime import datetime
from .i18n import tr, current_language

def get_daily_advice(model):
    """Obtener consejo del día basado en el día actual y el rendimiento.
    Devuelve un dict con 'title' y 'message'.
    """
    today_idx = datetime.now().weekday()  # 0=Lunes ... 6=Domingo
    total = model.get_total_profit_loss()
    percentage = model.get_profit_loss_percentage()
    initial = model.initial_capital
    balance = model.get_current_balance()

    positive = total > 0

    # Nombre del día según idioma
    day_keys = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    day = tr(day_keys[today_idx])

    # Línea base con métricas clave
    base = (
        f"{tr('capital_initial')} ${initial:.2f} | "
        f"{tr('current_balance')} ${balance:.2f} | "
        f"{tr('total_profit_loss')} ${total:.2f} ({percentage:.2f}%)"
    )

    if today_idx == 0:  # Lunes / Monday
        if current_language == 'es':
            msg = (
                "Arranca la semana con foco y energía 💪. Define 1-2 objetivos reales y planifica tus operaciones clave.\n"
                "• Revisa capital y riesgos antes de operar.\n"
                "• Calidad sobre cantidad: evita sobreoperar.\n"
                f"• {('Buen inicio, disciplina y pasos firmes 🚀' if positive else 'Si el inicio es flojo, sé selectivo y reduce tamaño 🧠')}"
            )
        else:
            msg = (
                "Kick off the week with focus and energy 💪. Set 1–2 realistic goals and plan core trades.\n"
                "• Review capital and risks before trading.\n"
                "• Quality over quantity: avoid overtrading.\n"
                f"• {('Strong start—discipline and steady steps 🚀' if positive else 'If the start is weak, be selective and cut size 🧠')}"
            )
        return {"title": f"{tr('daily_advice_title')} - {day}", "message": f"{base}\n\n{msg}"}

    if today_idx == 1:  # Martes / Tuesday
        if current_language == 'es':
            msg = (
                "Consolida el momentum: busca confirmaciones, no persigas entradas tardías.\n"
                "• Ajusta stops a estructura real, no a números redondos.\n"
                f"• {('Protege ganancias y cuida tu ventaja 🎯' if positive else 'Minimiza pérdidas y espera setups A+ 🧩')}"
            )
        else:
            msg = (
                "Consolidate momentum: seek confirmations, avoid chasing late entries.\n"
                "• Set stops to real structure, not round numbers.\n"
                f"• {('Protect gains and guard your edge 🎯' if positive else 'Minimize losses and wait for A+ setups 🧩')}"
            )
        return {"title": f"{tr('daily_advice_title')} - {day}", "message": f"{base}\n\n{msg}"}

    if today_idx == 2:  # Miércoles / Wednesday
        if current_language == 'es':
            msg = (
                "Mitad de semana: evalúa progreso y ajusta el rumbo.\n"
                "• Si vas bien, evita el exceso de confianza.\n"
                "• Si vas mal, simplifica y baja exposición.\n"
                "• Recuerda: consistencia > perfección ✅"
            )
        else:
            msg = (
                "Midweek: assess progress and adjust course.\n"
                "• If you’re doing well, avoid overconfidence.\n"
                "• If you’re not, simplify and reduce exposure.\n"
                "• Remember: consistency > perfection ✅"
            )
        return {"title": f"{tr('daily_advice_title')} - {day}", "message": f"{base}\n\n{msg}"}

    if today_idx == 3:  # Jueves / Thursday
        if current_language == 'es':
            msg = (
                "Prepara el cierre semanal. Sé selectivo y evita forzar trades.\n"
                "• Prioriza setups con confluencias claras.\n"
                "• No persigas recuperaciones a última hora.\n"
                "• Mantén la mente fría: el viernes debe encontrarte listo 🧊"
            )
        else:
            msg = (
                "Prepare the weekly close. Be selective and avoid forcing trades.\n"
                "• Prioritize setups with clear confluences.\n"
                "• Don’t chase last-minute recoveries.\n"
                "• Keep a cool head: be ready for Friday 🧊"
            )
        return {"title": f"{tr('daily_advice_title')} - {day}", "message": f"{base}\n\n{msg}"}

    if today_idx == 4:  # Viernes / Friday
        if current_language == 'es':
            msg = (
                "Cierra la semana con cabeza fría.\n"
                "• No arriesgues ganancias consolidadas.\n"
                "• Documenta aprendizajes clave para el sábado.\n"
                "• Termina fuerte y sin ansiedad 🏁"
            )
        else:
            msg = (
                "Close the week with a cool head.\n"
                "• Don’t risk consolidated gains.\n"
                "• Document key learnings for Saturday.\n"
                "• Finish strong, without anxiety 🏁"
            )
        return {"title": f"{tr('daily_advice_title')} - {day}", "message": f"{base}\n\n{msg}"}

    if today_idx == 5:  # Sábado / Saturday
        withdraw = max(0.0, total) * 0.30
        reinvest = max(0.0, total) - withdraw
        if current_language == 'es':
            msg = (
                "Día de promedio semanal y retiros.\n"
                f"• Resultado semanal: ${total:.2f}.\n"
                f"• Retiro recomendado: ${withdraw:.2f} (30% de las ganancias).\n"
                f"• Reinversión sugerida: ${reinvest:.2f}.\n"
                f"• {('¡Semana ganadora! Felicitaciones 👏' if positive else 'Semana en rojo: revisa, aprende y ajusta 📘')}\n"
                "• Celebra el proceso: progreso sostenido > impulsos 🔁"
            )
        else:
            msg = (
                "Weekly average and withdrawals day.\n"
                f"• Weekly result: ${total:.2f}.\n"
                f"• Recommended withdrawal: ${withdraw:.2f} (30% of gains).\n"
                f"• Suggested reinvestment: ${reinvest:.2f}.\n"
                f"• {('Winning week! Congrats 👏' if positive else 'Red week: review, learn, and adjust 📘')}\n"
                "• Celebrate the process: sustained progress > impulses 🔁"
            )
        return {"title": f"{tr('daily_advice_title')} - {day}", "message": f"{base}\n\n{msg}"}

    # Domingo / Sunday
    if current_language == 'es':
        msg = (
            "Descansa y prepara la estrategia de la próxima semana.\n"
            "• Revisa diarios y marcas clave.\n"
            "• Planifica escenarios y tus límites.\n"
            "• Recarga la mente: claridad trae oportunidades 🌤️"
        )
    else:
        msg = (
            "Rest and prepare next week's strategy.\n"
            "• Review journals and key levels.\n"
            "• Plan scenarios and your limits.\n"
            "• Reset your mind: clarity brings opportunities 🌤️"
        )
    return {"title": f"{tr('daily_advice_title')} - {day}", "message": f"{base}\n\n{msg}"}


def get_weekly_summary_message(model):
    """Construir mensaje de resumen semanal con sugerencia de retiro y reinversión."""
    total = model.get_total_profit_loss()
    percentage = model.get_profit_loss_percentage()
    initial = model.initial_capital
    balance = model.get_current_balance()
    withdraw = max(0.0, total) * 0.30
    reinvest = max(0.0, total) - withdraw

    if total >= 0:
        headline = ("¡Semana de ganancias! 🎉" if current_language == 'es' else "Profitable week! 🎉")
    else:
        headline = ("Semana desafiante 💡" if current_language == 'es' else "Challenging week 💡")

    if current_language == 'es':
        message = (
            f"{headline}\n\n"
            f"Capital inicial: ${initial:.2f}\n"
            f"Balance actual: ${balance:.2f}\n"
            f"Resultado semanal: ${total:.2f} ({percentage:.2f}%)\n\n"
            f"Retiro recomendado (30%): ${withdraw:.2f}\n"
            f"Reinversión sugerida: ${reinvest:.2f}\n"
            "\nConsejo: documenta tus mejores y peores operaciones para aprender rápido."
        )
    else:
        message = (
            f"{headline}\n\n"
            f"Initial capital: ${initial:.2f}\n"
            f"Current balance: ${balance:.2f}\n"
            f"Weekly result: ${total:.2f} ({percentage:.2f}%)\n\n"
            f"Recommended withdrawal (30%): ${withdraw:.2f}\n"
            f"Suggested reinvestment: ${reinvest:.2f}\n"
            "\nTip: document your best and worst trades to learn faster."
        )
    return message