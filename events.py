"""Функции для работы с мероприятиями (арт-маркеты, ярмарки и т.п.)."""
from datetime import date


def add_event(
    events: dict[int, dict],
    title: str,
    organization_id: int,
    event_date: date,
    location: str,
    volunteers_needed: int,
) -> int:
    """Добавить мероприятие в словарь events и вернуть его id."""
    event_id = max(events.keys(), default=0) + 1
    events[event_id] = {
        "id": event_id,
        "title": title,
        "organization_id": organization_id,
        "date": event_date.isoformat(),
        "location": location,
        "volunteers_needed": volunteers_needed,
    }
    return event_id


def find_event(events: dict[int, dict], query: str) -> list[dict]:
    """Найти мероприятия по подстроке в названии."""
    query = query.lower()
    return [
        event
        for event in events.values()
        if query in event["title"].lower()
    ]


def filter_events_by_date(
    events: dict[int, dict], event_date: date
) -> list[dict]:
    """Отобрать мероприятия, проходящие в указанную дату (генератор)."""
    target = event_date.isoformat()
    return list(event for event in events.values() if event["date"] == target)


def sort_events_by_date(events: dict[int, dict]) -> list[dict]:
    """Отсортировать мероприятия по дате проведения (lambda как ключ)."""
    return sorted(events.values(), key=lambda event: event["date"])
