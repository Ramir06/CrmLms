# CRM LMS — Django 5 учебный центр

Полноценная CRM + LMS система для управления учебным центром, построенная на Django 5, PostgreSQL и Bootstrap 5.

---

## Стек технологий

| Компонент | Версия |
|---|---|
| Python | 3.12+ |
| Django | 5.x |
| PostgreSQL | 15+ |
| Bootstrap | 5.3 |
| FullCalendar | 6.x |
| Chart.js | 3.x |
| django-environ | 0.11+ |
| Pillow | 10+ |
| openpyxl | 3.1+ |
| django-widget-tweaks | 1.5+ |
| whitenoise | 6.x |

---

## Быстрый старт

### 1. Клонируйте / распакуйте проект

```bash
cd crm_lms
```

### 2. Создайте виртуальное окружение и установите зависимости

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux / Mac
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Настройте переменные окружения

Скопируйте `.env.example` в `.env` и заполните:

```bash
copy .env.example .env   # Windows
cp .env.example .env     # Linux/Mac
```

Минимальный `.env`:
```
SECRET_KEY=your-very-secret-key-change-me
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=postgres://postgres:password@localhost:5432/crm_lms
```

### 4. Создайте базу данных PostgreSQL

```sql
CREATE DATABASE crm_lms;
```

### 5. Примените миграции

```bash
python manage.py migrate
```

### 6. Загрузите демо-данные

```bash
python manage.py seed_demo_data
```

Для сброса и повторной загрузки:
```bash
python manage.py seed_demo_data --flush
```

### 7. Запустите сервер

```bash
python manage.py runserver
```

Откройте: http://127.0.0.1:8000

---

## Тестовые учётные записи

| Роль | Email | Пароль |
|---|---|---|
| Администратор | admin@example.com | admin12345 |
| Ментор | mentor@example.com | mentor12345 |
| Ментор 2 | mentor2@example.com | mentor12345 |

---

## Структура проекта

```
crm_lms/
├── config/                  # Настройки Django
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── accounts/            # Пользователи, авторизация
│   ├── core/                # Middleware, mixins, management команды
│   ├── courses/             # Курсы, зачисления
│   ├── students/            # Студенты
│   ├── mentors/             # Менторы, профили
│   ├── lessons/             # Занятия (расписание)
│   ├── attendance/          # Посещаемость
│   ├── assignments/         # Задания, сдачи, оценки
│   ├── lectures/            # Лекционные материалы
│   ├── rating/              # Рейтинг студентов
│   ├── reviews/             # Отзывы
│   ├── leads/               # CRM лиды (канбан)
│   ├── payments/            # Платежи
│   ├── debts/               # Долги
│   ├── salaries/            # Зарплаты менторов
│   ├── finance/             # Финансы (доходы/расходы)
│   ├── news/                # Объявления
│   ├── reports/             # Отчёты
│   ├── calendar_app/        # API для FullCalendar
│   ├── dashboard/           # Дашборды
│   └── notifications/       # Уведомления
├── templates/
│   ├── base/                # Базовые шаблоны
│   ├── includes/            # Навбар, сайдбары, дровер
│   ├── auth/                # Логин, профиль
│   ├── admin/               # Шаблоны администратора
│   ├── mentor/              # Шаблоны ментора
│   └── course/              # LMS шаблоны курса
├── static/
│   ├── css/                 # app.css, admin.css, mentor.css
│   └── js/                  # app.js, calendar.js, leads.js, dashboard.js
├── media/                   # Загружаемые файлы
├── requirements.txt
├── .env.example
└── manage.py
```

---

## Возможности системы

### Администратор
- Дашборд с KPI, графиками доходов и новых студентов
- Управление курсами (список, карточка, форма)
- Управление студентами (список, карточка, форма, экспорт в Excel)
- Управление менторами (список, карточка, форма)
- CRM лиды — Kanban доска с drag-and-drop и историей действий
- Платежи, долги, зарплаты, финансы с экспортом
- Объявления (CRUD с публикацией)
- Календарь занятий (FullCalendar) с правым ящиком деталей
- Сводные отчёты по курсам

### Ментор
- Личный дашборд с курсами и статистикой
- Расписание (FullCalendar)
- LMS по каждому курсу:
  - Лекционные материалы (видео, файлы, ссылки, текст) по разделам
  - Задания + матрица сдачи + проверка работ с оценками
  - Занятия (недельный вид, CRUD)
  - Посещаемость с радио-кнопками по студентам
  - Рейтинг студентов (посещаемость + задания + отзывы)
  - Отзывы студентов
  - Смарт-отчёт курса с графиками
- Зарплата (история начислений)
- Объявления

---

## Управление статическими файлами

В production whitenoise обслуживает статику автоматически. Для сбора:

```bash
python manage.py collectstatic
```

---

## Экспорт в Excel

Используется `openpyxl`. Ссылки экспорта доступны:
- Список студентов → `/students/export/`
- Список менторов → `/mentors/export/`
- Платежи → `/payments/export/`
- Долги → `/debts/export/`
- Зарплаты → `/salaries/export/`
- Финансы → `/finance/export/`

---

## Переменные окружения (`.env`)

```
SECRET_KEY=          # Django secret key
DEBUG=               # True / False
ALLOWED_HOSTS=       # comma-separated hosts
DATABASE_URL=        # postgres://user:pass@host:port/db
MEDIA_ROOT=          # путь к медиа-файлам (опционально)
```
