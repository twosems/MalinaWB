import json
import os
from datetime import datetime, timedelta

USERS_FILE = "users.json"

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            text = f.read().strip()
            if not text:
                return {}
            return json.loads(text)
    except Exception:
        return {}

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def get_user(user_id):
    users = load_users()
    return users.get(str(user_id), {})

def save_user(user_id, data):
    users = load_users()
    users[str(user_id)] = data
    save_users(users)

def days_left(user_id):
    user = get_user(user_id)
    until = user.get("until")
    if until:
        dt_until = datetime.fromisoformat(until)
        left = (dt_until - datetime.now()).days
        if left > 0:
            return left
    return 0

def is_trial_active(user_id):
    user = get_user(user_id)
    trial_until = user.get("trial_until")
    if trial_until:
        dt_trial = datetime.fromisoformat(trial_until)
        if dt_trial > datetime.now():
            return True
    return False

def set_trial(user_id):
    user = get_user(user_id)
    if not user.get("trial_used"):
        trial_until = datetime.now() + timedelta(hours=1)
        user["trial_until"] = trial_until.isoformat()
        user["trial_used"] = True
        save_user(user_id, user)

def trial_left_minutes(user_id):
    user = get_user(user_id)
    trial_until = user.get("trial_until")
    if trial_until:
        dt_trial = datetime.fromisoformat(trial_until)
        left = int((dt_trial - datetime.now()).total_seconds() // 60)
        if left > 0:
            return left
    return 0

def mark_trial_used(user_id):
    user = get_user(user_id)
    user["trial_used"] = True
    save_user(user_id, user)

def set_api(user_id, api):
    user = get_user(user_id)
    user["api"] = api
    save_user(user_id, user)

def get_api(user_id):
    user = get_user(user_id)
    return user.get("api")

def del_api(user_id):
    user = get_user(user_id)
    if "api" in user:
        del user["api"]
    save_user(user_id, user)

def add_days(user_id, days):
    user = get_user(user_id)
    until = user.get("until")
    now = datetime.now()
    if until and datetime.fromisoformat(until) > now:
        base = datetime.fromisoformat(until)
    else:
        base = now
    user["until"] = (base + timedelta(days=days)).isoformat()
    save_user(user_id, user)
