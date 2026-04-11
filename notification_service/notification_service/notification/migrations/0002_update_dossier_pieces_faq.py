from django.db import migrations


NOUVEAU_CONTENU_DOSSIER = (
    "Les pièces obligatoires pour votre dossier sont :\n"
    "• Baccalauréat (copie certifiée)\n"
    "• Carte Nationale d'Identité\n"
    "• Photo d'identité récente\n"
    "• Acte de naissance\n\n"
    "Formats acceptés : PDF, JPEG, PNG. Taille max : 5 Mo.\n"
    "Des pièces complémentaires peuvent être demandées selon votre formation."
)


def update_dossier_faq(apps, schema_editor):
    BaseConnaissance = apps.get_model("notification", "BaseConnaissance")

    cibles = BaseConnaissance.objects.filter(categorie="dossier", actif=True)

    for entree in cibles:
        contenu = (entree.contenu or "").lower()
        if (
            "pièces obligatoires pour votre dossier" in contenu
            or "pieces obligatoires pour votre dossier" in contenu
            or "pièces justificatives" in contenu
            or "documents dossier" in (entree.questions or "").lower()
        ):
            entree.contenu = NOUVEAU_CONTENU_DOSSIER
            entree.save(update_fields=["contenu", "date_maj"])


def reverse_update_dossier_faq(apps, schema_editor):
    # Pas de rollback automatique du contenu texte.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("notification", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(update_dossier_faq, reverse_update_dossier_faq),
    ]
