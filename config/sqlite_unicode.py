"""Регистронезависимый поиск по кириллице в SQLite.

Встроенный оператор LIKE в SQLite игнорирует регистр только у латинских букв,
поэтому Django-поиск icontains не находит «Мастер» по запросу «мастер».
При каждом подключении к SQLite заменяем функцию like() на Python-версию,
которая сравнивает строки без учёта регистра для любых букв Unicode.
"""
import re
from functools import lru_cache

from django.db.backends.signals import connection_created


@lru_cache(maxsize=256)
def _compile(pattern, escape):
    regex, i = [], 0
    while i < len(pattern):
        char = pattern[i]
        if escape and char == escape and i + 1 < len(pattern):
            regex.append(re.escape(pattern[i + 1]))
            i += 2
            continue
        if char == "%":
            regex.append(".*")
        elif char == "_":
            regex.append(".")
        else:
            regex.append(re.escape(char))
        i += 1
    return re.compile("".join(regex), re.IGNORECASE | re.DOTALL)


def _like(pattern, value, escape=None):
    if pattern is None or value is None:
        return None
    return _compile(pattern, escape).fullmatch(str(value)) is not None


def register_unicode_like(sender, connection, **kwargs):
    if connection.vendor == "sqlite":
        connection.connection.create_function("like", 2, _like, deterministic=True)
        connection.connection.create_function("like", 3, _like, deterministic=True)


def setup():
    connection_created.connect(register_unicode_like, dispatch_uid="unicode_like")
