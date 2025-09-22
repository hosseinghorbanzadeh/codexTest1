from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.translation import gettext_lazy as _

SEGMENT_WIDTH = 4
SEGMENT_SEPARATOR = "/"


@dataclass(slots=True)
class RebuildStats:
    processed: int = 0


def _format_segment(index: int) -> str:
    return f"{index:0{SEGMENT_WIDTH}d}"


def compute_level(parent: Optional["Asset"]) -> int:
    return 1 if parent is None else parent.level + 1


def validate_no_cycle(instance: "Asset", parent: Optional["Asset"]) -> None:
    if parent is None or instance.pk is None and parent.pk is None:
        return
    cursor = parent
    while cursor is not None:
        if instance.pk is not None and cursor.pk == instance.pk:
            raise ValidationError({
                "parent": _("انتخاب این گره باعث ایجاد چرخه در درخت می‌شود."),
            })
        cursor = cursor.parent


def rebuild_branch(parent: Optional["Asset"]) -> RebuildStats:
    from .models import Asset

    stats = RebuildStats()

    def apply(node: Asset, index: int, parent_node: Optional[Asset]) -> None:
        nonlocal stats
        level = 1 if parent_node is None else parent_node.level + 1
        if level > Asset.MAX_LEVEL:
            raise ValidationError({
                "parent": _("عمق درخت بیش از حد مجاز است."),
            })
        segment = _format_segment(index)
        path = segment if parent_node is None else f"{parent_node.path}{SEGMENT_SEPARATOR}{segment}"
        Asset.objects.filter(pk=node.pk).update(level=level, path=path)
        node.level = level
        node.path = path
        stats.processed += 1
        children = list(node.children.all().order_by("name", "code", "pk"))
        for child_index, child in enumerate(children, start=1):
            apply(child, child_index, node)

    with transaction.atomic():
        if parent is None:
            roots = list(Asset.objects.filter(parent__isnull=True).order_by("name", "code", "pk"))
            for index, root in enumerate(roots, start=1):
                apply(root, index, None)
        else:
            parent = Asset.objects.select_related("parent").get(pk=parent.pk)
            siblings = list(parent.children.all().order_by("name", "code", "pk"))
            for index, node in enumerate(siblings, start=1):
                apply(node, index, parent)
    return stats


def rebuild_full_tree() -> RebuildStats:
    return rebuild_branch(parent=None)


def rebuild_descendants(root: "Asset") -> RebuildStats:
    from .models import Asset

    stats = RebuildStats()

    def apply(node: Asset, parent_node: Optional[Asset]) -> None:
        nonlocal stats
        level = compute_level(parent_node)
        if level > Asset.MAX_LEVEL:
            raise ValidationError({
                "parent": _("عمق درخت بیش از حد مجاز است."),
            })
        if parent_node is None:
            raise ValidationError({
                "parent": _("ریشه باید parent نداشته باشد."),
            })
        siblings = list(parent_node.children.all().order_by("name", "code", "pk"))
        for index, sibling in enumerate(siblings, start=1):
            segment = _format_segment(index)
            path = f"{parent_node.path}{SEGMENT_SEPARATOR}{segment}"
            Asset.objects.filter(pk=sibling.pk).update(level=level, path=path)
            sibling.level = level
            sibling.path = path
            stats.processed += 1
            children = list(sibling.children.all().order_by("name", "code", "pk"))
            for child in children:
                apply(child, sibling)

    with transaction.atomic():
        parent = root.parent
        if parent is None:
            raise ValidationError({
                "parent": _("زیرشاخه برای ریشه موجود نیست."),
            })
        apply(root, parent)
    return stats
