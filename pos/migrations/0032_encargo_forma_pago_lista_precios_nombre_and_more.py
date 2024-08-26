# Generated by Django 5.0.7 on 2024-08-25 21:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pos', '0031_lista_precios_alter_encargo_estado'),
    ]

    operations = [
        migrations.AddField(
            model_name='encargo',
            name='forma_pago',
            field=models.CharField(choices=[('Efectivo', 'Efectivo'), ('Tarjeta', 'Tarjeta')], default='Efectivo', max_length=20),
        ),
        migrations.AddField(
            model_name='lista_precios',
            name='Nombre',
            field=models.CharField(default=1, max_length=50),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='encargo',
            name='estado',
            field=models.CharField(choices=[('ENCARGO', 'Encargo'), ('EN_PROCESO', 'En proceso'), ('COMPLETADO', 'Completado'), ('ENTREGADO', 'Entregado'), ('INCIDENTE', 'Incidente')], default='ENCARGO', max_length=20),
        ),
    ]
