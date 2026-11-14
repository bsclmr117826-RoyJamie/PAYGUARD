from django.contrib import admin

from accounts.admin import RoleAdminMixin

from .models import RuleSetting
from .services import sync_rule_settings


@admin.register(RuleSetting)
class RuleSettingAdmin(RoleAdminMixin, admin.ModelAdmin):
    list_display = ("rule_code", "is_active")
    list_editable = ("is_active",)
    ordering = ("rule_code",)

    def changelist_view(self, request, extra_context=None):
        sync_rule_settings()
        return super().changelist_view(request, extra_context)

    def has_add_permission(self, request):
        return False        # rows are created by sync_rule_settings

    def has_delete_permission(self, request, obj=None):
        return False
