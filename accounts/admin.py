from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import Organization, User


class RoleAdminMixin:
    """Only users with the Admin role may use these admin pages (section 5.4 of the design)."""

    def _allowed(self, request):
        return request.user.is_active and getattr(request.user, "role", None) == "admin"

    def has_module_permission(self, request):
        return self._allowed(request)

    def has_view_permission(self, request, obj=None):
        return self._allowed(request)

    def has_add_permission(self, request):
        return self._allowed(request)

    def has_change_permission(self, request, obj=None):
        return self._allowed(request)

    def has_delete_permission(self, request, obj=None):
        return self._allowed(request)


@admin.register(User)
class UserAdmin(RoleAdminMixin, DjangoUserAdmin):
    list_display = ("username", "email", "role", "organization", "is_active")
    list_filter = ("role", "is_active")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(organization=request.user.organization)

    def get_fieldsets(self, request, obj=None):
        if request.user.is_superuser:
            return super().get_fieldsets(request, obj)
        if obj is None:
            return ((None, {"classes": ("wide",), "fields": ("username", "password1", "password2", "role")}),)
        return (
            (None, {"fields": ("username", "password")}),
            ("Personal info", {"fields": ("first_name", "last_name", "email")}),
            ("Access", {"fields": ("role", "is_active")}),
        )

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            obj.organization = request.user.organization     # Admins manage their own organisation only
        super().save_model(request, obj, form, change)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    """Superusers only (default model permissions; Admin-role users have none)."""
