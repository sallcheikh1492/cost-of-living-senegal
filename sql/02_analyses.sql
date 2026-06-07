-- =====================================================================
-- Projet : Coût de la vie et inflation au Sénégal
-- Fichier : 02_analyses.sql
-- Rôle    : requêtes analytiques pour répondre aux questions métier.
-- =====================================================================
SET search_path TO cout_vie;

-- ---------------------------------------------------------------------
-- 1. INFLATION MOYENNE ANNUELLE (glissement annuel moyen, national)
-- ---------------------------------------------------------------------
SELECT  EXTRACT(YEAR FROM date) AS annee,
        ROUND(AVG(var_annuelle_pct), 2) AS inflation_moyenne_pct
FROM    ihpc_national
WHERE   var_annuelle_pct IS NOT NULL
GROUP BY 1
ORDER BY 1;

-- ---------------------------------------------------------------------
-- 2. TOP 10 DES PRODUITS À LA PLUS FORTE HAUSSE (2018 -> dernier mois)
-- ---------------------------------------------------------------------
WITH bornes AS (
    SELECT  produit,
            MIN(date) AS d_min,
            MAX(date) AS d_max
    FROM    fact_prix
    GROUP BY produit
),
prix_bornes AS (
    SELECT  b.produit,
            AVG(p_min.prix_moyen) AS prix_debut,
            AVG(p_max.prix_moyen) AS prix_fin
    FROM    bornes b
    JOIN    fact_prix p_min ON p_min.produit = b.produit AND p_min.date = b.d_min
    JOIN    fact_prix p_max ON p_max.produit = b.produit AND p_max.date = b.d_max
    GROUP BY b.produit
)
SELECT  produit,
        ROUND(prix_debut, 0)                         AS prix_2018,
        ROUND(prix_fin, 0)                           AS prix_2026,
        ROUND((prix_fin / prix_debut - 1) * 100, 1)  AS hausse_cumulee_pct
FROM    prix_bornes
ORDER BY hausse_cumulee_pct DESC
LIMIT 10;

-- ---------------------------------------------------------------------
-- 3. COMPARAISON RÉGIONALE DES PRIX (panier moyen par région, dernière année)
-- ---------------------------------------------------------------------
SELECT  region,
        ROUND(AVG(cout_panier), 0) AS cout_panier_moyen_fcfa
FROM    panier_regional
WHERE   date >= (SELECT MAX(date) FROM panier_regional) - INTERVAL '11 months'
GROUP BY region
ORDER BY cout_panier_moyen_fcfa DESC;

-- ---------------------------------------------------------------------
-- 4. PRIX MOYEN PAR ANNÉE ET PAR PRODUIT (national)
-- ---------------------------------------------------------------------
SELECT  produit,
        EXTRACT(YEAR FROM date) AS annee,
        ROUND(AVG(prix_moyen), 0) AS prix_moyen_fcfa
FROM    fact_prix
GROUP BY produit, EXTRACT(YEAR FROM date)
ORDER BY produit, annee;

-- ---------------------------------------------------------------------
-- 5. ÉVOLUTION DU COÛT DU PANIER DE BASE (national, nominal vs réel)
-- ---------------------------------------------------------------------
SELECT  EXTRACT(YEAR FROM date) AS annee,
        ROUND(AVG(cout_panier), 0)       AS cout_nominal_fcfa,
        ROUND(AVG(cout_panier_reel), 0)  AS cout_reel_fcfa_2023
FROM    panier_national
GROUP BY 1
ORDER BY 1;

-- ---------------------------------------------------------------------
-- 6. CONTRIBUTION DE CHAQUE DIVISION À L'INFLATION (dernière période, 12 mois)
--    Contribution (pts) = variation annuelle de la division × poids de la division.
-- ---------------------------------------------------------------------
WITH nat_div AS (   -- indice national par division (moyenne pondérée des régions)
    SELECT  f.date,
            f.division_code,
            f.division,
            SUM(f.indice * r.poids_zone) / SUM(r.poids_zone) AS indice_nat
    FROM    fact_ihpc f
    JOIN    dim_region r ON r.region = f.region
    GROUP BY f.date, f.division_code, f.division
),
var12 AS (
    SELECT  division_code, division,
            (MAX(indice_nat) FILTER (WHERE date = (SELECT MAX(date) FROM nat_div)) /
             MAX(indice_nat) FILTER (WHERE date = (SELECT MAX(date) FROM nat_div) - INTERVAL '12 months')
             - 1) AS var_annuelle
    FROM    nat_div
    GROUP BY division_code, division
)
SELECT  v.division,
        ROUND(v.var_annuelle * 100, 2)                 AS inflation_division_pct,
        ROUND(d.poids_frac * 100, 1)                    AS poids_pct,
        ROUND(v.var_annuelle * d.poids_frac * 100, 2)  AS contribution_points
FROM    var12 v
JOIN    dim_division d ON d.division_code = v.division_code
ORDER BY contribution_points DESC;

-- ---------------------------------------------------------------------
-- 7. INFLATION ALIMENTAIRE vs ÉNERGÉTIQUE par année (KPI)
-- ---------------------------------------------------------------------
SELECT  EXTRACT(YEAR FROM date) AS annee,
        ROUND(AVG(var_annuelle_pct), 2)         AS inflation_globale_pct,
        ROUND(AVG(var_alim_annuelle_pct), 2)    AS inflation_alimentaire_pct,
        ROUND(AVG(var_energie_annuelle_pct), 2) AS inflation_energie_pct
FROM    ihpc_national
WHERE   var_annuelle_pct IS NOT NULL
GROUP BY 1
ORDER BY 1;

-- ---------------------------------------------------------------------
-- 8. PRODUITS LES PLUS VOLATILS (écart-type de la variation mensuelle)
-- ---------------------------------------------------------------------
SELECT  produit,
        ROUND(STDDEV_SAMP(var_mensuelle_pct), 2) AS volatilite_mensuelle_pct,
        ROUND(AVG(prix_moyen), 0)                AS prix_moyen_fcfa
FROM    fact_prix
WHERE   var_mensuelle_pct IS NOT NULL
GROUP BY produit
ORDER BY volatilite_mensuelle_pct DESC
LIMIT 10;

-- ---------------------------------------------------------------------
-- 9. MOIS DE PLUS FORTE INFLATION (pic historique)
-- ---------------------------------------------------------------------
SELECT  date, ROUND(var_annuelle_pct, 1) AS inflation_glissement_annuel_pct
FROM    ihpc_national
WHERE   var_annuelle_pct IS NOT NULL
ORDER BY var_annuelle_pct DESC
LIMIT 5;

-- ---------------------------------------------------------------------
-- 10. ÉROSION DU POUVOIR D'ACHAT (indice base 100 = 2023, par année)
-- ---------------------------------------------------------------------
SELECT  EXTRACT(YEAR FROM date) AS annee,
        ROUND(AVG(pouvoir_achat_index), 1) AS pouvoir_achat_index
FROM    ihpc_national
GROUP BY 1
ORDER BY 1;
