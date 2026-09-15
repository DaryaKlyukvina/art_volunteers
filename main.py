"""Точка запуска сервиса поиска волонтёров для арт-мероприятий."""
import organizations
import events
import volunteers
import registrations
import storage
from utils import input_int, input_date

DATA_DIR = "data"
ORG_FILE = f"{DATA_DIR}/organizations.json"
EVENTS_FILE = f"{DATA_DIR}/events.json"
VOLUNTEERS_FILE = f"{DATA_DIR}/volunteers.json"
REGISTRATIONS_FILE = f"{DATA_DIR}/registrations.json"

MENU = """
=== Сервис волонтёров для арт-мероприятий ===
1. Показать мероприятия
2. Найти мероприятие по названию
3. Показать свободные места на мероприятии
4. Зарегистрировать волонтёра на мероприятие
5. Отменить регистрацию
6. Показать регистрации
7. Добавить организацию
8. Добавить мероприятие
9. Добавить волонтёра
0. Выход
Выберите действие: """


def show_events(events_data: dict[int, dict]) -> None:
    """Вывести список мероприятий, отсортированных по дате."""
    if not events_data:
        print("Мероприятий пока нет")
        return
    for event in events.sort_events_by_date(events_data):
        print(
            f"[{event['id']}] {event['title']} — {event['date']} — "
            f"{event['location']} (нужно волонтёров: {event['volunteers_needed']})"
        )


def show_registrations(registrations_data: list[dict]) -> None:
    """Вывести список регистраций волонтёров на мероприятия."""
    if not registrations_data:
        print("Регистраций пока нет")
        return
    for reg in registrations_data:
        print(f"[{reg['id']}] мероприятие {reg['event_id']} — волонтёр {reg['volunteer_id']}")


def main() -> None:
    """Точка запуска приложения: меню и вызов функций проекта."""
    orgs = storage.load_dict(ORG_FILE)
    events_data = storage.load_dict(EVENTS_FILE)
    volunteers_data = storage.load_dict(VOLUNTEERS_FILE)
    registrations_data = storage.load_list(REGISTRATIONS_FILE)

    while True:
        choice = input(MENU)

        if choice == "1":
            show_events(events_data)

        elif choice == "2":
            query = input("Название или часть названия: ")
            found = events.find_event(events_data, query)
            show_events({event["id"]: event for event in found})

        elif choice == "3":
            event_id = input_int("ID мероприятия: ")
            try:
                free = registrations.free_slots(events_data, registrations_data, event_id)
                print(f"Свободных мест: {free}")
            except KeyError as error:
                print(error)

        elif choice == "4":
            event_id = input_int("ID мероприятия: ")
            volunteer_id = input_int("ID волонтёра: ")
            try:
                possible = registrations.is_registration_possible(
                    events_data, registrations_data, event_id, volunteer_id
                )
                print(registrations.get_registration_status(possible))
                if possible:
                    registrations.create_registration(
                        events_data, registrations_data, event_id, volunteer_id
                    )
                    storage.save_list(REGISTRATIONS_FILE, registrations_data)
            except KeyError as error:
                print(error)

        elif choice == "5":
            registration_id = input_int("ID регистрации для отмены: ")
            if registrations.cancel_registration(registrations_data, registration_id):
                storage.save_list(REGISTRATIONS_FILE, registrations_data)
                print("Регистрация отменена")
            else:
                print("Регистрация не найдена")

        elif choice == "6":
            show_registrations(registrations_data)

        elif choice == "7":
            name = input("Название организации: ")
            contact = input("Контакт: ")
            organizations.add_organization(orgs, name, contact)
            storage.save_dict(ORG_FILE, orgs)

        elif choice == "8":
            title = input("Название мероприятия: ")
            organization_id = input_int("ID организации: ")
            event_date = input_date("Дата (ДД.ММ.ГГГГ): ")
            location = input("Место проведения: ")
            needed = input_int("Сколько нужно волонтёров: ")
            events.add_event(events_data, title, organization_id, event_date, location, needed)
            storage.save_dict(EVENTS_FILE, events_data)

        elif choice == "9":
            name = input("Имя волонтёра: ")
            contact = input("Контакт: ")
            skills_raw = input("Навыки через запятую: ")
            skills = [skill.strip() for skill in skills_raw.split(",") if skill.strip()]
            volunteers.add_volunteer(volunteers_data, name, contact, skills)
            storage.save_dict(VOLUNTEERS_FILE, volunteers_data)

        elif choice == "0":
            print("До свидания!")
            break

        else:
            print("Неверный пункт меню, попробуйте снова")


if __name__ == "__main__":
    main()
