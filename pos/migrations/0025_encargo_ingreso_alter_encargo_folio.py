# Generated by Django 5.0.7 on 2024-07-31 23:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pos', '0024_remove_encargo_cliente_remove_encargo_pagado_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='encargo',
            name='ingreso',
            field=models.DecimalField(decimal_places=2, default=5, max_digits=10),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='encargo',
            name='Folio',
            field=models.CharField(max_length=30),
        ),
    ]
