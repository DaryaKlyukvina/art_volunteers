from django.core.validators import MinValueValidator
from django.db import models
from organizations.models import Organization


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


class Event(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Черновик"
        PUBLISHED = "published", "Опубликовано"
        COMPLETED = "completed", "Завершено"
        CANCELLED = "cancelled", "Отменено"

    title = models.CharField("Название", max_length=200)
    description = models.TextField("Описание")
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT,
                                     related_name="events", verbose_name="Организация")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name="events", verbose_name="Категория")
    date = models.DateTimeField("Дата и время проведения")
    location = models.CharField("Место проведения", max_length=255)
    volunteers_needed = models.PositiveIntegerField("Нужно волонтёров", default=0,
                                                    validators=[MinValueValidator(0)])
    ticket_url = models.URLField("Ссылка на покупку билетов", blank=True)
    image = models.ImageField("Изображение мероприятия", upload_to="events/", blank=True, null=True)
    status = models.CharField("Статус", max_length=20, choices=Status.choices, default=Status.DRAFT)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)

    class Meta:
        verbose_name = "мероприятие"
        verbose_name_plural = "мероприятия"
        ordering = ["date"]
        indexes = [models.Index(fields=["status", "date"], name="event_status_date_idx")]

    def __str__(self):
        return self.title
