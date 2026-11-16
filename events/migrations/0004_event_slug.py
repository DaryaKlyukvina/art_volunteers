"""Англоязычный slug мероприятия: поле, заполнение существующих записей, уникальность."""
from django.db import migrations, models
from django.utils.text import slugify

from events.slugs import transliterate


def fill_slugs(apps, schema_editor):
    Event = apps.get_model("events", "Event")
    used = set()
    for event in Event.objects.order_by("pk"):
        base = slugify(transliterate(event.title))[:200] or "event"
        slug, number = base, 2
        while slug in used:
            slug = f"{base}-{number}"
            number += 1
        used.add(slug)
        event.slug = slug
        event.save(update_fields=["slug"])


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0003_help_texts"),
    ]

    operations = [
        # 1. Поле без ограничения уникальности: у существующих записей пока пустая строка
        migrations.AddField(
            model_name="event",
            name="slug",
            field=models.SlugField(blank=True, default="", max_length=220, verbose_name="URL-имя"),
            preserve_default=False,
        ),
        # 2. Заполняем slug по названию (транслитерация + номер при совпадении)
        migrations.RunPython(fill_slugs, migrations.RunPython.noop),
        # 3. Только теперь включаем уникальность
        migrations.AlterField(
            model_name="event",
            name="slug",
            field=models.SlugField(
                blank=True,
                help_text="Латиницей. Если оставить пустым, сформируется из названия автоматически.",
                max_length=220,
                unique=True,
                verbose_name="URL-имя",
            ),
        ),
    ]
