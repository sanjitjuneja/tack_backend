# Generated by Django 4.0.6 on 2022-07-22 12:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('group', '0002_alter_group_invitation_link_grouptacks_groupmembers_and_more'),
        ('user', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='active_group',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='group.group'),
        ),
    ]
