from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import ContextTypes
from user_storage import get_api
from wb_api import get_stocks
import logging

logger = logging.getLogger(__name__)

def remains_keyboard(page, total_pages):
    buttons = []
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"remains_page_{page-1}"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("Вперёд ➡️", callback_data=f"remains_page_{page+1}"))
    if nav_buttons:
        buttons.append(nav_buttons)
    buttons.append([InlineKeyboardButton("🔙 В меню", callback_data="reports_menu")])
    return InlineKeyboardMarkup(buttons)

async def remains_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    api_key = get_api(user_id)
    logger.debug("[remains_menu] API key received and passed to request")

    # Определяем номер страницы из callback_data или берем 0 по умолчанию
    page = 0
    if update.callback_query and update.callback_query.data:
        data = update.callback_query.data
        if data.startswith("remains_page_"):
            try:
                page = int(data.split("_")[-1])
            except ValueError:
                page = 0

    if not api_key:
        await update.callback_query.edit_message_text(
            "❗ Для просмотра остатков необходимо ввести API-ключ.",
            reply_markup=remains_keyboard(0, 1),
            parse_mode="HTML"
        )
        return

    try:
        items = await get_stocks(api_key)
    except Exception as e:
        await update.callback_query.edit_message_text(
            "❗ Не удалось получить остатки, попробуйте позже.",
            reply_markup=remains_keyboard(0, 1),
            parse_mode="HTML"
        )
        return

    if not items:
        await update.callback_query.edit_message_text(
            "❗ Остатков не найдено.",
            reply_markup=remains_keyboard(0, 1),
            parse_mode="HTML"
        )
        return

    warehouse_data = {}
    for item in items:
        qty = item.get("quantity", 0)
        if qty == 0:
            continue
        wh = item.get("warehouseName", "Неизвестно")
        art = item.get("supplierArticle", "Без артикула")
        name = item.get("subject", "Без предмета")
        if wh not in warehouse_data:
            warehouse_data[wh] = []
        warehouse_data[wh].append((art, name, qty))

    if not warehouse_data:
        await update.callback_query.edit_message_text(
            "❗ Все склады пусты!",
            reply_markup=remains_keyboard(0, 1),
            parse_mode="HTML"
        )
        return

    warehouses = list(warehouse_data.items())
    batch_size = 10
    total_pages = (len(warehouses) + batch_size - 1) // batch_size

    # Границы текущей страницы
    start = page * batch_size
    end = start + batch_size
    batch = warehouses[start:end]

    text = ""
    for wh, products in batch:
        text += f"🏬 <b>Склад:</b> {wh}\n"
        for art, name, qty in sorted(products, key=lambda x: (-x[2], x[0])):
            text += f"  • <b>{art}</b> ({name}): <b>{qty}</b> шт\n"
        text += "\n"

    # Обновляем только текст и клавиатуру (edit_message_text)
    await update.callback_query.edit_message_text(
        text.strip() if text.strip() else "❗ Нет остатков для отображения.",
        parse_mode="HTML",
        reply_markup=remains_keyboard(page, total_pages)
    )