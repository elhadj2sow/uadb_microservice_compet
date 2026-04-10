from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dossier', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dossieretudiant',
            name='etudiant_id',
            field=models.IntegerField(
                help_text="ID de l'étudiant dans le service auth"
            ),
        ),
        migrations.AlterUniqueTogether(
            name='dossieretudiant',
            unique_together={('etudiant_id', 'annee_universitaire')},
        ),
    ]
