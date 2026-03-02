from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('aurora_studio_app', '0002_servicio_categoria'),
    ]

    operations = [
        migrations.AddField(
            model_name='reserva',
            name='codigo_reserva',
            field=models.CharField(
                blank=True,
                help_text='Código único para que la clienta gestione su cita',
                max_length=20,
                null=True,
                unique=True,
            ),
        ),
    ]
