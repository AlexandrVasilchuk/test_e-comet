# Тестовое задание: Создание парсера данных с GitHub API

## Описание

Это [тестовое задание](https://clck.ru/38ixNi) представляет собой разработку парсера данных с использованием GitHub API для извлечения информации о публичных репозиториях.  
Парсер должен извлекать основные характеристики каждого репозитория, такие как количество звезд, количество наблюдателей, количество форков и язык программирования. Полученные данные затем должны быть сохранены в базу данных.  
Так же создано приложение, где можно получить топ 100 репозиториев по количеству звезд и получить кол-во коммитов для определенного репозитория в промежутке дат.

## Технологии

Python 3.10+
asyncpg  
FastAPi  
Yandex.Cloud (для развёртывания функции и базы данных)

## ⚠ Зависимости

> **Warning**:
> Для запуска требуются установленные зависимости:  
> ![Docker-badge]

## Установка и запуск

- Установите и активируйте вирутальное окружение
- Установите зависимости из файла requirements.txt

```bash
pip install -r requirements.txt
```

- Заполните .env file по образцу

```.env
#Переменная необходимая для подключения alembic к БД. Используется FastApi контейнером
DATABASE_URL=postgresql+asyncpg://postgres:admin@db:5432/postgres
#Переменные используемые в settings FastApi.
DB_USER=postgres
DB_PASSWORD=admin
DB_NAME=postgres
DB_HOST=localhost
DB_PORT=5432
#Переменные для подключения к базе с YC
NGROK_HOST=*.tcp.eu.ngrok.io
NGROK_PORT=1**89
#Переменные используемые для аутентификации в api.github.com
GH_TOKEN=ghp*******H1TfULxasuC0xg56d
#Переменные для запуска функции
FUNCTION_ID=d4e****52cgbbv
```

---

### Справка по .env файлу

Значение перменных NGROK_HOST, NGROK_PORT можно
получить используя. Эти переменные нужны, чтобы
облачная функция могла записать значения в БД

```bash
ngrok tcp 5432
```

Значение переменной GH_TOKEN можно получить по [ссылке](https://github.com/settings/tokens). Это позволит увеличить
число запросов для парсера данных.

Значение переменной FUNCTION_ID можно получить после:

- настройки и установки yc. Пошаговая установка по [ссылке](https://cloud.yandex.ru/ru/docs/cli/quickstart)
- наполения .env файла остальными значениями перменных
- запуска скрипта create_function.sh

Теперь введите команду

```bash
yc serverless function list
```

В разделе ID получите требуемое значение переменной

---

- Запустите docker-compose.yml файл

```bash
docker compose up -d
```

- Запустите триггер парсера через файл run_timer.sh

---

<p style="text-align: center",>
Автор:
<a href=" https://github.com/AlexandrVasilchuk">Васильчук Александр</a>
</p>

### Контакты  

<a href="mailto:alexandrvsko@gmail.com">![Gmail-badge] <a/>
<a href="https://t.me/vsko_dev">![Telegram-badge] <a/>

[Gmail-badge]: https://img.shields.io/badge/Gmail-D14836?style=for-the-badge&logo=gmail&logoColor=white
[Telegram-badge]: https://img.shields.io/badge/Telegram-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white
