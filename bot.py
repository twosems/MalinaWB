from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    ConversationHandler, MessageHandler, filters
)
from scenes.start import start
from scenes.payment import payment_menu, payment_invoice, payment_trial_activate
from scenes.account import account_menu
from scenes.api_entry import api_entry_start, api_entry_finish, ENTER_API
from scenes.reports.menu import reports_menu
from scenes.reports.remains import remains_menu
from scenes.reports.sales import sales_callback  # <-- Импорт изменён
from scenes.reports.ads import ads_menu
from scenes.reports.storage import storage_menu
from scenes.reports.profit import profit_menu
from user_storage import days_left, get_api, del_api, is_trial_active, get_user
import config

# Для работы с БД
from db import init_db, create_user
init_db()

# Импорт админки
from scenes.admin import admin_start, admin_callback

async def callback_router(update, context):
    user_id = update.effective_user.id
    username = update.effective_user.username or ""
    create_user(user_id, username)

    user = get_user(user_id) or {}
    if user.get("is_banned") == 1:
        await update.callback_query.answer("🚫 Ваш аккаунт заблокирован. Обратитесь к администратору.")
        return

    data = update.callback_query.data
    balance = days_left(user_id)
    api_set = bool(get_api(user_id))

    # Обработка обычных кнопок
    if data == "start_btn":
        if balance == 0 and not is_trial_active(user_id):
            await payment_menu(update, context)
        else:
            await account_menu(update, context)
    elif data == "main_menu":
        await start(update, context)
    elif data == "pay_menu":
        await payment_menu(update, context)
    elif data == "pay_invoice":
        await payment_invoice(update, context)
    elif data == "trial_activate":
        await payment_trial_activate(update, context)
    elif data == "account_menu":
        if balance == 0 and not is_trial_active(user_id):
            await payment_menu(update, context)
        else:
            await account_menu(update, context)
    elif data == "api_remove":
        del_api(user_id)
        await account_menu(update, context)
    elif data == "reports_menu":
        await reports_menu(update, context)
    elif data == "remains_menu" or data.startswith("report:remains:"):
        await remains_menu(update, context)
    # Перенаправляем все sales_* колбеки в sales_callback
    elif data.startswith("sales_") or data.startswith("report:sales:"):
        await sales_callback(update, context)
    elif data == "ads_menu" or data.startswith("report:ads:"):
        await ads_menu(update, context)
    elif data == "storage_menu" or data.startswith("report:storage:"):
        await storage_menu(update, context)
    elif data == "profit_menu" or data.startswith("report:profit:"):
        await profit_menu(update, context)

    # Обработка админских callback (с префиксами)
    elif data.startswith("admin_users") or data.startswith("ban:") or data.startswith("unban:") or data.startswith("add30:") or data == "main_menu":
        await admin_callback(update, context)

    else:
        # Если сюда попали — это неизвестная команда, отвечаем "Пункт в разработке"
        await update.callback_query.answer("Пункт в разработке")

def main():
    app = ApplicationBuilder().token(config.TELEGRAM_TOKEN).build()

    # 1. Команда /start
    app.add_handler(CommandHandler("start", start))

    # 1.1 Команда /admin для админки
    app.add_handler(CommandHandler("admin", admin_start))

    # 2. FSM ConversationHandler для ввода API
    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(api_entry_start, pattern="^api_entry$")],
        states={ENTER_API: [MessageHandler(filters.TEXT & ~filters.COMMAND, api_entry_finish)]},
        fallbacks=[]
    ))

    # 3. CallbackQueryHandler для админских callback (с расширенным паттерном)
    app.add_handler(CallbackQueryHandler(admin_callback, pattern=r"^(admin_users|select_user:.*|ban:.*|unban:.*|add30:.*|main_menu)$"))

    # 4. CallbackQueryHandler для sales (отчёты по продажам)
    app.add_handler(CallbackQueryHandler(sales_callback, pattern=r"^(sales_menu|sales_main|sales_all|sales_articles|sales_articles_positive|sales_articles_all|sales_articles_page:.*|sales_article_select:.*|sales_period_.*|sales_date_select:.*|report:sales:.*)$"))

    # 5. CallbackQueryHandler для остальных callback (обычные кнопки)
    app.add_handler(CallbackQueryHandler(callback_router, pattern=r"^(start_btn|main_menu|pay_menu|pay_invoice|trial_activate|account_menu|api_remove|reports_menu|remains_menu|report:remains:.*|ads_menu|report:ads:.*|storage_menu|report:storage:.*|profit_menu|report:profit:.*)$"))

    print("Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
