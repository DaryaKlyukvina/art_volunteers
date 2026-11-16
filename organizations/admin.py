from django.contrib import admin
from django.db.models import Count

from events.models import Event

from .models import Organization, OrganizationMember


class OrganizationMemberInline(admin.TabularInline):
    model = OrganizationMember
    extra = 1
    autocomplete_fields = ("user",)


class EventInline(admin.TabularInline):
    """Мероприятия на странице организации (только просмотр, переход к редактированию по ссылке)."""
    model = Event
    extra = 0
    fields = ("title", "date", "status", "volunteers_needed")
    readonly_fields = fields
    can_delete = False
    show_change_link = True


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "contact", "website", "events_count", "created_at")
    search_fields = ("name", "contact", "description")
    ordering = ("name",)
    list_per_page = 20
    readonly_fields = ("created_at",)
    inlines = (OrganizationMemberInline, EventInline)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(events_total=Count("events"))

    @admin.display(description="Мероприятий", ordering="events_total")
    def events_count(self, obj):
        return obj.events_total


@admin.register(OrganizationMember)
class OrganizationMemberAdmin(admin.ModelAdmin):
    list_display = ("organization", "user", "added_at")
    list_filter = ("organization",)
    search_fields = ("organization__name", "user__username", "user__email")
    list_select_related = ("organization", "user")
    autocomplete_fields = ("organization", "user")
