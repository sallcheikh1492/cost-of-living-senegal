# -*- coding: utf-8 -*-
"""
generate_data.py
================
Génère le jeu de données du projet « Coût de la vie et inflation au Sénégal ».

MÉTHODOLOGIE & TRANSPARENCE
---------------------------
Les AGRÉGATS NATIONAUX (taux d'inflation annuel, pic de 2022, base 100 = 2023,
structure en divisions COICOP/NCOA, 6 zones de collecte) sont CALIBRÉS sur les
chiffres officiels publiés par l'ANSD et la Banque mondiale :

    Inflation annuelle moyenne (glissement annuel) :
        2018 ≈ 0,5 %   2019 ≈ 1,0 %   2020 ≈ 2,5 %   2021 ≈ 2,2 %
        2022 ≈ 9,7 %   (pic +14,1 % en nov. 2022)
        2023 ≈ 5,9 %   2024 ≈ 0,8 %   2025 ≈ 2,0 %   2026 ≈ 1,2 % (partiel)
    Base IHPC : 100 = année 2023 (pondérations EHCVM 2021-2022, indice de Young).

La GRANULARITÉ FINE (séries mensuelles par produit et par région) n'est PAS
publiée par l'ANSD dans un format structuré téléchargeable. Elle est donc
RECONSTRUITE ici de façon cohérente avec les agrégats officiels ci-dessus.
=> Données nationales : calibrées sur le réel.
=> Détail produit / région : simulé de façon réaliste (à ne pas citer comme
   chiffre officiel produit par produit).

Le script produit :
  data/raw/  : données « brutes » volontairement imparfaites (à nettoyer dans le
               notebook 01) + tables de référence.
  data/processed/ n'est PAS écrit ici : c'est le notebook 01 qui le produit.
"""

import os
import unicodedata
import numpy as np
import pandas as pd

RNG = np.random.default_rng(42)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
os.makedirs(RAW_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# 1. AXE TEMPS  (mensuel, janvier 2018 -> mai 2026)
# ---------------------------------------------------------------------------
DATES = pd.date_range("2018-01-01", "2026-05-01", freq="MS")
# On a aussi besoin de l'année 2017 comme amorce pour le glissement annuel.
SEED_DATES = pd.date_range("2017-01-01", "2017-12-01", freq="MS")
ALL_DATES = SEED_DATES.append(DATES)


def yearfrac(ts):
    """Fraction d'année continue, ex. juillet 2022 ~ 2022.5."""
    return ts.year + (ts.month - 1) / 12.0


# ---------------------------------------------------------------------------
# 2. COURBE D'INFLATION NATIONALE (glissement annuel mensuel)
#    Points d'ancrage calibrés sur les chiffres officiels ANSD / BM.
# ---------------------------------------------------------------------------
YOY_ANCHORS = [
    (2018.00, 0.6), (2018.50, 0.4), (2018.95, 0.6),
    (2019.00, 0.8), (2019.50, 1.1), (2019.95, 1.0),
    (2020.00, 1.6), (2020.45, 3.1), (2020.95, 2.6),
    (2021.00, 2.0), (2021.50, 2.1), (2021.95, 3.1),
    (2022.00, 4.6), (2022.35, 9.2), (2022.66, 12.4),
    (2022.83, 14.1), (2022.95, 11.4),
    (2023.00, 9.6), (2023.30, 6.6), (2023.60, 4.2), (2023.95, 2.9),
    (2024.00, 2.3), (2024.40, 0.5), (2024.70, 0.3), (2024.95, 0.6),
    (2025.00, 1.0), (2025.40, 2.0), (2025.70, 2.6), (2025.95, 2.8),
    (2026.00, 0.4), (2026.08, 0.8), (2026.16, 1.4), (2026.33, 1.0),
]
_xa = np.array([a for a, _ in YOY_ANCHORS])
_ya = np.array([b for _, b in YOY_ANCHORS])
national_yoy = {ts: float(np.interp(yearfrac(ts), _xa, _ya)) for ts in DATES}

# ---------------------------------------------------------------------------
# 3. DIVISIONS DE CONSOMMATION (COICOP / NCOA 2018) + pondérations (‰)
#    Pondérations approchées de la structure de consommation sénégalaise.
# ---------------------------------------------------------------------------
DIVISIONS = [
    # code, libellé, pondération (pour 1000), sensibilité à l'inflation, ampl. saison.
    ("D01", "Produits alimentaires et boissons non alcoolisées", 421, 1.25, 0.030),
    ("D02", "Boissons alcoolisées, tabac et stupéfiants",           9, 1.00, 0.005),
    ("D03", "Habillement et chaussures",                           62, 0.70, 0.010),
    ("D04", "Logement, eau, électricité, gaz et autres combustibles", 105, 1.15, 0.008),
    ("D05", "Meubles, articles de ménage et entretien courant",    51, 0.80, 0.006),
    ("D06", "Santé",                                               42, 0.60, 0.004),
    ("D07", "Transport",                                           92, 1.20, 0.006),
    ("D08", "Communication",                                       35, 0.30, 0.003),
    ("D09", "Loisirs et culture",                                  21, 0.60, 0.005),
    ("D10", "Enseignement",                                        43, 0.70, 0.004),
    ("D11", "Restaurants et hôtels",                               56, 1.00, 0.007),
    ("D12", "Biens et services divers",                            63, 0.80, 0.005),
]
div_df = pd.DataFrame(DIVISIONS, columns=["code", "libelle", "poids", "sens", "saison"])
div_df["poids_frac"] = div_df["poids"] / div_df["poids"].sum()

# Normalisation des sensibilités : la moyenne pondérée doit valoir 1 pour que
# l'indice global reproduise fidèlement la cible nationale d'inflation.
_w_sens = (div_df["poids_frac"] * div_df["sens"]).sum()
div_df["sens_norm"] = div_df["sens"] / _w_sens

# ---------------------------------------------------------------------------
# 4. ZONES / RÉGIONS DE COLLECTE (les 6 zones officielles de l'IHPC)
# ---------------------------------------------------------------------------
REGIONS = [
    # ville-centre, zone écologique, multiplicateur de niveau de prix, sensibilité inflation
    ("Dakar",       "Ouest",        1.060, 0.95),
    ("Thiès",       "Centre-Ouest", 1.000, 1.00),
    ("Saint-Louis", "Nord",         0.985, 1.03),
    ("Diourbel",    "Centre",       0.970, 1.05),
    ("Kaolack",     "Centre-Sud",   0.980, 1.04),
    ("Kolda",       "Sud",          1.015, 1.12),
]
reg_df = pd.DataFrame(REGIONS, columns=["region", "zone", "mult_prix", "sens_infl"])


# ---------------------------------------------------------------------------
# 5. CONSTRUCTION DES INDICES PAR DIVISION (base 100 = 2023)
# ---------------------------------------------------------------------------
def build_index(yoy_by_date, seed_level=80.0, seed_noise=0.0):
    """Reconstruit un niveau d'indice mensuel à partir d'une courbe de
    glissement annuel : niveau[t] = niveau[t-12] * (1 + yoy[t]/100)."""
    level = {}
    # Amorce 2017 : niveau quasi plat.
    for i, ts in enumerate(SEED_DATES):
        level[ts] = seed_level * (1 + seed_noise * RNG.standard_normal())
    for ts in DATES:
        prev = ts - pd.DateOffset(years=1)
        g = yoy_by_date[ts] / 100.0
        level[ts] = level[prev] * (1 + g)
    s = pd.Series(level)
    return s


def seasonal_factor(dates, amplitude):
    """Facteur saisonnier multiplicatif de moyenne 1 (pics avant Ramadan/Tabaski
    et pendant la soudure d'août-septembre)."""
    m = np.array([d.month for d in dates])
    # deux bosses : ~ramadan/tabaski (variable, approx. avril & juillet) et soudure (sep)
    f = (1
         + amplitude * np.sin((m - 3) / 12 * 2 * np.pi)
         + 0.5 * amplitude * np.cos((m - 9) / 12 * 2 * np.pi))
    f = f / f.mean()  # moyenne 1 sur l'année -> ne modifie pas la moyenne annuelle
    return pd.Series(f, index=dates)


# Indice national par division
division_index = {}   # code -> Series (index par date, sur DATES)
for _, row in div_df.iterrows():
    yoy_d = {ts: national_yoy[ts] * row["sens_norm"] for ts in DATES}
    lvl = build_index(yoy_d, seed_level=80.0)
    lvl = lvl.loc[DATES]
    # normalisation : moyenne 2023 = 100
    base = lvl[(lvl.index.year == 2023)].mean()
    lvl = lvl / base * 100.0
    # saisonnalité
    seas = seasonal_factor(DATES, row["saison"])
    lvl = lvl * seas.values
    division_index[row["code"]] = lvl

# Indice national global = somme pondérée des divisions
nat_index = sum(division_index[c] * w for c, w in
                zip(div_df["code"], div_df["poids_frac"]))
nat_index.name = "indice_global"

# ---------------------------------------------------------------------------
# 6. PRODUITS DU PANIER ESSENTIEL
# ---------------------------------------------------------------------------
# adm = prix administré (paliers discrets), sinon suit l'indice de sa division.
PRODUCTS = [
    # nom, division, categorie, prix_base_2023, unite, ampl_saison_extra, qte_panier, administre
    ("Riz brisé ordinaire",        "D01", "Alimentaire", 400,  "kg",        0.02, 30, False),
    ("Riz parfumé importé",        "D01", "Alimentaire", 525,  "kg",        0.02, 10, False),
    ("Mil (souna)",                "D01", "Alimentaire", 300,  "kg",        0.06, 8,  False),
    ("Maïs",                       "D01", "Alimentaire", 275,  "kg",        0.05, 5,  False),
    ("Huile végétale raffinée",    "D01", "Alimentaire", 1300, "litre",     0.03, 5,  False),
    ("Sucre cristallisé",          "D01", "Alimentaire", 675,  "kg",        0.02, 4,  False),
    ("Pain (baguette 190g)",       "D01", "Alimentaire", 175,  "unité",     0.00, 60, False),
    ("Farine de blé",              "D01", "Alimentaire", 500,  "kg",        0.02, 4,  False),
    ("Lait en poudre",             "D01", "Alimentaire", 3600, "kg",        0.01, 2,  False),
    ("Oignon local",               "D01", "Alimentaire", 500,  "kg",        0.18, 6,  False),
    ("Pomme de terre",             "D01", "Alimentaire", 500,  "kg",        0.15, 5,  False),
    ("Poisson frais (sardinelle)", "D01", "Alimentaire", 1200, "kg",        0.10, 8,  False),
    ("Viande de bœuf avec os",     "D01", "Alimentaire", 3200, "kg",        0.04, 4,  False),
    ("Gaz butane (6 kg)",          "D04", "Énergie",     3000, "bouteille", 0.00, 2,  True),
    ("Essence super (SP95)",       "D07", "Énergie",     890,  "litre",     0.00, 20, True),
    ("Gasoil (diesel)",            "D07", "Énergie",     775,  "litre",     0.00, 15, True),
    ("Électricité (tranche sociale)", "D04", "Énergie",  99,   "kWh",       0.00, 150, True),
]
prod_df = pd.DataFrame(PRODUCTS, columns=[
    "produit", "division_code", "categorie", "prix_base_2023",
    "unite", "saison_extra", "qte_panier", "administre"])


def administered_schedule(produit, ts):
    """Prix administrés : paliers discrets reflétant les hausses de 2022-2023."""
    y, m = ts.year, ts.month
    ym = y * 100 + m
    if produit == "Essence super (SP95)":
        if ym < 202201: return 745.0
        if ym < 202207: return 775.0
        if ym < 202303: return 890.0
        return 990.0
    if produit == "Gasoil (diesel)":
        if ym < 202201: return 645.0
        if ym < 202207: return 675.0
        if ym < 202303: return 755.0
        return 805.0
    if produit == "Gaz butane (6 kg)":
        if ym < 202201: return 2700.0
        if ym < 202301: return 2890.0
        return 3000.0
    if produit == "Électricité (tranche sociale)":
        if ym < 202301: return 91.0
        return 99.0
    return None


# ---------------------------------------------------------------------------
# 7. TABLE DE FAITS : IHPC par région et division
# ---------------------------------------------------------------------------
rows_ihpc = []
for _, r in reg_df.iterrows():
    for _, d in div_df.iterrows():
        nat = division_index[d["code"]]
        # déviation régionale autour de l'indice national + petit bruit
        reg_idx = 100 + (nat - 100) * r["sens_infl"]
        reg_idx = reg_idx * (1 + 0.0015 * RNG.standard_normal(len(reg_idx)))
        for ts, val in reg_idx.items():
            rows_ihpc.append((ts, r["region"], r["zone"], d["code"],
                              d["libelle"], d["poids"], round(float(val), 2)))
ihpc = pd.DataFrame(rows_ihpc, columns=[
    "date", "region", "zone", "division_code", "division", "ponderation", "indice"])

# ---------------------------------------------------------------------------
# 8. TABLE DE FAITS : prix moyens par produit et région
# ---------------------------------------------------------------------------
rows_price = []
for _, p in prod_df.iterrows():
    div_idx = division_index[p["division_code"]]
    for _, r in reg_df.iterrows():
        for ts in DATES:
            if p["administre"]:
                base = administered_schedule(p["produit"], ts)
                # l'énergie varie un peu selon la région (transport, distance)
                price = base * (1 + (r["mult_prix"] - 1) * 0.4)
                price *= (1 + 0.004 * RNG.standard_normal())
            else:
                idx = div_idx.loc[ts] / 100.0
                seas = 1 + p["saison_extra"] * np.sin((ts.month - 3) / 12 * 2 * np.pi)
                price = (p["prix_base_2023"] * idx * r["mult_prix"]
                         * seas * (1 + 0.02 * RNG.standard_normal()))
            rows_price.append((ts, r["region"], p["produit"], p["division_code"],
                               p["categorie"], p["unite"], round(float(price), 1)))
prices = pd.DataFrame(rows_price, columns=[
    "date", "region", "produit", "division_code", "categorie", "unite", "prix_moyen"])

# ---------------------------------------------------------------------------
# 9. INTRODUCTION DE DÉFAUTS « RÉELS » DANS LES DONNÉES BRUTES
#    (valeurs manquantes, doublons, formats de dates mélangés, valeurs aberrantes,
#     casse incohérente des régions) -> à nettoyer dans le notebook 01.
# ---------------------------------------------------------------------------
def messify(df):
    df = df.copy()
    # 9a. formats de dates mélangés
    mois_fr = {1: "Janvier", 2: "Février", 3: "Mars", 4: "Avril", 5: "Mai",
               6: "Juin", 7: "Juillet", 8: "Août", 9: "Septembre",
               10: "Octobre", 11: "Novembre", 12: "Décembre"}
    fmt_choice = RNG.integers(0, 3, len(df))
    new_dates = []
    for ts, c in zip(df["date"], fmt_choice):
        if c == 0:
            new_dates.append(ts.strftime("%Y-%m-%d"))
        elif c == 1:
            new_dates.append(ts.strftime("%d/%m/%Y"))
        else:
            new_dates.append(f"{mois_fr[ts.month]} {ts.year}")
    df["date"] = new_dates
    # 9b. casse incohérente des noms de région
    case_choice = RNG.integers(0, 3, len(df))
    df["region"] = [reg.upper() if c == 0 else (reg.lower() if c == 1 else reg + " ")
                    for reg, c in zip(df["region"], case_choice)]
    return df


prices_raw = messify(prices)
# 9c. valeurs manquantes (~3 % des prix)
mask_na = RNG.random(len(prices_raw)) < 0.03
prices_raw.loc[mask_na, "prix_moyen"] = np.nan
# 9d. quelques valeurs aberrantes (prix x10 par erreur de saisie)
mask_out = RNG.random(len(prices_raw)) < 0.004
prices_raw.loc[mask_out, "prix_moyen"] = prices_raw.loc[mask_out, "prix_moyen"] * 10
# 9e. séparateur décimal virgule sur une partie des lignes (texte)
prices_raw["prix_moyen"] = prices_raw["prix_moyen"].astype(object)
mask_comma = RNG.random(len(prices_raw)) < 0.15
idx_comma = prices_raw.index[mask_comma & prices_raw["prix_moyen"].notna()]
prices_raw.loc[idx_comma, "prix_moyen"] = (
    prices_raw.loc[idx_comma, "prix_moyen"].map(lambda v: str(v).replace(".", ",")))
# 9f. doublons (~1 %)
dups = prices_raw.sample(frac=0.01, random_state=7)
prices_raw = pd.concat([prices_raw, dups], ignore_index=True)

ihpc_raw = messify(ihpc)
mask_na2 = RNG.random(len(ihpc_raw)) < 0.02
ihpc_raw.loc[mask_na2, "indice"] = np.nan

# ---------------------------------------------------------------------------
# 10. ÉCRITURE DES FICHIERS
# ---------------------------------------------------------------------------
prices_raw.to_csv(os.path.join(RAW_DIR, "prix_produits_brut.csv"),
                  index=False, encoding="utf-8-sig")
ihpc_raw.to_csv(os.path.join(RAW_DIR, "ihpc_regions_brut.csv"),
                index=False, encoding="utf-8-sig")

# Tables de référence (propres) : dimensions
reg_df.to_csv(os.path.join(RAW_DIR, "ref_regions.csv"), index=False, encoding="utf-8-sig")
div_out = div_df[["code", "libelle", "poids", "poids_frac"]].copy()
div_out.to_csv(os.path.join(RAW_DIR, "ref_divisions.csv"), index=False, encoding="utf-8-sig")
prod_df.to_csv(os.path.join(RAW_DIR, "ref_produits.csv"), index=False, encoding="utf-8-sig")

# Série nationale officielle de référence (calibrée) pour validation
nat_out = pd.DataFrame({"date": nat_index.index, "indice_global": nat_index.values})
nat_out["var_annuelle_pct"] = (nat_out["indice_global"] /
                               nat_out["indice_global"].shift(12) - 1) * 100
nat_out.to_csv(os.path.join(RAW_DIR, "ihpc_national_reference.csv"),
               index=False, encoding="utf-8-sig")

# ---------------------------------------------------------------------------
# 11. VALIDATION : inflation annuelle moyenne reconstruite vs cibles officielles
# ---------------------------------------------------------------------------
val = nat_out.dropna(subset=["var_annuelle_pct"]).copy()
val["annee"] = pd.to_datetime(val["date"]).dt.year
recon = val.groupby("annee")["var_annuelle_pct"].mean().round(2)
cibles = {2019: 1.0, 2020: 2.5, 2021: 2.2, 2022: 9.7, 2023: 5.9,
          2024: 0.8, 2025: 2.0}
print("== Validation inflation annuelle moyenne (reconstruite vs officielle) ==")
for an, c in cibles.items():
    r = recon.get(an, float("nan"))
    print(f"  {an}: reconstruit={r:5.2f}%   officiel≈{c:4.1f}%")
print("\nFichiers écrits dans data/raw/ :")
for f in sorted(os.listdir(RAW_DIR)):
    print("  -", f)
print(f"\nLignes prix (brut) : {len(prices_raw):,} | Lignes IHPC (brut) : {len(ihpc_raw):,}")
