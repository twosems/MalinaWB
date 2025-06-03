from telegram import InlineKeyboardMarkup, InlineKeyboardButton
import config
import telegram

def landing_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("▶️ Старт", callback_data="start_btn")],
        [InlineKeyboardButton("ℹ️ О боте", url=config.LANDING_URL)]
    ])

def paginated_keyboard(report_key: str, page: int, total_pages: int, menu_callback: str = "reports_menu"):
    """
    Возвращает InlineKeyboardMarkup с кнопками пагинации для любого отчёта.
    report_key: ключ отчёта (например 'remains', 'storage')
    page: текущая страница (int)
    total_pages: всего страниц (int)
    menu_callback: callback_data для кнопки "В меню"
    """
    buttons = []
    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton("⬅️ Назад", callback_data=f"report:{report_key}:{page-1}")
        )
    if page < total_pages - 1:
        nav_buttons.append(
            InlineKeyboardButton("Вперёд ➡️", callback_data=f"report:{report_key}:{page+1}")
        )
    if nav_buttons:
        buttons.append(nav_buttons)
    buttons.append([InlineKeyboardButton("🔙 В меню", callback_data=menu_callback)])
    return InlineKeyboardMarkup(buttons)

# Безопасное редактирование сообщения (не падает, если "Message is not modified")
async def safe_edit_message_text(message_or_query, *args, **kwargs):
    try:
        # message_or_query может быть либо Message, либо CallbackQuery
        if hasattr(message_or_query, "edit_message_text"):
            return await message_or_query.edit_message_text(*args, **kwargs)
        elif hasattr(message_or_query, "message") and hasattr(message_or_query.message, "edit_text"):
            return await message_or_query.message.edit_text(*args, **kwargs)
    except telegram.error.BadRequest as e:
        if "Message is not modified" in str(e):
            pass  # Просто игнорируем
        else:
            raise