import io
import math
import uuid
import qrcode
import logging
from django.conf import settings
from django.utils import timezone
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, Image, HRFlowable
)
from reportlab.graphics.shapes import (
    Drawing, Circle, String, Group, Line, Rect, Polygon, Path, PolyLine
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


def creer_cachet_uadb(diametre_cm=5.0):
    """
    Cachet rond officiel UADB — fidèle au tampon physique :
    - « UNIVERSITE ALIOUNE DIOP » arc supérieur bien espacé
    - « DIRECTION DE LA SCOLARITE » arc inférieur bien espacé
    - « LE DIRECTEUR » centré avec étoiles et lignes
    - Rouge encre tampon, bande annulaire large et lisible
    """
    pts   = diametre_cm * cm
    cx    = cy = pts / 2
    rouge = colors.HexColor('#cc0000')

    # Bande annulaire généreuse : ~0.65cm de hauteur
    r_ext = pts / 2 - 2.5          # bord externe (laisser marge trait)
    r_int = r_ext - 18.5           # bord interne → bande ~0.65cm
    r_txt = (r_ext + r_int) / 2    # axe central des lettres

    d = Drawing(pts, pts)

    # ── Cercles ──
    d.add(Circle(cx, cy, r_ext,
                 fillColor=colors.white, strokeColor=rouge, strokeWidth=3.0))
    d.add(Circle(cx, cy, r_int,
                 fillColor=None,        strokeColor=rouge, strokeWidth=1.4))

    def _arc_texte(texte, span_deg, debut_deg, sens, fsize=8.0):
        """
        Pose chaque caractère centré sur son point d'arc.
        sens=-1 → arc supérieur (tops vers l'extérieur, lecture normale)
        sens=+1 → arc inférieur (tops vers l'intérieur, lecture normale)
        """
        n   = len(texte)
        pas = span_deg / max(n - 1, 1)
        for i, ch in enumerate(texte):
            ang    = math.radians(debut_deg + sens * i * pas)
            x      = cx + r_txt * math.cos(ang)
            y      = cy + r_txt * math.sin(ang)
            rot    = math.degrees(ang) - (90 if sens == -1 else -90)
            cr, sr = math.cos(math.radians(rot)), math.sin(math.radians(rot))
            g = Group(String(0, 0, ch,
                             fontSize=fsize, fontName='Helvetica-Bold',
                             fillColor=rouge, textAnchor='middle'))
            g.transform = (cr, sr, -sr, cr, x, y)
            d.add(g)

    # Arc supérieur : « UNIVERSITE ALIOUNE DIOP » (22 chars) sur 165°
    # debut = 90 + 165/2 = 172.5°, fin ≈ 7.5°
    _arc_texte("UNIVERSITE ALIOUNE DIOP",
               span_deg=165, debut_deg=172.5, sens=-1, fsize=8.0)

    # Arc inférieur : « DIRECTION DE LA SCOLARITE » (25 chars) sur 168°
    # debut = -90 - 168/2 = -174°, fin ≈ -6°
    _arc_texte("DIRECTION DE LA SCOLARITE",
               span_deg=168, debut_deg=-174.0, sens=+1, fsize=7.8)

    # ── Étoiles séparatrices gauche (186°) et droite (354°) ──
    for ang_deg in (186, 354):
        ang = math.radians(ang_deg)
        sx  = cx + r_txt * math.cos(ang)
        sy  = cy + r_txt * math.sin(ang)
        d.add(String(sx, sy - 3.5, '*',
                     fontSize=8, fontName='Helvetica-Bold',
                     fillColor=rouge, textAnchor='middle'))

    # ── Texte central : LE DIRECTEUR entre deux lignes ──
    lw = r_int * 0.80
    d.add(Line(cx - lw, cy + 11, cx + lw, cy + 11,
               strokeColor=rouge, strokeWidth=1.0))
    d.add(String(cx, cy + 2, 'LE DIRECTEUR',
                 fontSize=10, fontName='Helvetica-Bold',
                 fillColor=rouge, textAnchor='middle'))
    d.add(Line(cx - lw, cy - 5, cx + lw, cy - 5,
               strokeColor=rouge, strokeWidth=1.0))

    return d


def creer_signature_manuscrite(largeur_cm=3.8, hauteur_cm=1.8):
    """
    Signature cursive simulée par courbes de Bézier — style encre bleue.
    Produit une signature réaliste avec grande boucle, corps ondulant
    et trait de soulignement.
    """
    w    = largeur_cm * cm
    h    = hauteur_cm * cm
    d    = Drawing(w, h)
    bleu = colors.HexColor('#1a1a8c')

    def s(px, py):
        """Convertit coordonnées 0-100 / 0-60 vers pts réels."""
        return px * w / 100, py * h / 60

    # ── Trait 1 : grande boucle montante (lettre capitale) ──
    p1 = Path(strokeColor=bleu, strokeWidth=1.6, fillColor=None,
              strokeLineCap=1, strokeLineJoin=1)
    p1.moveTo(*s(3, 26))
    p1.curveTo(*s(1, 42), *s(9, 56), *s(17, 50))
    p1.curveTo(*s(25, 44), *s(19, 28), *s(27, 32))
    d.add(p1)

    # ── Trait 2 : corps central ondulant (lettres du milieu) ──
    p2 = Path(strokeColor=bleu, strokeWidth=1.4, fillColor=None,
              strokeLineCap=1, strokeLineJoin=1)
    p2.moveTo(*s(24, 34))
    p2.curveTo(*s(32, 42), *s(30, 20), *s(40, 28))
    p2.curveTo(*s(48, 34), *s(46, 18), *s(56, 26))
    p2.curveTo(*s(62, 32), *s(60, 44), *s(69, 36))
    p2.curveTo(*s(75, 30), *s(72, 18), *s(81, 24))
    p2.curveTo(*s(88, 30), *s(90, 40), *s(96, 32))
    d.add(p2)

    # ── Trait 3 : soulignement principal ──
    p3 = Path(strokeColor=bleu, strokeWidth=1.3, fillColor=None,
              strokeLineCap=1)
    p3.moveTo(*s(4, 13))
    p3.curveTo(*s(22, 17), *s(52, 10), *s(80, 15))
    p3.curveTo(*s(88, 17), *s(94, 13), *s(98, 11))
    d.add(p3)

    # ── Trait 4 : second soulignement léger ──
    p4 = Path(strokeColor=bleu, strokeWidth=0.7, fillColor=None,
              strokeLineCap=1)
    p4.moveTo(*s(10, 6))
    p4.curveTo(*s(28, 8), *s(58, 3), *s(84, 7))
    d.add(p4)

    return d


def _creer_icone_check():
    """
    Icône coche (✓) dessinée vectoriellement en blanc.
    Utilisée dans le bloc de signature numérique.
    """
    size = 36
    d    = Drawing(size, size)
    # Coche : segment court bas-gauche → pointe basse, puis long vers haut-droite
    d.add(PolyLine(
        [size * 0.15, size * 0.52,
         size * 0.38, size * 0.24,
         size * 0.85, size * 0.72],
        strokeColor=colors.white,
        strokeWidth=3.5,
        strokeLineCap=1,
        strokeLineJoin=1,
    ))
    return d


def creer_bloc_signature_numerique(attestation, styles):
    """
    Bloc de signature numérique professionnel.
    Bande bleue marine gauche avec icône + zone d'information bleu clair.
    """
    now            = timezone.now()
    date_signature = now.strftime('%d/%m/%Y à %H:%M:%S')
    bleu_marine    = colors.HexColor('#003580')
    bleu_clair     = colors.HexColor('#e8f0fb')
    bleu_texte     = colors.HexColor('#003580')
    vert_valide    = colors.HexColor('#1a7a3a')

    s_titre = ParagraphStyle(
        'sn_titre2', parent=styles['Normal'],
        fontSize=9.5, fontName='Helvetica-Bold',
        textColor=bleu_texte, spaceAfter=3, leading=13,
    )
    s_info = ParagraphStyle(
        'sn_info2', parent=styles['Normal'],
        fontSize=8.5, textColor=colors.HexColor('#1a1a2e'),
        leading=12, spaceAfter=1,
    )
    s_valide = ParagraphStyle(
        'sn_valide2', parent=styles['Normal'],
        fontSize=8.5, fontName='Helvetica-Bold',
        textColor=vert_valide, leading=13, spaceBefore=2,
    )

    # Colonne gauche : icône coche
    icone_drawing = _creer_icone_check()

    # Colonne droite : informations
    info_rows = [
        [Paragraph('Document signé numériquement', s_titre)],
        [Paragraph('Signé par : <b>Chef de la Scolarité</b>', s_info)],
        [Paragraph('Université Alioune Diop de Bambey (UADB)', s_info)],
        [Paragraph(f'Date de signature : {date_signature}', s_info)],
        [Paragraph('✔  Signature numérique valide', s_valide)],
    ]
    info_inner = Table(info_rows, colWidths=[11.2 * cm])
    info_inner.setStyle(TableStyle([
        ('TOPPADDING',    (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ('LEFTPADDING',   (0, 0), (-1, -1), 0),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 0),
    ]))

    bloc = Table(
        [[icone_drawing, info_inner]],
        colWidths=[1.6 * cm, 11.2 * cm],
    )
    bloc.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (0, 0), bleu_marine),
        ('BACKGROUND',    (1, 0), (1, 0), bleu_clair),
        ('BOX',           (0, 0), (-1, -1), 1.2, bleu_marine),
        ('LINEAFTER',     (0, 0), (0, 0),   0.8, bleu_marine),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN',         (0, 0), (0, 0),   'CENTER'),
        ('TOPPADDING',    (0, 0), (0, 0),   10),
        ('BOTTOMPADDING', (0, 0), (0, 0),   10),
        ('LEFTPADDING',   (0, 0), (0, 0),   4),
        ('RIGHTPADDING',  (0, 0), (0, 0),   4),
        ('TOPPADDING',    (1, 0), (1, 0),   8),
        ('BOTTOMPADDING', (1, 0), (1, 0),   8),
        ('LEFTPADDING',   (1, 0), (1, 0),   10),
        ('RIGHTPADDING',  (1, 0), (1, 0),   8),
    ]))
    return bloc


def generer_pdf_attestation(
    demande,
    attestation,
    profil_etudiant=None,
    formation_data=None,
    inscription_data=None,
):
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
        elements.append(Paragraph(
            f"Date d'émission : {timezone.now().strftime('%d/%m/%Y')}",
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

        date_naissance = 'N/A'
        if profil_etudiant:
            etudiant_info = profil_etudiant.get('etudiant', {})
            date_naissance = (
                etudiant_info.get('date_naissance')
                or etudiant_info.get('dateNaissance')
                or 'N/A'
            )

        filiere = 'N/A'
        niveau = 'N/A'
        if formation_data:
            filiere = (
                formation_data.get('specialite')
                or formation_data.get('libelle')
                or 'N/A'
            )
            niveau = formation_data.get('niveau') or 'N/A'

        annee = demande.annee_universitaire or 'N/A'
        statut_inscription = (
            (inscription_data or {}).get('statut_inscription', '')
            .replace('_', ' ')
            .title()
            or 'N/A'
        )

        info_etudiant = [
            ['Nom complet', f"{prenom} {nom}".strip()],
            ['Matricule', mat],
            ['Date naissance', str(date_naissance)],
        ]
        table_etudiant = Table(info_etudiant, colWidths=[5 * cm, 9 * cm])
        table_etudiant.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [
                colors.HexColor('#eef3f9'),
                colors.white,
            ]),
            ('GRID', (0, 0), (-1, -1), 0.3, colors.grey),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(Paragraph('<b>IDENTIFIANT DE L\'ÉTUDIANT</b>', s_corps))
        elements.append(table_etudiant)
        elements.append(Spacer(1, 0.35 * cm))

        info_academique = [
            ['Filière', filiere],
            ['Niveau', niveau],
            ['Année universitaire', annee],
            ['Statut inscription', statut_inscription],
        ]
        table_academique = Table(info_academique, colWidths=[5 * cm, 9 * cm])
        table_academique.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [
                colors.HexColor('#eef3f9'),
                colors.white,
            ]),
            ('GRID', (0, 0), (-1, -1), 0.3, colors.grey),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(Paragraph('<b>IDENTIFICATION ACADÉMIQUE</b>', s_corps))
        elements.append(table_academique)
        elements.append(Spacer(1, 0.5 * cm))

        # Corps selon le type d'attestation
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

        # ── Ligne date / titre signataire ─────────────────
        s_date_g = ParagraphStyle(
            'date_g', parent=styles['Normal'],
            fontSize=10, alignment=TA_LEFT,
        )
        s_titre_d = ParagraphStyle(
            'titre_d', parent=styles['Normal'],
            fontSize=10, alignment=TA_RIGHT,
        )
        date_gen = timezone.now().strftime('%d/%m/%Y')
        row_date = Table(
            [[Paragraph(f"Bambey, le {date_gen}", s_date_g),
              Paragraph("<b>Le Directeur de la Scolarité</b>", s_titre_d)]],
            colWidths=[7 * cm, 7 * cm],
        )
        row_date.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        elements.append(row_date)
        elements.append(Spacer(1, 0.3 * cm))

        # ── Signature manuscrite + Cachet + QR code ──────
        qr_buf    = generer_qr_code(str(attestation.code_verification))
        qr_img    = Image(qr_buf, width=3.0 * cm, height=3.0 * cm)
        cachet    = creer_cachet_uadb(5.0)
        signature = creer_signature_manuscrite(3.8, 1.8)

        s_nom_dir = ParagraphStyle(
            'nom_dir', parent=styles['Normal'],
            fontSize=9, fontName='Helvetica-Bold',
            alignment=TA_CENTER, textColor=colors.HexColor('#1a1a2e'),
        )
        nom_directeur_cell = Table(
            [[cachet], [Paragraph('M. AZIZ DIOUF', s_nom_dir)]],
            colWidths=[5.0 * cm],
        )
        nom_directeur_cell.setStyle(TableStyle([
            ('ALIGN',        (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING',   (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING',(0, 0), (-1, -1), 1),
        ]))

        row_stamp = Table(
            [[signature, nom_directeur_cell, qr_img]],
            colWidths=[4.5 * cm, 5.0 * cm, 4.5 * cm],
        )
        row_stamp.setStyle(TableStyle([
            ('VALIGN',       (0, 0), (-1, -1), 'BOTTOM'),
            ('ALIGN',        (0, 0), (-1, -1), 'CENTER'),
            ('LEFTPADDING',  (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING',   (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING',(0, 0), (-1, -1), 0),
        ]))
        elements.append(row_stamp)
        elements.append(Spacer(1, 0.5 * cm))

        # ── Bloc signature numérique ──────────────────────
        bloc_sig = creer_bloc_signature_numerique(attestation, styles)
        elements.append(bloc_sig)

        elements.append(Spacer(1, 0.4 * cm))
        elements.append(HRFlowable(
            width='100%', thickness=0.5,
            color=colors.grey
        ))
        elements.append(Spacer(1, 0.2 * cm))

        # ── Pied de page ──────────────────────────────────
        elements.append(Paragraph(
            "Ce document n'a pas \xe9t\xe9 modifi\xe9 depuis sa signature. "
            "Vous pouvez v\xe9rifier cette attestation en scannant le QR code "
            f"ou en visitant : {settings.PORTAIL_URL}/verifier/",
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
    formation_data=None,
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
        elements.append(Paragraph(
            f"Date d'émission : {timezone.now().strftime('%d/%m/%Y')}",
            ParagraphStyle(
                'ref_date', parent=styles['Normal'],
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

        filiere = 'N/A'
        niveau = 'N/A'
        if formation_data:
            filiere = (
                formation_data.get('specialite')
                or formation_data.get('libelle')
                or 'N/A'
            )
            niveau = formation_data.get('niveau') or 'N/A'
        elif resultat_data:
            niveau = resultat_data.get('niveau') or 'N/A'

        semestres = sorted({
            str(n.get('semestre')) for n in (notes_data or []) if n.get('semestre')
        })
        semestre_label = (
            ' + '.join(f"S{s}" for s in semestres)
            if semestres else 'Annuel'
        )

        info_data = [
            ['Nom et Prénom', nom],
            ['Matricule',     mat],
            ['Filière',       filiere],
            ['Niveau',        niveau],
            ['Année univ.',   demande.annee_universitaire or 'N/A'],
            ['Semestre',      semestre_label],
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

        # ── Ligne date / titre signataire ─────────────────
        date_gen = timezone.now().strftime('%d/%m/%Y')
        s_dg = ParagraphStyle('dg_rn', parent=styles['Normal'],
                              fontSize=10, alignment=TA_LEFT)
        s_dr = ParagraphStyle('dr_rn', parent=styles['Normal'],
                              fontSize=10, alignment=TA_RIGHT)
        row_date_rn = Table(
            [[Paragraph(f"Bambey, le {date_gen}", s_dg),
              Paragraph("<b>Le Chef de la Scolart\xe9</b>", s_dr)]],
            colWidths=[7 * cm, 9 * cm],
        )
        row_date_rn.setStyle(TableStyle([
            ('VALIGN',       (0, 0), (-1, -1), 'BOTTOM'),
            ('TOPPADDING',   (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING',(0, 0), (-1, -1), 0),
        ]))
        elements.append(row_date_rn)
        elements.append(Spacer(1, 0.3 * cm))

        # ── Signature manuscrite + Cachet + QR code ──────
        qr_buf    = generer_qr_code(str(attestation.code_verification))
        qr_img    = Image(qr_buf, width=3.0 * cm, height=3.0 * cm)
        cachet    = creer_cachet_uadb(3.6)
        signature = creer_signature_manuscrite(3.8, 1.8)

        row_stamp_rn = Table(
            [[Paragraph(''), signature, cachet, qr_img]],
            colWidths=[3.0 * cm, 4.0 * cm, 4.5 * cm, 4.5 * cm],
        )
        row_stamp_rn.setStyle(TableStyle([
            ('VALIGN',       (0, 0), (-1, -1), 'BOTTOM'),
            ('ALIGN',        (0, 0), (-1, -1), 'CENTER'),
            ('LEFTPADDING',  (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING',   (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING',(0, 0), (-1, -1), 0),
        ]))
        elements.append(row_stamp_rn)
        elements.append(Spacer(1, 0.5 * cm))

        # ── Bloc signature numérique ──────────────────────
        bloc_sig = creer_bloc_signature_numerique(attestation, styles)
        elements.append(bloc_sig)

        elements.append(Spacer(1, 0.4 * cm))
        elements.append(HRFlowable(width='100%', thickness=0.5, color=colors.grey))
        elements.append(Spacer(1, 0.2 * cm))
        elements.append(Paragraph(
            "Ce document n'a pas \xe9t\xe9 modifi\xe9 depuis sa signature. "
            "Vous pouvez v\xe9rifier cette attestation en scannant le QR code "
            f"ou en visitant : {settings.PORTAIL_URL}/verifier/",
            ParagraphStyle(
                'pied_rn', parent=styles['Normal'],
                fontSize=7, alignment=TA_CENTER,
                textColor=colors.grey,
            ),
        ))

        doc.build(elements)
        buffer.seek(0)
        return buffer

    except Exception as e:
        logger.error(f"Erreur génération relevé de notes : {e}")
        return None
