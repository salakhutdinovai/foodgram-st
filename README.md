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

