# Generated by Django 5.1.1 on 2024-10-12 16:55

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pos', '0036_producto_tipo'),
    ]

    operations = [
        migrations.AlterField(
            model_name='activacion',
            name='lavadora',
            field=models.CharField(choices=[('Lavadora 1', 'Lavadora 1'), ('Lavadora 2', 'Lavadora 2'), ('Lavadora 3', 'Lavadora 3'), ('Lavadora 4', 'Lavadora 4'), ('Lavadora 5', 'Lavadora 5'), ('Lavadora 6', 'Lavadora 6'), ('Secadora 1', 'Secadora 1'), ('Secadora 2', 'Secadora 2')], max_length=20),
        ),
        migrations.AlterField(
            model_name='encargo',
            name='forma_pago',
            field=models.CharField(choices=[('Efectivo', 'Efectivo'), ('Tarjeta', 'Tarjeta'), ('Transferencia', 'Transferencia')], default='Efectivo', max_length=20),
        ),
        migrations.CreateModel(
            name='PagosEncargos',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha', models.DateField()),
                ('pago', models.DecimalField(decimal_places=2, max_digits=10)),
                ('encargo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pos.encargo')),
            ],
        ),
    ]