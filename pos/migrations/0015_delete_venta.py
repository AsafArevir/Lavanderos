# Generated by Django 5.0.2 on 2024-04-30 13:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pos', '0014_alter_activacion_usuario_alter_encargo_usuario'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Venta',
        ),
    ]
