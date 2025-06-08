from db import (
    create_user, get_user, save_user,
    days_left, is_trial_active, set_trial, trial_left_minutes,
    mark_trial_used, set_api, get_api, del_api, add_days
)

def get_user_data(user_id):
    user = get_user(user_id)
    return user if user else {}

def save_user_data(user_id, data):
    save_user(user_id, data)

def days_left_for_user(user_id):
    return days_left(user_id)

def is_user_trial_active(user_id):
    return is_trial_active(user_id)

def set_user_trial(user_id, hours=1):
    set_trial(user_id, hours=hours)

def trial_minutes_left(user_id):
    return trial_left_minutes(user_id)

def mark_user_trial_used(user_id):
    mark_trial_used(user_id)

def set_user_api(user_id, api):
    set_api(user_id, api)

def get_user_api(user_id):
    return get_api(user_id)

def del_user_api(user_id):
    del_api(user_id)

def add_days_for_user(user_id, days):
    add_days(user_id, days)
