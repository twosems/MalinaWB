from telegram import Update
from telegram.ext import ContextTypes
from user_storage import get_api
from wb_api import get_stocks
from utils import paginated_keyboard

async def remains_report(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    user_id = update.effective_user.id
    api_key = get_api(user_id)

    if not api_key:
        await update.callback_query.edit_message_text(
            "❗ Для просмотра остатков необходимо ввести API-ключ.",
            reply_markup=paginated_keyboard("remains", 0, 1),
            parse_mode="HTML"
        )
        return

    try:
        items = await get_stocks(api_key)
    except Exception:
        await update.callback_query.edit_message_text(
            "❗ Не удалось получить остатки, попробуйте позже.",
            reply_markup=paginated_keyboard("remains", 0, 1),
            parse_mode="HTML"
        )
        return

    if not items:
        await update.callback_query.edit_message_text(
            "❗ Остатков не найдено.",
            reply_markup=paginated_keyboard("remains", 0, 1),
            parse_mode="HTML"
        )
        return

    # Группируем товары по складам
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

    warehouses = list(warehouse_data.items())
    batch_size = 10
    total_pages = max(1, (len(warehouses) + batch_size - 1) // batch_size)
    start = page * batch_size
    end = start + batch_size
    batch = warehouses[start:end]

    text = ""
    for wh, products in batch:
        text += f"🏬 <b>Склад:</b> {wh}\n"
        for art, name, qty in sorted(products, key=lambda x: (-x[2], x[0])):
            text += f"  • <b>{art}</b> ({name}): <b>{qty}</b> шт\n"
        text += "\n"

    await update.callback_query.edit_message_text(
        text.strip() if text.strip() else "❗ Нет остатков для отображения.",
        parse_mode="HTML",
        reply_markup=paginated_keyboard("remains", page, total_pages)
    )