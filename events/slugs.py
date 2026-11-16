"""Формирование англоязычного (латинского) slug из русского названия."""
from django.utils.text import slugify

TRANSLIT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e", "ж": "zh", "з": "z",
    "и": "i", "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o", "п": "p", "р": "r",
    "с": "s", "т": "t", "у": "u", "ф": "f", "х": "h", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sch",
    "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
}


def transliterate(text):
    return "".join(TRANSLIT.get(char, TRANSLIT.get(char.lower(), char)) for char in text.lower())


def unique_slug(model, title, exclude_pk=None, max_length=200):
    """Латинский slug, уникальный в таблице модели: «Ночь в галерее» -> «noch-v-galeree», при совпадении «-2»."""
    base = slugify(transliterate(title))[:max_length - 4] or "event"
    slug, number = base, 2
    queryset = model._default_manager.all()
    if exclude_pk:
        queryset = queryset.exclude(pk=exclude_pk)
    while queryset.filter(slug=slug).exists():
        slug = f"{base}-{number}"
        number += 1
    return slug
