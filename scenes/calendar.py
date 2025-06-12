from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
import calendar

CALENDAR_KEY = "calendar"  # для паттернов

RU_MONTHS = [
    "", "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
]

def build_calendar(year=None, month=None, action_prefix=CALENDAR_KEY, selected_start=None, selected_end=None):
    now = datetime.now()
    year = year or now.year
    month = month or now.month

    # Заголовок с выбранным периодом/датой
    if selected_start and selected_end:
        period_str = f"{selected_start.strftime('%d.%m.%Y')} — {selected_end.strftime('%d.%m.%Y')}"
        title = f"{RU_MONTHS[month]} {year} ({period_str})"
    elif selected_start:
        title = f"{RU_MONTHS[month]} {year} (с {selected_start.strftime('%d.%m.%Y')})"
    else:
        title = f"{RU_MONTHS[month]} {year}"

    markup = []
    markup.append([InlineKeyboardButton(title, callback_data=f"{action_prefix}:IGNORE")])
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

# --- Точка входа: показать календарь ---
async def calendar_menu(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        action_prefix=CALENDAR_KEY,
        title="Выберите дату:",
        select_range=False,        # True — диапазон, False — одна дата
        selected_start=None,
        selected_end=None
):
    kb = build_calendar(
        action_prefix=action_prefix,
        selected_start=selected_start,
        selected_end=selected_end
    )
    if update.callback_query:
        await update.callback_query.edit_message_text(
            title, reply_markup=kb
        )
    else:
        await update.message.reply_text(
            title, reply_markup=kb
        )

# --- Callback-обработчик календаря ---
async def calendar_callback(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        action_prefix=CALENDAR_KEY,
        on_date_selected=None,      # для одиночной даты
        on_range_selected=None,     # для диапазона
        select_range=False,         # True — диапазон, False — одна дата
        selected_start=None,
        selected_end=None,
        max_days=8                  # максимум дней в диапазоне!
):
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
        year, month, day = map(int, parts[2:5])
        chosen_date = datetime(year, month, day)
        if not select_range:
            # Одиночная дата
            if on_date_selected:
                await on_date_selected(update, context, chosen_date)
            else:
                await query.edit_message_text(f"Вы выбрали дату: {chosen_date.strftime('%d.%m.%Y')}")
            return
        # --- Диапазон ---
        range_key = f"{action_prefix}_range"
        range_state = context.user_data.get(range_key, {})
        if not range_state.get("start"):
            # Первый клик — старт диапазона
            context.user_data[range_key] = {"start": chosen_date}
            await calendar_menu(
                update, context,
                action_prefix=action_prefix,
                title="Выберите конечную дату:",
                select_range=True,
                selected_start=chosen_date,
                selected_end=None
            )
            return
        else:
            start = range_state["start"]
            end = chosen_date
            if end < start:
                start, end = end, start
            if (end - start).days > (max_days - 1):
                await query.answer(f"Период не должен превышать {max_days} дней!", show_alert=True)
                await calendar_menu(
                    update, context,
                    action_prefix=action_prefix,
                    title=f"Выбран старт: {start.strftime('%d.%m.%Y')}. Выберите конечную дату (не более {max_days} дней):",
                    select_range=True,
                    selected_start=start,
                    selected_end=None
                )
                return
            context.user_data[range_key] = {}
            if on_range_selected:
                await on_range_selected(update, context, start, end)
            else:
                await query.edit_message_text(f"Вы выбрали период: {start.strftime('%d.%m.%Y')} — {end.strftime('%d.%m.%Y')}")
            return

    elif action == "PREV" or action == "NEXT":
        year, month = map(int, parts[2:4])
        range_key = f"{action_prefix}_range"
        range_state = context.user_data.get(range_key, {})
        selected_start = range_state.get("start")
        kb = build_calendar(
            year=year, month=month,
            action_prefix=action_prefix,
            selected_start=selected_start,
            selected_end=None
        )
        await query.edit_message_reply_markup(reply_markup=kb)
        await query.answer()
        return

    await query.answer()
