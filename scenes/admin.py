from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import ContextTypes
from db import get_all_users, ban_user, unban_user, add_days
from utils import paginate, safe_edit_message_text
from datetime import datetime
from telegram.error import BadRequest

ADMIN_REPORT_KEY = "admin_users"
PAGE_SIZE = 10

def is_admin(user_id):
    from config import ADMINS
    return user_id in ADMINS

def build_user_text(user):
    status = []
    if user.get("is_banned"):
        status.append("🚫 Забанен")
    if user.get("sub_until"):
        until = datetime.fromisoformat(user["sub_until"])
        days_left = (until - datetime.now()).days
        if days_left > 0:
            status.append(f"✅ Подписка: {days_left} дн.")
    if user.get("trial_used"):
        status.append("💡 Был пробный доступ")
    status_text = ", ".join(status) if status else "—"
    return f"👤 ID: <code>{user['user_id']}</code>\n" \
           f"📛 Username: @{user.get('username') or 'нет'}\n" \
           f"Статус: {status_text}"

def build_user_list_keyboard(page_items, page, total_pages):
    buttons = []
    # Кнопки выбора пользователей
    for user in page_items:
        label = user.get("username") or str(user["user_id"])
        buttons.append([InlineKeyboardButton(label, callback_data=f"select_user:{user['user_id']}")])

    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"{ADMIN_REPORT_KEY}:{page-1}"))
    if page + 1 < total_pages:
        nav_buttons.append(InlineKeyboardButton("Вперёд ➡️", callback_data=f"{ADMIN_REPORT_KEY}:{page+1}"))
    if nav_buttons:
        buttons.append(nav_buttons)

    buttons.append([InlineKeyboardButton("⬅️ В меню", callback_data="main_menu")])

    return InlineKeyboardMarkup(buttons)

def build_user_control_keyboard(user_id):
    buttons = [
        [
            InlineKeyboardButton("🚫 Забанить", callback_data=f"ban:{user_id}"),
            InlineKeyboardButton("✅ Разбанить", callback_data=f"unban:{user_id}")
        ],
        [
            InlineKeyboardButton("+30 дней", callback_data=f"add30:{user_id}")
        ],
        [
            InlineKeyboardButton("⬅️ Назад к списку", callback_data=f"{ADMIN_REPORT_KEY}:0"),
            InlineKeyboardButton("⬅️ В меню", callback_data="main_menu")
        ]
    ]
    return InlineKeyboardMarkup(buttons)

async def admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("🚫 У вас нет доступа к админке.")
        return

    users = get_all_users()
    page = 0
    page_items, total_pages, page = paginate(users, page, PAGE_SIZE)
    text = "Список пользователей:\n\n"
    text += "\n\n".join(build_user_text(u) for u in page_items)
    await update.message.reply_text(
        text or "Пользователей нет.",
        reply_markup=build_user_list_keyboard(page_items, page, total_pages),
        parse_mode="HTML"
    )

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data

    if not is_admin(user_id):
        await query.answer("🚫 Нет доступа.")
        return

    if data == "main_menu":
        await query.answer()
        from scenes.start import start
        await start(update, context)
        return

    if data.startswith(f"{ADMIN_REPORT_KEY}:"):
        page = int(data.split(":")[1])
        users = get_all_users()
        page_items, total_pages, page = paginate(users, page, PAGE_SIZE)
        text = "Список пользователей:\n\n"
        text += "\n\n".join(build_user_text(u) for u in page_items)
        await safe_edit_message_text(
            query,
            text,
            reply_markup=build_user_list_keyboard(page_items, page, total_pages),
            parse_mode="HTML"
        )
        await query.answer()
        return

    if data.startswith("select_user:"):
        target_id = int(data.split(":")[1])
        users = get_all_users()
        target_user = next((u for u in users if u["user_id"] == target_id), None)
        if not target_user:
            await query.answer("Пользователь не найден")
            return
        text = build_user_text(target_user)
        await safe_edit_message_text(
            query,
            text,
            reply_markup=build_user_control_keyboard(target_id),
            parse_mode="HTML"
        )
        await query.answer()
        return

    if data.startswith("ban:"):
        target_id = int(data.split(":")[1])
        ban_user(target_id)
        await query.answer(f"Пользователь {target_id} забанен.")
        await refresh_user_list(query, context)
        return

    if data.startswith("unban:"):
        target_id = int(data.split(":")[1])
        unban_user(target_id)
        await query.answer(f"Пользователь {target_id} разбанен.")
        await refresh_user_list(query, context)
        return

    if data.startswith("add30:"):
        target_id = int(data.split(":")[1])
        add_days(target_id, 30)
        await query.answer(f"Пользователю {target_id} добавлено 30 дней подписки.")
        await refresh_user_list(query, context)
        return

async def refresh_user_list(query, context):
    users = get_all_users()
    page = 0
    page_items, total_pages, page = paginate(users, page, PAGE_SIZE)
    text = "Список пользователей:\n\n"
    text += "\n\n".join(build_user_text(u) for u in page_items)
    await safe_edit_message_text(
        query,
        text,
        reply_markup=build_user_list_keyboard(page_items, page, total_pages),
        parse_mode="HTML"
    )
