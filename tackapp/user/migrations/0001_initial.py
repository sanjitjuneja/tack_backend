# Generated by Django 4.0.7 on 2022-09-02 08:34

import core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import phonenumber_field.modelfields
import user.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('group', '0002_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('username', models.CharField(default='', max_length=150, validators=[core.validators.username_validator])),
                ('password', models.CharField(max_length=128)),
                ('profile_picture', models.ImageField(blank=True, null=True, upload_to=user.models.upload_path_user_avs)),
                ('first_name', models.CharField(default='', max_length=150)),
                ('last_name', models.CharField(default='', max_length=150)),
                ('phone_number', phonenumber_field.modelfields.PhoneNumberField(max_length=128, region=None, unique=True)),
                ('birthday', models.DateField(blank=True, null=True)),
                ('tacks_rating', models.DecimalField(decimal_places=2, default=5, max_digits=3)),
                ('tacks_amount', models.PositiveIntegerField(default=0)),
                ('email', models.EmailField(default=None, max_length=254, null=True, unique=True)),
                ('active_group', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='group.group')),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'User',
                'verbose_name_plural': 'Users',
                'db_table': 'users',
            },
        ),
    ]
