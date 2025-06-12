from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from scenes.reports.filters import (
    select_article,
    select_warehouse,
    select_date_or_period,
    FILTER_BACK_BUTTON,
)
from wb_api import get_paid_storage_report
from user_storage import get_api

# Точка входа — предупреждение о лимитах
async def storage_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    warning = (
        "<b>Отчёт о платном хранении</b>\n\n"
        "⚠️ <b>ВНИМАНИЕ!</b>\n"
        "• Запрашивать отчёт можно не чаще 1 раза в минуту.\n"
        "• За один запрос можно получить не более <b>8 дней</b>.\n\n"
        "Продолжая, вы подтверждаете согласие с этими условиями."
    )
    kb = [
        [InlineKeyboardButton("Продолжить", callback_data="storage_mode_menu")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="reports_menu")],
    ]
    await update.effective_chat.send_message(
        warning,
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="HTML"
    )

# Меню выбора режима (все товары/по артикулу)
async def storage_mode_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton("Все товары", callback_data="storage_all_menu")],
        [InlineKeyboardButton("По артикулу", callback_data="storage_by_article_menu")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="reports_menu")],
    ]
    await update.callback_query.edit_message_text(
        "<b>Отчёт по хранению</b>\nВыберите режим:",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="HTML"
    )

# Все товары: по всем складам/по складу
async def storage_all_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton("Все склады", callback_data="storage_all_warehouses")],
        [InlineKeyboardButton("По складу", callback_data="storage_by_warehouse")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="storage_mode_menu")],
    ]
    await update.callback_query.edit_message_text(
        "Выберите вариант:",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="HTML"
    )

# Все товары, все склады: выбор периода
async def storage_all_warehouses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await select_date_or_period(
        update, context, user_id,
        next_callback=storage_report_all_warehouses
    )

# Все товары, по складу: выбор склада → выбор периода
async def storage_by_warehouse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await select_warehouse(
        update, context, user_id,
        next_callback=storage_report_by_warehouse,
        prev_callback=storage_all_menu
    )

# По артикулу: по всем складам/по складу
async def storage_by_article_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton("Все склады", callback_data="storage_article_all_warehouses")],
        [InlineKeyboardButton("По складу", callback_data="storage_article_by_warehouse")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="storage_mode_menu")],
    ]
    await update.callback_query.edit_message_text(
        "Выберите вариант:",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="HTML"
    )

# По артикулу, все склады: выбор артикула → период
async def storage_article_all_warehouses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await select_article(
        update, context, user_id,
        next_callback=storage_report_article_all_warehouses,
        prev_callback=storage_by_article_menu
    )

# По артикулу, по складу: артикул → склад → период
async def storage_article_by_warehouse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await select_article(
        update, context, user_id,
        next_callback=storage_article_by_warehouse_warehouse,
        prev_callback=storage_by_article_menu
    )

async def storage_article_by_warehouse_warehouse(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id, article):
    await select_warehouse(
        update, context, user_id,
        next_callback=lambda u, c, uid, warehouse: storage_report_article_by_warehouse(u, c, uid, article, warehouse),
        prev_callback=storage_article_by_warehouse
    )

# ==== Итоговые функции для формирования отчёта ====

# Все товары, все склады
async def storage_report_all_warehouses(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id, date_from, date_to):
    await call_paid_storage_report(update, context, user_id, date_from, date_to)

# Все товары, по складу
async def storage_report_by_warehouse(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id, warehouse, date_from, date_to):
    await call_paid_storage_report(update, context, user_id, date_from, date_to, warehouse=warehouse)

# По артикулу, все склады
async def storage_report_article_all_warehouses(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id, article, date_from, date_to):
    await call_paid_storage_report(update, context, user_id, date_from, date_to, article=article)

# По артикулу, по складу
async def storage_report_article_by_warehouse(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id, article, warehouse, date_from, date_to):
    await call_paid_storage_report(update, context, user_id, date_from, date_to, article=article, warehouse=warehouse)

# ==== Основная функция формирования и показа отчёта ====

async def call_paid_storage_report(update, context, user_id, date_from, date_to, article=None, warehouse=None):
    from datetime import datetime
    # Ограничение: максимум 8 дней
    dt1 = datetime.strptime(date_from, "%Y-%m-%d")
    dt2 = datetime.strptime(date_to, "%Y-%m-%d")
    if (dt2 - dt1).days > 7:
        await update.effective_chat.send_message(
            "⚠️ Период не должен превышать 8 дней! Попробуйте снова.",
            reply_markup=FILTER_BACK_BUTTON()
        )
        return

    await update.effective_chat.send_message("⏳ Формируется отчёт по хранению...", parse_mode="HTML")

    try:
        # Получаем api_key
        api_key = get_api(user_id)
        result = await get_paid_storage_report(api_key, date_from, date_to, article, warehouse)
    except Exception as e:
        # Обработка лимита WB (1 запрос в минуту)
        if "429" in str(e) or "too many requests" in str(e).lower():
            await update.effective_chat.send_message(
                "❗️ Лимит запросов превышен (не чаще 1 раза в минуту). Попробуйте чуть позже.",
                reply_markup=FILTER_BACK_BUTTON()
            )
            return
        await update.effective_chat.send_message(
            f"Ошибка при формировании отчёта: {e}",
            reply_markup=FILTER_BACK_BUTTON()
        )
        return

    # Формируем красивый вывод
    if not result:
        await update.effective_chat.send_message(
            "Нет данных по выбранным фильтрам.",
            reply_markup=FILTER_BACK_BUTTON()
        )
        return

    # Пример вывода (настрой под свой формат данных)
    text = "<b>Отчёт о хранении</b>\n"
    total = 0
    for row in result:
        art = row.get("supplierArticle", "—")
        wh = row.get("warehouseName", "—")
        price = row.get("storagePrice", 0)
        amount = row.get("storageSum", 0)
        text += f"\n• <b>{art}</b> | {wh} | Цена: {price}₽ | Сумма: {amount}₽"
        total += amount
    text += f"\n\n<b>Общая сумма за хранение: {total}₽</b>"

    await update.effective_chat.send_message(
        text,
        parse_mode="HTML",
        reply_markup=FILTER_BACK_BUTTON()
    )
