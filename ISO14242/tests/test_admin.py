from __future__ import annotations

import pytest
from django.contrib.admin.sites import site
from django.contrib.auth import get_user_model
from django.test import RequestFactory

from ISO14242.admin import AssetAdmin
from ISO14242.models import Asset


@pytest.fixture
def admin_request(db):
    user_model = get_user_model()
    admin_user = user_model.objects.create_superuser(
        username='admin', email='admin@example.com', password='password'
    )
    request = RequestFactory().get('/admin/ISO14242/asset/')
    request.user = admin_user
    return request


@pytest.mark.django_db
def test_queryset_ordering_by_path(admin_request):
    root_b = Asset.objects.create(name='ب-ریشه')
    root_a = Asset.objects.create(name='الف-ریشه')
    child = Asset.objects.create(name='فرزند', parent=root_b)

    asset_admin = AssetAdmin(Asset, site)
    queryset = asset_admin.get_queryset(admin_request)
    paths = list(queryset.values_list('path', flat=True))
    assert paths == sorted(paths)
    assert child in queryset


@pytest.mark.django_db
def test_list_display_uses_indent_name(admin_request):
    asset_admin = AssetAdmin(Asset, site)
    display = asset_admin.get_list_display(admin_request)
    assert display[0] == 'indent_name'


@pytest.mark.django_db
def test_indent_name_renders_span(admin_request):
    asset = Asset.objects.create(name='ریشه')
    rendered = asset.indent_name
    assert 'asset-indent' in rendered
    assert 'asset-level-1' in rendered


def test_media_includes_custom_css():
    asset_admin = AssetAdmin(Asset, site)
    assert 'ISO14242/css/asset_admin.css' in asset_admin.Media.css['all']
