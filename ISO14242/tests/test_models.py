import pytest
from django.core.exceptions import ValidationError

from ISO14242.models import Asset


@pytest.mark.django_db
def test_depth_validation_and_success():
    parent = None
    last = None
    for index in range(1, 10):
        asset = Asset(name=f'گره {index}', parent=last)
        asset.save()
        last = asset
    assert last.level == 9
    with pytest.raises(ValidationError):
        Asset.objects.create(name='گره ۱۰', parent=last)


@pytest.mark.django_db
def test_cycle_prevention():
    root = Asset.objects.create(name='ریشه')
    child = Asset.objects.create(name='فرزند', parent=root)
    grand_child = Asset.objects.create(name='نوه', parent=child)

    root.parent = grand_child
    with pytest.raises(ValidationError):
        root.save()


@pytest.mark.django_db
def test_sibling_uniqueness():
    root = Asset.objects.create(name='ریشه')
    Asset.objects.create(name='پمپ', parent=root, code='P-100')

    with pytest.raises(ValidationError):
        Asset.objects.create(name='پمپ', parent=root)

    with pytest.raises(ValidationError):
        Asset.objects.create(name='شیر', parent=root, code='P-100')


@pytest.mark.django_db
def test_hierarchy_helpers():
    root = Asset.objects.create(name='ریشه')
    unit = Asset.objects.create(name='واحد', parent=root)
    equipment = Asset.objects.create(name='تجهیز', parent=unit)

    assert [a.name for a in equipment.get_ancestors()] == ['ریشه', 'واحد']
    assert [a.name for a in equipment.get_ancestors(include_self=True)] == ['ریشه', 'واحد', 'تجهیز']

    descendants = list(root.get_descendants())
    assert [a.name for a in descendants] == ['واحد', 'تجهیز']
    assert equipment.indent_name.endswith('تجهیز')
    assert equipment.breadcrumb == 'ریشه / واحد / تجهیز'
