from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inscription', '0002_alter_etapeworkflow_delai_max_heures_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inscription',
            name='numero_matricule',
            field=models.CharField(
                max_length=30,
                null=True,
                blank=True,
                help_text='Attribué après validation complète',
            ),
        ),
    ]
