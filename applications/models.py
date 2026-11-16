from django.conf import settings
from django.db import models
from events.models import Event


class VolunteerApplicationQuerySet(models.QuerySet):
    """Повторно используемые условия выборки заявок."""

    def pending(self):
        return self.filter(status=VolunteerApplication.Status.PENDING)

    def accepted(self):
        return self.filter(status=VolunteerApplication.Status.ACCEPTED)

    def rejected(self):
        return self.filter(status=VolunteerApplication.Status.REJECTED)

    def for_event(self, event):
        return self.filter(event=event)

    def for_organizations(self, organization_ids):
        return self.filter(event__organization_id__in=organization_ids)

    def with_related(self):
        return self.select_related("user", "event", "event__organization")


class VolunteerApplication(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "На рассмотрении"
        ACCEPTED = "accepted", "Принята"
        REJECTED = "rejected", "Отклонена"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name="volunteer_applications", verbose_name="Пользователь")
    event = models.ForeignKey(Event, on_delete=models.CASCADE,
                              related_name="applications", verbose_name="Мероприятие")
    applicant_name = models.CharField("Имя", max_length=150)
    contact = models.CharField("Контакт для связи", max_length=255, help_text="Телефон или электронная почта.")
    experience = models.TextField("Опыт волонтёрства", blank=True)
    status = models.CharField(
        "Статус", max_length=20, choices=Status.choices, default=Status.PENDING,
        help_text="Место волонтёра занимают только принятые заявки.",
    )
    created_at = models.DateTimeField("Дата отправки", auto_now_add=True)
    updated_at = models.DateTimeField("Последнее изменение", auto_now=True)

    objects = VolunteerApplicationQuerySet.as_manager()

    class Meta:
        verbose_name = "заявка волонтёра"
        verbose_name_plural = "заявки волонтёров"
        ordering = ["-created_at"]
        constraints = [models.UniqueConstraint(fields=["user", "event"], name="unique_user_event_application")]
        indexes = [models.Index(fields=["status", "created_at"], name="application_status_created_idx")]

    def __str__(self):
        return f"{self.applicant_name} — {self.event}"
