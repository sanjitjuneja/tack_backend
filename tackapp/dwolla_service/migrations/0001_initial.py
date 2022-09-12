# Generated by Django 4.0.7 on 2022-09-12 17:08

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='DwollaEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_id', models.UUIDField()),
                ('topic', models.CharField(max_length=64)),
                ('timestamp', models.DateTimeField()),
                ('self_res', models.JSONField(blank=True, null=True)),
                ('account', models.JSONField(blank=True, null=True)),
                ('resource', models.JSONField(blank=True, null=True)),
                ('customer', models.JSONField(blank=True, null=True)),
                ('created', models.DateTimeField()),
            ],
            options={
                'verbose_name': 'Dwolla event',
                'verbose_name_plural': 'Dwolla events',
                'db_table': 'dwolla_events',
            },
        ),
        migrations.CreateModel(
            name='DwollaRemovedAccount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dwolla_id', models.UUIDField()),
                ('creation_time', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Dwolla removed account',
                'verbose_name_plural': 'Dwolla removed accounts',
                'db_table': 'dwolla_removed_accounts',
            },
        ),
    ]
