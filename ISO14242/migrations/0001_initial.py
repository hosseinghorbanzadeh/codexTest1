# Generated manually for Django 5 project
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Asset',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255, verbose_name='نام تجهیز')),
                (
                    'code',
                    models.CharField(blank=True, max_length=50, null=True, verbose_name='کد تجهیز'),
                ),
                (
                    'level',
                    models.PositiveSmallIntegerField(default=1, editable=False, verbose_name='سطح'),
                ),
                (
                    'path',
                    models.CharField(
                        blank=True,
                        default='',
                        editable=False,
                        max_length=44,
                        verbose_name='مسیر درختی',
                    ),
                ),
                (
                    'standard_ref',
                    models.CharField(blank=True, max_length=100, null=True, verbose_name='مرجع استاندارد'),
                ),
                ('meta', models.JSONField(blank=True, null=True, verbose_name='متادیتا')),
                (
                    'parent',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='children',
                        to='iso14242.asset',
                        verbose_name='والد',
                    ),
                ),
            ],
            options={
                'verbose_name': 'دارایی',
                'verbose_name_plural': 'دارایی‌ها',
                'ordering': ['path'],
            },
        ),
        migrations.AddConstraint(
            model_name='asset',
            constraint=models.UniqueConstraint(
                fields=('parent', 'name'), name='uniq_asset_parent_name'
            ),
        ),
        migrations.AddConstraint(
            model_name='asset',
            constraint=models.UniqueConstraint(
                condition=models.Q(('code__isnull', False)),
                fields=('parent', 'code'),
                name='uniq_asset_parent_code',
            ),
        ),
    ]
