# Generated by Django 4.0.7 on 2022-09-02 08:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('group', '0001_initial'),
        ('tack', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='grouptacks',
            name='tack',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tack.tack'),
        ),
        migrations.AddField(
            model_name='groupmembers',
            name='group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='group.group'),
        ),
    ]
