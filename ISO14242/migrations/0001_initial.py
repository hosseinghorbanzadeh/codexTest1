# Generated manually for ISO14242 Asset model
from __future__ import annotations

import uuid

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Asset",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("name", models.CharField(max_length=255, verbose_name="نام")),
                (
                    "code",
                    models.CharField(
                        blank=True,
                        help_text="کد داخلی یا مرجع برای گره.",
                        max_length=64,
                        null=True,
                        verbose_name="کد",
                    ),
                ),
                (
                    "level",
                    models.PositiveSmallIntegerField(editable=False, verbose_name="سطح"),
                ),
                (
                    "path",
                    models.CharField(
                        blank=True,
                        editable=False,
                        max_length=44,
                        verbose_name="مسیر درختی",
                    ),
                ),
                (
                    "standard_ref",
                    models.CharField(
                        blank=True,
                        max_length=64,
                        null=True,
                        verbose_name="کد استاندارد",
                    ),
                ),
                ("meta", models.JSONField(blank=True, null=True, verbose_name="اطلاعات تکمیلی")),
                (
                    "parent",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="children",
                        to="ISO14242.asset",
                        verbose_name="بالادستی",
                    ),
                ),
            ],
            options={
                "ordering": ["path"],
                "verbose_name": "تجهیز",
                "verbose_name_plural": "تجهیزات",
            },
        ),
        migrations.AddConstraint(
            model_name="asset",
            constraint=models.UniqueConstraint(
                fields=("parent", "name"),
                name="asset_unique_sibling_name",
            ),
        ),
        migrations.AddConstraint(
            model_name="asset",
            constraint=models.UniqueConstraint(
                fields=("parent", "code"),
                name="asset_unique_sibling_code",
            ),
        ),
    ]
