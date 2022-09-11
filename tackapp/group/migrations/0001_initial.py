# Generated by Django 4.0.7 on 2022-09-11 09:15

from django.db import migrations, models
import django.db.models.deletion
import group.models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Group',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_active', models.BooleanField(default=True)),
                ('creation_time', models.DateTimeField(auto_now_add=True)),
                ('name', models.CharField(max_length=100)),
                ('description', models.CharField(blank=True, max_length=256, null=True)),
                ('image', models.ImageField(blank=True, null=True, upload_to=group.models.upload_path_group_image)),
                ('is_public', models.BooleanField(default=False)),
                ('invitation_link', models.CharField(default=uuid.uuid4, max_length=36, unique=True)),
            ],
            options={
                'verbose_name': 'Group',
                'verbose_name_plural': 'Groups',
                'db_table': 'groups',
            },
        ),
        migrations.CreateModel(
            name='GroupInvitations',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'verbose_name': 'Group invitation',
                'verbose_name_plural': 'Groups invitation',
                'db_table': 'group_invitations',
            },
        ),
        migrations.CreateModel(
            name='GroupMembers',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_muted', models.BooleanField(default=False)),
                ('date_joined', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Group membership',
                'verbose_name_plural': 'Groups membership',
                'db_table': 'group_membership',
            },
        ),
        migrations.CreateModel(
            name='GroupTacks',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('group', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='group.group')),
            ],
            options={
                'verbose_name': 'Group Tack',
                'verbose_name_plural': 'Group Tacks',
                'db_table': 'group_tacks',
            },
        ),
    ]
