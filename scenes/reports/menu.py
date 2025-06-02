from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import ContextTypes

def reports_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📦 Остатки товара", callback_data="remains_menu")],
        [InlineKeyboardButton("💸 Отчёт по продажам", callback_data="sales_menu")],
        [InlineKeyboardButton("📣 Отчёт по рекламе", callback_data="ads_menu")],
        [InlineKeyboardButton("📦 Отчёт по хранению", callback_data="storage_menu")],
        [InlineKeyboardButton("💰 Отчёт по прибыли", callback_data="profit_menu")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="account_menu")]
    ])

async def reports_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text(
        "📊 <b>Раздел отчётов</b>\n\nВыберите тип отчёта:",
        reply_markup=reports_keyboard(),
        parse_mode="HTML"
    )
