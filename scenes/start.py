from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import ContextTypes
from db import create_user   # <-- добавили импорт

START_DESCRIPTION = (
    "🤖 <b>Добро пожаловать!</b>\n\n"
    "Это бот для автоматизации аналитики Wildberries. "
    "Вы можете получать подробные отчёты по остаткам, продажам, рекламе и прибыли."
    "\n\n"
    "Подробнее: <a href='https://your-landing-page.ru'>Официальная страница бота</a>\n\n"
    "Нажмите <b>Старт</b>, чтобы продолжить."
)

def start_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Старт", callback_data="start_btn")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # --- создание пользователя в БД ---
    user_id = update.effective_user.id
    username = update.effective_user.username or ""
    create_user(user_id, username)
    # --- конец добавления ---

    # Всегда показываем стартовую страницу — даже если есть подписка или trial
    if update.message:
        await update.message.reply_text(
            START_DESCRIPTION, reply_markup=start_keyboard(), parse_mode="HTML", disable_web_page_preview=True
        )
    else:
        await update.callback_query.edit_message_text(
            START_DESCRIPTION, reply_markup=start_keyboard(), parse_mode="HTML", disable_web_page_preview=True
        )
