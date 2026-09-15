"""Начальный сценарий индивидуального проекта (ПР1).

"""
from datetime import date

event_title = "Арт-маркет «Осенний двор»"
organization_name = "АртПространство «Лук»"
volunteers_needed = 8
volunteers_registered = 8
event_date = date(2026, 10, 4)

# переехала целиком без изменений в registrations.py

def format_event_info(title: str, organization: str, when: date) -> str: 
    """Сформировать строку с краткой информацией о мероприятии."""
    return f"{title} ({organization}), дата проведения: {when}"

 # превратилась в free_slots() в registrations.py

def slots_available(needed: int, registered: int) -> bool:
    """Проверить, остались ли свободные места волонтёров."""
    return registered < needed

 # её логику вывода взяла на себя show_events() в main.py

def get_registration_status(is_available: bool) -> str:
    """Вернуть текстовый статус набора волонтёров на мероприятие."""
    if is_available:
        return "Можно зарегистрироваться волонтёром"
    return "Мест нет, набор волонтёров закрыт"


print(format_event_info(event_title, organization_name, event_date))
availability = slots_available(volunteers_needed, volunteers_registered)
print(get_registration_status(availability))
