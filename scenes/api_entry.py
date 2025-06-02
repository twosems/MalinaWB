from telegram.ext import ConversationHandler
from user_storage import set_api
from scenes.account import account_menu

ENTER_API = 1

async def api_entry_start(update, context):
    """FSM старт: пользователь хочет добавить или изменить API"""
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        "Пожалуйста, отправьте свой <b>новый API-ключ</b> (его можно скопировать в личном кабинете WB):",
        parse_mode="HTML"
    )
    return ENTER_API

async def api_entry_finish(update, context):
    api = update.message.text.strip()
    user_id = update.effective_user.id
    set_api(user_id, api)
    await update.message.reply_text("API-ключ сохранён! Теперь доступны все функции.")
    await account_menu(update, context)
    return ConversationHandler.END
