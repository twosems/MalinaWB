from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import ContextTypes

def ads_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Назад", callback_data="reports_menu")]
    ])

async def ads_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text(
        "📣 <b>Отчёт по рекламе</b>\n\nВетка в разработке.",
        reply_markup=ads_keyboard(),
        parse_mode="HTML"
    )
