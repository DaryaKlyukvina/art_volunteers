from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0004_event_slug"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="is_large",
            field=models.GeneratedField(
                db_persist=True,
                expression=models.Case(
                    models.When(then=models.Value(True), volunteers_needed__gte=10),
                    default=models.Value(False),
                ),
                output_field=models.BooleanField(),
                verbose_name="Крупное мероприятие",
            ),
        ),
    ]
