from __future__ import annotations

from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.db.models import Count
from django.http import HttpRequest
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import Asset
from .services import rebuild_tree


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ('display_indent_name', 'code', 'level', 'parent', 'children_count_display')
    search_fields = ('name', 'code', 'standard_ref')
    list_filter = ('level',)
    ordering = ('path',)
    raw_id_fields = ('parent',)
    readonly_fields = ('level', 'path', 'breadcrumb_display')
    actions = ('action_rebuild_tree',)

    def get_queryset(self, request: HttpRequest):
        qs = super().get_queryset(request)
        return qs.annotate(children_total=Count('children'))

    @admin.display(description=_('تعداد فرزندان'))
    def children_count_display(self, obj: Asset) -> int:
        return getattr(obj, 'children_total', obj.children.count())

    @admin.display(description=_('نام سلسله‌مراتبی'), ordering='path')
    def display_indent_name(self, obj: Asset) -> str:
        return format_html(
            '<span class="asset-indent asset-level-{}">{}</span>',
            obj.level,
            obj.indent_name,
        )

    @admin.display(description=_('مسیر سلسله‌مراتبی'))
    def breadcrumb_display(self, obj: Asset) -> str:
        return obj.breadcrumb

    @admin.action(description=_('بازسازی درخت (مسیر/سطح)'))
    def action_rebuild_tree(self, request: HttpRequest, queryset):
        try:
            rebuild_tree()
        except ValidationError as exc:
            self.message_user(
                request,
                _('خطا در بازسازی: %(error)s') % {'error': exc},
                level=messages.ERROR,
            )
        else:
            self.message_user(
                request,
                _('مسیر و سطوح دارایی‌ها با موفقیت بازسازی شد.'),
                level=messages.SUCCESS,
            )

    class Media:
        css = {
            'all': ('ISO14242/admin.css',),
        }
