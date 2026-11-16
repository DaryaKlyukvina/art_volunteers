from django.contrib import admin
from .models import Organization, OrganizationMember


class OrganizationMemberInline(admin.TabularInline):
    model = OrganizationMember
    extra = 1


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "contact", "website", "created_at")
    search_fields = ("name", "contact", "description")
    ordering = ("name",)
    inlines = (OrganizationMemberInline,)


@admin.register(OrganizationMember)
class OrganizationMemberAdmin(admin.ModelAdmin):
    list_display = ("organization", "user", "added_at")
    list_filter = ("organization",)
    search_fields = ("organization__name", "user__username", "user__email")
