# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('popolo', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='EntityName',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.TextField(db_index=True)),
                ('start_date', models.DateField(help_text=b'What date did this name/position start', null=True, blank=True)),
                ('end_date', models.DateField(help_text=b'What date did this name/position end', null=True, blank=True)),
                ('person', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='popolo.Person', help_text=b'The Popolo Person that this is a possible name for')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
