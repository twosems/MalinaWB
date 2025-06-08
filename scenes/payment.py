from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import ContextTypes
from user_storage import is_trial_active, set_trial, trial_left_minutes, get_user
from utils import safe_edit_message_text
from db import create_user  # <--- добавили импорт

def payment_keyboard(user_id):
    user = get_user(user_id) or {}  # <--- теперь всегда dict
    kb = [[InlineKeyboardButton("💳 Оплатить", callback_data="pay_invoice")]]
    if not user.get("trial_used"):
        kb.append([InlineKeyboardButton("💡 Попробовать бесплатно (1 час)", callback_data="trial_activate")])
    kb.append([InlineKeyboardButton("⬅️ На старт", callback_data="main_menu")])
    return InlineKeyboardMarkup(kb)

async def payment_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or ""
    create_user(user_id, username)  # <--- Гарантия, что пользователь будет создан
    trial_active = is_trial_active(user_id)
    msg = (
        "🔒 <b>Доступ к функциям бота платный.</b>\n"
        "Стоимость: <b>450₽/месяц</b>\n\n"
        "Вы можете оплатить подписку, либо воспользоваться <b>1 часом бесплатного доступа</b> для знакомства с ботом."
    )
    if trial_active:
        mins = trial_left_minutes(user_id)
        msg += f"\n\n💡 <b>У вас сейчас активирован пробный доступ: осталось {mins} мин.</b>"
    await safe_edit_message_text(
        update.callback_query, msg, reply_markup=payment_keyboard(user_id), parse_mode="HTML"
    )

async def payment_invoice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer("Функция оплаты пока не реализована.")

from scenes.account import account_menu

async def payment_trial_activate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or ""
    create_user(user_id, username)  # <--- На всякий случай!
    set_trial(user_id)
    await update.callback_query.answer("Пробный доступ на 1 час активирован!")
    await account_menu(update, context)
