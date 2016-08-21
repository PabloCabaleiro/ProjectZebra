# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-08-05 16:49
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Axis',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=2)),
            ],
        ),
        migrations.CreateModel(
            name='Experiment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128)),
                ('is_atlas', models.BooleanField(default=False)),
                ('info', models.CharField(max_length=512, null=True)),
                ('front_axis', models.CharField(default='Z', max_length=1)),
                ('side_axis', models.CharField(default='X', max_length=1)),
                ('top_axis', models.CharField(default='Y', max_length=1)),
                ('owner', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Galery',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128)),
                ('total_times', models.IntegerField(default=0)),
                ('x_size', models.IntegerField(default=0)),
                ('y_size', models.IntegerField(default=0)),
                ('z_size', models.IntegerField(default=0)),
                ('experiment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tfgWeb.Experiment')),
            ],
        ),
        migrations.CreateModel(
            name='Image',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to=b'static/tfgWeb_images/')),
                ('pos', models.IntegerField(default=-1)),
                ('time', models.IntegerField(default=-1)),
                ('axis', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tfgWeb.Axis')),
            ],
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('organization', models.CharField(blank=True, default='none', max_length=20)),
                ('username', models.OneToOneField(default=None, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Zone',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128)),
                ('max_x', models.IntegerField(default=0)),
                ('min_x', models.IntegerField(default=0)),
                ('max_y', models.IntegerField(default=0)),
                ('min_y', models.IntegerField(default=0)),
                ('max_z', models.IntegerField(default=0)),
                ('min_z', models.IntegerField(default=0)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='axis',
            name='galery',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tfgWeb.Galery'),
        ),
    ]
