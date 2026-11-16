# ArtVolunteers — платформа волонтёров для арт-мероприятий

## О проекте
Django-сайт, который помогает посетителям находить актуальные арт-мероприятия,
переходить на внешние сервисы покупки билетов и подавать заявки на волонтёрство.
Организаторы рассматривают заявки и принимают или отклоняют кандидатов.

## Технологии
- Python 3.11+
- Django 5.2+ (проверено на Django 6.0)
- SQLite (`db.sqlite3`), доступ к данным только через Django ORM
- Pillow — изображения мероприятий и логотипы организаций
- pytest, pytest-django, flake8

## Роли
- **Гость:** ищет и фильтрует опубликованные будущие мероприятия, смотрит страницы организаций и статистику.
- **Пользователь/волонтёр:** регистрируется, отправляет одну заявку на мероприятие, видит её статус.
- **Сотрудник организации:** видит заявки только своей организации, фильтрует их, принимает или отклоняет.
- **Администратор сайта:** управляет всеми данными через Django Admin.

## Страницы
| Адрес | Назначение |
|---|---|
| `/` | Каталог: поиск, фильтры по категории, организации и датам, «только со свободными местами», сортировка, пагинация |
| `/events/<id>/` | Мероприятие: описание, организация, свободные места, другие мероприятия организации |
| `/statistics/` | Статистика: заявки по статусам, категории, организации |
| `/organizations/<id>/` | Организация и её предстоящие мероприятия |
| `/applications/event/<id>/apply/` | Форма заявки волонтёра (нужен вход) |
| `/applications/mine/` | Мои заявки |
| `/applications/organization/` | Заявки организации: фильтры, сортировка, пагинация, принятие/отклонение |
| `/accounts/signup/`, `/accounts/login/` | Регистрация и вход |
| `/admin/` | Административная панель |

## Модели данных
- `User` — встроенная модель Django.
- `Organization` — организатор (название, описание, контакт, сайт, логотип).
- `OrganizationMember` — сотрудник организации: `ForeignKey` на `Organization` и `User`, уникальная пара.
- `Category` — категория мероприятий (`slug` уникален).
- `Event` — мероприятие: `ForeignKey` на `Organization` (`on_delete=PROTECT`, `related_name="events"`)
  и `Category` (`SET_NULL`), дата, место, `volunteers_needed`, ссылка на билеты, изображение,
  статус `draft` / `published` / `completed` / `cancelled`.
- `VolunteerApplication` — заявка: `ForeignKey` на `User` и `Event` (`CASCADE`,
  `related_name="volunteer_applications"` / `"applications"`), контакты, опыт,
  статус `pending` / `accepted` / `rejected`.

Правила предметной области:
- повторная заявка одного пользователя на одно мероприятие запрещена ограничением БД `unique_user_event_application`;
- число принятых заявок не может превышать `volunteers_needed` (`applications/services.py`);
- свободные места считаются только по **принятым** заявкам: отклонённые и ожидающие место не занимают.

ORM-запросы проекта перечислены в [docs/ORM_QUERIES.md](docs/ORM_QUERIES.md).

## Установка и запуск
```bash
git clone https://github.com/DaryaKlyukvina/art_volunteers.git
cd art_volunteers
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo
python manage.py runserver
```
Откройте `http://127.0.0.1:8000/`. Админ-панель: `http://127.0.0.1:8000/admin/`.

## Наполнение базы данных
База `db.sqlite3` не хранится в репозитории: таблицы создаются миграциями.
- `python manage.py seed_demo` — демонстрационные организации, категории, 15 мероприятий,
  6 волонтёров и организатор `organizer` (пароль всех демо-пользователей `DemoPass123!`).
  Повторный запуск не создаёт дублей, `--reset` пересоздаёт мероприятия и заявки.
- `python manage.py import_legacy_json --directory data` — перенос организаций и мероприятий
  из JSON-файлов прежней консольной версии.

## Проверка
```bash
python manage.py check
python manage.py makemigrations --check
python manage.py showmigrations
pytest -v
flake8 .
```

## Структура
- `config/` — настройки проекта Django.
- `accounts/` — регистрация, вход и личный кабинет.
- `organizations/` — организации, сотрудники, команды `seed_demo` и `import_legacy_json`.
- `events/` — категории, мероприятия, каталог и статистика.
- `applications/` — заявки волонтёров, их статусы и кабинет организатора.
- `templates/` — HTML-шаблоны; `docs/` — документация.
- `media/` — загружаемые изображения (не хранится в репозитории).

Старые консольные модули (`main.py`, `storage.py`, `legacy_events.py`,
`legacy_organizations.py` и др.) оставлены как история первых практических работ.

## Автор
Лихтина Дарья Алексеевна, группа ЭФБО-05-24.
