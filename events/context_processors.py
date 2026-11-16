"""Общие данные для всех шаблонов (подключено в settings.TEMPLATES)."""
from .models import Event


def site_context(request):
    return {
        "site_name": "ArtVolunteers",
        # count() выполняет подсчёт в базе данных, а не загружает записи в память
        "upcoming_events_count": Event.objects.published().upcoming().count(),
    }
