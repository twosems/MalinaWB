import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from user_storage import get_api
from wb_api import get_stocks
from utils import paginate, paginated_keyboard, page_info_str

REPORT_KEY = "remains"
PAGE_SIZE = 10

async def remains_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    api_key = get_api(user_id)
    data = update.callback_query.data

    # Можно уведомлять пользователя, что отчет готовится (но это опционально)
    try:
        await update.callback_query.edit_message_text("⏳ Готовится отчёт...", parse_mode="HTML")
    except Exception:
        pass  # Молча игнорируем ошибки редактирования

    # Получаем остатки
    if not api_key:
        await update.effective_chat.send_message(
            "❗ Для просмотра остатков необходимо ввести API-ключ.",
            reply_markup=paginated_keyboard(REPORT_KEY, 0, 1),
            parse_mode="HTML"
        )
        return

    items = await get_stocks(api_key)
    if not items:
        await update.effective_chat.send_message(
            "❗ Остатков не найдено.",
            reply_markup=paginated_keyboard(REPORT_KEY, 0, 1),
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
        await update.effective_chat.send_message(
            "❗ Все склады пусты!",
            reply_markup=paginated_keyboard(REPORT_KEY, 0, 1),
            parse_mode="HTML"
        )
        return

    page = 0
    if data.startswith("report:remains:"):
        try:
            page = int(data.split(":")[-1])
        except Exception:
            page = 0

    warehouses = list(warehouse_data.items())
    page_items, total_pages, page = paginate(warehouses, page, PAGE_SIZE)

    text_blocks = []
    for wh, products in page_items:
        text = f"🏬 <b>Склад:</b> {wh}\n"
        for art, name, qty in sorted(products, key=lambda x: (-x[2], x[0])):
            text += f"  • <b>{art}</b> ({name}): <b>{qty}</b> шт\n"
        text_blocks.append(text)
    final_text = "\n\n".join(text_blocks)
    final_text += f"\n\n{page_info_str(page, total_pages)}"

    await update.effective_chat.send_message(
        final_text,
        reply_markup=paginated_keyboard(REPORT_KEY, page, total_pages),
        parse_mode="HTML"
    )
