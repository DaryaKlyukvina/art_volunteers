from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Count, F, Q
from django.urls import reverse
from django.utils import timezone

from organizations.models import Organization

from .slugs import unique_slug


class Category(models.Model):
    name = models.CharField("Название категории", max_length=100, unique=True)
    slug = models.SlugField("URL-имя", max_length=110, unique=True, allow_unicode=True)
    description = models.TextField("Описание", blank=True)

    class Meta:
        verbose_name = "категория мероприятий"
        verbose_name_plural = "категории мероприятий"
        ordering = ["name"]

    def __str__(self):
        return self.name


class EventQuerySet(models.QuerySet):
    """Повторно используемые условия выборки мероприятий."""

    def published(self):
        return self.filter(status=Event.Status.PUBLISHED)

    def upcoming(self):
        return self.filter(date__gte=timezone.now())

    def active(self):
        """Все мероприятия, кроме отменённых."""
        return self.exclude(status=Event.Status.CANCELLED)

    def for_date(self, day):
        return self.filter(date__date=day)

    def catalog(self):
        """Опубликованные будущие мероприятия вместе с организацией и категорией."""
        return self.published().upcoming().select_related("organization", "category")

    def with_free_slots(self):
        """Принятые заявки и свободные места. Место занимают только принятые заявки."""
        from applications.models import VolunteerApplication

        return self.annotate(
            accepted_count=Count(
                "applications", filter=Q(applications__status=VolunteerApplication.Status.ACCEPTED),
            ),
        ).annotate(free_slots=F("volunteers_needed") - F("accepted_count"))


class Event(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Черновик"
        PUBLISHED = "published", "Опубликовано"
        COMPLETED = "completed", "Завершено"
        CANCELLED = "cancelled", "Отменено"

    title = models.CharField("Название", max_length=200)
    slug = models.SlugField(
        "URL-имя", max_length=220, unique=True, blank=True,
        help_text="Латиницей. Если оставить пустым, сформируется из названия автоматически.",
    )
    description = models.TextField("Описание")
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT,
                                     related_name="events", verbose_name="Организация")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name="events", verbose_name="Категория")
    date = models.DateTimeField("Дата и время проведения")
    location = models.CharField("Место проведения", max_length=255,
                                help_text="Город и площадка, например: «Москва, Флакон».")
    volunteers_needed = models.PositiveIntegerField(
        "Нужно волонтёров", default=0, validators=[MinValueValidator(0)],
        help_text="Сколько заявок организатор может принять. Свободные места = это число минус принятые заявки.",
    )
    ticket_url = models.URLField("Ссылка на покупку билетов", blank=True,
                                 help_text="Необязательно. Внешний сайт продажи билетов.")
    image = models.ImageField("Изображение мероприятия", upload_to="events/", blank=True, null=True)
    status = models.CharField(
        "Статус", max_length=20, choices=Status.choices, default=Status.DRAFT,
        help_text="На сайте показываются только опубликованные мероприятия.",
    )
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    # Вычисляемое поле: значение формирует сама база данных по выражению
    is_large = models.GeneratedField(
        expression=models.Case(
            models.When(volunteers_needed__gte=10, then=models.Value(True)),
            default=models.Value(False),
        ),
        output_field=models.BooleanField(),
        db_persist=True,
        verbose_name="Крупное мероприятие",
    )

    objects = EventQuerySet.as_manager()

    class Meta:
        verbose_name = "мероприятие"
        verbose_name_plural = "мероприятия"
        ordering = ["date"]
        indexes = [models.Index(fields=["status", "date"], name="event_status_date_idx")]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(Event, self.title, exclude_pk=self.pk)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("event_detail", kwargs={"slug": self.slug})

    def cancel(self):
        """Отмена мероприятия: запись остаётся в базе, меняется только статус."""
        self.status = self.Status.CANCELLED
        self.save(update_fields=["status"])
