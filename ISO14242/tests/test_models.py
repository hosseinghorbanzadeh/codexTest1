from __future__ import annotations

import pytest
from django.core.exceptions import ValidationError

from ISO14242.models import Asset


@pytest.mark.django_db
def test_nine_level_chain_is_valid() -> None:
    parent = None
    for idx in range(1, 10):
        parent = Asset.objects.create(name=f"گره {idx}", parent=parent)
        assert parent.level == idx
        expected_slashes = max(idx - 1, 0)
        assert parent.path.count("/") == expected_slashes


@pytest.mark.django_db
def test_tenth_level_raises_validation_error() -> None:
    parent = None
    for idx in range(1, 10):
        parent = Asset.objects.create(name=f"پله {idx}", parent=parent)
    with pytest.raises(ValidationError):
        Asset.objects.create(name="پله ۱۰", parent=parent)


@pytest.mark.django_db
def test_cycle_detection_prevents_parent_from_descendant() -> None:
    root = Asset.objects.create(name="ریشه")
    child = Asset.objects.create(name="فرزند", parent=root)
    root.parent = child
    with pytest.raises(ValidationError):
        root.save()


@pytest.mark.django_db
def test_unique_name_and_code_among_siblings() -> None:
    root = Asset.objects.create(name="ریشه")
    Asset.objects.create(name="گره الف", code="CODE1", parent=root)
    with pytest.raises(ValidationError):
        Asset.objects.create(name="گره الف", parent=root)
    with pytest.raises(ValidationError):
        Asset.objects.create(name="گره ب", code="CODE1", parent=root)


@pytest.mark.django_db
def test_indent_name_and_descendants_ordering() -> None:
    root = Asset.objects.create(name="ریشه")
    child = Asset.objects.create(name="فرزند", parent=root)
    grand = Asset.objects.create(name="نوه", parent=child)

    assert "asset-level-1" in root.indent_name
    assert "asset-level-2" in child.indent_name
    descendants = list(root.get_descendants())
    assert descendants == [child, grand]
