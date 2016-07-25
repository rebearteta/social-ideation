# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0024_auto_20160724_1711'),
    ]

    operations = [
        migrations.AlterField(
            model_name='participauser',
            name='ideascale_id',
            field=models.IntegerField(blank=True),
        ),
    ]
