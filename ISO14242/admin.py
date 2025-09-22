from __future__ import annotations

from django.contrib import admin, messages
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from . import services
from .models import Asset


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin[Asset]):
    list_display = ("indent_name", "code", "level", "parent", "children_count")
    search_fields = ("name", "code", "standard_ref")
    list_filter = ("level",)
    ordering = ("path",)
    actions = ("rebuild_tree",)
    raw_id_fields = ("parent",)
    readonly_fields = ("level", "path", "breadcrumb_display")
    fieldsets = (
        (
            _("مشخصات"),
            {
                "fields": ("name", "code", "standard_ref", "parent", "meta"),
            },
        ),
        (
            _("ساختار درختی"),
            {
                "fields": ("level", "path", "breadcrumb_display"),
            },
        ),
    )

    @admin.display(description=_("ردیف درخت"))
    def breadcrumb_display(self, obj: Asset | None) -> str:
        if obj is None or obj.pk is None:
            return "—"
        chain = [ancestor.name for ancestor in obj.get_ancestors()] + [obj.name]
        return " \u203a ".join(chain)

    def get_queryset(self, request: HttpRequest):  # type: ignore[override]
        qs = super().get_queryset(request)
        return qs.select_related("parent")

    @admin.action(description=_("بازسازی درخت (مسیر/سطح)"))
    def rebuild_tree(self, request: HttpRequest, queryset):
        stats = services.rebuild_full_tree()
        self.message_user(
            request,
            _("{} گره بازسازی شد.").format(stats.processed),
            level=messages.SUCCESS,
        )

    class Media:
        css = {
            "all": ("ISO14242/css/asset_admin.css",),
        }
