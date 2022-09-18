# Generated by Django 4.0.7 on 2022-09-13 08:29

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('group', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='groupmembers',
            name='member',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='groupinvitations',
            name='group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='group.group'),
        ),
        migrations.AddField(
            model_name='groupinvitations',
            name='invitee',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='gi_invitee', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='group',
            name='owner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddConstraint(
            model_name='groupmembers',
            constraint=models.UniqueConstraint(fields=('group', 'member'), name='unique_member_for_group'),
        ),
    ]
