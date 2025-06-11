# filters.py

from datetime import datetime

def filter_by_date(items, date_key, target_date):
    """
    Оставляет только те элементы, у которых поле date_key совпадает с target_date (строка "YYYY-MM-DD").
    """
    return [item for item in items if item.get(date_key, '')[:10] == target_date]

def filter_by_period(items, date_key, date_from, date_to):
    """
    Оставляет только те элементы, у которых поле date_key попадает в диапазон date_from...date_to (строки "YYYY-MM-DD").
    """
    dt_from = datetime.strptime(date_from, "%Y-%m-%d")
    dt_to = datetime.strptime(date_to, "%Y-%m-%d")
    filtered = []
    for item in items:
        dt_item = item.get(date_key, '')[:10]
        try:
            dt = datetime.strptime(dt_item, "%Y-%m-%d")
            if dt_from <= dt <= dt_to:
                filtered.append(item)
        except Exception:
            continue
    return filtered

def filter_by_article(items, article_key, article):
    """
    Оставляет только те элементы, у которых поле article_key совпадает с article.
    """
    return [item for item in items if item.get(article_key, '') == article]

def filter_by_warehouse(items, warehouse_key, warehouse_name):
    """
    Оставляет только те элементы, у которых поле warehouse_key совпадает с warehouse_name.
    """
    return [item for item in items if item.get(warehouse_key, '') == warehouse_name]

def filter_by_brand(items, brand_key, brand_name):
    """
    Оставляет только те элементы, у которых поле brand_key совпадает с brand_name.
    """
    return [item for item in items if item.get(brand_key, '') == brand_name]

def filter_by_doc_type(items, doc_type_key, doc_type_name):
    """
    Оставляет только те элементы, у которых поле doc_type_key совпадает с doc_type_name.
    """
    return [item for item in items if item.get(doc_type_key, '') == doc_type_name]

def filter_by_gnumber(items, gnumber_key, gnumber_value):
    """
    Оставляет только те элементы, у которых поле gnumber_key совпадает с gnumber_value (номер заказа).
    """
    return [item for item in items if item.get(gnumber_key, '') == gnumber_value]

# --- Пример интеграции с календарём (смотри scenes/calendar.py) ---
#
# При выборе даты:
# selected_date = datetime(year, month, day)
# filtered = filter_by_date(items, "date", selected_date.strftime("%Y-%m-%d"))
#
# При выборе диапазона:
# filtered = filter_by_period(items, "date", date_from, date_to)
#
# По артикулу:
# filtered = filter_by_article(items, "supplierArticle", art)
