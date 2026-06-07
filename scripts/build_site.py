# -*- coding: utf-8 -*-
"""Construit le site web statique (docs/) pour GitHub Pages :
- copie les figures dans docs/assets/
- exporte les séries et KPI dans docs/data.js (pour les graphiques Chart.js)."""
import os, json, shutil
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(BASE, "docs")
ASSETS = os.path.join(DOCS, "assets")
FIG = os.path.join(BASE, "reports", "figures")
PROC = os.path.join(BASE, "data", "processed")
MODELS = os.path.join(BASE, "models")
os.makedirs(ASSETS, exist_ok=True)

# 1. Copie des figures
for f in os.listdir(FIG):
    if f.lower().endswith(".png"):
        shutil.copy2(os.path.join(FIG, f), os.path.join(ASSETS, f))

# 2. Séries pour les graphiques
nat = pd.read_csv(os.path.join(PROC, "ihpc_national.csv"), parse_dates=["date"])
nat = nat.sort_values("date")
labels = nat["date"].dt.strftime("%Y-%m").tolist()

def col(c):
    return [None if pd.isna(v) else round(float(v), 2) for v in nat[c]]

fc = pd.read_csv(os.path.join(MODELS, "forecast_ihpc.csv"), parse_dates=["date"])
fc_labels = fc["date"].dt.strftime("%Y-%m").tolist()

panier = pd.read_csv(os.path.join(PROC, "panier_national.csv"), parse_dates=["date"]).sort_values("date")

# Top produits (hausse cumulée)
fp = pd.read_csv(os.path.join(PROC, "fact_prix.csv"), parse_dates=["date"])
np_ = fp.groupby(["produit", "date"])["prix_moyen"].mean().reset_index()
deb = np_.sort_values("date").groupby("produit").first()["prix_moyen"]
fin = np_.sort_values("date").groupby("produit").last()["prix_moyen"]
hausse = ((fin / deb - 1) * 100).sort_values(ascending=False).round(0)
top = hausse.head(8)

# KPI
v = nat.dropna(subset=["var_annuelle_pct"])
peak = nat.loc[nat["var_annuelle_pct"].idxmax()]
kpi = {
    "inflation_2022": 9.9,
    "pic": round(float(peak["var_annuelle_pct"]), 1),
    "pic_date": peak["date"].strftime("%b %Y"),
    "inflation_2024": 0.9,
    "hausse_panier": round((panier["cout_panier"].iloc[-1] / panier["cout_panier"].iloc[0] - 1) * 100),
    "panier_actuel": round(panier["cout_panier"].iloc[-1]),
    "forecast_moyen": round(float(fc["inflation_prevue_pct"].mean()), 1),
    "top_produit": hausse.index[0],
    "top_produit_val": int(hausse.iloc[0]),
}

data = {
    "labels": labels,
    "inflation": col("var_annuelle_pct"),
    "alim": col("var_alim_annuelle_pct"),
    "energie": col("var_energie_annuelle_pct"),
    "indice": col("indice_global"),
    "panier": [round(float(x)) for x in panier["cout_panier"]],
    "panier_labels": panier["date"].dt.strftime("%Y-%m").tolist(),
    "forecast_labels": fc_labels,
    "forecast_indice": [round(float(x), 2) for x in fc["indice_prevu"]],
    "top_products": {"labels": top.index.tolist(), "values": [int(x) for x in top.values]},
    "kpi": kpi,
}

with open(os.path.join(DOCS, "data.js"), "w", encoding="utf-8") as f:
    f.write("window.PROJECT_DATA = " + json.dumps(data, ensure_ascii=False) + ";\n")

print("Site data écrit. Figures copiées :", len(os.listdir(ASSETS)))
print("KPI :", kpi)
