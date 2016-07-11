# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0022_auto_20151021_1417'),
    ]

    operations = [
        migrations.AlterField(
            model_name='socialnetworkapp',
            name='community',
            field=models.ForeignKey(blank=True, to='app.SocialNetworkAppCommunity', null=True),
        ),
    ]
