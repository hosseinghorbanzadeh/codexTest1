"""WSGI config for iso_admin project."""
from __future__ import annotations

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "iso_admin.settings")

application = get_wsgi_application()
