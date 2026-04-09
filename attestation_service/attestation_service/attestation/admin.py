from django.contrib import admin
from .models import DemandeAttestation, Attestation


class AttestationInline(admin.StackedInline):
    model         = Attestation
    extra         = 0
    readonly_fields = [
        'numero_ordre', 'code_verification',
        'pdf_path', 'qr_code_path',
        'date_generation', 'date_retrait'
    ]
    fields = [
        'numero_ordre', 'type_attestation',
        'statut_attestation', 'code_verification',
        'date_generation', 'date_retrait',
        'pdf_path'
    ]


@admin.register(DemandeAttestation)
class DemandeAttestationAdmin(admin.ModelAdmin):
    list_display  = [
        'id', 'etudiant_id', 'type_attestation',
        'annee_universitaire', 'statut', 'decision_ia',
        'date_demande', 'date_traitement'
    ]
    list_filter   = ['statut', 'type_attestation', 'annee_universitaire']
    search_fields = ['etudiant_id']
    readonly_fields = [
        'date_demande', 'date_traitement',
        'decision_ia', 'statut'
    ]
    inlines = [AttestationInline]


@admin.register(Attestation)
class AttestationAdmin(admin.ModelAdmin):
    list_display  = [
        'numero_ordre', 'type_attestation',
        'annee_universitaire', 'statut_attestation',
        'date_generation', 'date_retrait'
    ]
    list_filter   = ['statut_attestation', 'type_attestation']
    search_fields = ['numero_ordre', 'code_verification']
    readonly_fields = [
        'numero_ordre', 'code_verification',
        'pdf_path', 'qr_code_path',
        'date_generation', 'date_retrait'
    ]

    def has_add_permission(self, request):
        return False
