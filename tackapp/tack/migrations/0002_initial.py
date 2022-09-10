# Generated by Django 4.0.7 on 2022-09-10 07:59

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('group', '0003_initial'),
        ('tack', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='tack',
            name='runner',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='tack_runner', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='tack',
            name='tacker',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tack_tacker', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='populartack',
            name='group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='group.group'),
        ),
        migrations.AddField(
            model_name='populartack',
            name='tacker',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='offer',
            name='runner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='offer',
            name='tack',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tack.tack'),
        ),
        migrations.AddConstraint(
            model_name='offer',
            constraint=models.UniqueConstraint(condition=models.Q(('is_active', True)), fields=('tack', 'runner'), name='unique_runner_for_tack'),
        ),
    ]
