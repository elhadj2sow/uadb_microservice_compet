from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inscription', '0003_alter_inscription_numero_matricule'),
    ]

    operations = [
        migrations.AlterField(
            model_name='paiement',
            name='mode_paiement',
            field=models.CharField(
                blank=True,
                choices=[
                    ('especes', 'Espèces'),
                    ('virement', 'Virement bancaire'),
                    ('orange_money', 'Orange Money'),
                    ('wave', 'Wave'),
                    ('cheque', 'Chèque'),
                    ('paytech', 'PayTech'),
                ],
                max_length=30,
            ),
        ),
        migrations.AddField(
            model_name='paiement',
            name='provider',
            field=models.CharField(
                blank=True,
                help_text='Fournisseur de paiement en ligne (ex: paytech)',
                max_length=30,
            ),
        ),
        migrations.AddField(
            model_name='paiement',
            name='transaction_id',
            field=models.CharField(
                blank=True,
                help_text='ID transaction côté fournisseur',
                max_length=120,
            ),
        ),
        migrations.AddField(
            model_name='paiement',
            name='transaction_token',
            field=models.CharField(
                blank=True,
                help_text='Token/session de paiement fournisseur',
                max_length=180,
            ),
        ),
        migrations.AddField(
            model_name='paiement',
            name='payment_url',
            field=models.TextField(
                blank=True,
                help_text='URL de redirection de paiement',
            ),
        ),
        migrations.AddField(
            model_name='paiement',
            name='statut_externe',
            field=models.CharField(
                blank=True,
                help_text='Statut brut renvoyé par le fournisseur',
                max_length=40,
            ),
        ),
        migrations.AddField(
            model_name='paiement',
            name='callback_payload',
            field=models.JSONField(
                blank=True,
                help_text='Dernier payload callback du fournisseur',
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='paiement',
            name='date_callback',
            field=models.DateTimeField(
                blank=True,
                help_text='Date du dernier callback fournisseur',
                null=True,
            ),
        ),
    ]
