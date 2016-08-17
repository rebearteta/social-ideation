# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0029_auto_20160802_2057'),
    ]

    operations = [
        migrations.AddField(
            model_name='campaign',
            name='notified',
            field=models.BooleanField(default=False),
        ),
    ]
