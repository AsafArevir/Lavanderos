# Generated by Django 5.0.2 on 2024-03-22 02:26

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pos', '0002_cliente'),
    ]

    operations = [
        migrations.CreateModel(
            name='Encargo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha_encargo', models.DateField()),
                ('fecha_entrega', models.DateField()),
                ('estado', models.CharField(choices=[('ENCARGO', 'Encargo'), ('EN_PROCESO', 'En proceso'), ('COMPLETADO', 'Completado')], default='ENCARGO', max_length=20)),
                ('costo', models.DecimalField(decimal_places=2, max_digits=10)),
                ('pagado', models.BooleanField(default=False)),
                ('adeudo', models.DecimalField(decimal_places=2, max_digits=10)),
                ('cliente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pos.cliente')),
            ],
        ),
    ]