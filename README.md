# Marketplace API (HW2)

REST API маркетплейса с JWT-аутентификацией и ролевой моделью доступа.

## Стек технологий

* FastAPI
* Python 3.10+
* JWT (PyJWT)
* Pydantic
* HTTP Bearer Authentication

---

# Реализованный функционал

## Аутентификация

### Регистрация

`POST /auth/register`

* email
* password
* role (USER / SELLER / ADMIN)

### Логин

`POST /auth/login`

Возвращает:

* access_token
* refresh_token

### Refresh токена

`POST /auth/refresh`

* Принимает refresh_token
* Выдаёт новый access_token

---

##  JWT

Access token содержит:

* `sub` — user_id
* `role` — роль пользователя
* `type` — access
* `exp` — срок действия

Refresh token:

* `sub`
* `type` — refresh
* `exp`

Ошибки:

* `TOKEN_EXPIRED`
* `TOKEN_INVALID`
* `REFRESH_TOKEN_INVALID`

---

# Ролевая модель доступа (RBAC)

Три роли:

* USER
* SELLER
* ADMIN

Роль передаётся в JWT (claim `role`).

При недостаточных правах возвращается:

```json
{
  "error_code": "ACCESS_DENIED"
}
```

HTTP статус: `403`

---

# Products API

## GET /products

Доступ: USER, SELLER, ADMIN
Возвращает список всех товаров.

## GET /products/{id}

Доступ: USER, SELLER, ADMIN

## POST /products

* SELLER — может создавать только свои товары
* ADMIN — может создавать любые
* USER — запрещено

## PUT /products/{id}

* SELLER — может редактировать только свои товары
* ADMIN — любые
* USER — запрещено

## DELETE /products/{id}

* SELLER — может удалять только свои товары
* ADMIN — любые
* USER — запрещено

В таблице продукта есть поле `seller_id`.

---

# Orders API

## POST /orders

* USER — может создавать заказы
* ADMIN — может
* SELLER — запрещено

## GET /orders/{id}

* USER — только свои заказы
* ADMIN — любые
* SELLER — запрещено

## PUT /orders/{id}

* USER — только свои
* ADMIN — любые
* SELLER — запрещено

## POST /orders/{id}/cancel

* USER — только свои
* ADMIN — любые
* SELLER — запрещено

---

# Promo Codes

## POST /promo-codes

* SELLER — разрешено
* ADMIN — разрешено
* USER — запрещено

Промокод применяет процентную скидку к заказу.

---

# Запуск проекта

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Запуск сервера

```bash
uvicorn main:app --reload
```

### 3. Swagger UI

Открыть в браузере:

```
http://127.0.0.1:8000/docs
```

---

# Архитектурные особенности

* In-memory базы данных (dict)
* JWT с разделением access/refresh
* Role-based access control
* Централизованная проверка токена через Depends
* Обработка ошибок через HTTPException

---

# Статус выполнения

Реализованы пункты:

* 1–6
* 8–10

Полная ролевая модель согласно матрице доступа.

---

# Ограничения

* Пароли хранятся без хеширования (упрощение для учебного проекта)
* Refresh токены не инвалидируются
* Данные не сохраняются между перезапусками (in-memory)

---

# Итог

Проект реализует:

* JWT-аутентификацию
* Refresh механизм
* Полный CRUD для продуктов
* Полный CRUD для заказов
* Ролевую модель доступа
* Промокоды
* Корректную обработку ошибок
