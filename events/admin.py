from django.contrib import admin
from django.db.models import Count, Q

from applications.models import VolunteerApplication

from .forms import EventAdminForm
from .models import Category, Event


class VolunteerApplicationInline(admin.TabularInline):
    """Заявки на странице мероприятия: просмотр и изменение статуса."""
    model = VolunteerApplication
    extra = 0
    fields = ("applicant_name", "user", "contact", "status", "created_at")
    readonly_fields = ("applicant_name", "user", "contact", "created_at")
    can_delete = False
    show_change_link = True


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "events_count")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(events_total=Count("events"))

    @admin.display(description="Мероприятий", ordering="events_total")
    def events_count(self, obj):
        return obj.events_total


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    form = EventAdminForm
    list_display = ("title", "organization", "category", "date", "status", "volunteers_needed", "accepted_count",
                    "is_large")
    list_display_links = ("title",)
    list_editable = ("status", "volunteers_needed")
    list_filter = ("status", "is_large", "category", "organization", "date")
    search_fields = ("title", "description", "location", "organization__name")
    list_select_related = ("organization", "category")
    ordering = ("date",)
    list_per_page = 20
    date_hierarchy = "date"
    autocomplete_fields = ("organization", "category")
    readonly_fields = ("created_at", "is_large")
    prepopulated_fields = {"slug": ("title",)}
    fieldsets = (
        (None, {"fields": ("title", "slug", "organization", "category", "status")}),
        ("Проведение", {"fields": ("date", "location", "volunteers_needed", "is_large", "ticket_url")}),
        ("Описание", {"fields": ("description", "image", "created_at")}),
    )
    inlines = (VolunteerApplicationInline,)
    actions = ("publish_events", "cancel_events")

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            accepted_total=Count("applications", filter=Q(applications__status=VolunteerApplication.Status.ACCEPTED)),
        )

    @admin.display(description="Принято", ordering="accepted_total")
    def accepted_count(self, obj):
        return obj.accepted_total

    @admin.action(description="Опубликовать выбранные мероприятия")
    def publish_events(self, request, queryset):
        updated = queryset.exclude(status=Event.Status.CANCELLED).update(status=Event.Status.PUBLISHED)
        self.message_user(request, f"Опубликовано мероприятий: {updated}.")

    @admin.action(description="Отменить выбранные мероприятия")
    def cancel_events(self, request, queryset):
        updated = queryset.update(status=Event.Status.CANCELLED)
        self.message_user(request, f"Отменено мероприятий: {updated}.")
