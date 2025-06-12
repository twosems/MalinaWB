import httpx
import asyncio

# --- Основные запросы Wildberries ---

async def get_stocks(api_key, date_from="2019-06-20"):
    """
    Остатки товаров на складах
    """
    url = "https://statistics-api.wildberries.ru/api/v1/supplier/stocks"
    headers = {"Authorization": api_key}
    params = {"dateFrom": date_from}
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers, params=params)
        resp.raise_for_status()
        return resp.json()

async def get_sales(api_key, date_from):
    """
    Продажи (и возвраты)
    """
    url = "https://statistics-api.wildberries.ru/api/v1/supplier/sales"
    headers = {"Authorization": api_key}
    params = {"dateFrom": date_from}
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.get(url, headers=headers, params=params)
        resp.raise_for_status()
        return resp.json()

async def get_finance_report_data(api_key, date_from, date_to, article=None, progress_callback=None):
    """
    Загрузка строк фин. отчета WB за период (и, опционально, только по артикулу).
    """
    url = "https://statistics-api.wildberries.ru/api/v5/supplier/reportDetailByPeriod"
    headers = {"Authorization": api_key}
    params = {
        "dateFrom": date_from,
        "dateTo": date_to,
        "limit": 100000,
        "rrdid": 0
    }
    results = []
    while True:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.get(url, headers=headers, params=params)
            resp.raise_for_status()
            batch = resp.json()
            if not batch:
                break
            # Фильтрация по артикулу (sa_name)
            if article:
                batch = [row for row in batch if row.get('supplierArticle') == article]
            results.extend(batch)
            if len(batch) < params["limit"]:
                break
            params["rrdid"] = batch[-1].get("rrd_id", 0)
            if progress_callback:
                await progress_callback(len(results))
    return results

# --- Универсальные справочники для фильтров ---

async def get_articles_list(user_id, date_from=None, date_to=None, api_key=None):
    """
    Возвращает список уникальных артикулов пользователя за период.
    """
    if not api_key:
        from user_storage import get_api  # Должно возвращать API-ключ по user_id
        api_key = get_api(user_id)  # <-- исправлено!
    sales = await get_sales(api_key, date_from or "2022-01-01")
    articles = {item.get('supplierArticle', '') for item in sales if item.get('supplierArticle')}
    return sorted(articles)

async def get_warehouses_list(user_id, date_from=None, date_to=None, article=None, api_key=None):
    """
    Возвращает список складов из остатков или продаж.
    """
    if not api_key:
        from user_storage import get_api
        api_key = get_api(user_id)  # <-- исправлено!
    stocks = await get_stocks(api_key, date_from or "2022-01-01")
    warehouses = {item.get('warehouseName', '') for item in stocks if item.get('warehouseName')}
    return sorted(warehouses)

async def get_brands_list(user_id, date_from=None, date_to=None, article=None, warehouse=None, api_key=None):
    """
    Возвращает список брендов пользователя по продажам.
    """
    if not api_key:
        from user_storage import get_api
        api_key = get_api(user_id)  # <-- исправлено!
    sales = await get_sales(api_key, date_from or "2022-01-01")
    # Фильтрация по артикулу и складу, если заданы
    if article and article != 'all':
        sales = [s for s in sales if s.get('supplierArticle') == article]
    if warehouse and warehouse != 'all':
        sales = [s for s in sales if s.get('warehouseName') == warehouse]
    brands = {item.get('brand', '') for item in sales if item.get('brand')}
    return sorted(brands)

# --- Если нужны другие фильтры (doc_type и т.д.) — реализуй аналогично ---

async def get_paid_storage_report(api_key, date_from, date_to, article=None, warehouse=None):
    """
    Генерирует и получает отчёт о платном хранении по WB.
    """
    url = "https://statistics-api.wildberries.ru/api/v1/paid_storage"
    headers = {"Authorization": api_key}
    payload = {
        "dateFrom": date_from,
        "dateTo": date_to,
    }
    if article and article != "all":
        payload["supplierArticle"] = article
    if warehouse and warehouse != "all":
        payload["warehouseName"] = warehouse

    async with httpx.AsyncClient(timeout=60) as client:
        # 1. Создаём задачу на генерацию отчёта
        resp = await client.post(url, headers=headers, json=payload)
        if resp.status_code == 429:
            raise Exception("WB: Too many requests")
        resp.raise_for_status()
        # 2. Получаем task_id (идентификатор задачи)
        task_id = resp.json().get("task_id")
        if not task_id:
            raise Exception("Не удалось создать задачу на генерацию отчёта о хранении")
        # 3. Периодически проверяем статус задачи (готовность)
        for _ in range(10):  # до 20 сек (2 сек × 10)
            await asyncio.sleep(2)
            report_url = f"{url}/{task_id}/result"
            report_resp = await client.get(report_url, headers=headers)
            if report_resp.status_code == 200:
                return report_resp.json()
            elif report_resp.status_code == 202:
                continue  # Отчёт ещё не готов, ждём
            else:
                raise Exception("Ошибка получения отчёта о хранении")
        raise Exception("Превышено время ожидания отчёта. Попробуйте позже.")
