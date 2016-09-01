# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0030_campaign_notified'),
    ]

    operations = [
        migrations.AddField(
            model_name='participauser',
            name='welcome_msg_sent',
            field=models.BooleanField(default=False),
        ),
    ]
