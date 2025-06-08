from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import ContextTypes
from user_storage import days_left, get_user, get_api, is_trial_active, trial_left_minutes
from scenes.payment import payment_menu
from utils import safe_edit_message_text
from db import create_user   # <--- добавлено

def account_keyboard(api_set, balance, trial_active):
    kb = []
    if balance == 0 and not trial_active:
        kb.append([InlineKeyboardButton("💳 Оплатить подписку", callback_data="pay_menu")])
    else:
        if api_set:
            kb.append([
                InlineKeyboardButton("📊 Отчёты", callback_data="reports_menu"),
                InlineKeyboardButton("✏️ Изменить API-ключ", callback_data="api_change"),
                InlineKeyboardButton("❌ Удалить API", callback_data="api_remove"),
            ])
        else:
            kb.append([InlineKeyboardButton("🔑 Ввести API", callback_data="api_entry")])
    kb.append([InlineKeyboardButton("⬅️ На старт", callback_data="main_menu")])
    return InlineKeyboardMarkup(kb)

async def account_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or ""
    create_user(user_id, username)  # <-- создаём пользователя в БД, если его нет

    user = get_user(user_id) or {}  # <-- безопасное получение данных пользователя
    balance = days_left(user_id)
    api = user.get("api_key")
    api_set = bool(api)
    trial_active = is_trial_active(user_id)

    if balance > 0:
        status = f"Баланс: <b>{balance} дн.</b>"
    elif trial_active:
        mins = trial_left_minutes(user_id)
        status = f"Пробный доступ: <b>{mins} мин.</b> осталось"
    else:
        await payment_menu(update, context)
        return

    if api_set:
        text = (
            f"👤 <b>Ваш аккаунт</b>\n"
            f"{status}\n\n"
            f"API-ключ добавлен ✅\n"
            "<b>Ваш API:</b>\n"
            f"<code>{api}</code>\n\n"
            "Вы можете изменить или удалить ключ."
        )
    else:
        text = (
            f"👤 <b>Ваш аккаунт</b>\n"
            f"{status}\n\n"
            "🚨 <b>API-ключ не введён</b>!\n"
            "Чтобы пользоваться ботом, добавьте ваш API-ключ WB. "
            "Где его взять — см. <a href='https://seller.wildberries.ru/supplier-settings/access-to-api'>инструкцию</a>."
        )

    if update.callback_query:
        await safe_edit_message_text(
            update.callback_query, text, reply_markup=account_keyboard(api_set, balance, trial_active), parse_mode="HTML", disable_web_page_preview=True
        )
    else:
        await update.message.reply_text(
            text, reply_markup=account_keyboard(api_set, balance, trial_active), parse_mode="HTML", disable_web_page_preview=True
        )
