# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-02-28 13:50
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_ca', '0004_certificateauthority'),
    ]

    operations = [
        migrations.AddField(
            model_name='certificateauthority',
            name='serial',
            field=models.CharField(default='', max_length=48),
            preserve_default=False,
        ),
    ]