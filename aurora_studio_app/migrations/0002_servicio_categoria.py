from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('aurora_studio_app', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='servicio',
            name='categoria',
            field=models.CharField(
                default='General',
                help_text='Categoría del servicio (ej: Uñas, Cejas, Pestañas, Facial)',
                max_length=100,
            ),
        ),
    ]
