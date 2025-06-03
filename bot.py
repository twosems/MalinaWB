from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    ConversationHandler, MessageHandler, filters
)
from scenes.start import start
from scenes.payment import payment_menu, payment_invoice, payment_trial_activate
from scenes.account import account_menu
from scenes.api_entry import api_entry_start, api_entry_finish, ENTER_API
from scenes.reports.menu import reports_menu
from scenes.reports.remains import remains_report
from scenes.reports.storage import storage_report
from scenes.reports.sales import sales_menu
from scenes.reports.ads import ads_menu
from scenes.reports.profit import profit_menu
from user_storage import days_left, get_api, del_api, is_trial_active
import config

# Универсальный handler для всех отчетов с пагинацией
async def report_router(update, context):
    data = update.callback_query.data
    # Формат: report:<report_key>:<page>
    try:
        _, report_key, page = data.split(":")
        page = int(page)
    except Exception:
        await update.callback_query.answer("Некорректный запрос.")
        return

    # Запуск нужного отчета по ключу
    if report_key == "remains":
        await remains_report(update, context, page)
    elif report_key == "storage":
        await storage_report(update, context, page)
    # Добавляй новые отчеты тут по аналогии:
    # elif report_key == "sales":
    #     await sales_report(update, context, page)
    else:
        await update.callback_query.answer("Неизвестный отчёт.")

# Старый общий роутер для других callback'ов
async def callback_router(update, context):
    data = update.callback_query.data
    user_id = update.effective_user.id
    balance = days_left(user_id)
    api_set = bool(get_api(user_id))

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
    elif data == "sales_menu":
        await sales_menu(update, context)
    elif data == "ads_menu":
        await ads_menu(update, context)
    elif data == "profit_menu":
        await profit_menu(update, context)
    else:
        await update.callback_query.answer("Пункт в разработке")

def main():
    app = ApplicationBuilder().token(config.TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(api_entry_start, pattern="^api_entry$")],
        states={ENTER_API: [MessageHandler(filters.TEXT & ~filters.COMMAND, api_entry_finish)]},
        fallbacks=[]
    ))

    # Универсальный пагинатор для всех report:...
    app.add_handler(CallbackQueryHandler(report_router, pattern="^report:"))
    app.add_handler(CallbackQueryHandler(reports_menu, pattern="^reports_menu$"))

    # Остальные callback-и через роутер
    app.add_handler(CallbackQueryHandler(callback_router))

    print("Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()