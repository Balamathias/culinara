# Generated by Django 5.0.7 on 2024-09-17 15:44

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('first_name', models.CharField(blank=True, max_length=30, null=True)),
                ('last_name', models.CharField(blank=True, max_length=30, null=True)),
                ('phone', models.CharField(blank=True, max_length=30, null=True)),
                ('username', models.CharField(blank=True, max_length=40, null=True, unique=True)),
                ('avatar', models.CharField(blank=True, max_length=2000, null=True)),
                ('metadata', models.JSONField(blank=True, default=dict, null=True)),
                ('joined', models.DateTimeField(auto_now_add=True)),
                ('is_active', models.BooleanField(default=False)),
                ('is_staff', models.BooleanField(default=False)),
                ('is_superuser', models.BooleanField(default=False)),
                ('otp', models.CharField(blank=True, max_length=6, null=True)),
                ('otp_created_at', models.DateTimeField(blank=True, null=True)),
                ('followers', models.ManyToManyField(blank=True, related_name='following', to=settings.AUTH_USER_MODEL)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
                ('followed_tags', models.ManyToManyField(blank=True, related_name='followed_by', to='api.tag')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(blank=True, null=True)),
                ('title', models.CharField(max_length=1000, null=True)),
                ('short_description', models.TextField(blank=True, null=True)),
                ('content', models.TextField()),
                ('thumbnail', models.JSONField(blank=True, default=dict, null=True)),
                ('video', models.CharField(blank=True, max_length=2000, null=True)),
                ('author', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='posts', to=settings.AUTH_USER_MODEL)),
                ('likes', models.ManyToManyField(blank=True, related_name='likes', to=settings.AUTH_USER_MODEL)),
                ('tags', models.ManyToManyField(blank=True, related_name='tags', to='api.tag')),
            ],
        ),
    ]
