# 📖 Dictionnaire des données

Modèle en étoile produit dans `data/processed/` par le notebook
`01_nettoyage_preparation.ipynb`.

## Source & nature
- **Agrégats nationaux** : calibrés sur les chiffres officiels **ANSD** et
  **Banque mondiale** (inflation annuelle, pic 2022, base 100 = 2023).
- **Détail produit / région** : **reconstruit** (cf. `scripts/generate_data.py`),
  non officiel.

---

## Dimensions

### `dim_date` (1 ligne / mois)
| Colonne | Type | Description |
|---|---|---|
| `date` | date | 1er jour du mois (clé) |
| `annee`, `mois` | entier | année, mois (1-12) |
| `mois_nom` | texte | nom du mois en français |
| `trimestre` | texte | T1…T4 |
| `annee_mois` | texte | « AAAA-MM » |

### `dim_region` (6 zones de collecte IHPC)
| Colonne | Type | Description |
|---|---|---|
| `region` | texte | ville-centre (Dakar, Thiès, Saint-Louis, Diourbel, Kaolack, Kolda) |
| `zone` | texte | zone écologique |
| `mult_prix` | décimal | multiplicateur de niveau de prix |
| `sens_infl` | décimal | sensibilité régionale à l'inflation |
| `poids_zone` | décimal | poids démographique (somme = 1) |

### `dim_division` (12 divisions COICOP / NCOA 2018)
| Colonne | Type | Description |
|---|---|---|
| `division_code` | texte | code D01…D12 |
| `division` | texte | libellé |
| `poids` | entier | pondération pour 1000 |
| `poids_frac` | décimal | pondération (somme = 1) |

### `dim_produit` (17 produits du panier)
| Colonne | Type | Description |
|---|---|---|
| `produit` | texte | nom du produit (clé) |
| `division_code` | texte | division de rattachement |
| `categorie` | texte | Alimentaire / Énergie |
| `prix_base_2023` | décimal | prix de référence 2023 (FCFA) |
| `unite` | texte | kg, litre, unité, kWh… |
| `qte_panier` | décimal | quantité mensuelle dans le panier-type |
| `administre` | booléen | prix administré (paliers) ou non |

---

## Tables de faits

### `fact_ihpc` (date × région × division)
| Colonne | Description |
|---|---|
| `indice` | IHPC de la division (base 100 = 2023) |
| `ponderation` | poids de la division (‰) |
| `var_mensuelle_pct` | variation mensuelle (%) |
| `var_annuelle_pct` | glissement annuel (%) |
| `indice_ma3` | moyenne mobile 3 mois |

### `fact_prix` (date × région × produit)
| Colonne | Description |
|---|---|
| `prix_moyen` | prix moyen (FCFA) |
| `var_mensuelle_pct` / `var_annuelle_pct` | variations |
| `prix_ma3` | moyenne mobile 3 mois |
| `prix_reel` | prix déflaté (FCFA constants 2023) |

### `ihpc_national` (1 ligne / mois)
`indice_global`, `var_mensuelle_pct`, `var_annuelle_pct`,
`indice_alimentaire`, `var_alim_annuelle_pct`,
`indice_energie`, `var_energie_annuelle_pct`,
`pouvoir_achat_index` (base 100 = 2023, ↓ quand les prix montent).

### `ihpc_regional` (date × région)
`indice_global`, `var_annuelle_pct`.

### `panier_national` / `panier_regional`
`cout_panier` (FCFA/mois), `cout_panier_reel` (déflaté).

---

## Données brutes (`data/raw/`)
Versions **volontairement imparfaites** (formats de dates mélangés, casse
incohérente, séparateur décimal virgule, valeurs manquantes, doublons, valeurs
aberrantes) servant à démontrer le **nettoyage** dans le notebook 01, plus les
tables de référence et la série nationale de validation.
