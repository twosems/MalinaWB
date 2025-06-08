from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import ContextTypes
from user_storage import get_api
from wb_api import get_stocks

PAGE_SIZE = 10  # Количество складов на страницу

def remains_keyboard(page, total_pages):
    buttons = []
    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton("⬅️ Предыдущая", callback_data=f"remains_page_{page-1}"))
    if page < total_pages:
        nav.append(InlineKeyboardButton("➡️ Следующая", callback_data=f"remains_page_{page+1}"))
    if nav:
        buttons.append(nav)
    buttons.append([InlineKeyboardButton("⬅️ Назад", callback_data="reports_menu")])
    return InlineKeyboardMarkup(buttons)

async def remains_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    api_key = get_api(user_id)
    print(f"[remains_menu] Отправляем API-ключ: >{api_key}<")  # Для отладки

    # Узнаём текущую страницу (из callback_data или user_data)
    page = 1
    if update.callback_query and update.callback_query.data.startswith("remains_page_"):
        try:
            page = int(update.callback_query.data.split("_")[-1])
        except Exception:
            page = 1

    # Кешируем данные в context.user_data, чтобы не грузить одни и те же остатки каждый раз
    if "remains_data" not in context.user_data or page == 1:
        if not api_key:
            await update.callback_query.edit_message_text(
                "❗ Для просмотра остатков необходимо ввести API-ключ.",
                reply_markup=remains_keyboard(1, 1),
                parse_mode="HTML"
            )
            return

        try:
            items = await get_stocks(api_key)
        except Exception as e:
            await update.callback_query.edit_message_text(
                f"Ошибка при получении остатков:\n{e}",
                reply_markup=remains_keyboard(1, 1),
                parse_mode="HTML"
            )
            return

        if not items:
            await update.callback_query.edit_message_text(
                "❗ Остатков не найдено.",
                reply_markup=remains_keyboard(1, 1),
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

        context.user_data["remains_data"] = warehouse_data
    else:
        warehouse_data = context.user_data["remains_data"]

    if not warehouse_data:
        await update.callback_query.edit_message_text(
            "❗ Все склады пусты!",
            reply_markup=remains_keyboard(1, 1),
            parse_mode="HTML"
        )
        return

    # Постраничный вывод складов
    warehouses = sorted(warehouse_data.items(), key=lambda x: x[0])
    total = len(warehouses)
    total_pages = (total + PAGE_SIZE - 1) // PAGE_SIZE
    page = max(1, min(page, total_pages))

    start = (page - 1) * PAGE_SIZE
    end = start + PAGE_SIZE
    selected_warehouses = warehouses[start:end]

    if not selected_warehouses:
        await update.callback_query.edit_message_text(
            "Нет складов на этой странице.",
            reply_markup=remains_keyboard(page, total_pages),
            parse_mode="HTML"
        )
        return

    text_list = []
    for wh, products in selected_warehouses:
        text = f"🏬 <b>Склад:</b> {wh}\n"
        for art, name, qty in sorted(products, key=lambda x: (-x[2], x[0])):
            text += f"  • <b>{art}</b> ({name}): <b>{qty}</b> шт\n"
        text_list.append(text)

    text = "\n\n".join(text_list)
    page_text = f"Страница {page} из {total_pages}"
    await update.callback_query.edit_message_text(
        f"{text}\n\n{page_text}",
        reply_markup=remains_keyboard(page, total_pages),
        parse_mode="HTML"
    )
