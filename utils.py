from telegram import InlineKeyboardMarkup, InlineKeyboardButton
import config
import telegram

def landing_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("▶️ Старт", callback_data="start_btn")],
        [InlineKeyboardButton("ℹ️ О боте", url=config.LANDING_URL)]
    ])

def paginate(items, page, page_size):
    """
    Возвращает кортеж (page_items, total_pages, page)
    - page_items: элементы на текущей странице
    - total_pages: всего страниц
    - page: скорректированный (валидный) номер страницы
    """
    total_pages = (len(items) + page_size - 1) // page_size if items else 1
    page = max(0, min(page, total_pages - 1))  # always in range
    start = page * page_size
    end = start + page_size
    return items[start:end], total_pages, page

def paginated_keyboard(report_key: str, page: int, total_pages: int, menu_callback: str = "reports_menu"):
    """
    Универсальная клавиатура для пагинации (может использоваться во всех отчётах).
    report_key — уникальный ключ отчёта (remains, sales, ...)
    page — текущая страница (с 0)
    total_pages — всего страниц
    menu_callback — куда вернуться в меню
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
    buttons.append([InlineKeyboardButton("↩️ В меню", callback_data=menu_callback)])
    return InlineKeyboardMarkup(buttons)

def page_info_str(page: int, total_pages: int) -> str:
    """
    Генерирует строку "Страница X/Y" (страницы считаются с 1 для пользователя)
    """
    return f"Страница {page + 1} из {total_pages}"

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
