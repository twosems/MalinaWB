import httpx

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
    :param api_key: API ключ WB
    :param date_from: Дата начала (строка "YYYY-MM-DD")
    :param date_to: Дата окончания (строка "YYYY-MM-DD")
    :param article: (опционально) Артикул продавца (строка)
    :param progress_callback: (опционально) функция для уведомлений о ходе (может быть None)
    :return: Список словарей — строки фин.отчета
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
                batch = [row for row in batch if row.get("sa_name", "").lower() == article.lower()]
            results.extend(batch)
            params["rrdid"] = batch[-1]["rrd_id"]
            if progress_callback:
                await progress_callback(f"Получено строк: {len(results)}")
    return results
