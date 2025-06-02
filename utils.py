from telegram import InlineKeyboardMarkup, InlineKeyboardButton
import config
import telegram

def landing_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("▶️ Старт", callback_data="start_btn")],
        [InlineKeyboardButton("ℹ️ О боте", url=config.LANDING_URL)]
    ])

# Безопасное редактирование сообщения (не падает, если "Message is not modified")
async def safe_edit_message_text(message_or_query, *args, **kwargs):
    try:
        # message_or_query может быть либо Message, либо CallbackQuery
        if hasattr(message_or_query, "edit_message_text"):
            return await message_or_query.edit_message_text(*args, **kwargs)
        elif hasattr(message_or_query, "message") and hasattr(message_or_query.message, "edit_text"):
            return await message_or_query.message.edit_text(*args, **kwargs)
    except telegram.error.BadRequest as e:
        if "Message is not modified" in str(e):
            pass  # Просто игнорируем
        else:
            raise
