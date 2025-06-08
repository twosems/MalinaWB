import sqlite3
from datetime import datetime, timedelta

DB_FILE = "malinawb.db"

def get_conn():
    return sqlite3.connect(DB_FILE)

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            api_key TEXT,
            sub_until TEXT,
            trial_until TEXT,
            trial_used INTEGER DEFAULT 0,
            is_banned INTEGER DEFAULT 0,
            created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def create_user(user_id, username=None):
    conn = get_conn()
    c = conn.cursor()
    c.execute('''
        INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)
    ''', (user_id, username))
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE user_id=?', (user_id,))
    row = c.fetchone()
    keys = [d[0] for d in c.description]
    conn.close()
    if not row:
        return None
    return dict(zip(keys, row))

def save_user(user_id, data):
    create_user(user_id)
    conn = get_conn()
    c = conn.cursor()
    fields = ', '.join([f"{k}=?" for k in data])
    values = list(data.values()) + [user_id]
    c.execute(f'UPDATE users SET {fields} WHERE user_id=?', values)
    conn.commit()
    conn.close()

def days_left(user_id):
    user = get_user(user_id)
    until = user.get("sub_until") if user else None
    if until:
        dt_until = datetime.fromisoformat(until)
        left = (dt_until - datetime.now()).days
        if left > 0:
            return left
    return 0

def is_trial_active(user_id):
    user = get_user(user_id)
    trial_until = user.get("trial_until") if user else None
    if trial_until:
        dt_trial = datetime.fromisoformat(trial_until)
        if dt_trial > datetime.now():
            return True
    return False

def set_trial(user_id, hours=1):
    user = get_user(user_id)
    if user and not user.get("trial_used"):
        trial_until = (datetime.now() + timedelta(hours=hours)).isoformat()
        save_user(user_id, {"trial_until": trial_until, "trial_used": 1})

def trial_left_minutes(user_id):
    user = get_user(user_id)
    trial_until = user.get("trial_until") if user else None
    if trial_until:
        dt_trial = datetime.fromisoformat(trial_until)
        left = int((dt_trial - datetime.now()).total_seconds() // 60)
        if left > 0:
            return left
    return 0

def mark_trial_used(user_id):
    save_user(user_id, {"trial_used": 1})

def set_api(user_id, api):
    save_user(user_id, {"api_key": api})

def get_api(user_id):
    user = get_user(user_id)
    return user.get("api_key") if user else None

def del_api(user_id):
    save_user(user_id, {"api_key": None})

def add_days(user_id, days):
    user = get_user(user_id)
    until = user.get("sub_until") if user else None
    now = datetime.now()
    if until and datetime.fromisoformat(until) > now:
        base = datetime.fromisoformat(until)
    else:
        base = now
    new_until = (base + timedelta(days=days)).isoformat()
    save_user(user_id, {"sub_until": new_until})

# --- Для админки/статистики ---

def get_all_users():
    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT * FROM users')
    keys = [d[0] for d in c.description]
    users = [dict(zip(keys, row)) for row in c.fetchall()]
    conn.close()
    return users

def get_stats():
    conn = get_conn()
    c = conn.cursor()
    stats = {}
    c.execute('SELECT COUNT(*) FROM users')
    stats["total"] = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM users WHERE trial_used=1')
    stats["trial"] = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM users WHERE sub_until IS NOT NULL AND sub_until > ?', (datetime.now().isoformat(),))
    stats["paid"] = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM users WHERE is_banned=1')
    stats["banned"] = c.fetchone()[0]
    conn.close()
    return stats

def ban_user(user_id):
    save_user(user_id, {"is_banned": 1})

def unban_user(user_id):
    save_user(user_id, {"is_banned": 0})

