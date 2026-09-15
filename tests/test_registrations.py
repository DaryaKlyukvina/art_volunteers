from registrations import create_registration, free_slots, is_registration_possible


def make_events():
    return {
        1: {
            "id": 1,
            "title": "Арт-маркет",
            "organization_id": 1,
            "date": "2026-10-04",
            "location": "Место",
            "volunteers_needed": 1,
        }
    }


def test_free_slots():
    events = make_events()
    assert free_slots(events, [], 1) == 1


def test_registration_possible():
    events = make_events()
    assert is_registration_possible(events, [], 1, 10)


def test_duplicate_registration_forbidden():
    events = make_events()
    registrations = []
    create_registration(events, registrations, 1, 10)
    assert not is_registration_possible(events, registrations, 1, 10)
