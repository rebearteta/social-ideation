# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0023_auto_20160710_0019'),
    ]

    operations = [
        migrations.CreateModel(
            name='ParticipaUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ideascale_id', models.CharField(max_length=50, blank=True)),
                ('valid_user', models.BooleanField(default=False)),
                ('name', models.CharField(max_length=100, null=True)),
                ('email', models.EmailField(max_length=254)),
                ('age', models.CharField(max_length=20, choices=[(b'<18', b'Menor de 18 a\xc3\xb1os'), (b'18-24', b'18 a 24 a\xc3\xb1os'), (b'25-34', b'25 a 34 a\xc3\xb1os'), (b'35-44', b'35 a 44 a\xc3\xb1os'), (b'45-54', b'45 a 54 a\xc3\xb1os'), (b'55-64', b'55 a 64 a\xc3\xb1os'), (b'>65', b'25 a 34 a\xc3\xb1os')])),
                ('city', models.CharField(max_length=20, choices=[('asunci\xf3n', 'Asunci\xf3n'), ('fernando', 'Fernando de la Mora'), ('lambar\xe9', 'Lambar\xe9'), ('otra', 'Otra')])),
                ('sex', models.CharField(max_length=10, choices=[(b'm', b'Masculino'), (b'f', b'Femenino')])),
            ],
        ),
        migrations.AddField(
            model_name='socialnetworkappuser',
            name='participa_user',
            field=models.OneToOneField(null=True, blank=True, to='app.ParticipaUser'),
        ),
    ]
