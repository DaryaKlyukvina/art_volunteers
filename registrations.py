"""Функции регистрации волонтёров на мероприятия."""


def free_slots(events: dict[int, dict], registrations: list[dict], event_id: int) -> int:
    """Вернуть количество свободных мест волонтёров на мероприятии."""
    event = events.get(event_id)
    if event is None:
        raise KeyError(f"Мероприятие с id={event_id} не найдено")
    taken = sum(1 for r in registrations if r["event_id"] == event_id)
    return event["volunteers_needed"] - taken


def is_registration_possible(
    events: dict[int, dict],
    registrations: list[dict],
    event_id: int,
    volunteer_id: int,
) -> bool:
    """Проверить, можно ли зарегистрировать волонтёра на мероприятие."""
    already_registered = any(
        r["event_id"] == event_id and r["volunteer_id"] == volunteer_id
        for r in registrations
    )
    if already_registered:
        return False
    return free_slots(events, registrations, event_id) > 0


def create_registration(
    events: dict[int, dict],
    registrations: list[dict],
    event_id: int,
    volunteer_id: int,
) -> dict:
    """Зарегистрировать волонтёра на мероприятие и вернуть запись о регистрации."""
    if not is_registration_possible(events, registrations, event_id, volunteer_id):
        raise ValueError(
            "Регистрация невозможна: мест нет или волонтёр уже зарегистрирован"
        )
    registration_id = max((r["id"] for r in registrations), default=0) + 1
    registration = {
        "id": registration_id,
        "event_id": event_id,
        "volunteer_id": volunteer_id,
    }
    registrations.append(registration)
    return registration


def cancel_registration(registrations: list[dict], registration_id: int) -> bool:
    """Отменить регистрацию по её id. Вернуть True при успехе."""
    for index, registration in enumerate(registrations):
        if registration["id"] == registration_id:
            del registrations[index]
            return True
    return False


def get_registration_status(is_available: bool) -> str:
    """Вернуть текстовый статус набора волонтёров (функция из ПР1)."""
    if is_available:
        return "Можно зарегистрироваться волонтёром"
    return "Мест нет или вы уже зарегистрированы"
