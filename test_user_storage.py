import httpx
import time

API_KEY = "eyJhbGciOiJFUzI1NiIsImtpZCI6IjIwMjUwNTIwdjEiLCJ0eXAiOiJKV1QifQ.eyJlbnQiOjEsImV4cCI6MTc2NDI1NzI4NiwiaWQiOiIwMTk3MWExNS0zMjhkLTcwNzgtYmNkMS01NjdmN2E5YzQxNmYiLCJpaWQiOjY1MjgzMzMsIm9pZCI6Mjc0MzIzLCJzIjozNiwic2lkIjoiOWM2NjI4MjMtOTM2MC00YTg1LTg2NmUtM2U2YzM0OGU5ODhiIiwidCI6ZmFsc2UsInVpZCI6NjUyODMzM30.FYgzJRhFgl9VhQH7szvLTU5Wrz10l7Jb3dqK_TV3FV2VWnmsSU4FPvROVAuaAUFmL9zRxwCHKhj2neXBGTJFug"  # твой ключ

def get_remains():
    url_create = "https://seller-analytics-api.wildberries.ru/api/v1/warehouse_remains"
    headers = {"Authorization": API_KEY}
    resp = httpx.get(url_create, headers=headers, timeout=30)
    print("Создание отчёта:", resp.status_code, resp.text)
    if resp.status_code != 200:
        print("Ошибка создания отчёта")
        return
    task_id = resp.json()["data"]["taskId"]

    # Пробуем новый путь статуса
    url_status = f"https://seller-analytics-api.wildberries.ru/api/v1/warehouse_remains/{task_id}/status"
    while True:
        resp = httpx.get(url_status, headers=headers, timeout=30)
        print("Статус отчёта:", resp.status_code, resp.text)
        if resp.status_code != 200:
            print("Ошибка проверки статуса")
            return
        if resp.json()["data"]["status"] == "DONE":
            break
        time.sleep(1)

    url_result = f"https://seller-analytics-api.wildberries.ru/api/v1/warehouse_remains/{task_id}/result"
    resp = httpx.get(url_result, headers=headers, timeout=30)
    print("Результат:", resp.status_code)
    print(resp.text)

if __name__ == "__main__":
    get_remains()
