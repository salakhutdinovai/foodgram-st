# ДЛЯ **ЗАПУСКА** **POSTMAN_COLLECTION** В SETTINGS.PY - **РАСКОММЕНТИРОВАТЬ** НАСТРОЙКУ POSTGRESQL И **ЗАКОММЕНТИРОВАТЬ** SQLITE НАСТРОЙКУ!!!
# ПОДНИМИТЕ POSTGRESQL, ВВЕДИТЕ **ЮЗЕРНЕЙМ** И **ПАРОЛЬ** ОТ POSTGRESQL В SETTINGS.PY, СДЕЛАЙТЕ `manage.py migrate`, **ЗАПУСТИТЕ ДЖАНГО СЕРВЕР, ЗАПУСТИТЕ КОЛЛЕКЦИЮ ТЕСТОВ POSTMAN**

# Foodgram - сервис для публикации рецептов

## Описание проекта
Foodgram - это веб-приложение, где пользователи могут публиковать свои рецепты, подписываться на других авторов, добавлять рецепты в избранное и формировать список покупок.

## Технологии
- Python 3.9
- Django 3.2
- Django REST Framework
- PostgreSQL
- Docker
- Nginx
- React

## Запуск проекта

### Локальный запуск (без Docker)

1. Клонируйте репозиторий:
```bash
git clone https://github.com/your-username/foodgram-aim.git
cd foodgram-aim
```

2. Создайте и активируйте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # для Linux/Mac
venv\Scripts\activate     # для Windows
```

3. Установите зависимости:
```bash
cd backend
pip install -r requirements.txt
```

4. Создайте файл .env в директории backend/ со следующими переменными:
```
DEBUG=True
SECRET_KEY=your-secret-key
DB_ENGINE=django.db.backends.postgresql
DB_NAME=foodgram
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432
```

5. Примените миграции:
```bash
python manage.py migrate
```

6. Создайте суперпользователя:
```bash
python manage.py createsuperuser
```

7. Загрузите ингредиенты в базу данных:
```bash
python manage.py load_ingredients
```

8. Запустите сервер разработки:
```bash
python manage.py runserver
```

### Запуск с использованием Docker

1. Установите Docker и Docker Compose на вашу систему.

2. Создайте файл .env в директории infra/ со следующими переменными:
```
DEBUG=False
SECRET_KEY=your-secret-key
DB_ENGINE=django.db.backends.postgresql
DB_NAME=foodgram
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-password
DB_HOST=db
DB_PORT=5432
```

3. Запустите проект:
```bash
cd infra
docker-compose up
```

После запуска:
- Фронтенд будет доступен по адресу: http://localhost
- API документация: http://localhost/api/docs/
- Админ-панель: http://localhost/admin/

## Дополнительная информация

### Загрузка данных
Для загрузки ингредиентов в базу данных используйте команду:
```bash
python manage.py load_ingredients
```

### API Endpoints
Основные эндпоинты API:
- `/api/users/` - управление пользователями
- `/api/recipes/` - управление рецептами
- `/api/ingredients/` - список ингредиентов
- `/api/tags/` - список тегов

### Администрирование
Для доступа к админ-панели используйте учетные данные суперпользователя, созданного при настройке проекта.

# Новые возможности и интеграции

## 1. Новые API эндпоинты

- **/api/users/{id}/info/** — GET, информация о пользователе по id (публично)
- **/api/users/without_recipes/** — GET, список пользователей без рецептов (публично)
- **/api/recipes/filter_by_ingredients/?ingredients=1,2,3** — GET, рецепты с любым из указанных ингредиентов (публично)
- **/api/auth/password-reset/** — POST, сброс пароля по email (публично)
- **/api/password-reset-confirm/{user_id}/{token}/** — POST, подтверждение сброса пароля (публично)

## 2. WebSocket-функционал

- **ws://<host>/ws/echo/** — EchoConsumer: возвращает обратно любое полученное сообщение
- **ws://<host>/ws/notify/** — NotifyConsumer: отправляет приветствие при подключении и уведомление при получении сообщения

## 3. Google OAuth2 (Вход через Google)

- Поддержка входа через Google-аккаунт с помощью social-auth-app-django
- Настроены все необходимые параметры, client_id и client_secret
- Для работы нужно добавить redirect_uri вида:
  - `http://127.0.0.1:8000/api/auth/complete/google-oauth2/` (или ваш production-адрес) в Google Cloud Console
- URL для входа: `/api/auth/login/google-oauth2/`

## 4. Публичные GET API

- Все GET-запросы (включая кастомные action-методы) теперь доступны без авторизации

## 5. GitHub Actions: автоматическое тестирование

- В проект добавлен workflow `.github/workflows/tests.yml`
- При каждом push/pull request в main:
  - Разворачивается PostgreSQL
  - Устанавливаются зависимости
  - Применяются миграции
  - Запускаются Django unittest (`python backend/manage.py test`)

---

**Все новые возможности подробно описаны выше в README. Если нужно добавить примеры запросов или расширить документацию — дайте знать!**

