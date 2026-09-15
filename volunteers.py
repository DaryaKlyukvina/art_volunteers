"""Функции для работы с волонтёрами — пользователями сервиса."""
from typing import Iterator


def add_volunteer(
    volunteers: dict[int, dict], name: str, contact: str, skills: list[str]
) -> int:
    """Добавить волонтёра в словарь volunteers и вернуть его id."""
    volunteer_id = max(volunteers.keys(), default=0) + 1
    volunteers[volunteer_id] = {
        "id": volunteer_id,
        "name": name,
        "contact": contact,
        "skills": skills,
    }
    return volunteer_id


def find_volunteers_by_skill(
    volunteers: dict[int, dict], skill: str
) -> Iterator[dict]:
    """Отобрать волонтёров, владеющих указанным навыком (генератор)."""
    skill = skill.lower()
    for volunteer in volunteers.values():
        if any(skill in s.lower() for s in volunteer["skills"]):
            yield volunteer
