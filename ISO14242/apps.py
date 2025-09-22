from __future__ import annotations

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class Iso14242Config(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ISO14242"
    verbose_name = _("مدیریت دارایی‌های ISO 14224")
