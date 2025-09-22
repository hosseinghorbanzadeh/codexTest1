from __future__ import annotations

import uuid
from typing import List

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _

from . import services
from .constants import MAX_DEPTH, PATH_MAX_LENGTH


class Asset(models.Model):
    """نمایانگر تجهیز در ساختار استاندارد ISO 14224."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_('نام تجهیز'), max_length=255)
    code = models.CharField(_('کد تجهیز'), max_length=50, null=True, blank=True)
    level = models.PositiveSmallIntegerField(_('سطح'), default=1, editable=False)
    parent = models.ForeignKey(
        'self',
        verbose_name=_('والد'),
        related_name='children',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    path = models.CharField(
        _('مسیر درختی'),
        max_length=PATH_MAX_LENGTH,
        editable=False,
        blank=True,
        default='',
    )
    standard_ref = models.CharField(_('مرجع استاندارد'), max_length=100, null=True, blank=True)
    meta = models.JSONField(_('متادیتا'), null=True, blank=True)

    class Meta:
        verbose_name = _('دارایی')
        verbose_name_plural = _('دارایی‌ها')
        ordering = ['path']
        constraints = [
            models.UniqueConstraint(
                fields=['parent', 'name'], name='uniq_asset_parent_name'
            ),
            models.UniqueConstraint(
                fields=['parent', 'code'],
                name='uniq_asset_parent_code',
                condition=~models.Q(code__isnull=True),
            ),
        ]

    def __str__(self) -> str:  # pragma: no cover - خوانایی
        return self.name

    def clean(self) -> None:
        super().clean()
        parent = self.parent
        if self.code == '':
            self.code = None
        services.ensure_no_cycles(self, parent)
        self.level = services.compute_level(parent)
        if self.level > MAX_DEPTH:
            raise ValidationError(
                {'parent': _('حداکثر عمق مجاز ساختار ۹ سطح است.')}
            )

    def save(self, *args, **kwargs) -> None:
        old_root_pk = None
        if self.pk:
            try:
                old_instance = type(self).objects.select_related('parent').get(pk=self.pk)
            except type(self).DoesNotExist:  # pragma: no cover - شرایط نادر
                old_instance = None
            if old_instance is not None:
                old_root_pk = old_instance.get_root().pk
        self.full_clean()
        with transaction.atomic():
            super().save(*args, **kwargs)
            new_root = self.get_root()
            services.rebuild_subtree(self)
            if old_root_pk and old_root_pk != new_root.pk:
                try:
                    old_root = type(self).objects.get(pk=old_root_pk)
                except type(self).DoesNotExist:  # pragma: no cover - حذف همزمان
                    old_root = None
                if old_root is not None:
                    services.rebuild_subtree(old_root)

    def delete(self, using=None, keep_parents=False):
        parent = self.parent
        with transaction.atomic():
            super().delete(using=using, keep_parents=keep_parents)
            services.rebuild_subtree(parent)

    # --- متدهای کمکی ---
    def get_children(self) -> models.QuerySet['Asset']:
        return self.children.all().order_by('path')

    def get_descendants(self, include_self: bool = False) -> models.QuerySet['Asset']:
        if not self.path:
            return Asset.objects.none()
        lookup = {'path__startswith': self.path}
        qs = Asset.objects.filter(**lookup).order_by('path')
        if not include_self:
            qs = qs.exclude(pk=self.pk)
        return qs

    def get_ancestors(self, include_self: bool = False) -> List['Asset']:
        ancestors: List['Asset'] = []
        node = self.parent if not include_self else self
        while node is not None:
            ancestors.append(node)
            node = node.parent
        ancestors.reverse()
        return ancestors

    @property
    def indent_name(self) -> str:
        prefix = '—' * max(self.level - 1, 0)
        return f"{prefix} {self.name}" if prefix else self.name

    @property
    def breadcrumb(self) -> str:
        ancestors = self.get_ancestors(include_self=True)
        return ' / '.join(asset.name for asset in ancestors)

    def children_count(self) -> int:
        return self.children.count()

    children_count.short_description = _('تعداد فرزندان')

    def get_root(self) -> 'Asset':
        node = self
        while node.parent_id:
            node = node.parent  # type: ignore[assignment]
        return node
