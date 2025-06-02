from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import ContextTypes

def sales_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Назад", callback_data="reports_menu")]
    ])

async def sales_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text(
        "💸 <b>Отчёт по продажам</b>\n\nВетка в разработке.",
        reply_markup=sales_keyboard(),
        parse_mode="HTML"
    )
