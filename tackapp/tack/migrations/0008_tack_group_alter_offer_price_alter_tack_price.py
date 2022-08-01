# Generated by Django 4.0.6 on 2022-07-28 13:22

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('group', '0004_groupmembers_unique_member_for_group'),
        ('tack', '0007_remove_tack_group_alter_offer_price_alter_tack_price'),
    ]

    operations = [
        migrations.AddField(
            model_name='tack',
            name='group',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='group.group'),
        ),
        migrations.AlterField(
            model_name='offer',
            name='price',
            field=models.IntegerField(null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(99999999)]),
        ),
        migrations.AlterField(
            model_name='tack',
            name='price',
            field=models.IntegerField(validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(99999999)]),
        ),
    ]