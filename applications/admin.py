from django.contrib import admin, messages
from django.core.exceptions import ValidationError

from .models import VolunteerApplication
from .services import set_application_status


@admin.register(VolunteerApplication)
class VolunteerApplicationAdmin(admin.ModelAdmin):
    list_display = ("applicant_name", "event", "event_date", "user", "status", "created_at")
    list_display_links = ("applicant_name",)
    list_filter = ("status", "created_at", "event__organization", "event")
    search_fields = ("applicant_name", "contact", "user__username", "user__email", "event__title")
    list_select_related = ("user", "event", "event__organization")
    ordering = ("-created_at",)
    list_per_page = 25
    date_hierarchy = "created_at"
    readonly_fields = ("user", "event", "created_at", "updated_at")
    actions = ("accept_applications", "reject_applications")

    @admin.display(description="Дата мероприятия", ordering="event__date")
    def event_date(self, obj):
        return obj.event.date

    def _change_status(self, request, queryset, status):
        changed = 0
        for application in queryset:
            try:
                set_application_status(application, status)
                changed += 1
            except ValidationError as error:
                self.message_user(request, f"{application}: {error.messages[0]}", level=messages.WARNING)
        self.message_user(request, f"Изменено заявок: {changed}.")

    @admin.action(description="Принять выбранные заявки (с проверкой свободных мест)")
    def accept_applications(self, request, queryset):
        self._change_status(request, queryset, VolunteerApplication.Status.ACCEPTED)

    @admin.action(description="Отклонить выбранные заявки")
    def reject_applications(self, request, queryset):
        self._change_status(request, queryset, VolunteerApplication.Status.REJECTED)
