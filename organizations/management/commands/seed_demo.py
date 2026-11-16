"""Наполнение базы демонстрационными данными.

    python manage.py seed_demo           # добавить данные (повторный запуск ничего не дублирует)
    python manage.py seed_demo --reset   # удалить демо-данные и создать заново
"""
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from applications.models import VolunteerApplication
from events.models import Category, Event
from organizations.models import Organization, OrganizationMember

DEMO_PASSWORD = "DemoPass123!"

ORGANIZATIONS = [
    ("Галерея «Флакон»", "info@flacon.example", "Пространство современного искусства и дизайна."),
    ("Музей уличного искусства", "hello@streetart.example", "Музей и площадка для фестивалей стрит-арта."),
    ("Театр «Арт-Причал»", "team@artpier.example", "Независимый театр на набережной."),
]

CATEGORIES = [
    ("Выставки", "vystavki"),
    ("Фестивали", "festivali"),
    ("Мастер-классы", "master-klassy"),
    ("Театр", "teatr"),
    ("Лекции", "lekcii"),  # специально без мероприятий — для проверки LEFT JOIN в статистике
]

# (название, организация, категория, через сколько дней, место, нужно волонтёров, статус)
EVENTS = [
    ("Ночь в галерее", 0, 0, 3, "Москва, Флакон", 6, "published"),
    ("Ярмарка молодых художников", 0, 1, 6, "Москва, Флакон", 12, "published"),
    ("Мастер-класс по шелкографии", 0, 2, 9, "Москва, Флакон, мастерская", 3, "published"),
    ("Фестиваль граффити «Стены»", 1, 1, 12, "Москва, Хлебозавод", 15, "published"),
    ("Экскурсия по стрит-арту", 1, 0, 15, "Москва, Хлебозавод", 2, "published"),
    ("Мастер-класс по трафарету", 1, 2, 18, "Москва, Хлебозавод", 4, "published"),
    ("Премьера «Чайки»", 2, 3, 21, "Москва, Причал 7", 5, "published"),
    ("Летний театральный фестиваль", 2, 1, 25, "Москва, Причал 7", 20, "published"),
    ("Иммерсивный спектакль", 2, 3, 30, "Москва, Причал 7", 3, "published"),
    ("Выставка керамики", 0, 0, 34, "Москва, Флакон", 4, "published"),
    ("Ночь музеев на Хлебозаводе", 1, 1, 40, "Москва, Хлебозавод", 10, "published"),
    ("Читка новой пьесы", 2, 3, 45, "Москва, Причал 7", 2, "published"),
    ("Весенняя выставка (прошедшая)", 0, 0, -20, "Москва, Флакон", 5, "completed"),
    ("Отменённый перформанс", 1, 1, 8, "Москва, Хлебозавод", 4, "cancelled"),
    ("Черновик: детский мастер-класс", 2, 2, 50, "Москва, Причал 7", 3, "draft"),
]

VOLUNTEERS = [
    ("anna", "Анна", "Смирнова"), ("ivan", "Иван", "Петров"), ("maria", "Мария", "Козлова"),
    ("oleg", "Олег", "Соколов"), ("daria", "Дарья", "Морозова"), ("pavel", "Павел", "Волков"),
]

# (индекс волонтёра, индекс мероприятия, статус)
APPLICATIONS = [
    (0, 0, "accepted"), (1, 0, "accepted"), (2, 0, "pending"), (3, 0, "rejected"),
    (0, 1, "pending"), (4, 1, "accepted"), (5, 1, "pending"),
    (1, 2, "accepted"), (2, 2, "accepted"), (3, 2, "accepted"),
    (4, 3, "pending"), (5, 3, "accepted"), (0, 3, "rejected"),
    (2, 4, "accepted"), (3, 4, "accepted"),
    (4, 6, "pending"), (5, 6, "rejected"), (1, 7, "accepted"),
    (0, 12, "accepted"), (2, 12, "accepted"),
]


class Command(BaseCommand):
    help = "Создаёт демонстрационные организации, категории, мероприятия, пользователей и заявки"

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Удалить демо-данные перед созданием")

    @transaction.atomic
    def handle(self, *args, **options):
        if options["reset"]:
            VolunteerApplication.objects.filter(user__username__in=[v[0] for v in VOLUNTEERS]).delete()
            Event.objects.filter(title__in=[e[0] for e in EVENTS]).delete()
            self.stdout.write("Старые демо-данные удалены.")

        organizations = []
        for name, contact, description in ORGANIZATIONS:
            organization, _ = Organization.objects.get_or_create(
                name=name, defaults={"contact": contact, "description": description},
            )
            organizations.append(organization)

        categories = []
        for name, slug in CATEGORIES:
            category, _ = Category.objects.get_or_create(slug=slug, defaults={"name": name})
            categories.append(category)

        organizer, created = User.objects.get_or_create(
            username="organizer", defaults={"first_name": "Ольга", "email": "organizer@example.com"},
        )
        if created:
            organizer.set_password(DEMO_PASSWORD)
            organizer.save()
        for organization in organizations[:2]:
            OrganizationMember.objects.get_or_create(organization=organization, user=organizer)

        now = timezone.now().replace(minute=0, second=0, microsecond=0)
        events = []
        for title, org_i, cat_i, days, location, needed, status in EVENTS:
            event, _ = Event.objects.get_or_create(
                title=title,
                organization=organizations[org_i],
                defaults={
                    "description": f"{title}. Нужны помощники на регистрацию гостей, навигацию и монтаж.",
                    "category": categories[cat_i],
                    "date": now.replace(hour=18) + timedelta(days=days),
                    "location": location,
                    "volunteers_needed": needed,
                    "status": status,
                },
            )
            events.append(event)

        volunteers = []
        for username, first_name, last_name in VOLUNTEERS:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={"first_name": first_name, "last_name": last_name, "email": f"{username}@example.com"},
            )
            if created:
                user.set_password(DEMO_PASSWORD)
                user.save()
            volunteers.append(user)

        for user_i, event_i, status in APPLICATIONS:
            user = volunteers[user_i]
            VolunteerApplication.objects.get_or_create(
                user=user,
                event=events[event_i],
                defaults={
                    "applicant_name": user.get_full_name(),
                    "contact": user.email,
                    "experience": "Помогала на городских фестивалях." if user_i % 2 == 0 else "",
                    "status": status,
                },
            )

        self.stdout.write(self.style.SUCCESS(
            f"Готово: организаций {Organization.objects.count()}, категорий {Category.objects.count()}, "
            f"мероприятий {Event.objects.count()}, заявок {VolunteerApplication.objects.count()}. "
            f"Пароль демо-пользователей (organizer, anna, ivan, ...): {DEMO_PASSWORD}"
        ))
