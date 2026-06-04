# Кондитерская «Сладкий Олимп» — Django-проект

## Запуск

### Вариант 1 — Docker (рекомендуется)

```bash
docker-compose up --build
```

Сайт будет доступен по адресу: **http://localhost:8000**

БД: SQLite (файл `/app/db/db.sqlite3` внутри контейнера, сохраняется в volume `sqlite_data`).

### Вариант 2 — Локально (без Docker)

```bash
pip install -r requirements.txt
mkdir -p db logs media staticfiles
python manage.py migrate
python manage.py seed_data
python manage.py runserver
```

## Учётные данные по умолчанию

| Роль          | Логин        | Пароль   |
|---------------|--------------|----------|
| Администратор | `admin`      | `admin123` |
| Сотрудник     | `ivanova_m`  | `pass1234` |
| Клиент        | `client1`    | `pass1234` |

## Структура

- `shop/` — товары, заказы, клиенты, сотрудники
- `users/` — кастомная модель пользователя
- `api/` — REST API (DRF)
- `main/` — главные страницы (главная, о нас, контакты и т.д.)
- `templates/` — HTML-шаблоны

## База данных

Используется **SQLite** — не требует установки дополнительных сервисов.
Файл базы: `db/db.sqlite3`
