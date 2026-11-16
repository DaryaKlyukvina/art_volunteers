"""Импорт организаций и мероприятий из старых JSON-файлов консольной версии."""
import json
from datetime import date
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from events.models import Event
from organizations.models import Organization


class Command(BaseCommand):
    help = "Импортирует организации и мероприятия из каталога data старой версии проекта"

    def add_arguments(self, parser):
        parser.add_argument("--directory", default="data", help="Путь к каталогу с JSON-файлами")

    def handle(self, *args, **options):
        directory = Path(options["directory"])
        organizations_file = directory / "organizations.json"
        events_file = directory / "events.json"
        if not organizations_file.exists() or not events_file.exists():
            raise CommandError("Не найдены organizations.json и/или events.json в указанном каталоге")

        organizations_data = json.loads(organizations_file.read_text(encoding="utf-8"))
        events_data = json.loads(events_file.read_text(encoding="utf-8"))
        organization_map = {}
        for item in organizations_data:
            organization, _ = Organization.objects.update_or_create(
                name=item["name"],
                defaults={"contact": item.get("contact", "Не указан")},
            )
            organization_map[item["id"]] = organization

        imported = 0
        for item in events_data:
            organization = organization_map.get(item["organization_id"])
            if not organization:
                self.stderr.write(self.style.WARNING(f"Пропущено мероприятие {item['title']}: организация не найдена"))
                continue
            event_date = date.fromisoformat(item["date"])
            event_datetime = timezone.make_aware(
                timezone.datetime.combine(event_date, timezone.datetime.min.time())
            )
            status = Event.Status.COMPLETED if event_datetime < timezone.now() else Event.Status.DRAFT
            Event.objects.update_or_create(
                title=item["title"], organization=organization,
                defaults={
                    "description": "Импортировано из прежней версии проекта.",
                    "date": event_datetime,
                    "location": item["location"],
                    "volunteers_needed": item["volunteers_needed"],
                    "status": status,
                },
            )
            imported += 1
        self.stdout.write(self.style.SUCCESS(
            f"Импорт завершён: организаций — {len(organization_map)}, мероприятий — {imported}. "
            "Старые записи волонтёров не импортированы: теперь волонтёры используют аккаунты Django."
        ))
