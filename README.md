## Ссылка на сайт
https://foodgramyus.ddns.net/

## Технологии:

- Python

- Django

- DjangoRestFramework

- PostgresSQL

- Nginx

- Docker

- Docker-compose

- DockerHub

## Запуск проекта локально:

**1. Клонировать репозиторий и перейти в него в командной строке:**
```
git clone git@github.com:Filosf/foodgram-project-react.git
```
**2. В терминале перейдите в каталог:**
```
cd .../foodgram-project-react/infra
```
**3. Создать файл .env для хранения ключей:**
```
DEBUG_STATUS = False, еcли планируете использовать проект для разработки укажите  True
SECRET_KEY = 'секретный ключ Django проекта'
DB_ENGINE=django.db.backends.postgresql # указываем, что используем postgresql
DB_NAME=postgres # указываем имя созданной базы данных
POSTGRES_USER=postgres # указываем имя своего пользователя для подключения к БД
POSTGRES_PASSWORD=postgres # устанавливаем свой пароль для подключения к БД
DB_HOST=db # указываем название сервиса (контейнера)
DB_PORT=5432 # указываем порт для подключения к БД 
```

**4. Запустите окружение:**
- Запустите docker-compose, развёртывание контейнеров выполниться в «фоновом режиме»:

```
docker-compose up
```

- выполните миграции:

```
docker-compose exec backend python manage.py makemigrations
docker-compose exec backend python manage.py migrate
```

- соберите статику:

```
docker-compose exec backend python manage.py collectstatic --no-input
```

- создайте суперпользователя:

```
docker-compose exec backend python manage.py createsuperuser
```

- загрузите в базу список ингредиентов:

```
docker-compose exec backend python manage.py load_csv

```