# 📊 Tableau de bord Power BI — Coût de la vie et inflation au Sénégal

Ce dossier décrit comment construire le rapport Power BI à partir des données
traitées (`data/processed/`). Le fichier `.pbix` étant un binaire propriétaire,
il ne peut pas être généré par script : suivez ce guide pour le reconstruire en
~30 min, puis enregistrez `cout_vie_senegal.pbix` ici.

> Les mesures DAX prêtes à copier sont dans [`mesures_dax.txt`](mesures_dax.txt).

---

## 1. Importer les données

1. **Accueil → Obtenir les données → Dossier** → pointer sur `data/processed/`.
   (ou importer chaque CSV individuellement en *Texte/CSV*).
2. Vérifier l'encodage **65001 : Unicode (UTF-8)** pour les accents.
3. Vérifier les types : `date` → *Date*, indices/prix/variations → *Nombre décimal*.

Tables à charger :

| Table | Rôle | Granularité |
|---|---|---|
| `dim_date` | Dimension temps | 1 ligne / mois |
| `dim_region` | Dimension région (6 zones) | 1 ligne / région |
| `dim_division` | Dimension division COICOP | 1 ligne / division |
| `dim_produit` | Dimension produit | 1 ligne / produit |
| `fact_ihpc` | IHPC par région × division × mois | fait |
| `fact_prix` | Prix par produit × région × mois | fait |
| `ihpc_national` | IHPC global + sous-indices (national) | 1 ligne / mois |
| `ihpc_regional` | IHPC global par région | région × mois |
| `panier_national` / `panier_regional` | Coût du panier | mois (× région) |

---

## 2. Modèle en étoile (relations)

Créer les relations (vue *Modèle*), toutes **1 → \*** (un-vers-plusieurs),
sens de filtre simple depuis les dimensions :

```
dim_date[date]            1 → *  fact_ihpc[date]
dim_date[date]            1 → *  fact_prix[date]
dim_date[date]            1 → *  ihpc_national[date]
dim_date[date]            1 → *  ihpc_regional[date]
dim_date[date]            1 → *  panier_national[date]
dim_date[date]            1 → *  panier_regional[date]
dim_region[region]        1 → *  fact_ihpc[region]
dim_region[region]        1 → *  fact_prix[region]
dim_region[region]        1 → *  ihpc_regional[region]
dim_region[region]        1 → *  panier_regional[region]
dim_division[division_code] 1 → * fact_ihpc[division_code]
dim_division[division_code] 1 → * fact_prix[division_code]
dim_produit[produit]      1 → *  fact_prix[produit]
```

> Marquer `dim_date` comme **table de dates** (Outils de table → Marquer comme
> table de dates → colonne `date`) pour activer la Time Intelligence DAX.

---

## 3. KPI principaux (cartes)

Placer en haut du rapport, en **cartes** :

- **Taux d'inflation global** — `Inflation globale`
- **Inflation alimentaire** — `Inflation alimentaire`
- **Inflation énergie** — `Inflation énergie`
- **IHPC global** — `IHPC global`
- **Coût du panier de base** — `Cout panier`
- **Pouvoir d'achat** — `Pouvoir achat`

---

## 4. Visualisations recommandées

| Visuel | Type | Champs |
|---|---|---|
| Évolution de l'inflation 2018-2026 | Courbe + axe secondaire | Axe : `dim_date[date]` ; Valeurs : `IHPC global`, `Inflation globale` |
| Prix des produits essentiels | Courbes multiples | Axe : `date` ; Valeurs : `[prix_moyen]` ; Légende : `produit` |
| Comparaison par région | Histogramme groupé / Carte | `dim_region[region]`, `Cout panier` |
| Contribution des produits à l'inflation | Barres | `division`, `Contribution inflation` |
| Prévisions des prix futurs | Courbe avec prévision | `ihpc_national` + table `models/forecast_ihpc.csv` |
| Heatmap régionale des prix | Matrice (mise en forme cond.) | Lignes `region`, Colonnes `Année`, Valeurs `Inflation région` |

### Carte du Sénégal
- Visuel **Carte** (ou *Shape Map* / *Azure Maps*).
- Champ `dim_region[region]` (Dakar, Thiès, Saint-Louis, Diourbel, Kaolack,
  Kolda) reconnu comme localisation (catégorie de données = *Ville* / *Lieu*).
- Taille/couleur des bulles = `Cout panier` ou `Inflation région`.

---

## 5. Filtres (segments)

Ajouter en panneau latéral des **segments** sur :
- `dim_date[annee]` et `dim_date[mois_nom]`
- `dim_region[region]`
- `dim_produit[produit]`
- `dim_produit[categorie]` (Alimentaire / Énergie / …)
- `dim_division[division]`

---

## 6. Mise en page suggérée (3 pages)

1. **Vue d'ensemble** : KPI + courbe inflation + alimentaire vs énergie + jauge
   pouvoir d'achat.
2. **Produits & panier** : top produits, boxplot/volatilité, coût du panier,
   contribution à l'inflation.
3. **Régions & prévisions** : carte du Sénégal, heatmap régionale, prévision
   IHPC et panier (table `models/forecast_*.csv`).

---

## 7. Thème
Palette suggérée : bleu nuit `#1F4E79` (structure), rouge `#C0392B`
(inflation/alerte), vert `#27AE60` (alimentaire), orange `#E67E22` (énergie).
Importer via **Affichage → Thèmes → Personnaliser le thème actuel**.
