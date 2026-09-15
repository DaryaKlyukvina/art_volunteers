"""Начальный сценарий индивидуального проекта (ПР1).

Сохранён без изменений для истории проекта, как того требует ПР2:
реализованная здесь логика позже переносится в модуль registrations.py
и дорабатывается для работы с коллекциями (см. registrations.py,
функция get_registration_status).
"""
from datetime import date

event_title = "Арт-маркет «Осенний двор»"
organization_name = "АртПространство «Флакон»"
volunteers_needed = 8
volunteers_registered = 8
event_date = date(2026, 10, 4)


def format_event_info(title: str, organization: str, when: date) -> str:
    """Сформировать строку с краткой информацией о мероприятии."""
    return f"{title} ({organization}), дата проведения: {when}"


def slots_available(needed: int, registered: int) -> bool:
    """Проверить, остались ли свободные места волонтёров."""
    return registered < needed


def get_registration_status(is_available: bool) -> str:
    """Вернуть текстовый статус набора волонтёров на мероприятие."""
    if is_available:
        return "Можно зарегистрироваться волонтёром"
    return "Мест нет, набор волонтёров закрыт"


print(format_event_info(event_title, organization_name, event_date))
print(get_registration_status(slots_available(volunteers_needed, volunteers_registered)))
