"""Сохранение и загрузка данных проекта в формате JSON."""
import json


def load_list(filename: str) -> list[dict]:
    """Загрузить список записей из JSON-файла через контекстный менеджер."""
    try:
        with open(filename, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        print(f"Файл {filename} повреждён, используется пустой список")
        return []


def save_list(filename: str, data: list[dict]) -> None:
    """Сохранить список записей в JSON-файл через контекстный менеджер."""
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def load_dict(filename: str) -> dict[int, dict]:
    """Загрузить записи из JSON-файла и вернуть их в виде словаря по id."""
    records = load_list(filename)
    return {record["id"]: record for record in records}


def save_dict(filename: str, data: dict[int, dict]) -> None:
    """Сохранить словарь записей в JSON-файл в виде списка."""
    save_list(filename, list(data.values()))
