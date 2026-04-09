import io
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle,
    Paragraph, Spacer
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import logging

logger = logging.getLogger(__name__)


def generer_pv_deliberation(deliberation):
    """
    Génère le PV de délibération en PDF.
    Retourne un buffer BytesIO contenant le PDF.
    """
    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize    = landscape(A4),
            topMargin   = 2 * cm,
            bottomMargin= 2 * cm,
            leftMargin  = 1.5 * cm,
            rightMargin = 1.5 * cm,
        )

        styles   = getSampleStyleSheet()
        elements = []

        # ── En-tête ───────────────────────────────────────
        style_titre = ParagraphStyle(
            'titre',
            parent    = styles['Title'],
            fontSize  = 14,
            alignment = TA_CENTER,
            spaceAfter= 6,
        )
        style_sous  = ParagraphStyle(
            'sous_titre',
            parent    = styles['Normal'],
            fontSize  = 11,
            alignment = TA_CENTER,
            spaceAfter= 4,
        )

        elements.append(Paragraph(
            "UNIVERSITÉ ALIOUNE DIOP DE BAMBEY",
            style_titre
        ))
        elements.append(Paragraph(
            "PROCÈS-VERBAL DE DÉLIBÉRATION",
            style_titre
        ))
        elements.append(Spacer(1, 0.3 * cm))
        elements.append(Paragraph(
            f"Session : {deliberation.get_session_display()} | "
            f"Semestre S{deliberation.semestre} | "
            f"Année : {deliberation.annee_universitaire} | "
            f"Niveau : {deliberation.niveau}",
            style_sous
        ))
        if deliberation.date_deliberation:
            elements.append(Paragraph(
                f"Date de délibération : "
                f"{deliberation.date_deliberation.strftime('%d/%m/%Y')}",
                style_sous
            ))
        elements.append(Spacer(1, 0.5 * cm))

        # ── Tableau des résultats ─────────────────────────
        resultats = deliberation.resultats.all().order_by('rang', 'etudiant_id')

        if not resultats.exists():
            elements.append(Paragraph(
                "Aucun résultat enregistré.",
                styles['Normal']
            ))
        else:
            # En-tête du tableau
            en_tete = [
                'N°', 'ID Étudiant', 'Moy. Annuelle',
                'Crédits', 'Décision', 'Mention', 'Obs.'
            ]
            data = [en_tete]

            for i, r in enumerate(resultats, start=1):
                moy = (
                    f"{float(r.moyenne_annuelle):.2f}/20"
                    if r.moyenne_annuelle else '-'
                )
                data.append([
                    str(i),
                    str(r.etudiant_id),
                    moy,
                    f"{r.credits_valides}/{r.credits_total}",
                    r.get_decision_display(),
                    r.get_mention_display() if r.mention else '-',
                    r.observation[:30] if r.observation else '',
                ])

            col_widths = [
                1.2*cm, 2.5*cm, 3.5*cm,
                2.5*cm, 3.5*cm, 3.5*cm, 5*cm
            ]
            table = Table(data, colWidths=col_widths, repeatRows=1)
            table.setStyle(TableStyle([
                # En-tête
                ('BACKGROUND',   (0, 0), (-1, 0), colors.HexColor('#1a4a7a')),
                ('TEXTCOLOR',    (0, 0), (-1, 0), colors.white),
                ('FONTNAME',     (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE',     (0, 0), (-1, 0), 9),
                ('ALIGN',        (0, 0), (-1, 0), 'CENTER'),
                # Corps
                ('FONTSIZE',     (0, 1), (-1, -1), 8),
                ('ALIGN',        (0, 1), (-1, -1), 'CENTER'),
                ('VALIGN',       (0, 0), (-1, -1), 'MIDDLE'),
                ('ROWBACKGROUNDS',(0, 1),(-1,-1),
                    [colors.white, colors.HexColor('#f0f4f8')]),
                # Coloration selon décision
                ('GRID',         (0, 0), (-1, -1), 0.5, colors.grey),
                ('TOPPADDING',   (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING',(0, 0), (-1, -1), 4),
            ]))

            # Colorier les lignes selon la décision
            for i, r in enumerate(resultats, start=1):
                if r.decision == 'admis':
                    table.setStyle(TableStyle([
                        ('TEXTCOLOR', (4, i), (4, i),
                         colors.HexColor('#155724')),
                        ('FONTNAME',  (4, i), (4, i), 'Helvetica-Bold'),
                    ]))
                elif r.decision == 'rattrapage':
                    table.setStyle(TableStyle([
                        ('TEXTCOLOR', (4, i), (4, i),
                         colors.HexColor('#856404')),
                    ]))
                elif r.decision == 'ajourné':
                    table.setStyle(TableStyle([
                        ('TEXTCOLOR', (4, i), (4, i),
                         colors.HexColor('#721c24')),
                    ]))

            elements.append(table)
            elements.append(Spacer(1, 0.5 * cm))

            # ── Statistiques ──────────────────────────────
            total  = resultats.count()
            admis  = resultats.filter(decision='admis').count()
            ratt   = resultats.filter(decision='rattrapage').count()
            ajour  = resultats.filter(decision='ajourné').count()
            taux   = round((admis / total) * 100, 1) if total else 0

            style_stat = ParagraphStyle(
                'stat',
                parent   = styles['Normal'],
                fontSize = 9,
                spaceBefore = 2,
            )
            elements.append(Paragraph(
                f"<b>Statistiques :</b> "
                f"Total : {total} | "
                f"Admis : {admis} ({taux}%) | "
                f"Rattrapage : {ratt} | "
                f"Ajournés : {ajour}",
                style_stat
            ))

        elements.append(Spacer(1, 1 * cm))

        # ── Zone de signatures ────────────────────────────
        sig_data = [[
            "Le Président du Jury",
            "Le Chef de Département",
            "Le Responsable Pédagogique"
        ]]
        sig_table = Table(
            sig_data,
            colWidths=[9*cm, 9*cm, 9*cm]
        )
        sig_table.setStyle(TableStyle([
            ('ALIGN',      (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME',   (0,0), (-1,-1), 'Helvetica-Bold'),
            ('FONTSIZE',   (0,0), (-1,-1), 9),
            ('TOPPADDING', (0,0), (-1,-1), 20),
        ]))
        elements.append(sig_table)

        doc.build(elements)
        buffer.seek(0)
        return buffer

    except Exception as e:
        logger.error(f"Erreur génération PV : {e}")
        return None
