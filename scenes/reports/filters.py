from datetime import datetime
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import CallbackContext

### --- ЧИСТЫЕ ФИЛЬТРЫ (оставляем для совместимости) ---

def filter_by_date(items, date_key, target_date):
    return [item for item in items if item.get(date_key, '')[:10] == target_date]

def filter_by_period(items, date_key, date_from, date_to):
    dt_from = datetime.strptime(date_from, "%Y-%m-%d")
    dt_to = datetime.strptime(date_to, "%Y-%m-%d")
    filtered = []
    for item in items:
        dt_item = item.get(date_key, '')[:10]
        try:
            dt = datetime.strptime(dt_item, "%Y-%m-%d")
            if dt_from <= dt <= dt_to:
                filtered.append(item)
        except Exception:
            continue
    return filtered

def filter_by_article(items, article_key, article):
    return [item for item in items if item.get(article_key, '') == article]

def filter_by_warehouse(items, warehouse_key, warehouse_name):
    return [item for item in items if item.get(warehouse_key, '') == warehouse_name]

def filter_by_brand(items, brand_key, brand_name):
    return [item for item in items if item.get(brand_key, '') == brand_name]

def filter_by_doc_type(items, doc_type_key, doc_type_name):
    return [item for item in items if item.get(doc_type_key, '') == doc_type_name]

def filter_by_gnumber(items, gnumber_key, gnumber_value):
    return [item for item in items if item.get(gnumber_key, '') == gnumber_value]

### --- КНОПКА НАЗАД (универсальный шаблон) ---

def FILTER_BACK_BUTTON(prev_callback=None):
    # prev_callback можно передавать для автоматизации возврата
    kb = [[InlineKeyboardButton("⬅️ Назад", callback_data="filter_back")]]
    return InlineKeyboardMarkup(kb)

### --- СЕЛЕКТОРЫ ДЛЯ ИНТЕРАКТИВНОГО ВЫБОРА ФИЛЬТРОВ ---

# --- Выбор даты/периода ---
async def select_date_or_period(update: Update, context: CallbackContext, user_id, next_callback, prev_callback=None):
    from scenes.calendar import calendar_menu
    # Можно реализовать как меню "день", "период", "месяц" или сразу календарь
    await calendar_menu(
        update, context,
        action_prefix="calendar_sales_period",
        title="Выберите дату или период",
        # после выбора календарь вызывает next_callback(date_from, date_to)
    )

# --- ВНИМАНИЕ: исправленный выбор артикула по индексу ---
async def select_article(update: Update, context: CallbackContext, user_id, next_callback, prev_callback=None, date_from=None, date_to=None, **kwargs):
    from wb_api import get_articles_list
    articles = await get_articles_list(user_id, date_from=date_from, date_to=date_to)
    context.user_data["articles_list"] = articles
    kb = [
        [InlineKeyboardButton(article[:32], callback_data=f"article_idx:{idx}")]
        for idx, article in enumerate(articles)
    ]
    kb.append([InlineKeyboardButton("Все", callback_data="article:all")])
    if prev_callback:
        kb.append([InlineKeyboardButton("⬅️ Назад", callback_data="filter_back")])
    await update.callback_query.edit_message_text(
        "Выберите артикул:",
        reply_markup=InlineKeyboardMarkup(kb)
    )

# --- ВНИМАНИЕ: исправленный выбор склада по индексу ---
async def select_warehouse(update: Update, context: CallbackContext, user_id, next_callback, prev_callback=None, date_from=None, date_to=None, article=None, **kwargs):
    from wb_api import get_warehouses_list
    warehouses = await get_warehouses_list(user_id, date_from=date_from, date_to=date_to, article=article)
    context.user_data["warehouses_list"] = warehouses
    kb = [
        [InlineKeyboardButton(wh[:32], callback_data=f"warehouse_idx:{idx}")]
        for idx, wh in enumerate(warehouses)
    ]
    kb.append([InlineKeyboardButton("Все", callback_data="warehouse:all")])
    if prev_callback:
        kb.append([InlineKeyboardButton("⬅️ Назад", callback_data="filter_back")])
    await update.callback_query.edit_message_text(
        "Выберите склад:",
        reply_markup=InlineKeyboardMarkup(kb)
    )

# --- Выбор бренда ---
async def select_brand(update: Update, context: CallbackContext, user_id, next_callback, prev_callback=None, date_from=None, date_to=None, article=None, warehouse=None, **kwargs):
    from wb_api import get_brands_list
    brands = await get_brands_list(user_id, date_from=date_from, date_to=date_to, article=article, warehouse=warehouse)
    kb = [
        [InlineKeyboardButton(brand, callback_data=f"brand:{brand}")]
        for brand in brands
    ]
    kb.append([InlineKeyboardButton("Все", callback_data="brand:all")])
    if prev_callback:
        kb.append([InlineKeyboardButton("⬅️ Назад", callback_data="filter_back")])
    await update.callback_query.edit_message_text(
        "Выберите бренд:",
        reply_markup=InlineKeyboardMarkup(kb)
    )

# --- Выбор типа документа ---
async def select_doc_type(update: Update, context: CallbackContext, user_id, next_callback, prev_callback=None, date_from=None, date_to=None, article=None, warehouse=None, brand=None, **kwargs):
    # Типы документов можешь сделать динамическими — пример для статического списка:
    doc_types = ["Продажа", "Возврат", "Корректировка"]
    kb = [
        [InlineKeyboardButton(doc_type, callback_data=f"doc_type:{doc_type}")]
        for doc_type in doc_types
    ]
    kb.append([InlineKeyboardButton("Все", callback_data="doc_type:all")])
    if prev_callback:
        kb.append([InlineKeyboardButton("⬅️ Назад", callback_data="filter_back")])
    await update.callback_query.edit_message_text(
        "Выберите тип документа:",
        reply_markup=InlineKeyboardMarkup(kb)
    )
