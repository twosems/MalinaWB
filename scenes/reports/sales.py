from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from user_storage import get_api
from wb_api import get_sales, get_stocks
from utils import paginate, page_info_str, paginated_keyboard
from scenes.calendar import calendar_menu, calendar_callback
from datetime import datetime

REPORT_KEY = "sales"
PAGE_SIZE = 10

# Точка входа — один callback для всех sales_*
async def sales_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = update.callback_query.data

    # 1. Главное меню
    if data == "sales_menu":
        kb = [
            [InlineKeyboardButton("🛒 Отчёт по всем товарам", callback_data="sales_all_menu")],
            [InlineKeyboardButton("🔍 Отчёт по артикулам", callback_data="sales_articles_menu")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="reports_menu")]
        ]
        await update.callback_query.edit_message_text(
            "<b>Отчёт по продажам</b>\nВыберите раздел:",
            reply_markup=InlineKeyboardMarkup(kb),
            parse_mode="HTML"
        )
        return

    # 2. Меню выбора периода для всех товаров
    if data == "sales_all_menu":
        kb = [
            [InlineKeyboardButton("📅 За месяц", callback_data="sales_all_month")],
            [InlineKeyboardButton("📆 За день", callback_data="sales_all_day")],
            [InlineKeyboardButton("🗓 За период", callback_data="sales_all_period_calendar")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="sales_menu")]
        ]
        await update.callback_query.edit_message_text(
            "Выберите период для отчёта по всем товарам:",
            reply_markup=InlineKeyboardMarkup(kb),
            parse_mode="HTML"
        )
        return

    # 3. Выбор периода — Календарь для дня
    if data == "sales_all_day":
        await calendar_menu(update, context, action_prefix="calendar_sales_day", title="Выберите дату:")
        return

    # 4. Выбор периода — Календарь для произвольного интервала
    if data == "sales_all_period_calendar":
        await calendar_menu(update, context, action_prefix="calendar_sales_period_start", title="Выберите начальную дату периода:")
        return

    # 5. За месяц (автоматически за текущий)
    if data == "sales_all_month":
        date_from = datetime.now().replace(day=1).strftime("%Y-%m-%d")
        await show_sales_all(update, context, date_from)
        return

    # 6. Артикулы меню
    if data == "sales_articles_menu":
        kb = [
            [InlineKeyboardButton("🟢 Артикулы с остатком", callback_data="sales_articles_with_stock:0")],
            [InlineKeyboardButton("📋 Все артикулы", callback_data="sales_articles_all:0")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="sales_menu")]
        ]
        await update.callback_query.edit_message_text(
            "Выберите тип артикула:",
            reply_markup=InlineKeyboardMarkup(kb),
            parse_mode="HTML"
        )
        return

    # 7. Артикулы с остатком (страницы)
    if data.startswith("sales_articles_with_stock"):
        page = int(data.split(":")[1]) if ":" in data else 0
        await show_articles_with_stock(update, context, page)
        return

    # 8. Все артикулы (страницы)
    if data.startswith("sales_articles_all"):
        page = int(data.split(":")[1]) if ":" in data else 0
        await show_articles_all(update, context, page)
        return

    # 9. Переход к выбору периода для конкретного артикула
    if data.startswith("sales_article_period:"):
        art = data.split(":", 1)[1]
        kb = [
            [InlineKeyboardButton("📅 За месяц", callback_data=f"sales_article:{art}:month")],
            [InlineKeyboardButton("📆 За день", callback_data=f"sales_article:{art}:day")],
            [InlineKeyboardButton("🗓 За период", callback_data=f"sales_article_period_calendar:{art}")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="sales_articles_menu")]
        ]
        await update.callback_query.edit_message_text(
            f"<b>Артикул:</b> <code>{art}</code>\nВыберите период:",
            reply_markup=InlineKeyboardMarkup(kb),
            parse_mode="HTML"
        )
        return

    # 10. Календарь для артикула за день
    if data.startswith("sales_article:") and data.endswith(":day"):
        art = data.split(":")[1]
        await calendar_menu(update, context, action_prefix=f"calendar_article_day_{art}", title="Выберите дату для артикула:")
        return

    # 11. Календарь для артикула за период
    if data.startswith("sales_article_period_calendar:"):
        art = data.split(":")[1]
        await calendar_menu(update, context, action_prefix=f"calendar_article_period_start_{art}", title="Выберите начальную дату периода:")
        return

    # 12. За месяц по артикулу
    if data.startswith("sales_article:") and data.endswith(":month"):
        art = data.split(":")[1]
        date_from = datetime.now().replace(day=1).strftime("%Y-%m-%d")
        await show_sales_article(update, context, art, date_from)
        return

    # 13. Callback от пагинации (для всех товаров)
    if data.startswith("report:sales:"):
        try:
            page = int(data.split(":")[-1])
        except Exception:
            page = 0
        date_from = context.user_data.get("sales_date_from", datetime.now().replace(day=1).strftime("%Y-%m-%d"))
        await show_sales_all(update, context, date_from, page)
        return

    # 14. Callback от пагинации (для артикулов)
    if data.startswith("sales_articles_page:"):
        _, page = data.split(":")
        await show_articles_all(update, context, int(page))
        return

    await update.callback_query.answer("Пункт в разработке")

# ---- Helpers ----

async def show_sales_all(update, context, date_from, page=0):
    user_id = update.effective_user.id
    api_key = get_api(user_id)
    if not api_key:
        await update.callback_query.edit_message_text(
            "❗ Для просмотра отчёта необходимо ввести API-ключ.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔑 Ввести API", callback_data="api_entry")]]),
            parse_mode="HTML"
        )
        return
    await update.callback_query.edit_message_text("⏳ Формируется отчёт...", parse_mode="HTML")
    sales = await get_sales(api_key, date_from)
    stats = {}
    for item in sales:
        art = item.get("supplierArticle", "—")
        stats.setdefault(art, 0)
        stats[art] += 1
    arts = sorted(stats.items(), key=lambda x: -x[1])
    page_items, total_pages, page = paginate(arts, page, PAGE_SIZE)
    text = f"<b>Продажи</b>\n\n"
    for art, qty in page_items:
        text += f"• <b>{art}</b>: {qty} шт\n"
    text += f"\n{page_info_str(page, total_pages)}"
    await update.effective_chat.send_message(
        text,
        reply_markup=paginated_keyboard(REPORT_KEY, page, total_pages),
        parse_mode="HTML"
    )

async def show_articles_with_stock(update, context, page=0):
    user_id = update.effective_user.id
    api_key = get_api(user_id)
    stocks = await get_stocks(api_key)
    arts = sorted(set(i["supplierArticle"] for i in stocks if i.get("quantity", 0) > 0))
    page_items, total_pages, page = paginate(arts, page, PAGE_SIZE)
    text = "<b>Артикулы с остатком:</b>\n\n"
    for art in page_items:
        text += f"• <b>{art}</b>\n"
    text += f"\n{page_info_str(page, total_pages)}"
    kb = []
    if page > 0:
        kb.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"sales_articles_with_stock:{page-1}"))
    if page + 1 < total_pages:
        kb.append(InlineKeyboardButton("Вперёд ➡️", callback_data=f"sales_articles_with_stock:{page+1}"))
    nav = [kb] if kb else []
    for art in page_items:
        nav.insert(0, [InlineKeyboardButton(f"Артикул: {art}", callback_data=f"sales_article_period:{art}")])
    nav.append([InlineKeyboardButton("⬅️ Назад", callback_data="sales_articles_menu")])
    await update.callback_query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(nav),
        parse_mode="HTML"
    )

async def show_articles_all(update, context, page=0):
    user_id = update.effective_user.id
    api_key = get_api(user_id)
    stocks = await get_stocks(api_key)
    arts = sorted(set(i["supplierArticle"] for i in stocks))
    page_items, total_pages, page = paginate(arts, page, PAGE_SIZE)
    text = "<b>Все артикулы:</b>\n\n"
    for art in page_items:
        text += f"• <b>{art}</b>\n"
    text += f"\n{page_info_str(page, total_pages)}"
    kb = []
    if page > 0:
        kb.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"sales_articles_all:{page-1}"))
    if page + 1 < total_pages:
        kb.append(InlineKeyboardButton("Вперёд ➡️", callback_data=f"sales_articles_all:{page+1}"))
    nav = [kb] if kb else []
    for art in page_items:
        nav.insert(0, [InlineKeyboardButton(f"Артикул: {art}", callback_data=f"sales_article_period:{art}")])
    nav.append([InlineKeyboardButton("⬅️ Назад", callback_data="sales_articles_menu")])
    await update.callback_query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(nav),
        parse_mode="HTML"
    )

async def show_sales_article(update, context, art, date_from, page=0):
    user_id = update.effective_user.id
    api_key = get_api(user_id)
    sales = await get_sales(api_key, date_from)
    filtered = [item for item in sales if item.get("supplierArticle") == art]
    stats = {}
    for item in filtered:
        wh = item.get("warehouseName", "—")
        stats.setdefault(wh, 0)
        stats[wh] += 1
    text = f"<b>Продажи по артикулу <code>{art}</code></b>\n\n"
    for wh, qty in stats.items():
        text += f"• <b>{wh}</b>: {qty} шт\n"
    text += "\n⬅️ <b>Назад</b>: к выбору периода"
    kb = [[InlineKeyboardButton("⬅️ Назад", callback_data=f"sales_article_period:{art}")]]
    await update.effective_chat.send_message(
        text,
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="HTML"
    )

# ---- Calendar Callbacks (регистрировать в bot.py) ----

async def calendar_sales_day_callback(update, context):
    async def on_date_selected(update, context, selected_date):
        date_from = selected_date.strftime("%Y-%m-%d")
        context.user_data["sales_date_from"] = date_from
        await show_sales_all(update, context, date_from)
    await calendar_callback(update, context, action_prefix="calendar_sales_day", on_date_selected=on_date_selected)

async def calendar_sales_period_start_callback(update, context):
    async def on_date_selected(update, context, selected_date):
        context.user_data["period_start"] = selected_date.strftime("%Y-%m-%d")
        await calendar_menu(update, context, action_prefix="calendar_sales_period_end", title="Выберите конечную дату периода:")
    await calendar_callback(update, context, action_prefix="calendar_sales_period_start", on_date_selected=on_date_selected)

async def calendar_sales_period_end_callback(update, context):
    async def on_date_selected(update, context, selected_date):
        start = context.user_data.get("period_start")
        end = selected_date.strftime("%Y-%m-%d")
        # Можно реализовать отчёт по периоду
        await show_sales_all(update, context, start)  # Используй период start-end
    await calendar_callback(update, context, action_prefix="calendar_sales_period_end", on_date_selected=on_date_selected)

async def calendar_article_day_callback(update, context):
    data = update.callback_query.data
    prefix = data.split(":")[0]
    art = prefix[len("calendar_article_day_"):]

    async def on_date_selected(update, context, selected_date):
        date_from = selected_date.strftime("%Y-%m-%d")
        await show_sales_article(update, context, art, date_from)

    await calendar_callback(update, context, action_prefix=prefix, on_date_selected=on_date_selected)

async def calendar_article_period_start_callback(update, context):
    data = update.callback_query.data
    prefix = data.split(":")[0]
    art = prefix[len("calendar_article_period_start_"):]

    async def on_date_selected(update, context, selected_date):
        context.user_data["period_start"] = selected_date.strftime("%Y-%m-%d")
        await calendar_menu(update, context, action_prefix=f"calendar_article_period_end_{art}", title="Выберите конечную дату периода:")

    await calendar_callback(update, context, action_prefix=prefix, on_date_selected=on_date_selected)

async def calendar_article_period_end_callback(update, context):
    data = update.callback_query.data
    prefix = data.split(":")[0]
    art = prefix[len("calendar_article_period_end_"):]

    async def on_date_selected(update, context, selected_date):
        start = context.user_data.get("period_start")
        end = selected_date.strftime("%Y-%m-%d")
        # Можно реализовать отчёт по периоду
        await show_sales_article(update, context, art, start)  # Используй период start-end

    await calendar_callback(update, context, action_prefix=prefix, on_date_selected=on_date_selected)