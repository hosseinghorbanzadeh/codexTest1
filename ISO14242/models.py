from __future__ import annotations

import uuid
from typing import List

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from . import services


class Asset(models.Model):
    """Asset model representing ISO 14224 hierarchical elements."""

    MAX_LEVEL = 9
    SEGMENT_WIDTH = 4

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, verbose_name=_("نام"))
    code = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        verbose_name=_("کد"),
        help_text=_("کد داخلی یا مرجع برای گره."),
    )
    level = models.PositiveSmallIntegerField(editable=False, verbose_name=_("سطح"))
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
        verbose_name=_("بالادستی"),
    )
    path = models.CharField(
        max_length=SEGMENT_WIDTH * MAX_LEVEL + (MAX_LEVEL - 1),
        editable=False,
        blank=True,
        verbose_name=_("مسیر درختی"),
    )
    standard_ref = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        verbose_name=_("کد استاندارد"),
    )
    meta = models.JSONField(blank=True, null=True, verbose_name=_("اطلاعات تکمیلی"))

    class Meta:
        verbose_name = _("تجهیز")
        verbose_name_plural = _("تجهیزات")
        ordering = ["path"]
        constraints = [
            models.UniqueConstraint(
                fields=["parent", "name"],
                name="asset_unique_sibling_name",
            ),
            models.UniqueConstraint(
                fields=["parent", "code"],
                name="asset_unique_sibling_code",
            ),
        ]

    def __str__(self) -> str:
        return self.name

    def clean(self) -> None:
        super().clean()
        if self.code == "":
            self.code = None
        parent = self.parent if self.parent_id else None
        services.validate_no_cycle(self, parent)
        level = services.compute_level(parent)
        if level > self.MAX_LEVEL:
            raise ValidationError({
                "parent": _("عمق درخت نمی‌تواند بیش از ۹ باشد."),
            })
        self.level = level

    def save(self, *args, **kwargs) -> None:
        old_parent = None
        if self.pk:
            try:
                old_parent = Asset.objects.get(pk=self.pk).parent
            except Asset.DoesNotExist:
                old_parent = None
        self.full_clean()
        super().save(*args, **kwargs)
        parent = self.parent
        if parent is None:
            services.rebuild_branch(None)
        else:
            services.rebuild_branch(parent)
        if old_parent and (parent is None or old_parent.pk != parent.pk):
            services.rebuild_branch(old_parent)
        self.refresh_from_db(fields=["path", "level"])

    def get_ancestors(self) -> List["Asset"]:
        ancestors: List[Asset] = []
        node = self.parent
        while node is not None:
            ancestors.append(node)
            node = node.parent
        ancestors.reverse()
        return ancestors

    def get_children(self) -> models.QuerySet["Asset"]:
        return self.children.all().order_by("path")

    def get_descendants(self) -> models.QuerySet["Asset"]:
        if not self.path:
            return Asset.objects.none()
        lookup = f"{self.path}{services.SEGMENT_SEPARATOR}"
        return Asset.objects.filter(path__startswith=lookup).order_by("path")

    @property
    def indent_name(self) -> str:
        prefix = "" if self.level <= 1 else "— " * (self.level - 1)
        return format_html(
            '<span class="asset-indent asset-level-{}">{}</span>',
            self.level,
            f"{prefix}{self.name}",
        )

    indent_name.fget.short_description = _("نام")  # type: ignore[attr-defined]
    indent_name.fget.admin_order_field = "path"  # type: ignore[attr-defined]

    def children_count(self) -> int:
        return self.children.count()

    children_count.short_description = _("تعداد زیرمجموعه")
