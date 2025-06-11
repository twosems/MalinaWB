import asyncio
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import ContextTypes
from user_storage import get_api
from wb_api import get_sales  # Предполагается, что в wb_api есть функция get_sales
from utils import paginate, paginated_keyboard, page_info_str, safe_edit_message_text

REPORT_KEY = "sales"
PAGE_SIZE = 10

# --- Кнопки для главного меню отчёта продаж ---
def sales_main_keyboard():
    buttons = [
        [InlineKeyboardButton("📦 Отчёт по всем товарам", callback_data="sales_all")],
        [InlineKeyboardButton("🔢 Отчёт по артикулам", callback_data="sales_articles")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="reports_menu")]
    ]
    return InlineKeyboardMarkup(buttons)

# --- Кнопки выбора типа артикулов ---
def sales_articles_keyboard():
    buttons = [
        [InlineKeyboardButton("Артикулы с положительным остатком", callback_data="sales_articles_positive")],
        [InlineKeyboardButton("Все артикулы", callback_data="sales_articles_all")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="sales_main")]
    ]
    return InlineKeyboardMarkup(buttons)

# --- Кнопки выбора периода для отчёта всех товаров ---
def sales_period_keyboard():
    buttons = [
        [InlineKeyboardButton("По календарному месяцу", callback_data="sales_period_month")],
        [InlineKeyboardButton("По конкретному дню", callback_data="sales_period_day")],
        [InlineKeyboardButton("За произвольный период", callback_data="sales_period_custom")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="sales_main")]
    ]
    return InlineKeyboardMarkup(buttons)

# --- Кнопки навигации и назад для списка артикулов ---
def sales_articles_list_keyboard(page, total_pages):
    buttons = []
    # Навигация по страницам
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"sales_articles_page:{page-1}"))
    if page + 1 < total_pages:
        nav_buttons.append(InlineKeyboardButton("Вперёд ➡️", callback_data=f"sales_articles_page:{page+1}"))
    if nav_buttons:
        buttons.append(nav_buttons)
    # Кнопка назад
    buttons.append([InlineKeyboardButton("⬅️ Назад", callback_data="sales_articles")])
    return InlineKeyboardMarkup(buttons)

# --- Основная функция обработки callback для sales ---
async def sales_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id
    api_key = get_api(user_id)

    if not api_key:
        await query.answer("❗ Для просмотра отчётов нужен API-ключ.")
        return

    # Главный раздел отчёта продаж
    if data == "sales_main" or data == "sales_menu":
        await query.edit_message_text(
            "📊 <b>Отчёт по продажам</b>\nВыберите тип отчёта:",
            reply_markup=sales_main_keyboard(),
            parse_mode="HTML"
        )
        await query.answer()
        return

    # Отчёт по всем товарам — меню выбора периода
    if data == "sales_all":
        await query.edit_message_text(
            "Выберите период для отчёта по всем товарам:",
            reply_markup=sales_period_keyboard(),
            parse_mode="HTML"
        )
        await query.answer()
        return

    # Отчёт по артикулам — меню выбора типа артикула
    if data == "sales_articles":
        await query.edit_message_text(
            "Выберите тип артикулов для отчёта:",
            reply_markup=sales_articles_keyboard(),
            parse_mode="HTML"
        )
        await query.answer()
        return

    # Выбор конкретного типа артикула
    if data == "sales_articles_positive":
        # Получаем только артикулы с положительным остатком
        items = await get_sales_articles(api_key, positive_only=True)
        await show_articles_list(query, items, 0)
        return

    if data == "sales_articles_all":
        # Получаем все артикулы
        items = await get_sales_articles(api_key, positive_only=False)
        await show_articles_list(query, items, 0)
        return

    # Навигация по списку артикулов
    if data.startswith("sales_articles_page:"):
        page = int(data.split(":")[1])
        # Сохраним в context.user_data список артикулов, либо загрузим заново
        items = context.user_data.get("sales_articles_items")
        if not items:
            # На всякий случай
            items = await get_sales_articles(api_key, positive_only=False)
            context.user_data["sales_articles_items"] = items
        await show_articles_list(query, items, page)
        return

    # При выборе артикула — переходим к выбору даты для него
    if data.startswith("sales_article_select:"):
        article = data.split(":",1)[1]
        context.user_data["selected_article"] = article
        await show_date_selection(query, article)
        return

    # Выбор периода для отчёта всех товаров (тут нужно доработать под твои реалии)
    if data.startswith("sales_period_"):
        period = data.split("_", 1)[1]
        # Запускаем генерацию отчёта по выбранному периоду
        await generate_sales_report_all(query, api_key, period)
        return

    # Выбор даты для отчёта по артикулу
    if data.startswith("sales_date_select:"):
        date = data.split(":",1)[1]
        article = context.user_data.get("selected_article")
        if not article:
            await query.answer("Ошибка: артикул не выбран")
            return
        # Запускаем генерацию отчёта по артикулу и дате
        await generate_sales_report_article(query, api_key, article, date)
        return

    await query.answer("Пункт в разработке")


# --- Помощник для показа списка артикулов с пагинацией ---
async def show_articles_list(query, items, page):
    PAGE_SIZE_ARTICLES = 10
    context = query._bot_data or {}  # Получим context.user_data, но зависит от версии PTB

    if items is None or len(items) == 0:
        await query.edit_message_text("Нет доступных артикулов.")
        await query.answer()
        return

    page_items, total_pages, page = paginate(items, page, PAGE_SIZE_ARTICLES)
    buttons = []

    for art in page_items:
        buttons.append([InlineKeyboardButton(art, callback_data=f"sales_article_select:{art}")])

    kb = sales_articles_list_keyboard(page, total_pages)
    # Добавим кнопки выбора артикула
    kb.inline_keyboard = buttons + kb.inline_keyboard

    text = f"Список артикулов (страница {page+1} из {total_pages}):"
    await query.edit_message_text(text, reply_markup=kb, parse_mode="HTML")
    await query.answer()

# --- Пример функции получения артикулов (замени на реальный вызов API и логику) ---
async def get_sales_articles(api_key, positive_only=False):
    # Для примера — получаем остатки с API (замени на твой источник)
    stocks = await get_stocks(api_key)
    articles = set()
    for item in stocks:
        qty = item.get("quantity", 0)
        art = item.get("supplierArticle", "")
        if not art:
            continue
        if positive_only and qty <= 0:
            continue
        articles.add(art)
    # Отсортируем для удобства
    return sorted(articles)

# --- Показать меню выбора даты для артикула ---
async def show_date_selection(query, article):
    buttons = [
        [InlineKeyboardButton("По календарному месяцу", callback_data=f"sales_date_select:month")],
        [InlineKeyboardButton("По конкретному дню", callback_data=f"sales_date_select:day")],
        [InlineKeyboardButton("За произвольный период", callback_data=f"sales_date_select:custom")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="sales_articles")]
    ]
    text = f"Выберите период для артикула <b>{article}</b>:"
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="HTML")
    await query.answer()

# --- Генерация отчёта по всем товарам ---
async def generate_sales_report_all(query, api_key, period):
    # TODO: Реализуй логику получения данных по всем товарам и периодам
    await query.answer(f"Генерация отчёта по всем товарам за период: {period}")
    await query.edit_message_text(f"Здесь будет отчёт по всем товарам за период: <b>{period}</b>", parse_mode="HTML")

# --- Генерация отчёта по артикулу и дате ---
async def generate_sales_report_article(query, api_key, article, date):
    # TODO: Реализуй логику получения данных по артикулу и дате
    await query.answer(f"Генерация отчёта по артикулу {article} за период: {date}")
    await query.edit_message_text(f"Здесь будет отчёт по артикулу <b>{article}</b> за период: <b>{date}</b>", parse_mode="HTML")
