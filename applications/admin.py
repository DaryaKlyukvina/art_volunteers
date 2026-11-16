from django.contrib import admin
from .models import VolunteerApplication

@admin.register(VolunteerApplication)
class VolunteerApplicationAdmin(admin.ModelAdmin):
    list_display = ("applicant_name", "event", "user", "status", "created_at")
    list_filter = ("status", "event__organization", "event")
    search_fields = ("applicant_name", "contact", "user__username", "event__title")
    list_select_related = ("user", "event", "event__organization")
    readonly_fields = ("user", "event", "created_at", "updated_at")
