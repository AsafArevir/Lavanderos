# Generated by Django 5.1.1 on 2024-10-19 16:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pos', '0038_rename_encargo_pagosencargos_encargocompleto'),
    ]

    operations = [
        migrations.AlterField(
            model_name='activacion',
            name='lavadora',
            field=models.CharField(choices=[('Lavadora 1', 'Lavadora 1'), ('Lavadora 2', 'Lavadora 2'), ('Lavadora 3', 'Lavadora 3'), ('Lavadora 4', 'Lavadora 4'), ('Lavadora 5', 'Lavadora 5'), ('Lavadora 6', 'Lavadora 6'), ('Lavadora 8', 'Lavadora 8'), ('Lavadora 9', 'Lavadora 9'), ('Lavadora 10', 'Lavadora 10'), ('Secadora 1', 'Secadora 1'), ('Secadora 2', 'Secadora 2')], max_length=20),
        ),
    ]