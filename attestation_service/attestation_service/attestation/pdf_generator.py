import io
import uuid
import qrcode
import logging
from django.conf import settings
from django.utils import timezone
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, Image, HRFlowable
)

logger = logging.getLogger(__name__)

LABELS_TYPE = {
    'inscription' : "ATTESTATION D'INSCRIPTION",
    'passage'     : 'ATTESTATION DE PASSAGE',
    'reussite'    : 'ATTESTATION DE RÉUSSITE',
    'releve_notes': 'RELEVÉ DE NOTES',
    'scolarite'   : 'CERTIFICAT DE SCOLARITÉ',
}


def generer_qr_code(code_verification):
    """Génère un QR code pointant vers le portail de vérification."""
    url = (
        f"{settings.PORTAIL_URL}"
        f"/verifier/{code_verification}"
    )
    qr = qrcode.QRCode(
        version           = 1,
        error_correction  = qrcode.constants.ERROR_CORRECT_H,
        box_size          = 6,
        border            = 2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img     = qr.make_image(fill_color='black', back_color='white')
    buf     = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf


def generer_pdf_attestation(demande, attestation, profil_etudiant=None):
    """
    Génère le PDF officiel de l'attestation.
    Retourne un buffer BytesIO contenant le PDF.

    profil_etudiant : dict optionnel avec nom, prenom, matricule, etc.
    """
    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize     = A4,
            topMargin    = 2.5 * cm,
            bottomMargin = 2.5 * cm,
            leftMargin   = 3 * cm,
            rightMargin  = 3 * cm,
        )

        styles   = getSampleStyleSheet()
        elements = []

        # ── Styles personnalisés ──────────────────────────
        s_entete = ParagraphStyle(
            'entete',
            parent    = styles['Normal'],
            fontSize  = 10,
            alignment = TA_CENTER,
            leading   = 14,
        )
        s_titre = ParagraphStyle(
            'titre_doc',
            parent    = styles['Title'],
            fontSize  = 15,
            alignment = TA_CENTER,
            spaceAfter= 8,
            textColor = colors.HexColor('#1a4a7a'),
        )
        s_corps = ParagraphStyle(
            'corps',
            parent    = styles['Normal'],
            fontSize  = 11,
            alignment = TA_JUSTIFY,
            leading   = 18,
            spaceAfter= 6,
        )
        s_ref = ParagraphStyle(
            'reference',
            parent    = styles['Normal'],
            fontSize  = 9,
            alignment = TA_CENTER,
            textColor = colors.grey,
        )
        s_bold = ParagraphStyle(
            'bold',
            parent     = styles['Normal'],
            fontSize   = 11,
            alignment  = TA_JUSTIFY,
            leading    = 18,
            fontName   = 'Helvetica-Bold',
            spaceAfter = 6,
        )

        # ── En-tête institutionnel ────────────────────────
        elements.append(Paragraph(
            "RÉPUBLIQUE DU SÉNÉGAL",
            s_entete
        ))
        elements.append(Paragraph(
            "<b>Un Peuple — Un But — Une Foi</b>",
            s_entete
        ))
        elements.append(Spacer(1, 0.3 * cm))
        elements.append(Paragraph(
            "<b>UNIVERSITÉ ALIOUNE DIOP DE BAMBEY (UADB)</b>",
            s_entete
        ))
        elements.append(Paragraph(
            "Service de la Scolarité Centrale",
            s_entete
        ))
        elements.append(Spacer(1, 0.3 * cm))

        elements.append(HRFlowable(
            width='100%', thickness=2,
            color=colors.HexColor('#1a4a7a')
        ))
        elements.append(Spacer(1, 0.5 * cm))

        # ── Titre du document ─────────────────────────────
        titre = LABELS_TYPE.get(
            demande.type_attestation,
            "ATTESTATION ADMINISTRATIVE"
        )
        elements.append(Paragraph(titre, s_titre))
        elements.append(Paragraph(
            f"N° {attestation.numero_ordre}",
            s_ref
        ))
        elements.append(Spacer(1, 0.8 * cm))

        # ── Corps du document ─────────────────────────────
        elements.append(Paragraph(
            "Le Recteur de l'Université Alioune Diop de Bambey,",
            s_corps
        ))
        elements.append(Spacer(1, 0.3 * cm))
        elements.append(Paragraph("Certifie que :", s_corps))
        elements.append(Spacer(1, 0.3 * cm))

        # Informations de l'étudiant
        if profil_etudiant:
            etudiant_info = profil_etudiant.get('etudiant', {})
            nom    = etudiant_info.get('nom', '').upper()
            prenom = etudiant_info.get('prenom', '')
            mat    = etudiant_info.get('matricule', 'Non attribué')
        else:
            nom    = f"ÉTUDIANT N°{demande.etudiant_id}"
            prenom = ''
            mat    = 'N/A'

        elements.append(Paragraph(
            f"M./Mme <b>{prenom} {nom}</b>",
            s_corps
        ))
        elements.append(Paragraph(
            f"Matricule : <b>{mat}</b>",
            s_corps
        ))

        # Corps selon le type d'attestation
        annee = demande.annee_universitaire or 'N/A'

        if demande.type_attestation == 'inscription':
            elements.append(Paragraph(
                f"est régulièrement inscrit(e) à l'Université Alioune Diop "
                f"de Bambey pour l'année universitaire "
                f"<b>{annee}</b>.",
                s_corps
            ))

        elif demande.type_attestation == 'scolarite':
            elements.append(Paragraph(
                f"est étudiant(e) régulier(ère) à l'Université Alioune Diop "
                f"de Bambey pour l'année universitaire <b>{annee}</b> "
                f"et remplit toutes les conditions de scolarité requises.",
                s_corps
            ))

        elif demande.type_attestation == 'passage':
            elements.append(Paragraph(
                f"a été admis(e) en classe supérieure à l'issue de "
                f"l'année universitaire <b>{annee}</b> "
                f"conformément aux décisions du jury de délibération.",
                s_corps
            ))

        elif demande.type_attestation == 'reussite':
            elements.append(Paragraph(
                f"a satisfait aux épreuves de l'année universitaire "
                f"<b>{annee}</b> et a obtenu la décision "
                f"<b>ADMIS(E)</b> du jury de délibération.",
                s_corps
            ))

        elif demande.type_attestation == 'releve_notes':
            elements.append(Paragraph(
                f"Le présent document constitue un relevé de notes officiel "
                f"pour l'année universitaire <b>{annee}</b>.",
                s_corps
            ))

        elements.append(Spacer(1, 0.5 * cm))
        elements.append(Paragraph(
            "La présente attestation est délivrée à l'intéressé(e) "
            "pour servir et valoir ce que de droit.",
            s_corps
        ))
        elements.append(Spacer(1, 0.8 * cm))

        # ── Date et lieu ──────────────────────────────────
        date_gen = timezone.now().strftime('%d/%m/%Y')
        elements.append(Paragraph(
            f"Bambey, le {date_gen}",
            ParagraphStyle(
                'date', parent=styles['Normal'],
                fontSize=11, alignment=TA_LEFT
            )
        ))
        elements.append(Spacer(1, 1 * cm))

        # ── Signature + QR code (côte à côte) ────────────
        qr_buf = generer_qr_code(str(attestation.code_verification))
        qr_img = Image(qr_buf, width=3 * cm, height=3 * cm)

        sig_data = [[
            Paragraph(
                "<b>Le Recteur</b><br/><br/><br/><br/>"
                "Signature et cachet",
                ParagraphStyle(
                    'sig', parent=styles['Normal'],
                    fontSize=10, alignment=TA_CENTER
                )
            ),
            qr_img,
        ]]
        sig_table = Table(
            sig_data,
            colWidths=[9 * cm, 5 * cm]
        )
        sig_table.setStyle(TableStyle([
            ('ALIGN',      (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN',     (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(sig_table)

        elements.append(Spacer(1, 0.5 * cm))
        elements.append(HRFlowable(
            width='100%', thickness=0.5,
            color=colors.grey
        ))
        elements.append(Spacer(1, 0.2 * cm))

        # ── Pied de page ──────────────────────────────────
        elements.append(Paragraph(
            f"Document généré électroniquement — "
            f"Code de vérification : "
            f"<b>{str(attestation.code_verification)[:16].upper()}</b> — "
            f"Vérifiez l'authenticité sur : "
            f"{settings.PORTAIL_URL}/verifier/",
            s_ref
        ))

        doc.build(elements)
        buffer.seek(0)
        return buffer

    except Exception as e:
        logger.error(f"Erreur génération PDF attestation : {e}")
        return None


def generer_pdf_releve_notes(
    demande,
    attestation,
    notes_data,
    profil_etudiant=None,
    resultat_data=None,
):
    """
    Génère un relevé de notes détaillé avec tableau des UEs.
    notes_data : liste de dict {code_ue, libelle_ue, valeur, credit, mention}
    resultat_data : dict optionnel (moyenne_annuelle, decision, mention, ...)
    """
    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize     = A4,
            topMargin    = 2.5 * cm,
            bottomMargin = 2.5 * cm,
            leftMargin   = 2 * cm,
            rightMargin  = 2 * cm,
        )

        styles   = getSampleStyleSheet()
        elements = []

        s_entete = ParagraphStyle(
            'entete', parent=styles['Normal'],
            fontSize=10, alignment=TA_CENTER, leading=14
        )
        s_titre = ParagraphStyle(
            'titre_doc', parent=styles['Title'],
            fontSize=13, alignment=TA_CENTER, spaceAfter=8,
            textColor=colors.HexColor('#1a4a7a')
        )

        # En-tête
        elements.append(Paragraph(
            "UNIVERSITÉ ALIOUNE DIOP DE BAMBEY",
            s_entete
        ))
        elements.append(Paragraph(
            "Service de la Scolarité — Relevé de Notes Officiel",
            s_entete
        ))
        elements.append(Spacer(1, 0.3 * cm))
        elements.append(HRFlowable(
            width='100%', thickness=2,
            color=colors.HexColor('#1a4a7a')
        ))
        elements.append(Spacer(1, 0.3 * cm))
        elements.append(Paragraph("RELEVÉ DE NOTES", s_titre))
        elements.append(Paragraph(
            f"N° {attestation.numero_ordre}", ParagraphStyle(
                'ref', parent=styles['Normal'],
                fontSize=9, alignment=TA_CENTER,
                textColor=colors.grey
            )
        ))
        elements.append(Spacer(1, 0.5 * cm))

        # Infos étudiant
        if profil_etudiant:
            e   = profil_etudiant.get('etudiant', {})
            nom = f"{e.get('prenom','')} {e.get('nom','').upper()}"
            mat = e.get('matricule', 'N/A')
        else:
            nom = f"Étudiant N°{demande.etudiant_id}"
            mat = 'N/A'

        info_data = [
            ['Nom et Prénom', nom],
            ['Matricule',     mat],
            ['Année univ.',   demande.annee_universitaire or 'N/A'],
        ]
        info_table = Table(info_data, colWidths=[5 * cm, 11 * cm])
        info_table.setStyle(TableStyle([
            ('FONTNAME',     (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE',     (0, 0), (-1, -1), 10),
            ('ROWBACKGROUNDS',(0, 0),(-1,-1),
             [colors.HexColor('#f0f4f8'), colors.white]),
            ('GRID',         (0, 0), (-1, -1), 0.3, colors.grey),
            ('TOPPADDING',   (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING',(0, 0), (-1, -1), 4),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 0.5 * cm))

        # Tableau des notes
        if notes_data:
            en_tete = [
                'Code UE', 'Intitulé', 'Crédits', 'Note /20', 'Résultat'
            ]
            data = [en_tete]
            for n in notes_data:
                valeur  = n.get('valeur')
                val_str = f"{float(valeur):.2f}" if valeur else 'ABS'
                res     = 'Validé' if (valeur and float(valeur) >= 10) else 'Non validé'
                data.append([
                    n.get('code_ue', '-'),
                    n.get('libelle_ue', '-'),
                    str(n.get('credit', 3)),
                    val_str,
                    res,
                ])
            notes_table = Table(
                data,
                colWidths=[2.5*cm, 8*cm, 2*cm, 2.5*cm, 2.5*cm],
                repeatRows=1
            )
            notes_table.setStyle(TableStyle([
                ('BACKGROUND',   (0, 0), (-1, 0), colors.HexColor('#1a4a7a')),
                ('TEXTCOLOR',    (0, 0), (-1, 0), colors.white),
                ('FONTNAME',     (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE',     (0, 0), (-1, 0), 9),
                ('ALIGN',        (0, 0), (-1, 0), 'CENTER'),
                ('FONTSIZE',     (0, 1), (-1, -1), 9),
                ('ALIGN',        (2, 1), (-1, -1), 'CENTER'),
                ('ROWBACKGROUNDS',(0, 1),(-1,-1),
                 [colors.white, colors.HexColor('#f7f9fc')]),
                ('GRID',         (0, 0), (-1, -1), 0.3, colors.grey),
                ('TOPPADDING',   (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING',(0, 0), (-1, -1), 4),
            ]))
            elements.append(notes_table)

        # Synthèse académique
        moyenne = None
        decision = ''
        mention = ''
        if resultat_data:
            moyenne = resultat_data.get('moyenne_annuelle')
            decision = resultat_data.get('decision', '')
            mention = resultat_data.get('mention', '')

        moyenne_str = (
            f"{float(moyenne):.2f}/20"
            if moyenne not in (None, '') else 'N/A'
        )
        decision_str = decision if decision else 'N/A'
        mention_str = mention if mention else 'Sans mention'

        elements.append(Spacer(1, 0.5 * cm))
        synthese_data = [
            ['Moyenne générale', moyenne_str],
            ['Décision', decision_str],
            ['Mention', mention_str],
        ]
        synthese_table = Table(synthese_data, colWidths=[5 * cm, 11 * cm])
        synthese_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1),
             [colors.HexColor('#eef3f9'), colors.white]),
            ('GRID', (0, 0), (-1, -1), 0.3, colors.grey),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(synthese_table)

        elements.append(Spacer(1, 1 * cm))
        date_gen = timezone.now().strftime('%d/%m/%Y')
        elements.append(Paragraph(
            f"Bambey, le {date_gen}",
            ParagraphStyle(
                'date', parent=styles['Normal'],
                fontSize=10, alignment=TA_LEFT
            )
        ))
        elements.append(Spacer(1, 0.8 * cm))

        # Signature + QR
        qr_buf = generer_qr_code(str(attestation.code_verification))
        qr_img = Image(qr_buf, width=3 * cm, height=3 * cm)
        sig_data = [[
            Paragraph(
                "<b>Le Chef de la Scolarité</b><br/><br/><br/>Signature",
                ParagraphStyle(
                    'sig', parent=styles['Normal'],
                    fontSize=10, alignment=TA_CENTER
                )
            ),
            qr_img,
        ]]
        sig_table = Table(sig_data, colWidths=[10 * cm, 5 * cm])
        sig_table.setStyle(TableStyle([
            ('ALIGN',  (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(sig_table)

        doc.build(elements)
        buffer.seek(0)
        return buffer

    except Exception as e:
        logger.error(f"Erreur génération relevé de notes : {e}")
        return None
