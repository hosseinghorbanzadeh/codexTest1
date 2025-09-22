import pytest
from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory

from ISO14242.admin import AssetAdmin
from ISO14242.models import Asset


class DummyAdminSite(AdminSite):
    site_header = 'سایت تست'


@pytest.fixture
def asset_admin():
    return AssetAdmin(Asset, DummyAdminSite())


@pytest.mark.django_db
def test_admin_queryset_ordering(asset_admin):
    root_a = Asset.objects.create(name='الف')
    Asset.objects.create(name='الف-۱', parent=root_a)
    Asset.objects.create(name='الف-۲', parent=root_a)
    root_b = Asset.objects.create(name='ب')
    Asset.objects.create(name='ب-۱', parent=root_b)

    request = RequestFactory().get('/')
    qs = asset_admin.get_queryset(request)
    paths = list(qs.values_list('path', flat=True))
    assert paths == sorted(paths)


@pytest.mark.django_db
def test_indent_name_render(asset_admin):
    root = Asset.objects.create(name='ریشه')
    child = Asset.objects.create(name='فرزند', parent=root)

    html = asset_admin.display_indent_name(child)
    assert 'asset-level-2' in html
    assert 'فرزند' in html


@pytest.mark.django_db
def test_rebuild_action(asset_admin):
    root = Asset.objects.create(name='ریشه')
    child = Asset.objects.create(name='فرزند', parent=root)

    # دستکاری مسیر برای شبیه‌سازی نیاز به بازسازی
    Asset.objects.filter(pk=child.pk).update(path='9999')

    request = RequestFactory().post('/')
    request.user = type('User', (), {'is_staff': True, 'has_perm': lambda self, perm: True})()
    asset_admin.action_rebuild_tree(request, Asset.objects.all())
    child.refresh_from_db()
    assert child.path != '9999'
