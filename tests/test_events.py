from datetime import date

from events import add_event, find_event, sort_events_by_date


def test_add_event():
    events = {}
    add_event(events, "Арт-маркет", 1, date(2026, 10, 4), "Флакон", 5)
    assert len(events) == 1


def test_find_event():
    events = {}
    add_event(events, "Ярмарка мастеров", 1, date(2026, 10, 10), "Парк", 3)
    assert find_event(events, "ярмарка")


def test_sort_events_by_date():
    events = {}
    add_event(events, "Второе мероприятие", 1, date(2026, 11, 1), "Место", 2)
    add_event(events, "Первое мероприятие", 1, date(2026, 10, 1), "Место", 2)
    sorted_events = sort_events_by_date(events)
    assert sorted_events[0]["title"] == "Первое мероприятие"
