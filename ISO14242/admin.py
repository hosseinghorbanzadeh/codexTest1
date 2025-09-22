from __future__ import annotations

from typing import TYPE_CHECKING
from django.contrib import admin, messages
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from . import services
from .models import Asset

# --- برای تایپ‌هینتِ جنریک بدون ایجاد خطای زمان اجرا ---
if TYPE_CHECKING:
    from django.contrib.admin import ModelAdmin as _ModelAdmin

    class _AssetAdmin(_ModelAdmin[Asset]): ...
    BaseAdmin = _AssetAdmin
else:
    BaseAdmin = admin.ModelAdmin
# --------------------------------------------------------

@admin.register(Asset)
class AssetAdmin(BaseAdmin):
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
            {"fields": ("name", "code", "standard_ref", "parent", "meta")},
        ),
        (
            _("ساختار درختی"),
            {"fields": ("level", "path", "breadcrumb_display")},
        ),
    )

    @admin.display(description=_("ردیف درخت"))
    def breadcrumb_display(self, obj: Asset | None) -> str:
        if not obj or not getattr(obj, "pk", None):
            return "—"
        chain = [a.name for a in obj.get_ancestors()] + [obj.name]
        return " \u203a ".join(chain)

    def get_queryset(self, request: HttpRequest) -> QuerySet[Asset]:  # type: ignore[override]
        qs = super().get_queryset(request)
        return qs.select_related("parent")

    @admin.action(description=_("بازسازی درخت (مسیر/سطح)"))
    def rebuild_tree(self, request: HttpRequest, queryset: QuerySet[Asset]) -> None:
        stats = services.rebuild_full_tree()
        processed = getattr(stats, "processed", None) or getattr(stats, "count", None) or 0
        self.message_user(
            request,
            _("{} گره بازسازی شد.").format(processed),
            level=messages.SUCCESS,
        )

    class Media:
        css = {"all": ("ISO14242/css/asset_admin.css",)}
