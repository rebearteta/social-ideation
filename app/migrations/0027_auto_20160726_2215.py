# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0026_auto_20160726_2209'),
    ]

    operations = [
        migrations.AlterField(
            model_name='participauser',
            name='first_name',
            field=models.CharField(default='', max_length=100, blank=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='participauser',
            name='last_name',
            field=models.CharField(default='', max_length=100, blank=True),
            preserve_default=False,
        ),
    ]
