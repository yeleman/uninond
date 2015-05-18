# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Contact',
            fields=[
                ('identity', models.CharField(max_length=50, serialize=False, verbose_name='Num\xe9ro t\xe9l\xe9phone', primary_key=True)),
                ('name', models.CharField(max_length=200, null=True, verbose_name='Nom', blank=True)),
                ('role', models.SlugField(choices=[('dugutigi', 'Chef de village'), ('DRPC', 'DRPC'), ('sous-prefet', 'Sous-pr\xe9fet'), ('maire', 'Maire'), ('prefet', 'Pr\xe9fet'), ('DRS', 'DRS'), ('gouverneur', 'Gouverneur'), ('DRDSES', 'DRDSES')], max_length=200, blank=True, null=True, verbose_name='R\xf4le')),
                ('position', models.CharField(max_length=500, null=True, verbose_name='Fonction', blank=True)),
                ('active', models.BooleanField(default=True, verbose_name='Actif ?')),
            ],
        ),
        migrations.CreateModel(
            name='FloodEvent',
            fields=[
                ('ident', models.SlugField(max_length=10, serialize=False, primary_key=True)),
                ('created_on', models.DateTimeField(default=django.utils.timezone.now)),
                ('status', models.SlugField(default='created', choices=[('cancelled', 'Annul\xe9e'), ('confirmed', 'Confirm\xe9e'), ('expired', 'Expir\xe9e'), ('restrained', 'Contenue'), ('created', 'Cr\xe9\xe9')])),
                ('expired_on', models.DateTimeField(null=True, blank=True)),
                ('initial_flooded_area', models.PositiveIntegerField(choices=[(1, '1/3'), (2, '2/3'), (3, '3/3')])),
                ('initial_homes_destroyed', models.PositiveIntegerField(default=0)),
                ('initial_dead', models.PositiveIntegerField(default=0)),
                ('initial_wounded', models.PositiveIntegerField(default=0)),
                ('cancelled_on', models.DateTimeField(null=True, blank=True)),
                ('restrained_on', models.DateTimeField(null=True, blank=True)),
                ('restrained_flooded_area', models.PositiveIntegerField(blank=True, null=True, choices=[(1, '1/3'), (2, '2/3'), (3, '3/3')])),
                ('restrained_homes_destroyed', models.PositiveIntegerField(null=True, blank=True)),
                ('restrained_dead', models.PositiveIntegerField(null=True, blank=True)),
                ('restrained_wounded', models.PositiveIntegerField(null=True, blank=True)),
                ('restrained_comment', models.CharField(max_length=1600, null=True, blank=True)),
                ('confirmed_on', models.DateTimeField(null=True, blank=True)),
                ('confirmed_flooded_area', models.PositiveIntegerField(blank=True, null=True, choices=[(1, '1/3'), (2, '2/3'), (3, '3/3')])),
                ('confirmed_homes_destroyed', models.PositiveIntegerField(null=True, blank=True)),
                ('confirmed_dead', models.PositiveIntegerField(null=True, blank=True)),
                ('confirmed_wounded', models.PositiveIntegerField(null=True, blank=True)),
                ('confirmed_comment', models.CharField(max_length=1600, null=True, blank=True)),
                ('cancelled_by', models.ForeignKey(related_name='cancelled_flood_events', blank=True, to='uninond.Contact', null=True)),
                ('confirmed_by', models.ForeignKey(related_name='confirmed_flood_events', blank=True, to='uninond.Contact', null=True)),
                ('created_by', models.ForeignKey(related_name='flood_events', to='uninond.Contact')),
            ],
            options={
                'ordering': ['-created_on'],
                'verbose_name': 'Inondation',
                'verbose_name_plural': 'Inondations',
            },
        ),
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('slug', models.SlugField(unique=True, null=True)),
                ('name', models.CharField(max_length=150)),
                ('location_type', models.SlugField(choices=[('arrondissement', 'Arrondissement'), ('commune', 'Commune'), ('region', 'R\xe9gion'), ('vfq', 'Village'), ('cercle', 'Cercle')])),
                ('main_contact', models.ForeignKey(related_name='locations', blank=True, to='uninond.Contact', null=True)),
                ('parent', models.ForeignKey(blank=True, to='uninond.Location', null=True)),
            ],
            options={
                'verbose_name': 'Location',
                'verbose_name_plural': 'Locations',
            },
        ),
        migrations.CreateModel(
            name='SMSMessage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('direction', models.CharField(max_length=75, choices=[('outgoing', 'Envoy\xe9'), ('incoming', 'Re\xe7u')])),
                ('identity', models.CharField(max_length=250)),
                ('created_on', models.DateTimeField(default=django.utils.timezone.now)),
                ('event_on', models.DateTimeField(default=django.utils.timezone.now)),
                ('text', models.TextField()),
                ('handled', models.BooleanField(default=False)),
                ('validity', models.PositiveIntegerField(null=True, blank=True)),
                ('deferred', models.PositiveIntegerField(null=True, blank=True)),
                ('delivery_status', models.CharField(default='unknown', max_length=75, choices=[('buffered', 'Message Buffered'), ('success', 'Delivery Success'), ('smsc_submit', 'SMSC Submit'), ('smsc_notifications', 'SMSC Intermediate Notifications'), ('unknown', 'Unknown'), ('failure', 'Delivery Failure'), ('smsc_reject', 'SMSC Reject')])),
            ],
            options={
                'verbose_name': 'SMS Message',
                'verbose_name_plural': 'SMS Messages',
            },
        ),
        migrations.AddField(
            model_name='floodevent',
            name='location',
            field=models.ForeignKey(related_name='flood_events', to='uninond.Location'),
        ),
        migrations.AddField(
            model_name='floodevent',
            name='messages',
            field=models.ManyToManyField(related_name='flood_events', to='uninond.SMSMessage', blank=True),
        ),
        migrations.AddField(
            model_name='floodevent',
            name='restrained_by',
            field=models.ForeignKey(related_name='restrained_flood_events', blank=True, to='uninond.Contact', null=True),
        ),
        migrations.AddField(
            model_name='contact',
            name='location',
            field=models.ForeignKey(verbose_name='Localit\xe9', to='uninond.Location'),
        ),
    ]
