from django.contrib import admin
from .models import Category, Event
from .forms import EventAdminForm
from applications.models import VolunteerApplication

class VolunteerApplicationInline(admin.TabularInline):
    model = VolunteerApplication
    extra = 0
    fields = ("applicant_name", "user", "contact", "status", "created_at")
    readonly_fields = fields
    can_delete = False
    show_change_link = True

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    form = EventAdminForm
    list_display = ("title", "organization", "category", "date", "status", "volunteers_needed")
    list_filter = ("status", "category", "organization", "date")
    search_fields = ("title", "description", "location", "organization__name")
    list_select_related = ("organization", "category")
    ordering = ("date",)
    date_hierarchy = "date"
    autocomplete_fields = ("organization", "category")
    inlines = (VolunteerApplicationInline,)
