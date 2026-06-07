# -*- coding: utf-8 -*-
"""Génère reports/rapport_analytique.pdf à partir des figures et résultats."""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Image,
                                Table, TableStyle, PageBreak)
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(BASE, "reports", "figures")
OUT = os.path.join(BASE, "reports", "rapport_analytique.pdf")

NAVY = colors.HexColor("#1F4E79")
RED = colors.HexColor("#C0392B")

styles = getSampleStyleSheet()
styles.add(ParagraphStyle("Title2", parent=styles["Title"], textColor=NAVY, fontSize=24, leading=28))
styles.add(ParagraphStyle("Sub", parent=styles["Normal"], alignment=TA_CENTER, fontSize=12, textColor=colors.grey))
styles.add(ParagraphStyle("H", parent=styles["Heading2"], textColor=NAVY, spaceBefore=14))
styles.add(ParagraphStyle("Body", parent=styles["Normal"], alignment=TA_JUSTIFY, fontSize=10, leading=14))
styles.add(ParagraphStyle("Note", parent=styles["Normal"], fontSize=9, textColor=colors.HexColor("#7d6608"),
                          backColor=colors.HexColor("#FCF3CF"), borderPadding=6, leading=13))
styles.add(ParagraphStyle("Cap", parent=styles["Normal"], alignment=TA_CENTER, fontSize=8, textColor=colors.grey))

S = []


def fig(name, w=15.5):
    p = os.path.join(FIG, name)
    if os.path.exists(p):
        from PIL import Image as PILImage
        iw, ih = PILImage.open(p).size
        h = w * ih / iw
        S.append(Image(p, width=w * cm, height=h * cm))
        S.append(Spacer(1, 6))


def h(t): S.append(Paragraph(t, styles["H"]))
def p(t): S.append(Paragraph(t, styles["Body"])); S.append(Spacer(1, 4))


def table(data, widths, header_bg=NAVY):
    t = Table(data, colWidths=widths)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), header_bg),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F4F6F7")]),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    S.append(t); S.append(Spacer(1, 8))


# ---- Couverture ----
S.append(Spacer(1, 3 * cm))
S.append(Paragraph("Coût de la vie et inflation au Sénégal", styles["Title2"]))
S.append(Spacer(1, 6))
S.append(Paragraph("Rapport analytique — Business Intelligence (2018–2026)", styles["Sub"]))
S.append(Spacer(1, 1 * cm))
fig("01_inflation_nationale.png", 15)
S.append(Spacer(1, 0.5 * cm))
S.append(Paragraph("Projet portfolio Data Analyst / BI Developer", styles["Sub"]))
S.append(PageBreak())

# ---- Note méthodo ----
h("Note méthodologique sur les données")
S.append(Paragraph(
    "Ce projet combine des <b>données officielles</b> et une "
    "<b>reconstruction documentée</b>. Les agrégats nationaux (trajectoire de "
    "l'inflation, pic de 2022, base 100 = 2023, 12 divisions COICOP/NCOA, 6 zones "
    "de collecte) sont <b>calibrés sur les chiffres officiels ANSD / Banque "
    "mondiale</b>. Le détail mensuel par produit et région est <b>reconstruit</b> "
    "de façon cohérente avec ces agrégats (granularité non publiée par l'ANSD). "
    "Écart moyen &lt; 0,2 point vs inflation officielle.", styles["Note"]))
S.append(Spacer(1, 10))
table([
    ["Année", "Inflation officielle", "Reconstruite"],
    ["2019", "1,0 %", "1,0 %"], ["2020", "2,5 %", "2,6 %"], ["2021", "2,2 %", "2,3 %"],
    ["2022", "9,7 %", "9,9 %"], ["2023", "5,9 %", "5,7 %"], ["2024", "0,8 %", "0,9 %"],
    ["2025", "2,0 %", "2,0 %"],
], [4 * cm, 5 * cm, 5 * cm])

# ---- Synthèse ----
h("1. Synthèse exécutive")
p("Entre 2018 et 2026, le coût de la vie au Sénégal a connu trois régimes : "
  "<b>stabilité</b> (2018-2021, inflation &lt; 3 %), <b>choc inflationniste</b> "
  "(2022, +9,9 % en moyenne, pic +14,0 % en novembre 2022 sous l'effet des prix "
  "alimentaires et énergétiques mondiaux), puis <b>désinflation</b> (2023-2026, "
  "retour vers 1-2 %). Le coût du panier de base a augmenté de +37 % sur la "
  "période, érodant le pouvoir d'achat des ménages.")

# ---- Produits ----
h("2. Produits les plus inflationnistes")
table([
    ["Produit", "Hausse cumulée 2018→2026"],
    ["Oignon local", "+96 %"], ["Pomme de terre", "+77 %"],
    ["Poisson frais", "+62 %"], ["Mil (souna)", "+56 %"],
    ["Huile végétale", "+49 %"], ["Riz brisé ordinaire", "+46 %"],
], [9 * cm, 5 * cm])
fig("03_top_produits.png", 14)
S.append(Paragraph("Hausse cumulée des prix par produit", styles["Cap"]))
S.append(PageBreak())

h("Alimentaire vs énergie")
p("L'inflation alimentaire dépasse systématiquement l'inflation globale "
  "(12,1 % en 2022). L'énergie culmine en 2023 (10,1 %), décalée d'un an en "
  "raison des révisions tarifaires administrées (carburants, électricité).")
fig("04_alim_vs_energie.png", 14)
fig("02_heatmap_divisions.png", 15)
S.append(Paragraph("Inflation par division de consommation et par année", styles["Cap"]))
S.append(PageBreak())

# ---- Régions ----
h("3. Analyse régionale")
p("Dakar est la zone où le panier coûte le plus cher mais où l'inflation est la "
  "plus modérée ; les zones du Sud et du Centre (Kolda, Diourbel, Kaolack) "
  "subissent une inflation plus forte.")
table([
    ["Région", "Coût moyen du panier (12 derniers mois)"],
    ["Dakar", "~139 600 FCFA"], ["Kolda", "~135 000 FCFA"],
    ["Thiès", "~133 800 FCFA"], ["Saint-Louis", "~132 200 FCFA"],
    ["Kaolack", "~131 700 FCFA"], ["Diourbel", "~130 700 FCFA"],
], [7 * cm, 8 * cm])
fig("14_carte_inflation.png", 11)
S.append(Paragraph("Inflation moyenne sur 12 mois projetée sur les 14 régions administratives", styles["Cap"]))
fig("15_carte_panier.png", 11)
S.append(Paragraph("Coût moyen du panier de base par région", styles["Cap"]))

# ---- Panier / pouvoir d'achat ----
h("4. Coût du panier & pouvoir d'achat")
p("Le coût mensuel du panier de base passe d'environ 101 500 FCFA (2018) à "
  "139 300 FCFA (2026), soit +37 %. Le pouvoir d'achat s'est érodé, surtout "
  "pendant le choc 2022-2023.")
fig("09_cout_panier.png", 13)
fig("10_pouvoir_achat.png", 13)
S.append(PageBreak())

# ---- Prévisions ----
h("5. Prévisions (forecasting)")
p("Quatre approches comparées sur 12 mois de test. Le modèle SARIMA(1,1,1)"
  "(1,1,0)₁₂ est retenu (erreur la plus faible) et prévoit une inflation "
  "maîtrisée (~0,7 %) sur les 12 prochains mois.")
table([
    ["Modèle", "RMSE", "MAE", "MAPE"],
    ["SARIMA (retenu)", "0,77", "0,61", "0,60 %"],
    ["Marche aléatoire sais.", "2,02", "1,86", "1,79 %"],
    ["Régression linéaire", "3,07", "2,55", "2,49 %"],
], [6 * cm, 3 * cm, 3 * cm, 3 * cm])
p("<i>Prophet (Meta) est également intégré et comparé automatiquement lorsqu'il "
  "est exécutable (backend Stan compatible).</i>")
fig("12_forecast_ihpc.png", 14)
fig("13_forecast_panier.png", 14)
S.append(PageBreak())

# ---- Recommandations ----
h("6. Recommandations économiques")
for t in [
    "<b>Surveiller les produits volatils</b> : oignon, pomme de terre, poisson, "
    "huile — fortes hausses et saisonnalité marquée.",
    "<b>Cibler les régions du Sud/Centre</b> (Kolda, Diourbel, Kaolack) pour les "
    "politiques de soutien.",
    "<b>Sécuriser les filières stratégiques</b> (riz, huile, sucre) par le "
    "stockage et la diversification des importations.",
    "<b>Suivre mensuellement le panier de base</b> comme indicateur social de "
    "référence.",
    "<b>Anticiper les pics saisonniers</b> (Ramadan, Tabaski, soudure) par des "
    "mesures préventives d'approvisionnement.",
]:
    S.append(Paragraph("• " + t, styles["Body"])); S.append(Spacer(1, 4))

S.append(Spacer(1, 12))
S.append(Paragraph(
    "<i>Données : ANSD (calibration nationale) + reconstruction documentée. "
    "Outils : Python, SQL (PostgreSQL), Power BI.</i>", styles["Cap"]))


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.grey)
    canvas.drawString(2 * cm, 1 * cm, "Coût de la vie et inflation au Sénégal")
    canvas.drawRightString(19 * cm, 1 * cm, "Page %d" % doc.page)
    canvas.restoreState()


doc = SimpleDocTemplate(OUT, pagesize=A4, topMargin=1.5 * cm, bottomMargin=1.8 * cm,
                        leftMargin=2 * cm, rightMargin=2 * cm,
                        title="Coût de la vie et inflation au Sénégal")
doc.build(S, onFirstPage=footer, onLaterPages=footer)
print("PDF généré :", os.path.relpath(OUT, BASE))
