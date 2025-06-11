from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
import calendar

CALENDAR_KEY = "calendar"  # для паттернов

def build_calendar(year=None, month=None, action_prefix=CALENDAR_KEY):
    now = datetime.now()
    year = year or now.year
    month = month or now.month

    markup = []
    # Шапка
    markup.append([InlineKeyboardButton(f"{calendar.month_name[month]} {year}", callback_data=f"{action_prefix}:IGNORE")])
    week_days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    markup.append([InlineKeyboardButton(day, callback_data=f"{action_prefix}:IGNORE") for day in week_days])

    month_calendar = calendar.monthcalendar(year, month)
    for week in month_calendar:
        row = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(" ", callback_data=f"{action_prefix}:IGNORE"))
            else:
                row.append(InlineKeyboardButton(str(day), callback_data=f"{action_prefix}:DAY:{year}:{month}:{day}"))
        markup.append(row)

    prev_month = month - 1 or 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1
    markup.append([
        InlineKeyboardButton("«", callback_data=f"{action_prefix}:PREV:{prev_year}:{prev_month}"),
        InlineKeyboardButton("Отмена", callback_data=f"{action_prefix}:CANCEL"),
        InlineKeyboardButton("»", callback_data=f"{action_prefix}:NEXT:{next_year}:{next_month}")
    ])
    return InlineKeyboardMarkup(markup)

# --- Основная точка входа для отображения календаря ---
async def calendar_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, action_prefix=CALENDAR_KEY, title="Выберите дату:"):
    kb = build_calendar(action_prefix=action_prefix)
    if update.callback_query:
        await update.callback_query.edit_message_text(
            title, reply_markup=kb
        )
    else:
        await update.message.reply_text(
            title, reply_markup=kb
        )

# --- Callback-обработчик для календаря ---
async def calendar_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, action_prefix=CALENDAR_KEY, on_date_selected=None):
    query = update.callback_query
    data = query.data
    parts = data.split(":")
    if len(parts) < 2 or parts[0] != action_prefix:
        await query.answer()
        return

    action = parts[1]

    if action == "IGNORE":
        await query.answer()
        return

    elif action == "CANCEL":
        await query.edit_message_text("❌ Выбор даты отменён.")
        return

    elif action == "DAY":
        # parts: ["calendar", "DAY", "2024", "6", "13"]
        year, month, day = map(int, parts[2:5])
        selected_date = datetime(year, month, day)
        if on_date_selected:
            await on_date_selected(update, context, selected_date)
        else:
            await query.edit_message_text(f"Вы выбрали дату: {selected_date.strftime('%d.%m.%Y')}")
        return

    elif action == "PREV" or action == "NEXT":
        year, month = map(int, parts[2:4])
        kb = build_calendar(year=year, month=month, action_prefix=action_prefix)
        await query.edit_message_reply_markup(reply_markup=kb)
        await query.answer()
        return

    await query.answer()

# --- Пример использования календаря в любом отчёте ---
# scenes/reports/some_report.py

# from scenes.calendar import calendar_menu, calendar_callback

# async def some_report_menu(update, context):
#     await calendar_menu(update, context, action_prefix="calendar_some_report", title="Выберите дату для отчёта:")

# async def calendar_some_report_callback(update, context):
#     async def on_date_selected(update, context, selected_date):
#         # Тут логика — формируешь отчёт по выбранной дате
#         await update.callback_query.edit_message_text(f"Готовим отчёт за {selected_date.strftime('%d.%m.%Y')}")
#     await calendar_callback(update, context, action_prefix="calendar_some_report", on_date_selected=on_date_selected)
