"""Пользователи Django с заявками и членством в организациях в карточке."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from applications.models import VolunteerApplication
from organizations.models import OrganizationMember


class UserApplicationInline(admin.TabularInline):
    model = VolunteerApplication
    fk_name = "user"
    extra = 0
    fields = ("event", "applicant_name", "status", "created_at")
    readonly_fields = ("event", "applicant_name", "created_at")
    can_delete = False
    show_change_link = True
    verbose_name_plural = "Заявки волонтёра"


class UserMembershipInline(admin.TabularInline):
    model = OrganizationMember
    fk_name = "user"
    extra = 0
    autocomplete_fields = ("organization",)
    verbose_name_plural = "Сотрудник организаций"


admin.site.unregister(User)


@admin.register(User)
class VolunteerUserAdmin(UserAdmin):
    list_display = ("username", "email", "first_name", "last_name", "is_staff", "date_joined")
    list_filter = ("is_staff", "is_superuser", "is_active", "groups")
    search_fields = ("username", "first_name", "last_name", "email")
    ordering = ("username",)
    list_per_page = 25
    inlines = (UserMembershipInline, UserApplicationInline)
