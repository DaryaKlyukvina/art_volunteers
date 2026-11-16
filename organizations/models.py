from django.conf import settings
from django.db import models


class Organization(models.Model):
    name = models.CharField("Название", max_length=200, unique=True)
    description = models.TextField("Описание", blank=True)
    contact = models.CharField("Контакт организации", max_length=255)
    website = models.URLField("Сайт", blank=True)
    logo = models.ImageField("Логотип", upload_to="organizations/", blank=True, null=True)
    created_at = models.DateTimeField("Дата добавления", auto_now_add=True)

    class Meta:
        verbose_name = "организация"
        verbose_name_plural = "организации"
        ordering = ["name"]

    def __str__(self):
        return self.name


class OrganizationMember(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE,
                                     related_name="members", verbose_name="Организация")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name="organization_memberships", verbose_name="Пользователь")
    added_at = models.DateTimeField("Дата назначения", auto_now_add=True)

    class Meta:
        verbose_name = "сотрудник организации"
        verbose_name_plural = "сотрудники организаций"
        constraints = [models.UniqueConstraint(fields=["organization", "user"], name="unique_organization_member")]

    def __str__(self):
        return f"{self.user} — {self.organization}"
