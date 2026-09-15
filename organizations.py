"""Функции для работы с организациями — организаторами мероприятий."""


def add_organization(
    organizations: dict[int, dict], name: str, contact: str
) -> int:
    """Добавить организацию в словарь organizations и вернуть её id."""
    org_id = max(organizations.keys(), default=0) + 1
    organizations[org_id] = {
        "id": org_id,
        "name": name,
        "contact": contact,
    }
    return org_id


def find_organization(
    organizations: dict[int, dict], query: str
) -> list[dict]:
    """Найти организации по подстроке в названии."""
    query = query.lower()
    return [
        org for org in organizations.values()
        if query in org["name"].lower()
    ]
