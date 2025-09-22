from __future__ import annotations

from collections import defaultdict
from typing import List, Optional, Sequence

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from .constants import MAX_DEPTH, PADDING_WIDTH

SEGMENT_FORMAT = f"{{:0{PADDING_WIDTH}d}}"


def compute_level(parent: Optional['Asset']) -> int:
    return 1 if parent is None else parent.level + 1


def ensure_no_cycles(instance: 'Asset', parent: Optional['Asset']) -> None:
    """بررسی جلوگیری از حلقه در ساختار."""

    if parent is None or instance.pk is None and parent.pk is None:
        return

    current = parent
    while current is not None:
        if instance.pk is not None and current.pk == instance.pk:
            raise ValidationError({'parent': _('انتخاب فرزند به عنوان والد مجاز نیست.')})
        current = current.parent


def rebuild_subtree(node: Optional['Asset']) -> None:
    if node is None:
        rebuild_tree()
        return
    root = node.get_root()
    rebuild_tree([root])


def rebuild_tree(root_nodes: Optional[Sequence['Asset']] = None) -> None:
    """بازسازی مسیر و سطح برای کل درخت یا زیرمجموعه‌ای از ریشه‌ها."""

    from .models import Asset

    with transaction.atomic():
        all_assets: List[Asset] = list(Asset.objects.select_related('parent'))
        children_map: defaultdict[Optional[str], List[Asset]] = defaultdict(list)
        for asset in all_assets:
            children_map[str(asset.parent_id) if asset.parent_id else None].append(asset)

        def sort_nodes(nodes: List[Asset]) -> List[Asset]:
            return sorted(
                nodes,
                key=lambda obj: (
                    obj.name.casefold(),
                    (obj.code or '').casefold(),
                    str(obj.pk),
                ),
            )

        def walk(nodes: List[Asset], prefix: str, level: int, updates: List[Asset]) -> None:
            if level > MAX_DEPTH:
                raise ValidationError({'parent': _('حداکثر عمق مجاز ساختار ۹ سطح است.')})
            for index, node in enumerate(sort_nodes(nodes), start=1):
                node.level = level
                segment = SEGMENT_FORMAT.format(index)
                node.path = f"{prefix}/{segment}" if prefix else segment
                updates.append(node)
                children = children_map.get(str(node.id)) or []
                walk(children, node.path, level + 1, updates)

        updates: List[Asset] = []
        roots = children_map.get(None, [])
        if root_nodes:
            root_ids = {root.pk for root in root_nodes if root.pk is not None}
            roots = [root for root in roots if root.pk in root_ids]
        walk(sort_nodes(roots), '', 1, updates)

        if updates:
            Asset.objects.bulk_update(updates, ['level', 'path'])


__all__ = [
    'compute_level',
    'ensure_no_cycles',
    'rebuild_subtree',
    'rebuild_tree',
]
