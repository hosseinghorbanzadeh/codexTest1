from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ISO14242Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ISO14242'
    label = 'iso14242'
    verbose_name = _('مدیریت دارایی ISO 14224')
